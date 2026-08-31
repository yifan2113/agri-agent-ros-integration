# 农业机器人智能体 ROS 集成实验

本项目用于验证 DeepSeek Harness、MCP、ROS Noetic 与 Agri_ROS 之间的分阶段
集成链路。实验从完全不依赖硬件的 mock 工具开始，逐步完成服务器 ROS 环境、
MCP→ROS 桥接以及 MacBook→服务器的跨机器调用。

阶段 1–4 当前只验证智能体编排和只读通信链路，不启动导航、建图、传感器驱动、
底盘、电机或其他执行器。

## 总体链路

```text
用户自然语言任务
  -> MacBook DeepSeek Harness
  -> agri_ros MCP 工具
  -> Tailscale Streamable HTTP
  -> Ubuntu agri_mcp_server
  -> 固定白名单 ROS adapter
  -> ROS master 与 /agri/demo_status
  -> 结构化结果返回 Harness
```

## 阶段概览

| 阶段 | 主要工作 | 阶段性结果 |
| --- | --- | --- |
| 阶段 1 | 在 MacBook 上编写 mock 农业工具，验证 Harness 工具编排 | 模型按顺序调用状态、地图、路径规划和模拟任务工具 |
| 阶段 2 | 在 Ubuntu 上安装 ROS Noetic，编译 Agri_ROS 接口并实现安全状态服务 | ROS service 调用成功，所有动作型请求默认拒绝 |
| 阶段 3 | 编写 `agri_mcp_server`，连接 Python 3.12 MCP 与 Python 3.8 ROS | 本机 MCP Client 可发现并调用四个只读 ROS 工具 |
| 阶段 4 | 通过 Tailscale 将 MacBook Harness 接入服务器 MCP | Harness 成功跨机器获取真实 ROS 节点、topic 和状态 |
| 阶段 5 | 逐步接入离线数据、仿真和真实算法 | 计划中 |

## 仓库结构

```text
catkin_ws/src/Agri_ROS/          Agri_ROS 上游 submodule
catkin_ws/src/agri_stage2_demo/  阶段 2 安全状态服务
agri_mcp_server/                 阶段 3–4 MCP 与 ROS 桥接服务
harness/                         Harness MCP 配置模板
scripts/                         ROS Noetic 精简安装脚本
docs/                            实验报告、架构和安全说明
data/                            数据管理规范
```

## 获取源码

```bash
git clone --recurse-submodules \
  https://github.com/yifan2113/agri-agent-ros-integration.git
cd agri-agent-ros-integration
```

如果克隆时未初始化 Agri_ROS submodule，可执行：

```bash
git submodule update --init --recursive
```

Agri_ROS 固定在本实验验证过的提交
`75e9a04eaad7c76b2440a22a9c3b1c63bc850204`，阶段 2–4 没有修改其上游源码。

## 阶段 1：Harness mock 农业工具

### 工作内容

