import time
import requests

ESP32_ARMS = {
    "arm_1": {"ip": "10.106.120.123", "port": 80},
    "arm_2": {"ip": "10.106.120.150", "port": 80},
}

HTTP_TIMEOUT = 1.0      # IMPORTANT
RETRIES = 3
DELAY_BETWEEN = 0.5     # IMPORTANT

session = requests.Session()

def test_esp32(arm_id, ip, port):
    url = f"http://{ip}:{port}/heartbeat"
    payload = {"session_id": int(time.time())}

    for attempt in range(1, RETRIES + 1):
        try:
            t0 = time.time()
            r = session.post(url, json=payload, timeout=HTTP_TIMEOUT)
            latency = int((time.time() - t0) * 1000)

            if r.status_code == 200:
                return True, latency, r.text.strip()

        except requests.exceptions.RequestException:
            time.sleep(0.2)

    return False, None, "No response after retries"

if __name__ == "__main__":
    print("\n🔍 ESP32 COMM CHECK (robust mode)\n")

    alive, dead = [], []

    for arm_id, cfg in ESP32_ARMS.items():
        ok, latency, info = test_esp32(
            arm_id, cfg["ip"], cfg["port"]
        )

        if ok:
            alive.append(arm_id)
            print(f"✅ {arm_id:<6} | {latency:>4} ms | OK | {info}")
        else:
            dead.append(arm_id)
            print(f"❌ {arm_id:<6} | FAIL | {info}")

        time.sleep(DELAY_BETWEEN)

    print("\n==============================")
    print("🟢 ONLINE :", alive)
    print("🔴 OFFLINE:", dead)
    print("==============================\n")
