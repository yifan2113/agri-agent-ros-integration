# 农业机器人智能体平台阶段 1–4 实验报告

## 1. 报告信息

| 项目 | 内容 |
| --- | --- |
| 项目名称 | 基于 DeepSeek Harness、MCP 与 Agri_ROS 的农业机器人智能体平台 |
| 报告范围 | 阶段 1–4 |
| MacBook 项目路径 | `<HARNESS_ROOT>` |
| Ubuntu catkin 工作空间 | `<REPOSITORY_ROOT>/catkin_ws` |
| Agri_ROS 版本 | `75e9a04eaad7c76b2440a22a9c3b1c63bc850204` |
| 阶段 1 GitHub | <https://github.com/yifan2113/deepseek-harness-agri-demo> |
| 阶段 2–5 GitHub | <https://github.com/yifan2113/agri-agent-ros-integration> |
| 报告状态 | 阶段 1–4 已完成 |

## 2. 摘要

本实验的目标是验证一条从大语言模型智能体到农业机器人 ROS 系统的安全调用链，
并为后续接入建图、导航、感知和控制算法建立可复现的工程基础。

实验按风险和依赖逐步推进：

1. 在 MacBook 上使用 DeepSeek Harness 原生插件和 mock 数据验证智能体工具调用闭环。
2. 在 Ubuntu 20.04 服务器上安装精简 ROS Noetic，建立 catkin 工作空间，并实现无硬件、只读的 ROS 状态服务。
3. 编写独立 `agri_mcp_server`，通过受限适配器连接现代 MCP Python 环境与 ROS Noetic Python 环境。
4. 使用 Tailscale 和 Streamable HTTP 将 MacBook Harness 与服务器 MCP/ROS 链路连通，并完成真实跨机器验收。

最终实现的链路为：

```text
用户自然语言任务
  -> MacBook DeepSeek Harness
  -> mcp__agri_ros__* 工具
  -> Tailscale Streamable HTTP
  -> Ubuntu agri_mcp_server
  -> 固定白名单 ROS adapter
  -> ROS master / ROS service
  -> 结构化结果返回 Harness
```

阶段 1–4 均不连接真实机器人硬件，不发布控制 topic，不启动导航、SLAM、
传感器驱动或电机节点。实验验证的是智能体编排、ROS/MCP 通信和安全边界，
不是机器人现场作业性能。

## 3. 总体实验目的

### 3.1 功能目的

- 验证 DeepSeek Harness 能根据自然语言任务主动选择和调用农业工具。
- 验证 Ubuntu 服务器能够运行 ROS Noetic 与 Agri_ROS 自有接口类型。
- 验证 MCP Server 能将 ROS 能力转换为 Harness 可发现、可调用的工具。
- 验证 MacBook 与 Ubuntu 服务器之间可以通过受限网络完成跨机器调用。
- 为阶段 5 的真实算法、回放数据和硬件接入提供统一接口基础。

### 3.2 安全目的

- 不让大模型直接访问 `/cmd_vel`、CAN、串口、电机或任意 ROS API。
- 初期仅开放状态读取和系统自检工具。
- 对含义不明确的控制字段采用默认拒绝策略。
- 将 ROS master 限制在服务器 loopback，将远程入口限制在 Tailscale MCP 端口。
- 明确区分“ROS 在线”“模拟服务在线”和“真实硬件已连接”。

### 3.3 工程目的

- 分离 Harness、MCP 和 ROS 的运行环境，减少依赖冲突。
- 保持上游 Agri_ROS 源码干净并固定版本。
- 使用测试、依赖锁文件和启动脚本保证实验可复现。
- 为阶段 5 建立可逐项扩展的任务级工具结构。

## 4. 实验环境

### 4.1 MacBook 端

| 项目 | 内容 |
| --- | --- |
| 操作系统 | macOS / Apple Silicon arm64 |
| Harness 路径 | `<HARNESS_ROOT>` |
| 阶段 1 patch | `scratch-plugin/cordis.yml` |
| 阶段 4 patch | `scratch-plugin/cordis.stage4.yml` |
| Web UI | `http://127.0.0.1:3080` |
| Tailscale IPv4 | `<MACBOOK_TAILSCALE_IP>` |

