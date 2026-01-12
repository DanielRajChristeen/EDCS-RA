from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import asyncio
import json
import time
import cv2
import requests

# ============================================================
# CONFIG (MATCHES test_esp.py)
# ============================================================

ARMS = ["arm-1", "arm-2"]
HEARTBEAT_TIMEOUT = 10

HTTP_TIMEOUT = 1.0
SESSION_ID = int(time.time())  # same pattern as test_esp.py

ESP32_ARMS = {
    "arm-1": {"ip": "10.106.120.123", "port": 80},
    "arm-2": {"ip": "10.106.120.150", "port": 80},
}

# ============================================================
# GLOBAL STATE
# ============================================================

clients = {}          # client_id -> websocket
arm_owner = {}        # arm_id -> client_id
last_heartbeat = {}   # client_id -> timestamp

session = requests.Session()

# ============================================================
# FASTAPI LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Backend starting")
    asyncio.create_task(heartbeat_watchdog())
    yield
    print("🛑 Backend shutting down")

app = FastAPI(lifespan=lifespan)

# ============================================================
# CAMERA (VIEW-ONLY, SHARED)
# ============================================================

CAMERA = cv2.VideoCapture(0, cv2.CAP_DSHOW)

def camera_stream():
    while True:
        ok, frame = CAMERA.read()
        if not ok:
            time.sleep(0.05)
            continue

        _, jpeg = cv2.imencode(".jpg", frame)
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            jpeg.tobytes() + b"\r\n"
        )

@app.get("/cam/{arm_id}")
def cam_feed(arm_id: str):
    return StreamingResponse(
        camera_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

# ============================================================
# ESP COMMUNICATION (IDENTICAL TO test_esp.py)
# ============================================================

def esp_url(arm_id: str, path: str) -> str:
    cfg = ESP32_ARMS[arm_id]
    return f"http://{cfg['ip']}:{cfg['port']}{path}"

def esp_heartbeat(arm_id: str):
    url = esp_url(arm_id, "/heartbeat")
    payload = {"session_id": SESSION_ID}
    session.post(url, json=payload, timeout=HTTP_TIMEOUT)

def esp_command(arm_id: str, payload: dict):
    url = esp_url(arm_id, "/command")
    session.post(url, json=payload, timeout=HTTP_TIMEOUT)

# ============================================================
# WEBSOCKET
# ============================================================

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    client_id = None

    try:
        while True:
            msg = json.loads(await ws.receive_text())
            msg_type = msg.get("type")

            if msg_type == "hello":
                client_id = msg["client_id"]
                clients[client_id] = ws
                last_heartbeat[client_id] = time.time()

                # Auto-assign first free arm
                for arm in ARMS:
                    if arm not in arm_owner:
                        arm_owner[arm] = client_id
                        await ws.send_json({
                            "type": "control_granted",
                            "arm_id": arm
                        })
                        print(f"🔐 Control granted: {client_id} -> {arm}")
                        break

                await broadcast_clients()
                print(f"👤 Connected: {client_id}")

            elif msg_type == "heartbeat":
                last_heartbeat[client_id] = time.time()
                await ws.send_json({"type": "heartbeat_ack"})

            elif msg_type in ("command", "preset"):
                await handle_command(ws, msg)

            elif msg_type == "emergency_stop":
                await broadcast({
                    "type": "error",
                    "code": "EMERGENCY_STOP",
                    "message": "Emergency stop triggered"
                })

    except WebSocketDisconnect:
        print(f"❌ Disconnected: {client_id}")
    finally:
        await cleanup_client(client_id)

# ============================================================
# COMMAND HANDLING (RACE-FREE OWNERSHIP)
# ============================================================

async def handle_command(ws: WebSocket, msg: dict):
    client_id = msg["client_id"]
    arm_id = msg["arm_id"]

    owner = arm_owner.get(arm_id)
    if owner is None:
        arm_owner[arm_id] = client_id
        await ws.send_json({
            "type": "control_granted",
            "arm_id": arm_id
        })

    elif owner != client_id:
        await ws.send_json({
            "type": "control_revoked",
            "new_owner": owner
        })
        return

    joints = msg["payload"]["joints"]
    speed = msg["payload"].get("speed", 0.5)

    # 🔑 SEND ALL JOINTS (THIS FIXES EVERYTHING)
    for servo, angle in joints.items():
        esp_command(
            arm_id,
            {
                "session_id": SESSION_ID,
                "target": {
                    "servo": servo,
                    "angle": angle,
                    "speed": speed
                }
            }
        )

    await ws.send_json({
        "type": "ack",
        "sequence_id": msg.get("sequence_id", 0),
        "latency_ms": 20
    })

    print(f"🎮 {client_id} -> {arm_id} | ALL SERVOS SENT")

# ============================================================
# PAYLOAD TRANSLATION (MATCHES ESP JSON)
# ============================================================

def build_esp_payload(msg: dict) -> dict:
    if msg["type"] == "command":
        joints = msg["payload"]["joints"]
        speed = msg["payload"].get("speed", 0.5)

        servo, angle = next(iter(joints.items()))

        return {
            "session_id": SESSION_ID,
            "target": {
                "servo": servo,
                "angle": angle,
                "speed": speed
            }
        }

    if msg["type"] == "preset":
        return {
            "session_id": SESSION_ID,
            "target": {
                "servo": "gripper",
                "angle": 30 if msg["payload"]["name"] == "pick" else 70,
                "speed": 0.5
            }
        }

    raise ValueError("Invalid message")

# ============================================================
# CLIENT MANAGEMENT
# ============================================================

async def cleanup_client(client_id):
    if not client_id:
        return

    clients.pop(client_id, None)
    last_heartbeat.pop(client_id, None)

    released = []
    for arm, owner in list(arm_owner.items()):
        if owner == client_id:
            del arm_owner[arm]
            released.append(arm)

    await broadcast_clients()
    print(f"🧹 Cleaned {client_id}, released {released}")

async def broadcast_clients():
    await broadcast({
        "type": "clients_update",
        "count": len(clients)
    })

async def broadcast(msg: dict):
    for ws in list(clients.values()):
        try:
            await ws.send_json(msg)
        except:
            pass

# ============================================================
# HEARTBEAT WATCHDOG (UI CLIENTS)
# ============================================================

async def heartbeat_watchdog():
    while True:
        now = time.time()
        for cid, ts in list(last_heartbeat.items()):
            if now - ts > HEARTBEAT_TIMEOUT:
                print(f"⏱️ Timeout: {cid}")
                await cleanup_client(cid)
        await asyncio.sleep(2)
