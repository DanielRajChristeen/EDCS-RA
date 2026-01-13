#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

/* ================= WIFI ================= */
const char* ssid = "Dani";
const char* password = "Daniel@342004";

/* ================= SERVER ================= */
WebServer server(80);

/* ================= WATCHDOG ================= */
#define WATCHDOG_TIMEOUT_MS 5000

/* ================= SERVO PINS ================= */
#define BASE_PIN   5
#define ARM_PIN    18
#define ELBOW_PIN  19
#define GRIP_PIN   21

Servo baseServo, armServo, elbowServo, gripServo;

/* ================= ARM-1 LIMITS ================= */
#define BASE_MIN   0
#define BASE_MAX   180
#define ARM_MIN    0
#define ARM_MAX    140
#define ELBOW_MIN  60
#define ELBOW_MAX  140
#define GRIP_MIN   20
#define GRIP_MAX   40

/* ================= STATE ================= */
uint32_t activeSessionId = 0;
uint32_t lastValidMsgMs = 0;
bool servosAttached = false;

/* ================= SERVO MOTION ================= */
struct ServoMotion {
  Servo* servo;
  int minA;
  int maxA;
  int current;
  int target;
};

ServoMotion baseM  = { &baseServo,  BASE_MIN,  BASE_MAX,  90, 90 };
ServoMotion armM   = { &armServo,   ARM_MIN,   ARM_MAX,   70, 70 };
ServoMotion elbowM = { &elbowServo, ELBOW_MIN, ELBOW_MAX, 90, 90 };
ServoMotion gripM  = { &gripServo,  GRIP_MIN,  GRIP_MAX, 30, 30 };

ServoMotion* servos[] = { &baseM, &armM, &elbowM, &gripM };

/* ================= MOTION TIMING ================= */
uint32_t lastMoveMs = 0;
uint16_t moveIntervalMs = 15;

/* ================= UTILS ================= */
int clamp(int v, int lo, int hi) {
  if (v < lo) return lo;
  if (v > hi) return hi;
  return v;
}

uint16_t speedToInterval(float speed) {
  speed = constrain(speed, 0.05, 1.0);
  return map(speed * 100, 5, 100, 40, 5);
}

/* ================= SAFETY ================= */
void detachAll() {
  baseServo.detach();
  armServo.detach();
  elbowServo.detach();
  gripServo.detach();
  servosAttached = false;
  Serial.println("[SAFETY] Servos DETACHED");
}

void attachAll() {
  if (servosAttached) return;

  baseServo.attach(BASE_PIN, 500, 2500);
  armServo.attach(ARM_PIN, 500, 2500);
  elbowServo.attach(ELBOW_PIN, 500, 2500);
  gripServo.attach(GRIP_PIN, 500, 2500);

  servosAttached = true;
  Serial.println("[CONTROL] Servos ATTACHED");
}

/* ================= HEARTBEAT ================= */
void handleHeartbeat() {
  StaticJsonDocument<128> doc;

  if (deserializeJson(doc, server.arg("plain"))) {
    server.send(400, "Bad JSON");
    return;
  }

  uint32_t sid = doc["session_id"] | 0;

  // Accept any new session safely
  if (activeSessionId != sid) {
    activeSessionId = sid;
    Serial.print("[SESSION] Accepted session ");
    Serial.println(activeSessionId);
  }

  lastValidMsgMs = millis();
  attachAll();
  server.send(200, "HB OK");
}

/* ================= COMMAND ================= */
void handleCommand() {
  attachAll();   // 🔑 THIS IS THE FIX

  StaticJsonDocument<256> doc;
  if (deserializeJson(doc, server.arg("plain"))) {
    server.send(400, "Bad JSON");
    return;
  }

  uint32_t sid = doc["session_id"] | 0;
  if (sid != activeSessionId) {
    activeSessionId = sid;
    Serial.println("[SESSION] Re-synced from command");
  }

  JsonObject t = doc["target"];
  const char* servo = t["servo"] | "";
  int angle = t["angle"] | 0;
  float speed = t["speed"] | 0.5;

  moveIntervalMs = speedToInterval(speed);

  if (!strcmp(servo, "base")) {
    baseM.current = baseServo.read();
    baseM.target  = clamp(angle, BASE_MIN, BASE_MAX);
  }
  else if (!strcmp(servo, "arm")) {
    armM.current = armServo.read();
    armM.target  = clamp(angle, ARM_MIN, ARM_MAX);
  }
  else if (!strcmp(servo, "elbow")) {
    elbowM.current = elbowServo.read();
    elbowM.target  = clamp(angle, ELBOW_MIN, ELBOW_MAX);
  }
  else if (!strcmp(servo, "gripper")) {
    gripM.current = gripServo.read();
    gripM.target  = clamp(angle, GRIP_MIN, GRIP_MAX);
  }

  lastValidMsgMs = millis();

  Serial.print("[CMD] ");
  Serial.print(servo);
  Serial.print(" -> ");
  Serial.print(angle);
  Serial.print(" | speed=");
  Serial.println(speed);

  server.send(200, "CMD OK");
}

/* ================= MOTION ENGINE ================= */
void processMotion() {
  if (!servosAttached) return;
  if (millis() - lastMoveMs < moveIntervalMs) return;

  lastMoveMs = millis();

  for (auto s : servos) {
    if (s->current == s->target) continue;
    s->current += (s->current < s->target) ? 1 : -1;
    s->servo->write(s->current);
  }
}

/* ================= WATCHDOG ================= */
void watchdog() {
  if (servosAttached && millis() - lastValidMsgMs > WATCHDOG_TIMEOUT_MS) {
    Serial.println("[WATCHDOG] Timeout");
    detachAll();
    activeSessionId = 0;
  }
}

/* ================= SETUP / LOOP ================= */
void setup() {
  Serial.begin(115200);
  delay(500);

  detachAll();

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(200);
  }

  Serial.print("[NET] ESP32 IP: ");
  Serial.println(WiFi.localIP());

  server.on("/heartbeat", HTTP_POST, handleHeartbeat);
  server.on("/command", HTTP_POST, handleCommand);
  server.begin();

  Serial.println("[SYSTEM] ARM 1 READY");
}

void loop() {
  server.handleClient();
  processMotion();
  watchdog();
  vTaskDelay(1);
}