### 4.2 Ubuntu 服务器端

| 项目 | 内容 |
| --- | --- |
| 操作系统 | Ubuntu 20.04 |
| ROS | ROS Noetic，`roslaunch 1.17.4` |
| catkin 工作空间 | `<REPOSITORY_ROOT>/catkin_ws` |
| ROS Python | `/usr/bin/python3`，Python 3.8.10 |
| MCP Python | 项目 `.venv`，Python 3.12.7 |
| MCP SDK | `mcp==2.1.1` |
| Tailscale IPv4 | `<SERVER_TAILSCALE_IP>` |
| ROS master | `127.0.0.1:11311` |
| MCP endpoint | `http://<SERVER_TAILSCALE_IP>:8000/mcp` |

### 4.3 源码与依赖状态

- Agri_ROS 上游仓库：<https://github.com/Fontainebleau2021/Agri_ROS>。
- 实验固定提交：`75e9a04eaad7c76b2440a22a9c3b1c63bc850204`。
- Agri_ROS 当前工作树干净，没有为阶段 2–4 修改上游源码。
- catkin 共识别 32 个 ROS 包，阶段 2 只目标构建 `agr_service` 和
  `agri_stage2_demo`。
- MCP 使用 `uv.lock` 固定依赖版本；`.venv` 不应提交到 Git。

## 5. 阶段 1：Harness mock 农业智能体 demo

### 5.1 实验目的

在不依赖 ROS、服务器、网络和硬件的情况下，优先验证以下最小智能体闭环：

```text
用户提出农业任务
  -> 模型理解任务
  -> 模型选择工具
  -> Harness 执行工具
  -> 工具结果返回模型
  -> 模型组织后续步骤
  -> 输出最终结果
```

阶段 1 回答的问题是“模型和 Harness 能否完成农业任务级工具编排”，不回答
“ROS 能否运行”或“机器人能否真实作业”。

### 5.2 实验内容

在 DeepSeek Harness 中新增 Cordis 原生插件：

```text
scratch-plugin/src/agri-demo.ts
```

插件注册四个工具：

| 工具 | 输入 | 模拟输出与作用 |
| --- | --- | --- |
| `get_robot_status` | `robotId` | 电量 82%、idle、模拟位姿、weeder、安全状态 ok |
| `get_field_map` | `fieldId` | 玉米地、8 行、0.6 m 行距、作业区和两个障碍物 |
| `plan_weeding_path` | `robotId`、`fieldId` | 420 m、38 min、96% 覆盖率和模拟 waypoint |
| `start_weeding_task` | `robotId`、`pathId` | 返回 `simulated=true` 的模拟任务，不发送真实命令 |

加载配置：

```yaml
- insert:
    - id: agri-demo-tools
      name: !!js process.cwd() + '/scratch-plugin/src/agri-demo.ts'
```

### 5.3 实验流程

1. 在 MacBook 的 Harness 源码目录中创建 `scratch-plugin`。
2. 使用 TypeScript 定义机器人状态、农田地图、除草路径和任务结果类型。
3. 使用 `defineTool` 注册四个农业工具，并为输入参数编写说明。
4. 确保 `start_weeding_task` 明确返回 `simulated=true`。
5. 使用 Cordis patch 将插件插入 Web profile。
6. 启动 Harness：

   ```bash
   pnpm dsh web --patch ./scratch-plugin/cordis.yml
   ```

7. 在 `http://127.0.0.1:3080` 输入除草任务，要求模型先检查状态、读取地图、
   规划路径，再启动模拟任务。
8. 检查模型是否按任务依赖关系调用工具，而不是直接跳到最后一步。

### 5.4 实验结果

模型能够按以下逻辑完成农业任务编排：

```text
get_robot_status
  -> get_field_map
  -> plan_weeding_path
  -> start_weeding_task
```

阶段 1 验证成功：

- Harness 能加载自定义农业插件。
- 模型能读取工具描述并构造正确参数。
- 模型能根据前序工具结果继续调用下一工具。
- 最终结果明确说明任务为模拟任务，不控制真实机器人。

