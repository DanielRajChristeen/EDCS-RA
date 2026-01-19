# **System Requirements**
**EDCS-RA — Hardware & Software Dependencies**

This document lists the required hardware and software components to build,
flash, and operate the EDCS-RA robotic arm system.

It defines **what is required**, not how the system behaves internally.

---

## **Hardware Requirements**

| Component | Quantity | Purpose / Notes |
|---------|----------|-----------------|
| ESP32 Dev Kit V1 | 1 per arm | Embedded actuation controller |
| Servo Motors (SG90 / MG90S or equivalent) | 4 per arm | Base, Arm, Elbow, Gripper joints |
| SMPS (Switched Mode Power Supply) | 1 | Primary power source |
| Step-down Buck Converter | 1 | Converts SMPS output to stable 5V |
| External 5V Power Lines | As required | Servo power distribution |
| Common Ground Wiring | Required | Shared ground between ESP32 and servos |
| Jumper Wires / Connectors | As required | Signal and power connections |
| USB to Micro USB Cable | 1 | ESP32 programming and debugging |
| Multimeter (Recommended) | 1 | Voltage verification |
| Robotic Arm Frame | 1 | Mechanical structure for servos |

> **Important:** Always tune and verify the buck converter output to **stable 5V before connecting the ESP32 or servo motors**.  
> Connecting an uncalibrated buck converter can permanently damage the ESP32.

---

## **Software Requirements**

| Software / Tool | Purpose |
|-----------------|---------|
| Arduino IDE | Firmware development and flashing |
| ESP32 Board Package (Espressif) | ESP32 compilation support |
| ESP32Servo Library | PWM-based servo control |
| ArduinoJson Library | JSON parsing for command input |
| WiFi Library (ESP32) | Network connectivity |
| Serial Monitor | Debug logging |
| Web Browser / HTTP Client | Sending commands and heartbeats |

---

## **ESP32 Board Package Installation (Arduino IDE)**

To compile and upload firmware to the ESP32, the official Espressif board
package must be installed in Arduino IDE.

### **Board Package URL (Reference)**

https://dl.espressif.com/dl/package_esp32_index.json

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
- `firmware/README.md` — embedded firmware behavior & safety
- `architecture.md` — system-level design

---
