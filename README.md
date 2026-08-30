# Agri Agent ROS Integration

Safe integration experiments between DeepSeek Harness, MCP, ROS Noetic, and
Agri_ROS.

Stages 2–4 establish a hardware-free ROS baseline, a local read-only MCP
bridge, and a Tailscale-restricted Harness connection. They intentionally do
not launch navigation, SLAM, sensors, motor control, or actuators.

| Stage | Result |
| --- | --- |
| 1 | Harness mock demo; maintained in the separate stage 1 repository |
| 2 | ROS Noetic, Agri_ROS interface, and safe status-only service |
| 3 | Local MCP-to-ROS process bridge with four read-only tools |
| 4 | MacBook Harness calls those tools through a Tailscale-only endpoint |
| 5 | Planned progressive integration with simulation, recorded data, then hardware |

## Stage 2 scope

```text
ROS client
  -> /agri/demo_status
  -> agri_stage2_status_server
  -> structured JSON status
```

The status service accepts only `state=status` with `control`, `planning`,
`slam`, and `navigation` all set to zero. All action-like requests fail closed.

## Workspace

```bash
git clone --recurse-submodules \
  https://github.com/yifan2113/agri-agent-ros-integration.git
cd agri-agent-ros-integration/catkin_ws

source /opt/ros/noetic/setup.bash
catkin init
catkin config --extend /opt/ros/noetic \
  --cmake-args -DCMAKE_BUILD_TYPE=Release -DPYTHON_EXECUTABLE=/usr/bin/python3
catkin build agr_service agri_stage2_demo
source devel/setup.bash
roslaunch agri_stage2_demo status_demo.launch
```

See [`catkin_ws/src/agri_stage2_demo/README.md`](catkin_ws/src/agri_stage2_demo/README.md)
for the service contract and validation request.

## Stage 3: local MCP bridge

Stage 3 adds four allowlisted, read-only tools:

- `ros_check_online`
- `ros_list_nodes`
- `ros_list_topics`
- `get_robot_status`

The MCP process uses Python 3.12, while a small subprocess adapter uses ROS
Noetic's system Python 3.8. This keeps the two incompatible dependency sets
separate.

```bash
cd agri_mcp_server
uv sync --python 3.12 --locked
./scripts/run_server.sh
```

The stage 3 endpoint is local-only: `http://127.0.0.1:8000/mcp`.
See [`agri_mcp_server/README.md`](agri_mcp_server/README.md) for the complete
architecture and test instructions.

## Stage 4: Harness connection

On the server, start the ROS and MCP processes in isolated tmux sessions:

```bash
cd agri_mcp_server
./scripts/start_stage4_stack.sh
./scripts/status_stage4_stack.sh
```

On the MacBook, copy [`harness/cordis.stage4.yml.example`](harness/cordis.stage4.yml.example)
to the Harness patch location, replace `<SERVER_TAILSCALE_IP>`, and run the
Harness web command. ROS itself remains bound to server loopback; only the
read-only MCP endpoint is reachable over Tailscale.

The detailed experiment procedure, results, Git history plan, and stage 5
roadmap are in [`docs/experiment-report-stage1-4.md`](docs/experiment-report-stage1-4.md).

## Safety

This repository does not currently provide arbitrary ROS service calls, topic
publishing, `/cmd_vel`, CAN, serial, motor, or actuator tools.