### 5.5 阶段限制

- 所有结果为固定 mock 数据。
- 不连接 ROS、数据库、地图服务、仿真器或机器人。
- 路径规划结果没有经过几何、动力学或障碍物算法验证。
- “任务已启动”仅是返回值，不代表存在后台任务进程。

### 5.6 Git 状态

- GitHub 仓库：`yifan2113/deepseek-harness-agri-demo`。
- 农业插件初始提交：`92ca2efa`（`Add agricultural robot agent demo`）。
- 当前主分支提交：`8a8ff170`（`Make demo README the repository landing page`）。

## 6. 阶段 2：Ubuntu ROS Noetic 与安全状态服务

### 6.1 实验目的

- 在 Ubuntu 服务器上建立最小 ROS Noetic 运行环境。
- 验证 Agri_ROS 自有 service 类型可被 catkin 编译和 Python 导入。
- 创建一个不依赖硬件的真实 ROS service 调用闭环。
- 在进入 MCP 前先建立 ROS 层的默认拒绝安全边界。

阶段 2 中 MacBook Harness 与 Ubuntu ROS 仍然独立；跨机器连接属于阶段 4。

### 6.2 ROS 安装与工作空间准备

采用精简安装方案：

```text
ros-noetic-ros-base
python3-rosdep
python3-catkin-tools
build-essential
```

没有安装 `desktop-full`、Gazebo、RViz 或完整仿真环境。安装前通过 APT dry-run
检查变更，并使用隔离的软件源列表避免已有 `focal-proposed`、第三方 GCC、
CUDA、NVIDIA、Docker 和 OpenEMMA 运行环境被意外升级。

安装后完成：

- `rosdep init` 与 `rosdep update`。
- `roscore`、`rosout`、topic 和 service 基础验证。
- catkin 工作空间初始化。
- 工作空间显式扩展 `/opt/ros/noetic`。
- CMake 使用 `Release` 和 `/usr/bin/python3`。

设置系统 Python 的原因是 ROS Noetic Python 包安装在 Ubuntu 系统 Python
3.8 中，服务器默认 Conda Python 3.12 不能直接替代它。

### 6.3 为什么只构建两个包

#### `agr_service`

`agr_service` 是 Agri_ROS 中的接口定义包，其 `.srv` 内容为：

```text
string state
uint8 control
uint8 planning
uint8 slam
uint8 navigation
---
string result
```

编译它可验证：

- Agri_ROS 源码被 catkin 正确识别。
- 自定义 service 的 Python/C++ 类型可成功生成。
- 后续节点可以使用真实的 `agr_service/agr_service` 类型通信。

它只定义通信合同，本身不提供一个满足本实验安全要求的 service server。

#### `agri_stage2_demo`

`agri_stage2_demo` 是本项目新增的安全实现包，负责注册：

```text
/agri/demo_status
```

因此两个包共同形成最小但真实的 Agri_ROS 链路：

```text
agr_service：定义接口
agri_stage2_demo：实现接口
```

其余 30 个包涉及传感器、标定、SLAM、感知、规划、导航、控制和厂商依赖。
在没有硬件和数据的情况下全量构建，会把 ROS 基础验证与算法/驱动问题混在一起，
也可能启动高风险控制路径，所以本阶段不构建、不启动。

### 6.4 安全请求规则

服务仅接受：

```text
state == "status"
control == 0
planning == 0
slam == 0
navigation == 0
```

拒绝规则：

| 条件 | 错误码 | 目的 |
| --- | --- | --- |
| 任一数值控制字段非零 | `CONTROL_DISABLED_STAGE2` | 防止含义不明确的值触发模块或控制动作 |
| `state` 不是 `status` | `UNSUPPORTED_STATE_STAGE2` | 防止 `start`、`run` 等字符串被误认为动作命令 |

该策略采用 fail-closed 原则：当接口语义不明确时默认拒绝，而不是猜测
`navigation=1` 或 `control=1` 的真实含义。

正常返回明确包含：

