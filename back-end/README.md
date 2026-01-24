# Gateway Layer  
**Raspberry Pi Coordination & Routing — EDCS-RA**

---

## Overview

The Gateway layer runs on a **Raspberry Pi 4B** and acts as a **coordination and routing layer** between multiple users and multiple ESP32-based robotic arm controllers.

The Raspberry Pi **does not directly control any robotic arm**.  
All physical actuation, timing, and mechanical safety enforcement are handled **exclusively by ESP32 firmware**.

The gateway exists to:
- Coordinate multiple users
- Manage arm ownership
- Route commands to the correct ESP32
- Serve camera streams
- Provide a single secure entry point into the system

---

## System Topology (Authoritative)

```

Users (Web UI clients)
|
|  WebSocket / HTTP
|
Raspberry Pi (Gateway)

* Client coordination
* Ownership arbitration
* Camera streaming
* Command forwarding
  |
  |  HTTP JSON
  |
  ESP32-1   ESP32-2   ESP32-3   ...
  |         |         |
  Arm-1     Arm-2     Arm-3

````

**Control authority is strictly hierarchical:**

- Users generate intent
- Raspberry Pi coordinates and routes
- ESP32 executes actuation
- Arms respond only to ESP32 firmware

There is **no direct User → ESP32 communication path**.

---

## Gateway Execution Workflow

The gateway follows a continuous orchestration workflow:

**startup → client connect → ownership grant → command routing → monitoring → recovery**

At no point does the gateway perform actuation.

---

## 1. Startup & Application Lifespan

The gateway starts a FastAPI application with a managed lifespan.

On startup:
- Background watchdog tasks are spawned
- No ESP32 communication is initiated
- No state is assumed

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(heartbeat_watchdog())
    yield
````

The gateway is designed to tolerate restarts and transient failures.

---

## 2. Global State Model

The gateway maintains minimal in-memory state:

* `clients` → connected WebSocket clients
* `arm_owner` → exclusive arm ownership mapping
* `last_heartbeat` → client liveness tracking

There is **no persistent storage**.
All state is reconstructed dynamically.

---

## 3. ESP32 Node Abstraction

ESP32 nodes are treated as **stateless HTTP endpoints**.

```python
ESP32_ARMS = {
    "arm-1": {"ip": "...", "port": 80},
    "arm-2": {"ip": "...", "port": 80},
}
```

Each ESP32:

* Exposes `/heartbeat` and `/command`
* Enforces its own safety limits
* Is unaware of users, UI, or system topology

The gateway never assumes ESP32 availability or correctness.

---

## 4. Camera Streaming (View-Only)

A camera is attached to the Raspberry Pi and opened once:

```python
CAMERA = cv2.VideoCapture(0)
```

Camera characteristics:

* Shared across all users
* View-only
* Independent of arm ownership
* Not tied to actuation or safety

Stream endpoint:

```
GET /cam/{arm_id}
```

The `{arm_id}` parameter is logical, not physical.

---

## 5. WebSocket Control Channel

Clients connect to the gateway via:

```
/ws
```

Each client must identify itself using a `hello` message containing a unique `client_id`.

On connection:

* Client is registered
* Heartbeat tracking begins
* A free arm may be auto-assigned

---

## 6. Arm Ownership & Arbitration

Arm control is **exclusive**.

Rules:

* One arm → one controlling client
* Ownership is granted on first request
* Conflicts are resolved deterministically

```python
if owner != client_id:
    control_revoked
```

Ownership is released automatically when:

* Client disconnects
* Client heartbeat expires

This prevents stale or competing control.

---

## 7. Command Routing (No Actuation)

Commands received from clients are:

1. Validated for ownership
2. Translated into ESP32-compatible JSON
3. Forwarded to the correct ESP32 via HTTP

```python
for servo, angle in joints.items():
    esp_command(...)
```

Important guarantees:

* **All joint commands are forwarded**
* No joint-level logic is applied
* No safety limits are enforced here
* No PWM or timing logic exists in the gateway

The gateway **routes commands only**.

---

## 8. Heartbeat Model (Clients)

Each client must periodically send a heartbeat.

```python
HEARTBEAT_TIMEOUT = 10
```

A background watchdog:

* Detects inactive clients
* Cleans up ownership
* Frees arms automatically

This ensures system liveness during UI crashes or network drops.

---

## 9. ESP32 Communication Contract

Gateway → ESP32 communication uses:

* HTTP POST
* Short timeouts
* Stateless requests

```python
session.post(url, json=payload, timeout=HTTP_TIMEOUT)
```

Behavior:

* Fire-and-forget
* No retries during runtime
* No blocking on ESP32 response

ESP32 nodes are responsible for local recovery and safety.

---

## 10. ESP32 Health Check Utility (`test_esp.py`)

The `test_esp.py` script provides a **pre-flight connectivity check**.

Purpose:

* Verify ESP32 reachability
* Measure latency
* Detect offline nodes

Features:

* Retry logic
* Timeout enforcement
* Clear online/offline reporting

This tool is for **diagnostics only**, not runtime control.

---

## 11. Stateless & Failure-Tolerant Design

The gateway is intentionally:

* Stateless across restarts
* Resilient to client crashes
* Resilient to ESP32 downtime

Restarting the gateway:

* Disconnects all clients
* Clears ownership
* Requires clean reconnection

This behavior is **intentional and safe**.

---

## 12. Remote Access & Exposure

The gateway runs on a private network.

For external access:

* A secure tunnel (e.g., Cloudflare Tunnel) exposes the gateway
* No port forwarding or public IP is required
* ESP32 nodes remain private and unreachable externally

The gateway is the **only exposed control surface**.

---

## What the Gateway Explicitly Does NOT Do

The gateway does **not**:

* Control servos
* Generate PWM signals
* Enforce mechanical limits
* Perform motion planning
* Synchronize joint timing
* Store persistent state

These responsibilities belong to the ESP32 firmware and higher-level planning layers.

---

## Relationship to Other Layers

* **ESP32 firmware** → actuation, timing, mechanical safety
* **Gateway (this layer)** → coordination and routing
* **Frontend** → user intent and visualization
* **Tunnel** → secure remote access

System-level design is documented in `docs/architecture.md`.

---

## Closing Perspective

The Raspberry Pi gateway exists to **coordinate without controlling** and **route without interpreting**.

In EDCS-RA:

> * **The gateway coordinates control.**
> * **The ESP32 executes control.**

This separation is intentional, scalable, and safety-critical.
---
