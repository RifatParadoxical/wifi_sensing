import asyncio
import json
import os
import queue
import threading
from collections import deque

import serial
import websockets

SERIAL_PORT = os.getenv("CSI_SERIAL_PORT", "/dev/ttyUSB0")
BAUD_RATE = int(os.getenv("CSI_BAUD_RATE", "115200"))
WINDOW_SIZE = int(os.getenv("CSI_WINDOW_SIZE", "5"))
HOST = os.getenv("CSI_HOST", "localhost")
PORT = int(os.getenv("CSI_PORT", "8765"))
BROADCAST_INTERVAL = float(os.getenv("CSI_BROADCAST_INTERVAL", "0.01"))

data_queue = queue.Queue()
history = deque(maxlen=WINDOW_SIZE)

def read_serial():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    except serial.SerialException as exc:
        print(f"Error opening serial port {SERIAL_PORT}: {exc}")
        return

    while True:
        try:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue

            parts = line.split(",")
            if len(parts) < 6 or parts[0] != "CSI_DATA":
                continue

            raw_str = parts[5].strip()
            if not raw_str:
                continue

            raw_values = []
            for value in raw_str.split():
                try:
                    raw_values.append(int(value))
                except ValueError:
                    continue

            if len(raw_values) < 2:
                continue

            amplitudes = []
            for i in range(0, len(raw_values) - 1, 2):
                real = raw_values[i]
                imag = raw_values[i + 1]
                amplitudes.append((real**2 + imag**2) ** 0.5)

            if not amplitudes:
                continue

            history.append(amplitudes)

            num_subcarriers = len(amplitudes)
            smoothed = []
            for col in range(num_subcarriers):
                col_sum = sum(sample[col] for sample in history)
                smoothed.append(col_sum / len(history))

            data_queue.put(smoothed)
        except serial.SerialException as exc:
            print(f"Serial error: {exc}")
            break
        except Exception as exc:
            print(f"Error reading serial: {exc}")
            break

connected_clients = set()


async def register(websocket):
    connected_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.discard(websocket)


async def broadcast():
    while True:
        await asyncio.sleep(BROADCAST_INTERVAL)
        while not data_queue.empty():
            try:
                data = data_queue.get_nowait()
            except queue.Empty:
                break

            if connected_clients:
                message = json.dumps(data)
                await asyncio.gather(*(client.send(message) for client in connected_clients))


async def main():
    serial_thread = threading.Thread(target=read_serial, daemon=True)
    serial_thread.start()

    async with websockets.serve(register, HOST, PORT):
        print(f"WebSocket server listening on ws://{HOST}:{PORT}")
        await broadcast()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopping server...")