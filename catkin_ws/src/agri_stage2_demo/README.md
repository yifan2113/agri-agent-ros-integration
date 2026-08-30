# Agri Stage 2 Demo

这是阶段 2 的服务器侧、无硬件安全验证包。它证明 Ubuntu 服务器上的 ROS
Noetic、catkin 工作空间、Agri_ROS 接口包和 ROS service 调用链可以正常工作。

这不是完整 Agri_ROS 机器人系统：当前只编译了 Agri_ROS 的 `agr_service`
接口包，并新增本包作为模拟状态服务；导航、SLAM、传感器、底盘和电机控制均未启动。

## 数据流

```text
ROS client
  -> /agri/demo_status
  -> agri_stage2_status_server
  -> JSON 状态结果（无硬件、只读）
```

服务名：

```text
/agri/demo_status
```

请求复用了 `agr_service/agr_service` 类型。`state` 必须是 `status`，否则返回
`UNSUPPORTED_STATE_STAGE2`；`control`、`planning`、`slam`、`navigation`
四个字段必须全部为零，任何非零值都会被拒绝并返回
`CONTROL_DISABLED_STAGE2`。因此这个节点不能启动算法或控制机器人。

## 运行

```bash
cd <REPOSITORY_ROOT>/catkin_ws
source /opt/ros/noetic/setup.bash
source devel/setup.bash
roslaunch agri_stage2_demo status_demo.launch
```

验证：

```bash
rosservice call /agri/demo_status \
  "state: 'status'
control: 0
planning: 0
slam: 0
navigation: 0"
```

正常结果会明确包含：

```text
mode=safe_status_only
ros_online=true
hardware_connected=false
```
