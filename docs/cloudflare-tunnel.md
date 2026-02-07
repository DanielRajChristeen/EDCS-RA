#Cloudflare Tunnel in EDCS-RA

##Overview

In the EDCS-RA architecture, Cloudflare Tunnel is used as the exclusive remote connectivity mechanism between external user interfaces and the edge gateway. Its purpose is narrowly scoped: to provide secure, inbound-free access to the Raspberry Pi gateway without exposing any part of the robotic system to the public network.

The tunnel enables remote intent delivery while preserving EDCS-RA’s core principle that physical actuation components remain network-isolated by default.


---

##Architectural Rationale

EDCS-RA is designed to operate in constrained and heterogeneous network environments where public IP addresses, static routing, or manual port forwarding cannot be assumed. At the same time, the system requires reliable remote access to the gateway for control and coordination.

Cloudflare Tunnel satisfies these requirements by allowing the gateway to establish an outbound-initiated connection to the Cloudflare edge. This model ensures that the gateway is never directly reachable via inbound connections while still being accessible through a controlled entry point.

Within EDCS-RA, no alternative tunneling, VPN, or reverse-proxy mechanism is used.


---

##Position Within the System

The Cloudflare Tunnel is positioned strictly at the gateway boundary. All remote traffic enters the system through the tunnel and terminates at the Raspberry Pi gateway. No tunnel endpoints exist at the ESP32 layer or on any physical actuation hardware.

Conceptually, control flows from the remote user interface through the Cloudflare edge, across the tunnel, into the gateway, and only then—after local arbitration—toward the embedded controller.

This placement reinforces the gateway’s role as the sole network authority within the system.


---

##Gateway Responsibilities

The Raspberry Pi gateway is responsible for initiating, maintaining, and terminating the Cloudflare Tunnel connection. The tunnel client runs within the gateway’s operational environment and is managed as part of the gateway lifecycle.

All traffic received through the tunnel is processed at the gateway layer. The gateway validates incoming intent, applies coordination and safety logic, and conditionally forwards commands to the ESP32. The tunnel itself does not bypass, replace, or interfere with these responsibilities.


---

##Security Model

EDCS-RA relies on Cloudflare Tunnel to enforce a strictly outbound-only connectivity model. No inbound ports are opened on the gateway, and no device within the robotic system is directly exposed to the internet.

The ESP32 and robotic arm remain isolated within the local network and are never addressable from outside the gateway. Cloudflare is used solely as a transport and access layer and does not participate in control logic, safety enforcement, or real-time guarantees.

All safety-critical decisions remain local to the gateway and embedded firmware.


---

##Tunnel Initialization and Execution

In EDCS-RA, the Cloudflare Tunnel is started on the gateway using a token-based, ephemeral tunnel configuration. This approach avoids persistent credentials, interactive login flows, or long-lived configuration files on the device.

The tunnel is initiated using a randomly generated, Cloudflare-issued tunnel token and is executed directly on the gateway.

The command used in this project is:
```bash
cloudflared tunnel run --token <TUNNEL_TOKEN>
```

The <TUNNEL_TOKEN> uniquely identifies the tunnel instance and is supplied at runtime. No browser-based login or account session is required on the gateway. No authentication state is stored locally.

This command establishes an outbound connection from the gateway to the Cloudflare edge and exposes the locally running gateway service through the tunnel.


---

##Operational Characteristics

The tunnel process runs under the gateway’s control and is tied to the gateway’s operational lifecycle.

If the tunnel process terminates, remote access to the gateway immediately stops. No inbound exposure remains, and no residual connectivity persists. Restarting the tunnel process re-establishes remote access using the same token without requiring additional authentication steps.


---

##Failure Behavior

If the Cloudflare Tunnel becomes unavailable, remote access to the gateway is lost while local gateway and ESP32 operation continue unaffected. No unsafe behavior is triggered at the device level.

If the gateway becomes unavailable, the tunnel connection is automatically terminated. No remote commands can reach the system, and the embedded controller remains in a safe, isolated state.

Loss of internet connectivity results in graceful degradation to local-only operation.


---

##Scope and Non-Goals

Cloudflare Tunnel is not used for real-time motor control, device-level authentication, or safety enforcement. It does not participate in low-latency control loops and does not replace local arbitration logic.

Its role within EDCS-RA is intentionally limited to secure remote access to the gateway.


---

##Status

This document describes the current and only tunnel mechanism used in EDCS-RA.


---