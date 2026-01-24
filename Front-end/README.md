# Frontend Layer  

---

## Overview

The Frontend layer provides the primary human–machine interaction interface for the EDCS-RA system. It is implemented as a browser-based application that allows multiple users to observe system state, request control authority, and issue high-level control intents to robotic arms deployed remotely.

The frontend is intentionally designed as a thin client. It does not participate in actuation, motion planning, or safety enforcement. Instead, it focuses on accurate intent expression, real-time system visibility, and robust behavior under varying network conditions.

---

## Architectural Role

Within the EDCS-RA architecture, the frontend operates strictly as a client-facing interface. All interactions initiated from the browser are routed through the Raspberry Pi gateway, which arbitrates control ownership and forwards commands to ESP32-based arm controllers.

At no point does the frontend communicate directly with ESP32 devices, nor does it generate hardware-level control signals. This separation ensures that user-facing logic remains decoupled from time-critical and safety-critical control layers.

---

## Design Philosophy

The frontend is built around a small set of core principles. It remains intentionally lightweight, avoids hidden state, and does not assume uninterrupted connectivity. Control authority is always explicit, never inferred. When system conditions degrade or ownership is lost, the interface fails safely by disabling command emission while preserving visibility.

The application is also designed to be replaceable. It uses no frontend frameworks, build systems, or runtime dependencies, allowing it to be deployed, modified, or rewritten without affecting the rest of the system.

---

## Execution Model

The frontend is implemented as a single-page application using standard web technologies. HTML defines structural layout, CSS manages visual state and responsiveness, and vanilla JavaScript handles interaction logic and communication with the backend gateway.

Because the application has no external dependencies, it can be served as a static file or opened directly in a modern browser. No compilation or packaging step is required.

---

## Client Identity and Session Awareness

Each browser instance generates a unique client identifier on first load. This identifier is stored locally and reused across reloads to provide continuity during a session.

The client identifier is used by the gateway to track connected users, assign control ownership, and manage heartbeat-based liveness detection. The frontend itself does not issue or validate session authority; it merely presents identity information to the gateway and reacts to ownership decisions returned by it.

---

## Backend Discovery and Connectivity

The frontend does not embed fixed backend endpoints. Instead, the backend base URL is provided by the user at runtime, typically corresponding to a Cloudflare Tunnel endpoint exposed by the Raspberry Pi gateway.

Once provided, this base URL is cached for the duration of the browser session and used to derive REST endpoints, WebSocket endpoints, and camera stream URLs. Transport protocol selection is handled automatically, ensuring compatibility with both secure and non-secure deployments.

---

## Real-Time Communication Channel

All interactive communication between the frontend and the gateway occurs over a persistent WebSocket connection. This channel carries control commands, ownership notifications, heartbeat acknowledgements, error events, and system status updates.

The frontend does not attempt to reorder, replay, or reinterpret messages. State is always reconciled based on authoritative responses from the gateway, ensuring consistent behavior even under transient network failures.

---

## Control Ownership Model

Control over a robotic arm is exclusive and explicitly granted. The frontend visually and functionally reflects this ownership model by enabling or disabling control inputs based on gateway notifications.

When control is granted, the interface transitions into an active control state. When control is revoked or unavailable, the interface enters a view-only mode in which all command inputs are disabled. The frontend never assumes control based on user interaction alone.

---

## Control Modes and Intent Representation

The frontend supports multiple control modes as mechanisms for expressing user intent. In manual mode, users specify individual joint angles directly. In inverse kinematics mode, users specify desired Cartesian positions and orientations.

In both cases, the frontend does not perform validation, kinematic solving, or safety checks. All intent data is forwarded verbatim to the gateway, which determines how and whether it should be executed.

---

## Command Emission and Rate Management

User input is translated into structured command messages that include timestamps and sequence identifiers. To prevent command flooding and ensure responsiveness, command emission is rate-limited and throttled.

Only the most recent intent is transmitted at any given time, and the frontend does not queue or retry commands. This design prevents stale or conflicting control data from propagating through the system.

---

## Acknowledgement Handling and Latency Visibility

For operational transparency, the frontend tracks acknowledgements returned by the gateway and measures round-trip latency. Latency metrics are displayed to the user and logged in the system console.

These measurements are informational only. The frontend does not adapt control behavior based on latency, nor does it attempt to compensate for delays.

---

## Heartbeat and Liveness Monitoring

The frontend periodically transmits heartbeat messages to the gateway to signal liveness. Missed acknowledgements are interpreted as degraded connectivity, prompting the interface to visually indicate the issue and disable control inputs.

This mechanism ensures that control authority is not exercised when the connection state is uncertain.

---

## Reconnection and Fault Tolerance

When the connection to the gateway is lost, the frontend automatically attempts to reconnect using an exponential backoff strategy. During reconnection attempts, control inputs remain disabled.

Upon successful reconnection, the client identity is reasserted and control ownership is renegotiated. Control is only re-enabled after explicit confirmation from the gateway.

---

## Camera Stream Integration

Live camera feeds are rendered in the frontend using MJPEG streams served by the gateway. These streams are view-only and shared across all connected clients.

Camera selection is logically associated with the currently selected arm, but the frontend does not assume a fixed physical mapping between cameras and actuators.

---

## Emergency Stop Interaction

The frontend provides an emergency stop control as a high-priority intent signal. When activated, the interface immediately locks local controls and emits an emergency stop message to the gateway.

Further control remains disabled until the backend explicitly clears the locked state. The frontend itself does not interact directly with motors or firmware-level safety mechanisms.

---

## System Visibility and Diagnostics

An integrated console presents structured system messages with severity-based filtering. This console is intended to provide situational awareness and traceability for operators rather than deep debugging capabilities.

Console output is bounded to prevent unbounded memory growth.

---

## Explicit Non-Responsibilities

The frontend does not perform motor control, safety enforcement, motion planning, inverse kinematics solving, or persistent state storage. It does not communicate directly with ESP32 devices and does not attempt to override gateway decisions.

All hardware interaction is strictly delegated to downstream layers.

---

## Layer Relationship Summary

The frontend expresses user intent and visualizes system state. The gateway coordinates users, arbitrates ownership, and routes commands. ESP32 firmware executes physical actuation and enforces mechanical and electrical safety constraints.

This strict separation of concerns is central to the scalability and robustness of EDCS-RA.

---

## Closing Perspective

The frontend is intentionally lightweight, reactive, and disposable. Its purpose is not to control hardware, but to enable safe, observable, and coordinated interaction with a distributed robotic system.

In EDCS-RA, responsibility flows downward:

The frontend expresses intent.  
The gateway coordinates intent.  
The ESP32 executes intent.
