# Wi-Fi CSI Sensing

This project captures Channel State Information (CSI) from an ESP32 board, forwards the data to a Python server over serial, and visualizes the live subcarrier amplitudes in a browser-based chart.

## What the project does

- The Arduino sketch runs on an ESP32 and enables CSI collection from the Wi-Fi driver.
- The Python server reads the serial stream, converts the raw CSI values into amplitudes, smooths them over a short moving window, and broadcasts them to connected web clients.
- The browser page renders the latest amplitudes as a real-time line chart using Chart.js.

## Project files

- [wifi_sensing.ino](wifi_sensing.ino): ESP32 firmware that starts CSI collection and prints data to the serial port.
- [server.py](server.py): Python WebSocket server that reads serial data and streams it to the browser.
- [index.html](index.html): Frontend page that connects to the server and displays the chart.
- [wifi_credential.h](wifi_credential.h): Wi-Fi credentials header that must be created locally for your network.

## Hardware and software requirements

- An ESP32 development board
- Arduino IDE or PlatformIO
- Python 3.9 or newer
- A USB connection to the ESP32
- A Wi-Fi network you can join

## Prepare your Wi-Fi credentials

Create a local header file named [wifi_credential.h](wifi_credential.h) with content like this:

```cpp
#ifndef WIFI_CREDENTIAL_H
#define WIFI_CREDENTIAL_H

#define SSID "your-ssid"
#define PASS "your-password"

#endif
```

> Do not commit your real Wi-Fi credentials to version control.

## Upload the firmware

1. Open [wifi_sensing.ino](wifi_sensing.ino) in the Arduino IDE.
2. Select your ESP32 board and correct COM/serial port.
3. Upload the sketch to the board.
4. Open the Serial Monitor at 115200 baud to confirm that CSI data is being emitted.

The firmware prints lines in the following shape:

```text
CSI_DATA,<timestamp>,<rssi>,<channel>,<length>,<raw-values...>
```

## Run the Python server

Install the Python dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Then start the server:

```bash
python3 server.py
```

The default server listens on `localhost:8765`. You can override the serial port and host/port with environment variables:

```bash
CSI_SERIAL_PORT=/dev/ttyUSB0 CSI_HOST=0.0.0.0 CSI_PORT=8765 python3 server.py
```

## Open the visualization

Start a simple web server from the project directory:

```bash
python3 -m http.server 8000
```

Then open:

```text
http://localhost:8000/index.html
```

If the chart does not appear, check that:

- the ESP32 is printing CSI data over serial,
- the Python server is running without errors,
- the browser can reach `ws://localhost:8765`.

## Notes

- The server currently uses a small smoothing window to reduce noise in the visualized amplitudes.
- The serial port defaults to `/dev/USB0`; on many Linux systems the device may appear as `/dev/ttyUSB0` or another similar path.
- If your setup uses a different port, set the `CSI_SERIAL_PORT` environment variable before starting the server.