```json
{
  "success": true,
  "stage": 2,
  "mode": "safe_status_only",
  "ros_online": true,
  "hardware_connected": false
}
```

### 6.5 实验流程

1. 检查 Ubuntu 版本、CPU 架构、磁盘和现有关键进程。
2. 对精简 ROS 安装进行 APT dry-run。
3. 安装 ROS Noetic ros-base 与 catkin/rosdep 工具。
4. 初始化 `<REPOSITORY_ROOT>/catkin_ws`。
5. 将 Agri_ROS 放入 `catkin_ws/src/Agri_ROS` 并固定上游提交。
6. 创建 `catkin_ws/src/agri_stage2_demo`。
7. 目标构建：

   ```bash
   catkin build agr_service agri_stage2_demo
   ```

8. 启动：

   ```bash
   roslaunch agri_stage2_demo status_demo.launch
   ```

9. 调用正常状态请求。
10. 分别调用非零控制字段和非法 `state`，验证拒绝结果。

### 6.6 实验结果

- catkin 识别 32 个包。
- `agr_service` 与 `agri_stage2_demo` 均构建成功。
- 构建结果无 warning、无 failed、无 abandoned。
- ROS master、`/rosout` 和 `/agri_stage2_status_server` 正常注册。
- 合法状态请求返回 `safe_status_only`。
- 非零动作字段被拒绝。
- `state=start` 实测返回 `UNSUPPORTED_STATE_STAGE2`。
- OpenEMMA 任务未因 ROS 安装、构建和联调中断。

阶段 2 达到预期目标，但它代表“ROS 服务器侧最小安全基线完成”，不代表完整
Agri_ROS 算法栈或真实机器人已经运行。

## 7. 阶段 3：实现 agri_mcp_server 并连接 ROS

### 7.1 实验目的

- 将阶段 2 的 ROS 能力暴露为标准 MCP 工具。
- 解决 MCP 现代 Python 与 ROS Noetic 系统 Python 的版本隔离问题。
- 只开放固定、只读、可审计的 ROS 操作。
- 在对 MacBook 开放网络前，先完成服务器本机 MCP→ROS 闭环。

### 7.2 架构设计

```text
MCP Client
  -> Streamable HTTP 127.0.0.1:8000/mcp
  -> agri_mcp_server（Python 3.12.7）
  -> 动作白名单与 5 秒超时
  -> 异步子进程
  -> ros_adapter（系统 Python 3.8.10）
  -> ROS master /agri/demo_status
```

进程隔离的原因：

- 当前 MCP SDK 使用现代 Python 环境。
- ROS Noetic 的 `rospy`、`rosgraph` 和生成的 service 类型位于系统 Python 3.8。
- 在同一个解释器中强行混用会造成依赖和 ABI 风险。
- 子进程边界使 MCP 环境和 ROS 环境可独立升级、测试和排错。

### 7.3 工程内容

主要文件职责：

| 文件 | 职责 |
| --- | --- |
| `server.py` | 注册 MCP 工具、配置 HTTP 传输、安全 Host 校验 |
| `ros_bridge.py` | 异步启动 ROS adapter、解析 JSON、处理超时和进程错误 |
| `ros_adapter.py` | 在 Python 3.8 中查询 ROS master、节点、topic 和状态 service |
| `run_ros_adapter.sh` | source Noetic/catkin 环境并执行固定动作 |
| `run_server.sh` | 阶段 3 localhost 启动入口 |
| `uv.lock` | 锁定 MCP Python 依赖 |

MCP 工具：

| 工具 | 行为 |
| --- | --- |
| `ros_check_online` | 查询 ROS master 是否在线 |
| `ros_list_nodes` | 查询已注册 ROS 节点 |
| `ros_list_topics` | 查询已发布 topic 与类型 |
| `get_robot_status` | 用固定零控制字段调用 `/agri/demo_status` |

明确不提供：

```text
任意 rosservice call
任意 topic publish
任意 roslaunch
/cmd_vel
电机、CAN、串口和执行器控制
导航、SLAM、感知任务启动
```

### 7.4 实验流程

