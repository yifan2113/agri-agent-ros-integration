# Agri Agent ROS Integration

Safe integration experiments between DeepSeek Harness, MCP, ROS Noetic, and
Agri_ROS.

This repository starts with the stage 2 ROS baseline. It intentionally exposes
only a hardware-free status service and does not launch navigation, SLAM,
sensors, motor control, or actuators.

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

## Safety

This repository does not currently provide arbitrary ROS service calls, topic
publishing, `/cmd_vel`, CAN, serial, motor, or actuator tools.
