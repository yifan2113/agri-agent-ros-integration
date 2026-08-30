# Agri MCP Server — Stage 3

Read-only MCP bridge between a modern Python environment and ROS Noetic.

## Architecture

```text
MCP client
  -> Streamable HTTP (127.0.0.1:8000/mcp)
  -> agri_mcp_server (Python 3.12 / MCP SDK 2.x)
  -> allowlisted asynchronous subprocess
  -> ros_adapter (system Python 3.8 / ROS Noetic)
  -> ROS master and /agri/demo_status
```

The process boundary prevents the MCP environment from importing ROS Noetic's
system-Python packages and keeps both dependency sets reproducible.

## Tools

| Tool | Read-only behavior |
| --- | --- |
| `ros_check_online` | Check whether the local ROS master is reachable |
| `ros_list_nodes` | List node names registered with the ROS master |
| `ros_list_topics` | List published topic names and message types |
| `get_robot_status` | Call `/agri/demo_status` with every action field fixed to zero |

The server does not expose topic publishing, arbitrary service calls,
`roslaunch`, `/cmd_vel`, motors, navigation, SLAM, sensors, or actuators.

## Install

From the repository root:

```bash
cd agri_mcp_server
uv sync --python 3.12 --locked
```

The catkin workspace must already be built. By default the adapter uses
`../catkin_ws`; set `AGRI_CATKIN_WS` when deploying with another layout.

## Run locally

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

Endpoint: `http://127.0.0.1:8000/mcp`.

## Test

```bash
cd <REPOSITORY_ROOT>/agri_mcp_server
UV_CACHE_DIR=/tmp/agri_mcp_uv_cache uv run pytest -q
```