1. 创建独立 Python 3.12 项目和 `.venv`。
2. 通过 `uv` 安装并锁定 `mcp==2.1.1`。
3. 实现系统 Python 3.8 ROS adapter。
4. 在 shell 和 Python 两层分别校验动作白名单。
5. 为子进程增加 5 秒超时和结构化错误码。
6. MCP tool 使用异步子进程，避免同步线程调度卡住。
7. 编写工具发现、非法动作、ROS 离线、Tailscale Host 校验等测试。
8. 启动阶段 2 ROS service 和本机 MCP server。
9. 使用官方 MCP Client 发现并调用四个工具。

### 7.5 实验结果

- MCP Client 仅发现四个预期只读工具。
- `ros_check_online` 返回 ROS master 在线及 PID。
- `ros_list_nodes` 返回 `/rosout` 与 `/agri_stage2_status_server`。
- `ros_list_topics` 返回 `/rosout` 与 `/rosout_agg`。
- `get_robot_status` 返回 `safe_status_only` 和
  `hardware_connected=false`。
- 非白名单动作在到达 ROS 前被拒绝。
- 当前自动化测试共 5 项，全部通过。

阶段 3 达到“服务器本机 MCP→ROS 只读桥接成功”的目标。

## 8. 阶段 4：MacBook Harness 通过 MCP 调用 ROS

### 8.1 实验目的

- 将 MacBook 上的 Harness MCP Client 与 Ubuntu MCP Server 连接。
- 验证工具发现、调用、结构化结果和模型总结的跨机器闭环。
- 在不开放公网和校园网接口的情况下完成远程访问。
- 确认模型调用的是 MCP 工具，而不是阶段 1 mock 工具。

### 8.2 网络与安全设计

实验选择 Tailscale 私有网络：

```text
MacBook：<MACBOOK_TAILSCALE_IP>
服务器：<SERVER_TAILSCALE_IP>
```

最终监听：

```text
ROS master：127.0.0.1:11311
MCP Server：<SERVER_TAILSCALE_IP>:8000
```

安全措施：

- MCP 只允许绑定 localhost 或经过验证的 Tailscale CGNAT 地址。
- 代码拒绝 `0.0.0.0`、校园网 IP、公网 IP 和不在 `100.64.0.0/10` 的地址。
- DNS rebinding Host allowlist 只允许 localhost 与当前 Tailscale 地址。
- 设置 `ROS_IP=127.0.0.1`，使 ROS master 和 ROS 节点 XML-RPC 只监听本机。
- MacBook 不直接访问 ROS master，只访问 MCP。
- 工具集保持阶段 3 的四个只读工具。

当前 tailnet 是阶段 4 只读原型的网络边界。接入真实控制前仍需增加应用层认证、
Tailscale ACL、审计、人工确认、限速和急停。

### 8.3 Harness 配置

为避免模型误用阶段 1 mock 工具，阶段 4 使用独立 patch：

```text
scratch-plugin/cordis.stage4.yml
```

配置核心内容：

```yaml
- insert:
  - id: mcp-agri-ros
    name: '@deepseek-ai/dsh-mcp-client'
    config:
      serverName: agri_ros
      transport: streamable-http
      url: http://<SERVER_TAILSCALE_IP>:8000/mcp
      toolCallTimeoutMs: 10000
      failOnStartupError: true
```

模型看到的工具名为：

```text
mcp__agri_ros__ros_check_online
mcp__agri_ros__ros_list_nodes
mcp__agri_ros__ros_list_topics
mcp__agri_ros__get_robot_status
```

### 8.4 常驻运行方案

初次联调使用前台临时进程，跨实验会话后端口停止监听。随后改用两个独立
tmux 会话：

```text
agri-ros-stage4
agri-mcp-stage4
```

管理脚本：

```text
scripts/run_ros_stage4.sh
scripts/run_server_stage4.sh
scripts/start_stage4_stack.sh
scripts/status_stage4_stack.sh
```

重复执行启动脚本不会重复创建已有会话。

### 8.5 实验流程

