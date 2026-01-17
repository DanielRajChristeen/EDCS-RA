# ESP32 Firmware

**Embedded Actuation Layer — EDCS-RA**

---

## Overview

This document describes the ESP32 firmware as an **execution workflow**, not as isolated features. The firmware is part of the embedded actuation layer in EDCS-RA and is responsible for converting validated control commands into deterministic physical motion.

While the ESP32 firmware contains networking, parsing, and recovery logic, these exist in support of actuation—not as system-level ownership of coordination or intent.

---

## Firmware Workflow

The ESP32 firmware operates as a linear, repeatable workflow. Understanding this flow is essential to understanding both the code and the architectural constraints.

---

## 1. Boot and Initialization

When powered on or reset, the ESP32 initializes only the components required for stable operation: communication interfaces, servo timing, and safety defaults.

Servo timing is configured explicitly at startup to ensure predictable PWM behavior across resets.

```cpp
servo.setPeriodHertz(50);
servo.attach(SERVO_PIN, 500, 2400);
```

No dynamic configuration or runtime discovery is performed during boot. This guarantees that actuation behavior is known before any command is accepted.

---

## 2. Network Bring-Up (Transport Enablement)

The firmware includes Wi-Fi logic to enable command transport during development and constrained deployments. Network connectivity is established early to allow upstream systems to reach the actuator node.

Critically, Wi-Fi is treated as a **transport mechanism only**. Network state does not alter control logic, execution timing, or servo behavior. If connectivity is lost, the firmware simply stops receiving commands; it does not enter alternative modes or make assumptions about system health.

Architectural ownership of networking remains outside the embedded layer.

---

## 3. Idle and Wait State

After initialization, the firmware enters a passive wait state. No autonomous behavior is executed. The ESP32 does not generate motion, schedules, or background tasks.

This idle state reflects the core ideology of the embedded layer: **react, do not decide**.

---

## 4. Command Reception

Commands arrive via the configured communication channel. The firmware does not assume where the command originates—gateway, local client, or test interface.

The arrival of data is the only trigger for action.

```cpp
if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
}
```

There is no polling for state changes, no time-based logic, and no predictive execution.

---

## 5. Input Normalization and JSON Parsing

Incoming data may be structured (e.g., JSON) depending on the integration stage. The firmware includes lightweight JSON parsing to extract primitive actuation parameters.

This parsing is intentionally shallow. It exists only to normalize input into values that the actuator can consume.

The firmware does **not**:

* Interpret intent
* Validate workflows
* Perform semantic checks

JSON is treated as an ingress format, not a control model.

---

## 6. Local Validation

Before any actuation occurs, the firmware enforces minimal local safety constraints. These checks exist solely to protect hardware and actuators.

```cpp
if (angle < 0 || angle > 180) {
    return;
}
```

Validation is limited to range and format correctness. System-level validation and sequencing are assumed to be handled upstream.

---

## 7. Actuation Execution

Once validated, the command is applied immediately. The firmware translates the command into a physical signal without delay, buffering, or reinterpretation.

```cpp
servo.write(angle);
```

There is no retained command history and no awareness of previous or future states. Each command is treated as complete and independent.

---

## 8. Stateless Operation

After execution, the firmware returns to the idle wait state. No state is stored beyond the physical position of the actuator itself.

This stateless model ensures that:

* Firmware restarts are safe
* Partial failures do not corrupt behavior
* Debugging remains straightforward

---

## 9. Watchdog and Local Recovery

A watchdog mechanism is present to guarantee firmware liveness. Its scope is strictly local.

If the firmware becomes unresponsive, the watchdog triggers a reset of the ESP32 itself. This mechanism does not coordinate recovery with other system components and does not attempt to infer system-wide failure.

System supervision and orchestration are explicitly delegated to higher layers.

---

## 10. Multi-Arm Scaling via Replication

Each firmware file (`arm_1.ino`, `arm_2.ino`) corresponds to a single physical arm. There is no multi-arm awareness within a single firmware instance.

Scaling the system involves deploying additional ESP32 nodes running equivalent firmware, not increasing complexity within the firmware itself. This preserves determinism as the system grows.

---

## What This Firmware Explicitly Avoids

Throughout the workflow, the firmware deliberately avoids responsibilities that compromise clarity or timing:

* System-level decision-making
* Multi-arm coordination
* UI awareness
* Network orchestration
* Motion planning

These concerns belong to the gateway and frontend layers.

---

## Relationship to Other Layers

The ESP32 firmware assumes that command semantics and coordination logic are defined upstream. Detailed descriptions of command structure, sequencing, and recovery logic are documented in the gateway documentation.

System-wide data flow and architectural contracts are described in the architecture documentation.

---

## Closing Perspective

The ESP32 firmware in EDCS-RA is designed to be predictable, constrained, and reliable. Its success is measured not by feature richness, but by consistency of execution.

In this system, **a boring firmware is a correct firmware**.

---
