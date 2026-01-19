# **System Requirements**
**EDCS-RA — Hardware & Software Dependencies**

This document lists the required hardware and software components to build,
flash, and operate the EDCS-RA robotic arm system.

It defines **what is required**, not how the system behaves internally.

---

## **Hardware Requirements**

| Component | Quantity | Purpose / Notes |
|----------|----------|-----------------|
| ESP32 Dev Kit V1 | 1 per arm | Embedded actuation controller |
| Servo Motors (SG90 / MG90S or equivalent) | 4 per arm | Base, Arm, Elbow, Gripper joints |
| Raspberry Pi 4 Model B | 1 | Gateway, backend host, camera interface |
| microSD Card (16GB+) | 1 | Raspberry Pi OS and backend storage |
| Pi Camera / USB Camera | 1 | Live video stream source |
| SMPS (Switched Mode Power Supply) | 1 | Primary external power source |
| Step-down Buck Converter | 1 | Regulates SMPS output to stable 5V |
| Jumper Wires / Connectors | As required | Signal connections between ESP32 and servos |
| USB Cable | 1 | ESP32 programming and serial debugging |
| Multimeter (Recommended) | 1 | Voltage tuning and verification |
| Robotic Arm Frame | 1 | Mechanical structure for servos |

**Important:**

> ESP32 and servo motors share a common external 5V supply (via SMPS + buck)  
> with a shared ground reference. Servo current does **not** flow through the ESP32 board.
> Always tune and verify the buck converter output to **stable 5V before connecting the ESP32 or servo motors**.  
> Connecting an uncalibrated buck converter can permanently damage the ESP32.

---

## **Software Requirements**

### Embedded / Firmware

| Software / Tool | Purpose |
|-----------------|---------|
| Arduino IDE | Firmware development and flashing |
| ESP32 Board Package (Espressif) | ESP32 compilation support |
| ESP32Servo Library | PWM-based servo control |
| ArduinoJson Library | JSON parsing for command input |
| WiFi Library (ESP32) | Network connectivity |
| Serial Monitor | Debug logging |

---

### Gateway / Backend (Raspberry Pi 4B)

| Software / Library | Purpose |
|------------------|---------|
| Raspberry Pi OS (64-bit) | Operating system |
| Python 3.9+ | Backend runtime |
| FastAPI | REST & WebSocket control server |
| Uvicorn | ASGI server for FastAPI |
| asyncio | Asynchronous task scheduling |
| requests | HTTP communication with ESP32 |
| OpenCV (cv2) | Camera capture and video streaming |
| libcamera / V4L2 | Camera interface (Pi Camera / USB) |
| Cloudflared | Secure tunnel for external access |
| Git | Code version control |
| systemd (optional) | Backend service management |

**Backend responsibilities include:**
- Multi-client WebSocket control
- Arm ownership arbitration
- Heartbeat monitoring and watchdogs
- Command translation and dispatch to ESP32
- Camera stream serving
- Tunnel exposure for remote access

---

### Frontend (Control Dashboard)

| Technology | Purpose |
|-----------|---------|
| HTML5 | UI structure |
| CSS3 | Dashboard styling |
| JavaScript (Vanilla) | Control logic |
| WebSocket API | Real-time control communication |
| HTTP (MJPEG) | Live camera stream rendering |
| Modern Web Browser | UI execution environment |

---

### Networking & Remote Access

| Component | Purpose |
|----------|---------|
| Local Wi-Fi / LAN | ESP32 ↔ Raspberry Pi communication |
| HTTP | ESP32 command & heartbeat endpoints |
| WebSocket | Frontend ↔ backend control channel |
| Cloudflare Tunnel | Secure public access to Raspberry Pi localhost |

**Note:**
> Cloudflare Tunnel is used to expose the Raspberry Pi backend  
> (FastAPI + WebSocket + camera stream) without port forwarding or public IP.

---

## **ESP32 Board Package Installation (Arduino IDE)**

To compile and upload firmware to the ESP32, the official Espressif board
package must be installed in Arduino IDE.

### **Board Package URL (Reference)**

### **Installation Steps**

1. Open **Arduino IDE**
2. Go to **File → Preferences**
3. In **Additional Boards Manager URLs**, add:

https://dl.espressif.com/dl/package_esp32_index.json

(If multiple URLs exist, separate them with commas)
4. Click **OK**
5. Navigate to **Tools → Board → Boards Manager**
6. Search for **ESP32**
7. Install **“esp32 by Espressif Systems”**
8. Select your board from **Tools → Board**
- Example: *ESP32 Dev Module* or *ESP32 Dev Kit V1*

---

## **Calibration & Safety Reference**

| Resource | Purpose |
|--------|---------|
| ESP32 UART to Servo Control Repo | Servo testing and joint safety limit calibration |

Calibration reference repository:  
https://github.com/DanielRajChristeen/ESP32-UART-to-Servo

---

## **Scope Clarification**

This document covers **component and software requirements only**.

It does **not** include:
- Wiring diagrams
- Pin-level connections
- Firmware execution logic
- System architecture details

Refer to:
- `Firmware/README.md` — embedded firmware behavior & safety
- `architecture.md` — system-level design

---
