# **ESP32 Firmware**

**Embedded Actuation Layer — EDCS-RA**


---

## **Overview**

The ESP32 firmware represents the embedded actuation layer of the EDCS-RA system. Its responsibility is to convert explicit, pre-validated control commands into deterministic physical motion, while preserving electrical stability, timing predictability, and mechanical safety.

Although the ESP32 platform supports networking, JSON parsing, and higher-level logic, this firmware intentionally constrains those capabilities. The embedded layer executes commands; it does not interpret intent, coordinate systems, or manage global state.

This document describes the firmware in the exact order it operates, from power stability to actuation and recovery.


---

## **Firmware Execution Workflow**

The firmware follows a linear, repeatable execution model:

power stability → boot → pin binding → network enablement → wait → receive → parse → validate → enforce safety scope → actuate → recover

Each stage exists to protect determinism and physical integrity.


---

### **1. Power Architecture and Stability Assumptions**

The firmware assumes a segregated power architecture.

A single ESP32 cannot safely drive multiple servo motors due to current spikes and voltage sag during actuation. Powering servos directly from the ESP32 leads to brownouts, resets, and unstable PWM behavior.

To avoid this, the system uses:

SMPS + step-down buck converter to power all servo motors

Independent power for the ESP32 logic

A shared ground reference between ESP32 and servo power supply


The ESP32 provides control signals only and never supplies actuator power.

The firmware assumes these electrical conditions are satisfied before execution begins.


---

### **2. Boot and Initialization**

On power-up or reset, the ESP32 initializes only what is required for stable operation.

* All servos are detached at boot

* No actuation commands are issued

* No default positioning is applied


This guarantees no unintended motion during startup.
Servo movement begins only after the first valid command is received.


---

### **3. Hardware Binding and Pin Ownership**

Each firmware instance statically binds GPIO pins to physical joints at compile time. These bindings do not change at runtime.

Joint-to-Pin Mapping

Base joint → GPIO 5

Arm joint → GPIO 18

Elbow joint → GPIO 19

Gripper → GPIO 21

```cpp
#define BASE_PIN   5
#define ARM_PIN    18
#define ELBOW_PIN  19
#define GRIP_PIN   21
```

Each pin is exclusively owned by one joint. No multiplexing, reassignment, or dynamic role switching occurs.


---

### **4. Network Bring-Up (Transport Enablement)**

The firmware includes Wi-Fi connectivity to enable command transport.

Networking is treated strictly as a transport mechanism. Network state does not influence:

* Actuation timing

* Control logic

* Safety enforcement

* Servo behavior

Loss of connectivity results only in the absence of new commands. The firmware does not infer system failure or enter fallback modes.

Architectural ownership of networking remains outside the embedded layer.


---

### **5. Idle and Wait State**

After initialization, the firmware enters a passive wait state.

The ESP32 does not:

* Generate motion autonomously

* Schedule behaviors

* Predict future states


The embedded layer exists to react, not decide.


---

### **6. Command Reception**

Commands are received through HTTP endpoints exposed by the embedded web server.

Arrival of input is the only execution trigger. There is no polling, timing-based execution, or background motion logic.


---

### **7. Input Normalization and JSON Parsing**

The firmware uses lightweight JSON parsing to normalize incoming payloads into primitive actuation parameters.

Parsing is intentionally shallow and bounded. It exists only to extract explicit values. The firmware does not interpret intent, validate workflows, or apply semantic meaning to structured data.

JSON is treated as an ingress format, not a control model.


---

### **8. Arm Joint Safety Scope**

Before any actuation occurs, the firmware enforces an explicit Arm Joint Safety Scope.

This scope defines the mechanically safe motion envelope for each joint. It represents the absolute boundary within which the embedded layer is allowed to operate. Any command outside this scope is rejected locally, regardless of command source or system state.

The purpose of this scope is to ensure that no software behavior can physically damage the arm, even in the presence of upstream errors, network faults, or integration bugs.


---

### **Safety Scope Derivation**

The Arm Joint Safety Scope is established through isolated servo characterization and mechanical testing, performed outside the EDCS-RA distributed control stack.

Servos are tested individually using a minimal UART-to-servo control firmware to identify:

* Mechanical end stops

* Over-travel regions

* Dead zones

* Joint-specific mounting constraints


The calibration workflow used to derive these limits is documented here:

**🔗 ESP32 UART to Servo Control — Safety Calibration Reference**
https://github.com/DanielRajChristeen/ESP32-UART-to-Servo

This calibration is treated as a pre-integration activity, not a runtime responsibility.


---

### **Encoding Safety Scope in Firmware**

Once validated, safety boundaries are encoded as compile-time constants.

Example (ARM-1):

```cpp
/* ================= ARM-1 SAFETY SCOPE ================= */
#define BASE_MIN   0
#define BASE_MAX   180

#define ARM_MIN    0
#define ARM_MAX    140

#define ELBOW_MIN  60
#define ELBOW_MAX  140

#define GRIP_MIN   20
#define GRIP_MAX   40
```

These values are not tuning parameters. They represent validated mechanical truths.

Changing them requires re-calibration and firmware redeployment.


---

### **9. Local Validation**

Incoming commands are validated against format, range, and the Arm Joint Safety Scope before execution.

Unsafe commands are rejected explicitly. Values are not clamped, interpolated, or auto-corrected.

Rejection is observable through the absence of physical motion.


---

### **10. Actuation Execution**

Once validated, commands are applied immediately.

The firmware translates control values directly into PWM signals on the bound GPIO pins. Motion is executed incrementally to maintain smooth and predictable movement.

Each command is treated as complete and independent.


---

### **11. Command Rate Assumptions**

The firmware does not implement command buffering, queuing, or scheduling.

If commands arrive faster than the physical actuation capability of the servos, newer commands overwrite previous targets. Rate control and sequencing are the responsibility of upstream layers.


---

### **12. Stateless Operation**

After execution, the firmware returns to the idle wait state.

No command history is stored. The only persistent state is the physical position of the actuator itself.

This guarantees:

* Safe restarts

* Predictable recovery

* No hidden state coupling



---

### **13. Watchdog and Local Recovery**

A watchdog mechanism guarantees firmware liveness.

If no valid command or heartbeat is received within the configured timeout, the firmware:

* Detaches all servos

* Resets session state


The watchdog scope is strictly local. It does not supervise other system components or infer system-level health.


---

### **14. Multi-Arm Scaling via Replication**

Each firmware file (arm_1.ino, arm_2.ino) corresponds to one physical arm.

There is no multi-arm awareness within a single firmware instance. Scaling is achieved by deploying additional ESP32 nodes, not by increasing firmware complexity.


---

## **What This Firmware Explicitly Avoids**

The firmware intentionally avoids responsibilities that compromise clarity or timing:

* System-level decision making

* Multi-arm coordination

* UI awareness

* Network orchestration

* Motion planning or trajectory generation


These concerns belong to higher layers.


---

## **Relationship to Other Layers**

The ESP32 firmware operates under explicit contracts defined upstream. Command semantics, coordination logic, and system supervision are documented in the gateway layer.

End-to-end architecture is described in docs/architecture.md.


---

## **Closing Perspective**

The ESP32 firmware in EDCS-RA is intentionally constrained, predictable, and stable. Its value lies not in intelligence, but in reliable execution under load.

That reliability exists because:

Power is handled externally

Safety boundaries are declared and enforced locally

Complexity is pushed upward


In EDCS-RA, good power architecture enables boring firmware — and boring firmware is correct firmware.


---
