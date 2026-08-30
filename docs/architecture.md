# Architecture

## Stage 4 data flow

```text
MacBook
  DeepSeek Harness
    -> MCP client plugin
    -> Tailscale Streamable HTTP

Ubuntu server
  agri_mcp_server (Python 3.12)
    -> four-tool allowlist
    -> asynchronous subprocess with timeout
  ros_adapter (system Python 3.8)
    -> ROS master on 127.0.0.1
    -> /agri/demo_status
  agri_stage2_status_server
    -> status-only JSON response
```

The MacBook never connects directly to the ROS master. ROS XML-RPC and node
addresses stay on server loopback; only the MCP HTTP endpoint binds to the
server's exact Tailscale IPv4 address.

## Runtime separation

ROS Noetic on Ubuntu 20.04 installs its Python modules for system Python 3.8.
The MCP SDK runs in the project-local Python 3.12 virtual environment. A JSON
subprocess boundary keeps those dependency sets separate and gives the MCP
layer a fixed action allowlist and timeout.

## Source layout

- `catkin_ws/src/Agri_ROS`: upstream submodule fixed to the tested revision.
- `catkin_ws/src/agri_stage2_demo`: locally maintained safe ROS status package.
- `agri_mcp_server`: MCP tools, ROS adapter, deployment scripts, and tests.
- `harness`: sanitized client configuration templates.
- `docs`: experiment record, architecture, and safety policy.
