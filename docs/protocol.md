# **Communication Protocol — EDCS-RA**

## **Purpose""

This document defines the communication protocol used within EDCS-RA. It specifies how control intent, state information, and execution feedback flow between system components. The protocol is designed to support distributed control, fault isolation, and safety-first operation, rather than low-latency teleoperation.

The protocol definition is intentionally concise and opinionated to prevent ambiguity in implementation and extension.


---

## **Protocol Philosophy**

EDCS-RA follows an intent-driven, message-oriented communication model. Components do not issue low-level actuation commands directly to downstream devices. Instead, they exchange structured intent and state messages, with each layer retaining autonomy over execution decisions.

All communication is asynchronous. No component assumes guaranteed delivery, immediate execution, or real-time response. This model reflects the realities of distributed systems operating across heterogeneous networks.


---

## **Communication Scope**

The protocol applies to communication between the following components:

The frontend communicates exclusively with the edge gateway. It does not communicate directly with embedded controllers or physical devices. The gateway communicates with the embedded controller and acts as the sole mediator between user intent and actuation. The embedded controller communicates only with the gateway and never accepts external input.

This strict communication boundary is fundamental to the protocol and is not optional.


---

## **Message Categories**

All protocol messages fall into one of four categories.

Intent messages represent desired actions or goals expressed by the frontend. These messages describe what the user wants to achieve, not how the action should be executed.

State messages represent the current or recent status of a component. These messages are emitted by the gateway or embedded controller and provide observability into system behavior.

Acknowledgment messages confirm receipt and acceptance of an intent or state update. An acknowledgment does not imply successful execution.

Error messages indicate rejection, failure, or abnormal conditions detected by a component.

Each message category has a distinct role and must not be overloaded.


---

## **Intent Semantics**

Intent messages are declarative and bounded. They must be interpretable by the gateway without requiring additional context or hidden state. An intent expresses a permissible action within the system’s defined control space.

The gateway evaluates every intent against local arbitration rules, system state, and safety constraints. Only intents that pass validation are translated into device-level instructions. Intents may be modified, delayed, or rejected entirely.

The embedded controller never receives raw user intent.


---

## **Gateway Arbitration**

The gateway is the protocol authority within EDCS-RA. It is responsible for interpreting intent messages, resolving conflicts, enforcing rate limits, and coordinating execution across devices.

Arbitration decisions are local and final. Upstream components do not override gateway decisions and should not assume deterministic outcomes. This design prevents remote clients from exerting unsafe or excessive control over physical hardware.


---

## **Embedded Controller Interaction**

The embedded controller communicates with the gateway using a constrained subset of the protocol. It accepts only validated, device-level instructions and emits state and error messages.

The embedded controller does not retain session context, user identity, or intent history. It operates as a deterministic execution unit under gateway supervision.

If communication with the gateway is lost, the embedded controller transitions to a safe state.


---

## **Reliability and Failure Handling**

The protocol assumes unreliable networks and partial failures as normal operating conditions. Messages may be delayed, duplicated, or lost. Components must be tolerant of these conditions.

No component blocks indefinitely waiting for a response. Timeouts are treated as non-fatal events and handled through retries or state reconciliation where appropriate.

Safety is preserved by local enforcement rather than protocol guarantees.


---

## **Ordering and Idempotency**

The protocol does not guarantee strict message ordering. Implementations must treat messages as potentially out of order.

Intent messages should be idempotent wherever possible. Repeated receipt of the same intent must not result in unintended repeated actuation.


---

## **Versioning and Extensibility**

The protocol is versioned at the message level. Each message includes a protocol version identifier, allowing components to evolve independently while maintaining compatibility.

Backward-incompatible changes require explicit version increments. Silent behavior changes are prohibited.


---

## **Non-Goals**

The EDCS-RA protocol is not designed for real-time control loops, continuous streaming of actuator signals, or millisecond-level synchronization. It does not aim to replace industrial fieldbus protocols or real-time operating system messaging.

Its purpose is to enable safe, distributed, remote coordination of robotic systems under imperfect network conditions.


---