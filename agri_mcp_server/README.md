# Agri MCP Server — Stages 3 and 4

Read-only MCP bridge between a modern Python environment and ROS Noetic.

## Architecture

```text
Harness / MCP client
  -> Streamable HTTP (/mcp)
  -> agri_mcp_server (Python 3.12 / MCP SDK 2.x)
  -> fixed action allowlist + asynchronous subprocess
  -> ros_adapter (system Python 3.8 / ROS Noetic)
  -> ROS master and /agri/demo_status
```

The process boundary prevents the MCP environment from importing ROS Noetic's
system-Python packages and keeps both dependency sets reproducible.

## Read-only tools

| Tool | Behavior |
| --- | --- |
| `ros_check_online` | Check whether the local ROS master is reachable |
| `ros_list_nodes` | List node names registered with the ROS master |
| `ros_list_topics` | List published topic names and message types |
| `get_robot_status` | Call `/agri/demo_status` with every action field fixed to zero |

The server does not expose topic publishing, arbitrary service calls,
`roslaunch`, `/cmd_vel`, motors, navigation, SLAM, sensors, or actuators. Both
the shell adapter and Python bridge enforce the same four-action allowlist, and
each adapter request has a five-second timeout.

## Install

From the repository root:

```bash
cd agri_mcp_server
uv sync --python 3.12 --locked
```

The catkin workspace must already be built. By default the adapter uses
`../catkin_ws`; set `AGRI_CATKIN_WS` when deploying with another layout.

## Stage 3: local MCP

Start the stage 2 ROS service in one terminal:

```bash
cd <REPOSITORY_ROOT>/catkin_ws
source /opt/ros/noetic/setup.bash
source devel/setup.bash
export ROS_MASTER_URI=http://127.0.0.1:11311
export ROS_IP=127.0.0.1
roslaunch agri_stage2_demo status_demo.launch
```

Start MCP in another terminal:

```bash
cd <REPOSITORY_ROOT>/agri_mcp_server
./scripts/run_server.sh
```

The stage 3 endpoint is `http://127.0.0.1:8000/mcp`.

## Stage 4: Harness over Tailscale

Start the complete ROS and MCP stack:

```bash
cd <REPOSITORY_ROOT>/agri_mcp_server
./scripts/start_stage4_stack.sh
./scripts/status_stage4_stack.sh
```

The scripts create idempotent tmux sessions named `agri-ros-stage4` and
`agri-mcp-stage4`. The MCP launcher reads the server's current Tailscale IPv4
address dynamically. It refuses `0.0.0.0`, public/LAN addresses, or an address
outside Tailscale's `100.64.0.0/10` range. DNS-rebinding protection allows only
localhost and that exact Tailscale address.

ROS remains loopback-only (`ROS_IP=127.0.0.1`); the MacBook connects only to:

```text
http://<SERVER_TAILSCALE_IP>:8000/mcp
```

Copy [`examples/harness-stage4.cordis.yml`](examples/harness-stage4.cordis.yml)
into the Harness Cordis patch and replace the placeholder. The resulting tool
names are:

```text
mcp__agri_ros__ros_check_online
mcp__agri_ros__ros_list_nodes
mcp__agri_ros__ros_list_topics
mcp__agri_ros__get_robot_status
```

Tailscale is the network boundary for this read-only experiment. Before any
real control capability is added, introduce application authentication,
device-scoped ACLs, audit logs, human confirmation, limits, and emergency stop.

## Test

When the repository catkin workspace is built:

```bash
cd <REPOSITORY_ROOT>/agri_mcp_server
UV_CACHE_DIR=/tmp/agri_mcp_uv_cache uv run pytest -q
```

For another built workspace:

```bash
AGRI_CATKIN_WS=<BUILT_CATKIN_WORKSPACE> \
  UV_CACHE_DIR=/tmp/agri_mcp_uv_cache uv run pytest -q
```

With both services running, execute the live HTTP smoke test:

```bash
.venv/bin/python tests/http_smoke.py
```
