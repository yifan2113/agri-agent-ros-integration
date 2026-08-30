# Safety Boundary

Stages 2–4 are hardware-free and read-only. The exposed MCP surface contains
only ROS health, node/topic discovery, and the safe demo status service.

## Enforced restrictions

- No arbitrary ROS service or command execution.
- No topic publication, `/cmd_vel`, CAN, serial, motor, or actuator access.
- No navigation, SLAM, sensor driver, or robot launch controls.
- The ROS status request fixes all action-like fields to zero.
- Any nonzero `control`, `planning`, `slam`, or `navigation` field is rejected.
- MCP-to-ROS actions are checked against the same four-item allowlist in the
  bridge and shell adapter.
- ROS remains on loopback; remote MCP binding is limited to the exact detected
  Tailscale IPv4 address.
- MCP HTTP Host values are allowlisted to reduce DNS-rebinding risk.

## Stage 5 gate

Offline replay and simulation can be added without hardware, provided they use
separate profiles and cannot reach control interfaces. Before any real motion,
the project requires application authentication, device-scoped network ACLs,
audit logs, human confirmation, rate/speed limits, watchdogs, physical
emergency stop, an isolated test area, and an operator-defined stop procedure.

Actual device addresses, hostnames, credentials, field coordinates, raw sensor
records, and runtime logs must not be committed to this public repository.