阶段 1 位于独立仓库
[`deepseek-harness-agri-demo`](https://github.com/yifan2113/deepseek-harness-agri-demo)。
该阶段不连接 ROS、服务器和机器人，而是在 Harness 中注册四个固定 mock 工具：

| 工具 | 作用 |
| --- | --- |
| `get_robot_status` | 返回模拟电量、位姿、工作模式和安全状态 |
| `get_field_map` | 返回模拟农田、作物行和障碍物信息 |
| `plan_weeding_path` | 根据模拟地图生成除草路径 |
| `start_weeding_task` | 返回 `simulated=true` 的模拟任务结果 |

### 运行指令

在准备好的 Harness 源码目录中执行：

```bash
cd <HARNESS_ROOT>
pnpm install
pnpm dsh web --patch ./scratch-plugin/cordis.yml
```

浏览器访问 `http://127.0.0.1:3080`，输入农业任务并要求模型依次检查机器人、
读取地图、规划路径和启动模拟任务。

### 阶段性结果

模型能够按照
`get_robot_status → get_field_map → plan_weeding_path → start_weeding_task`
的依赖关系调用工具，并在最终结果中明确说明任务是模拟执行。该阶段证明 Harness
能够完成农业任务级工具编排，但不代表 ROS 或真实机器人已经运行。

## 阶段 2：Ubuntu ROS 与安全状态服务

### 工作内容

服务器采用 Ubuntu 20.04 与 ROS Noetic 精简环境。Agri_ROS 中只目标构建：

- `agr_service`：定义 Agri_ROS 使用的 service 通信类型。
- `agri_stage2_demo`：本项目新增的安全 service server。

新增 ROS service：

```text
/agri/demo_status
```

它仅接受 `state=status`，且 `control`、`planning`、`slam`、`navigation` 必须
全部为零。任何动作字段非零都会返回 `CONTROL_DISABLED_STAGE2`；其他 `state`
会返回 `UNSUPPORTED_STATE_STAGE2`。

### 安装与构建指令

精简安装脚本仅适用于 Ubuntu 20.04 amd64：

```bash
sudo bash scripts/install_ros_noetic_minimal.sh
```

构建两个目标包：

```bash
cd catkin_ws
source /opt/ros/noetic/setup.bash
catkin init
catkin config --extend /opt/ros/noetic \
  --cmake-args -DCMAKE_BUILD_TYPE=Release -DPYTHON_EXECUTABLE=/usr/bin/python3
catkin build agr_service agri_stage2_demo
source devel/setup.bash
```

### 启动与验证指令

```bash
roslaunch agri_stage2_demo status_demo.launch
```

在另一个已加载 ROS/catkin 环境的终端调用：

```bash
rosservice call /agri/demo_status \
  "state: 'status'
control: 0
planning: 0
slam: 0
navigation: 0"
```

### 阶段性结果

- `agr_service` 和 `agri_stage2_demo` 构建成功。
- ROS master、`/rosout` 和 `/agri_stage2_status_server` 正常注册。
- 合法状态请求返回 `mode=safe_status_only`、`ros_online=true` 和
  `hardware_connected=false`。
- 非零动作字段及非法状态请求均被拒绝。

详细协议见
[`catkin_ws/src/agri_stage2_demo/README.md`](catkin_ws/src/agri_stage2_demo/README.md)。

## 阶段 3：本机 MCP→ROS 桥接

### 工作内容

MCP SDK 运行于 Python 3.12，而 Ubuntu 20.04 的 ROS Noetic Python 模块位于
系统 Python 3.8。为避免依赖和 ABI 冲突，本项目采用两个进程：

```text
MCP Client
  -> agri_mcp_server（Python 3.12）
  -> 固定动作白名单、5 秒超时、JSON
  -> ros_adapter（系统 Python 3.8）
  -> ROS master / /agri/demo_status
```

MCP 仅公开四个只读工具：

| MCP 工具 | 对应行为 |
| --- | --- |
| `ros_check_online` | 检查本机 ROS master 是否可访问 |
| `ros_list_nodes` | 读取 ROS master 中注册的节点 |
| `ros_list_topics` | 读取已发布 topic 的名称和消息类型 |
| `get_robot_status` | 使用全零动作字段调用 `/agri/demo_status` |

### 运行指令

先按阶段 2 的方法启动 ROS 状态服务，再在另一个终端执行：

```bash
cd agri_mcp_server
uv sync --python 3.12 --locked
./scripts/run_server.sh
```

阶段 3 MCP endpoint 仅监听：

```text
http://127.0.0.1:8000/mcp
```

两个服务均运行时，可以执行本机 HTTP 冒烟验证：

```bash
.venv/bin/python tests/http_smoke.py
```

### 阶段性结果

- MCP Client 只能发现四个预期工具。
- ROS 在线检查返回 master URI 与 PID。
- 节点查询返回 `/rosout` 和 `/agri_stage2_status_server`。
- topic 查询返回 `/rosout` 和 `/rosout_agg`。
- 状态工具返回 `safe_status_only` 与 `hardware_connected=false`。
- 非白名单动作在到达 ROS 前即被拒绝。

## 阶段 4：MacBook Harness 跨机器调用

### 工作内容

阶段 4 使用 Tailscale 连接 MacBook 与 Ubuntu 服务器。ROS master 和 ROS 节点
仍限制在服务器 `127.0.0.1`；只有 MCP HTTP endpoint 绑定到服务器当前的
Tailscale IPv4。代码拒绝 `0.0.0.0`、普通局域网/公网地址以及不在
`100.64.0.0/10` 范围内的地址。

### 服务器端指令

使用两个 tmux 会话分别运行 ROS 与 MCP：

```bash
cd agri_mcp_server
./scripts/start_stage4_stack.sh
./scripts/status_stage4_stack.sh
```

脚本创建：

```text
agri-ros-stage4
agri-mcp-stage4
```

### MacBook 端指令

将 [`harness/cordis.stage4.yml.example`](harness/cordis.stage4.yml.example) 复制到
Harness 项目的 `scratch-plugin/cordis.stage4.yml`，并将
`<SERVER_TAILSCALE_IP>` 替换为服务器当前的 Tailscale IPv4。

先验证端口连通：

```bash
nc -vz <SERVER_TAILSCALE_IP> 8000
```

再启动 Harness：

```bash
cd <HARNESS_ROOT>
pnpm dsh web --patch scratch-plugin/cordis.stage4.yml
```

在 Web UI 中要求模型使用 `agri_ros` 工具检查 ROS 在线状态、节点、topic 和
机器人状态。

### 阶段性结果

- MacBook 成功连接服务器 Tailscale MCP endpoint。
- Harness 发现四个 `mcp__agri_ros__*` 工具。
- 模型返回的节点、topic 和状态与服务器 ROS 实际结果一致。
- 服务器日志记录到来自 MacBook 的 MCP GET/POST 请求。
- 全程没有加载或调用阶段 1 的 mock 农业工具。

由此完成：

```text
自然语言 -> Harness -> 远程 MCP Server -> ROS service -> 结果返回模型
```

## 测试

`agri_mcp_server/tests/` 当前包含 5 个 `pytest` 测试用例：

| 测试内容 | 验证目标 |
| --- | --- |
| MCP 工具发现与调用 | 只能发现四个预期工具，且调用能返回结构化结果 |
| Tailscale Host allowlist | 合法的 `100.64.0.0/10` 地址被允许，其他地址被拒绝 |
| MCP 绑定地址限制 | 只允许 localhost 或配置的准确 Tailscale 地址，拒绝 `0.0.0.0` |
| ROS 动作白名单 | `start_motor` 等未授权动作在启动 ROS adapter 前被拒绝 |
| ROS 在线/离线结构化结果 | 无论 ROS master 是否在线，都返回可解析的状态和错误码 |

运行前需要完成阶段 2 构建。若使用本仓库默认 catkin 工作空间：

```bash
cd agri_mcp_server
UV_CACHE_DIR=/tmp/agri_mcp_uv_cache uv run pytest -q
```

若使用其他已经构建的 catkin 工作空间：

```bash
AGRI_CATKIN_WS=<BUILT_CATKIN_WORKSPACE> \
  UV_CACHE_DIR=/tmp/agri_mcp_uv_cache uv run pytest -q
```

输出：

```text
.....                                                                    [100%]
5 passed
```

## 安全边界

当前版本不提供任意 ROS service 调用、topic 发布、`roslaunch`、`/cmd_vel`、
CAN、串口、电机或执行器控制。MCP 与 ROS adapter 均执行固定动作白名单，ROS
仅监听服务器 loopback，跨机器只开放只读 MCP endpoint。

## 文档

- [阶段 1–4 实验报告](docs/experiment-report-stage1-4.md)
- [系统架构](docs/architecture.md)
- [安全边界](docs/safety-boundary.md)
- [数据管理规范](data/README.md)