1. 检查服务器和 MacBook 的 Tailscale 地址及在线状态。
2. 测试两端 Tailscale 直连；服务器到 MacBook 延迟约 49 ms。
3. 配置 MCP 只绑定服务器 Tailscale 地址。
4. 配置 ROS 只绑定 loopback。
5. 使用 tmux 启动 ROS 和 MCP 常驻服务。
6. 在 MacBook 执行：

   ```bash
   nc -vz <SERVER_TAILSCALE_IP> 8000
   ```

7. 连接成功后启动 Harness：

   ```bash
   pnpm dsh web --patch scratch-plugin/cordis.stage4.yml
   ```

8. 在 Web UI 要求模型通过 `agri_ros` MCP 工具检查 ROS、节点、topic 和机器人状态。
9. 检查模型输出、Harness 工具轨迹和服务器 Uvicorn 请求日志。

### 8.6 实验结果

MacBook 端网络测试成功：

```text
Connection to <SERVER_TAILSCALE_IP> port 8000 succeeded
```

Harness 正常启动于：

```text
http://127.0.0.1:3080
```

模型通过 MCP 返回：

- ROS master 在线。
- Master URI 为 `http://127.0.0.1:11311`。
- 节点为 `/agri_stage2_status_server` 和 `/rosout`。
- topic 为 `/rosout` 和 `/rosout_agg`。
- `/agri/demo_status` 在线。
- 模式为 `safe_status_only`。
- `hardware_connected=false`。
- 全程未调用阶段 1 mock 农业工具。

服务器访问日志记录了来自 MacBook `<MACBOOK_TAILSCALE_IP>` 的 MCP GET/POST 请求，
证明结果确实经过跨机器 MCP 链路，而不是 MacBook 本地 mock 返回。

### 8.7 启动警告说明

MacBook 启动 Harness 时出现的以下内容不影响实验：

- Linux arm64/x64 原生包在 macOS 上 unsupported：属于可选平台包。
- cyclic workspace dependencies：Harness monorepo 工作区依赖提示。
- pnpm 有新版本：不影响当前锁文件安装和运行。
- 命令提示符 `[?]`：表示新的 stage4 Cordis 文件尚未纳入 Git。

### 8.8 阶段结论

阶段 4 完成，系统首次实现：

```text
自然语言
  -> Harness MCP tool
  -> 远程 MCP Server
  -> ROS service
  -> ROS 结果返回模型
```

## 9. 阶段 1–4 验收汇总

| 阶段 | 核心问题 | 验收结果 | 状态 |
| --- | --- | --- | --- |
| 1 | 模型能否编排农业工具 | 四个 mock 工具按依赖顺序调用 | 完成 |
| 2 | Ubuntu 能否运行最小 Agri_ROS service | 两包构建成功，合法请求成功，动作请求拒绝 | 完成 |
| 3 | MCP 能否安全连接 ROS | 四个只读工具发现和调用成功，5 项测试通过 | 完成 |
| 4 | Mac Harness 能否跨机器调用 MCP/ROS | Mac 请求日志、ROS 状态和模型输出三方一致 | 完成 |

## 10. 关键问题与解决方案

| 问题 | 原因 | 解决方案 |
| --- | --- | --- |
| ROS 安装可能升级服务器关键包 | 已有第三方源和 proposed 源 | 使用隔离安全源、dry-run 和受保护包检查 |
| ROS setup 出现 `ROS_DISTRO unbound variable` | ROS 脚本与 `set -u` 不兼容 | source 时临时关闭 nounset |
| Conda Python 无法直接使用 Noetic 包 | Python 3.12 与系统 ROS Python 3.8 分离 | MCP/ROS 使用两个进程和两个解释器 |
| MCP 同步工具调用卡住 | SDK 同步线程调度与子进程组合不稳定 | 改为 asyncio 异步子进程 |
| 阶段 4 端口跨会话消失 | 初始服务为临时前台进程 | 改为命名 tmux 常驻会话 |
| ROS master 初始监听 `0.0.0.0` | ROS1 XML-RPC 默认绑定行为 | 设置 `ROS_IP=127.0.0.1` 并重启 |
| 旧 MacBook 路径找不到 Cordis 文件 | Harness 目录已手工移动 | 将项目路径更新为 `<HARNESS_ROOT>` |
| mock 与 MCP 工具可能混用 | 两类插件同时加载会造成验证歧义 | 阶段 1、阶段 4 使用独立 Cordis patch |

