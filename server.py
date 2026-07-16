import sys
import json
import asyncio
import threading
import queue
from collections import deque
import serial
import websockets

SERIAL_PORT = "COM3"
BAUD_RATE = 115200
WINDOW_SIZE = 5

data_queue = queue.Queue()
history = deque(maxlen=WINDOW_SIZE)

def read_serial():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    except Exception as e:
        print(f"Error opening serial port: {e}")
        return

    while True:
        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line:
                continue
            
            parts = line.split(',')
            if len(parts) >= 6 and parts[0] == "CSI_DATA":
                raw_str = parts[5].strip()
                if not raw_str:
                    continue
                
                raw_values = [int(x) for x in raw_str.split()]
                
                amplitudes = []
                for i in range(0, len(raw_values) - 1, 2):
                    real = raw_values[i]
                    imag = raw_values[i+1]
                    amp = (real**2 + imag**2)**0.5
                    amplitudes.append(amp)
                
                if amplitudes:
                    history.append(amplitudes)
                    
                    num_subcarriers = len(amplitudes)
                    smoothed = []
                    for col in range(num_subcarriers):
                        col_sum = sum(sample[col] for sample in history)
                        smoothed.append(col_sum / len(history))
                    
                    data_queue.put(smoothed)
        except Exception as e:
            print(f"Error reading serial: {e}")
            break

connected_clients = set()

async def register(websocket):
    connected_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)

async def broadcast():
    while True:
        await asyncio.sleep(0.01)
        while not data_queue.empty():
            try:
                data = data_queue.get_nowait()
                if connected_clients:
                    message = json.dumps(data)
                    await asyncio.gather(*(client.send(message) for client in connected_clients))
            except queue.Empty:
                break

async def main():
    serial_thread = threading.Thread(target=read_serial, daemon=True)
    serial_thread.start()
    
    async with websockets.serve(register, "localhost", 8765):
        await broadcast()

if __name__ == "__main__":
    asyncio.run(main())