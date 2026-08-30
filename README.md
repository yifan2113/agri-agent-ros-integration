# 农业机器人智能体 ROS 集成实验

本仓库记录 DeepSeek Harness、MCP、ROS Noetic 与 Agri_ROS 的分阶段集成实验。
当前阶段以无硬件、只读验证为主，不启动导航、建图、传感器驱动、底盘或执行器。

## 实验阶段

| 阶段 | 实验内容 | 状态 |
| --- | --- | --- |
| 阶段 1 | 在 MacBook 上使用 mock 农业工具验证 Harness 智能体调用流程 | 已完成，位于[独立仓库](https://github.com/yifan2113/deepseek-harness-agri-demo) |
| 阶段 2 | 在 Ubuntu 服务器运行 ROS Noetic、Agri_ROS 接口与安全状态服务 | 已完成 |
| 阶段 3 | 实现只读 `agri_mcp_server`，连接 MCP 与 ROS | 已完成 |
| 阶段 4 | MacBook Harness 通过 Tailscale 调用服务器 MCP 工具 | 已完成 |
| 阶段 5 | 逐步接入离线数据、仿真和真实算法 | 计划中 |

## 仓库结构

```text
catkin_ws/src/Agri_ROS/          Agri_ROS 上游 submodule
catkin_ws/src/agri_stage2_demo/  阶段 2 安全状态服务
agri_mcp_server/                 阶段 3–4 MCP 与 ROS 桥接服务
harness/                         Harness 配置模板
scripts/                         ROS Noetic 安装脚本
docs/                            实验报告、架构和安全说明
data/                            数据管理规范
```

## 获取源码

```bash
git clone --recurse-submodules \
  https://github.com/yifan2113/agri-agent-ros-integration.git
cd agri-agent-ros-integration
```

如果克隆时没有初始化 submodule，可执行：

```bash
git submodule update --init --recursive
```

## 阶段 2：ROS 安全状态服务

阶段 2 只构建 Agri_ROS 的 `agr_service` 接口包和本仓库的
`agri_stage2_demo`。新增服务 `/agri/demo_status` 只接受状态查询，所有动作字段
必须为零；任何非零值都会被拒绝。

```bash
cd catkin_ws
source /opt/ros/noetic/setup.bash
catkin init
catkin config --extend /opt/ros/noetic \
  --cmake-args -DCMAKE_BUILD_TYPE=Release -DPYTHON_EXECUTABLE=/usr/bin/python3
catkin build agr_service agri_stage2_demo
source devel/setup.bash
roslaunch agri_stage2_demo status_demo.launch
```

详细服务协议见
[`catkin_ws/src/agri_stage2_demo/README.md`](catkin_ws/src/agri_stage2_demo/README.md)。

## 阶段 3：本机 MCP 与 ROS 桥接

阶段 3 提供四个白名单只读工具：

- `ros_check_online`
- `ros_list_nodes`
- `ros_list_topics`
- `get_robot_status`

MCP 服务使用 Python 3.12，ROS adapter 使用 ROS Noetic 的系统 Python 3.8，
两个环境通过受限子进程和 JSON 数据进行隔离。

```bash
cd agri_mcp_server
uv sync --python 3.12 --locked
./scripts/run_server.sh
```

阶段 3 仅监听 `http://127.0.0.1:8000/mcp`。

## 阶段 4：Harness 跨机器调用

服务器端通过 tmux 启动 ROS 与 MCP：

```bash
cd agri_mcp_server
./scripts/start_stage4_stack.sh
./scripts/status_stage4_stack.sh
```

MacBook 端可参考
[`harness/cordis.stage4.yml.example`](harness/cordis.stage4.yml.example)，将
`<SERVER_TAILSCALE_IP>` 替换为服务器实际 Tailscale IPv4。ROS master 始终限制
在服务器 loopback，跨机器只开放只读 MCP endpoint。

## 测试

```bash
cd agri_mcp_server
UV_CACHE_DIR=/tmp/agri_mcp_uv_cache uv run pytest -q
```

当前验收结果为 5 项测试全部通过。

## 文档

- [阶段 1–4 实验报告](docs/experiment-report-stage1-4.md)
- [系统架构](docs/architecture.md)
- [安全边界](docs/safety-boundary.md)
- [数据管理规范](data/README.md)

## 安全边界

当前版本不提供任意 ROS service 调用、topic 发布、`/cmd_vel`、CAN、串口、电机或
执行器工具。阶段 2–4 的目的仅是验证 Harness、MCP 与 ROS 之间的只读通信链路。