## 11. 当前安全边界与尚未验证内容

### 11.1 已建立的边界

- ROS master 仅监听 `127.0.0.1`。
- MCP 仅监听服务器 Tailscale IPv4。
- MCP 和 adapter 均使用固定动作白名单。
- adapter 每次调用有超时。
- 状态 service 只接受 `state=status` 和全零控制字段。
- 返回值明确区分 ROS 在线与硬件未连接。

### 11.2 尚未验证

- 真实 LiDAR、GNSS、IMU、Camera 驱动。
- 真实 TF 树、标定文件和时间同步。
- 真实 SLAM、定位、感知和路径规划精度。
- 真实机器人底盘、CAN、串口和 `/cmd_vel`。
- 急停、限速、看门狗、断网恢复和故障降级。
- 农田环境中的实时性、覆盖率、安全距离和作业效果。
- 应用层 Bearer token、细粒度 Tailscale ACL 和完整审计存储。

因此本报告不能被解释为“真实农业机器人系统已可自主作业”。

## 12. 版本管理说明

阶段 1 的 Harness mock demo 保存在独立仓库中；阶段 2–4 的 ROS、MCP 与
Harness 集成代码统一保存在本仓库。Agri_ROS 作为 submodule 固定到实验所用
版本，自研 ROS package、MCP 服务、配置模板和实验文档由本仓库管理。

各阶段使用 Git tag 标记稳定验收点。catkin 构建目录、Python 虚拟环境、运行
日志、密钥和实验数据不纳入普通 Git 版本控制，公开文件中的设备地址、hostname
和本地绝对路径均使用占位符。

## 13. 后续计划

后续工作将在现有只读链路基础上逐步扩展。首先使用合成数据、公开数据或 ROS bag
开展离线回放，验证感知、建图等算法的启动、状态查询、结果输出和异常处理；随后
将验证通过的算法封装为任务级 MCP 工具，并继续保持白名单、超时、取消和运行
环境隔离。具备设备与测试条件后，再依次开展传感器、标定、定位、导航和控制验证。

## 14. 结论

阶段 1–4 已完成从 Harness mock 工具到跨机器 MCP 调用 ROS service 的渐进式
验证。系统实现了 Harness、MCP 与 ROS 的分层，解决了 Python 运行环境隔离问题，
建立了固定工具白名单和受限网络入口，并能够返回 ROS 在线状态、节点、topic 与
机器人安全状态。

当前实验验证的是智能体编排和软件通信链路，尚未评价真实农业机器人在现场环境中
的感知精度、导航性能和控制安全性。后续将按照离线数据、仿真验证和受控设备实验的
顺序逐步扩展。

## 附录 A：关键文件

```text
<REPOSITORY_ROOT>/scripts/install_ros_noetic_minimal.sh
<REPOSITORY_ROOT>/catkin_ws/src/agri_stage2_demo/
<REPOSITORY_ROOT>/agri_mcp_server/
<REPOSITORY_ROOT>/harness/cordis.stage4.yml.example
<REPOSITORY_ROOT>/agri_mcp_server/scripts/start_stage4_stack.sh
<REPOSITORY_ROOT>/agri_mcp_server/scripts/status_stage4_stack.sh
```

## 附录 B：阶段 4 服务状态检查

```bash
cd <REPOSITORY_ROOT>/agri_mcp_server
./scripts/status_stage4_stack.sh
```

## 附录 C：资料来源

- 阶段 1 项目：<https://github.com/yifan2113/deepseek-harness-agri-demo>
- DeepSeek Harness：<https://github.com/deepseek-ai/deepseek-harness>
- Harness MCP Client：<https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/mcp/mcp-client>
- MCP Python SDK：<https://github.com/modelcontextprotocol/python-sdk>
- Agri_ROS：<https://github.com/Fontainebleau2021/Agri_ROS>
