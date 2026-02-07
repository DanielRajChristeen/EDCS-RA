# **Deployment Guide — EDCS-RA**

## **Purpose**

This document describes how to deploy and run EDCS-RA across its primary components: the embedded controller, the edge gateway, and the remote access layer. It focuses on practical execution, not architectural theory.

The deployment model assumes:

* Local hardware access to the robotic arm

* A Raspberry Pi–based gateway

* Remote access via Cloudflare Tunnel (free / quick tunnel mode)



---

## **Deployment Topology**

EDCS-RA is deployed as a three-layer system:

1. Embedded Layer (ESP32)
Responsible for direct motor control and local safety behavior.

2. Edge Gateway (Raspberry Pi)
Responsible for intent processing, arbitration, and device coordination.

3. Remote Access Layer (Cloudflare Tunnel)
Provides temporary, secure remote access to the gateway.

The frontend interacts only with the gateway and never communicates directly with the ESP32.


---

## **Pre-Deployment Assumptions**

Before deployment, the following conditions must be met:

* ESP32 firmware is compiled and flashed

* Raspberry Pi is running a supported Linux distribution

* Python runtime and required dependencies are available on the gateway

* Network access is available for outbound connections

* cloudflared is installed on the gateway


No public IP address or port forwarding is required.


---

## **Startup Order (Critical)**

Components must be started in the following order to ensure safe and predictable behavior:

1. ESP32 boots first
The embedded controller initializes in a safe, idle state and waits for gateway communication.


2. Gateway application starts
The gateway establishes local communication with the ESP32 and prepares to receive external intent.


3. Cloudflare Tunnel starts
Remote access to the gateway is enabled only after the gateway is fully operational.


4. Frontend connects
The frontend uses the generated Cloudflare URL to interact with the gateway.



This order prevents remote commands from reaching an uninitialized system.


---

## **Gateway Execution**

The gateway application is started locally on the Raspberry Pi.
A typical execution pattern is:

uvicorn app:app --host 0.0.0.0 --port 8080

The gateway listens only on the local network interface. It is not exposed directly to the internet.


---

## **Cloudflare Tunnel Execution**

Once the gateway service is running, remote access is enabled using Cloudflare quick tunnel mode:

cloudflared tunnel --url http://localhost:8080

This command:

* Creates an ephemeral tunnel

* Generates a temporary public URL

* Routes external traffic to the local gateway service


The generated URL is displayed in the terminal and is used by the frontend.


---

## **Verification Checklist**

After deployment, verify the following:

* The ESP32 is powered and responsive

* The gateway application is running without errors

* The Cloudflare Tunnel reports an active connection

* The generated URL is reachable from a remote browser

* Gateway logs show successful intent receipt

* No motion occurs unless explicitly commanded


If any step fails, remote control must not be attempted.


---

## **Shutdown Procedure**

To safely shut down the system:

1. Stop remote interaction from the frontend


2. Terminate the Cloudflare tunnel process


3. Stop the gateway application


4. Power down the ESP32 if required



This order ensures that no remote commands are in flight during shutdown.


---

## **Scope and Limitations**

This deployment guide describes the current development and demonstration setup for EDCS-RA. It does not cover:

* High-availability deployment

* Persistent public domains

* Multi-gateway orchestration

* Production-grade monitoring


These are considered future extensions and do not alter the core architecture.


---

