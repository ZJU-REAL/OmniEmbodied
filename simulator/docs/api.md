# API 文档

本文档提供了Embodied Simulator的完整API参考，包括核心类、方法和使用示例。

## 目录
- [核心API](#核心api)
- [环境描述API](#环境描述api)
- [提示词管理API](#提示词管理api)
- [数据加载API](#数据加载api)
- [动作系统API](#动作系统api)
- [可视化API](#可视化api)
- [任务验证API](#任务验证api)
- [配置API](#配置api)
- [错误处理](#错误处理)

## 核心API

### SimulationEngine

模拟引擎是系统的核心入口点，提供完整的仿真环境管理功能。

#### 构造函数

```python
from embodied_simulator.core import SimulationEngine

# 基本创建
engine = SimulationEngine()

# 带配置创建
config = {
    'visualization': {'enabled': True},
    'task_verification': {'mode': 'step_by_step'}
}
engine = SimulationEngine(config=config)

# 带任务能力创建
engine = SimulationEngine(
    config=config,
    task_abilities=["clean", "repair", "turn_on"]
)
```

#### 初始化方法

```python
# 方法1: 使用数据字典初始化（推荐）
data = {
    'scene': scene_data,      # 场景数据
    'task': task_data,        # 任务数据（可选）
    'verify': verify_data     # 验证数据（可选）
}
success = engine.initialize_with_data(data)

# 方法2: 使用任务文件初始化
success = engine.initialize_with_task("data/task/00001_task.json")

# 方法3: 使用场景文件初始化
success = engine.initialize("data/scene/00001_scene.json")
```

#### 主要属性

```python
# 获取核心组件
action_handler = engine.action_handler          # 动作处理器
agent_manager = engine.agent_manager            # 智能体管理器
env_manager = engine.env_manager                # 环境管理器
world_state = engine.world_state                # 世界状态
visualization_manager = engine.visualization_manager  # 可视化管理器
task_verifier = engine.task_verifier            # 任务验证器
```

#### 主要方法

```python
# 获取物体信息
obj_info = engine.get_object_info("object_id")

# 可视化控制
status = engine.get_visualization_status()      # 获取可视化状态
url = engine.get_visualization_url()            # 获取可视化URL
engine.stop_visualization()                     # 停止可视化
engine.restart_visualization()                  # 重启可视化

# 智能体管理
agents = engine.get_all_agents()                # 获取所有智能体
agent = engine.get_agent("agent_id")            # 获取特定智能体

# 动作描述（更新功能）
description = engine.get_agent_supported_actions_description(["agent_id"])  # 获取智能体支持的动作描述
```

## 数据加载API

### DataLoader

数据加载器提供统一的数据访问接口。

```python
from embodied_simulator.utils.data_loader import default_data_loader

# 加载完整场景（推荐）
scene_data, task_data, verify_data = default_data_loader.load_complete_scenario("00001")

# 单独加载各类数据
scene_data = default_data_loader.load_scene("00001")
task_data = default_data_loader.load_task("00001")
verify_data = default_data_loader.load_verify("00001")

# 获取任务能力
abilities = default_data_loader.get_task_abilities("00001")

# 获取任务命令
commands = default_data_loader.get_task_commands("00001", "direct_command")
```

## 环境描述API

### SimulatorBridge

模拟器桥接类提供了获取环境描述的统一接口。

#### 房间描述

```python
from embodied_framework.utils import SimulatorBridge

bridge = SimulatorBridge()
bridge.initialize_with_scenario("00001")

# 描述特定房间
room_desc = bridge.describe_room_natural_language("main_workbench_area")
print(room_desc)
# 输出:
# ▶ 房间：Main Workbench Area (ID: main_workbench_area)
#   • 房间属性: type: workbench
#   • 连接房间: Filter Simulation Station, Storage Shelves
#   • 智能体: robot_1 (位置、状态信息)
#   • 物体: [房间内所有物体的层次结构]

# 描述完整环境（所有房间）
env_desc = bridge.describe_environment_natural_language(
    sim_config={
        'nlp_show_object_properties': True,   # 显示物体属性
        'nlp_only_show_discovered': False     # 显示所有物体
    }
)
print(env_desc)
# 输出:
# ================ 环境概述 ================
# 共有 4 个房间, 54 个物体, 2 个智能体
#
# ================ 房间详情 ================
# [所有房间的详细信息]
#
# ================ 智能体详情 ================
# [所有智能体的详细状态]

# 描述智能体状态
agent_desc = bridge.describe_agent_natural_language("robot_1")
print(agent_desc)
```

#### 配置参数

环境描述支持以下配置参数：

```python
sim_config = {
    'nlp_show_object_properties': True,    # 是否显示物体详细属性
    'nlp_only_show_discovered': False,     # 是否只显示已发现物体
    'nlp_detail_level': 'full'             # 详细程度: full/room/brief
}

# 使用配置
env_desc = bridge.describe_environment_natural_language(sim_config=sim_config)
```

## 提示词管理API

### PromptManager

提示词管理器负责加载和格式化提示词模板，支持动态环境信息注入。

#### 基本使用

```python
from embodied_framework.utils import PromptManager

# 创建提示词管理器
prompt_manager = PromptManager("prompts_config")

# 获取提示词模板
system_prompt = prompt_manager.get_prompt_template("single_agent", "system")
task_template = prompt_manager.get_prompt_template("single_agent", "task_template")

# 格式化提示词
formatted_prompt = prompt_manager.get_formatted_prompt(
    "single_agent",
    "task_template",
    task_description="找到厨房，打开冰箱，取出苹果",
    environment_description="当前房间描述...",
    history_summary="历史行动记录..."
)
```

#### 环境描述注入

```python
# 自动添加环境描述到提示词
prompt_with_env = prompt_manager.add_environment_description(
    prompt="原始提示词模板",
    agent_id="robot_1",
    bridge=bridge,
    config={
        'detail_level': 'full',              # 完整环境描述
        'show_object_properties': True,      # 显示物体属性
        'only_show_discovered': False        # 显示所有物体
    }
)
```

#### 动态动作注入

```python
# 获取包含动态动作描述的系统提示词
system_prompt_with_actions = prompt_manager.get_system_prompt_with_actions(
    mode="single_agent",
    agent_id="robot_1",
    bridge=bridge
)
# 系统提示词中的 {dynamic_actions_description} 会被自动替换为当前可用动作列表
```

#### 历史记录格式化

```python
# 格式化历史记录
history = [
    {'action': 'GOTO main_workbench_area', 'status': 'SUCCESS', 'message': '成功移动'},
    {'action': 'GRAB oscilloscope_1', 'status': 'SUCCESS', 'message': '成功抓取'}
]

formatted_history = prompt_manager.format_history("single_agent", history, max_entries=10)
```

#### 环境描述配置工具

```python
from embodied_framework.utils import create_env_description_config

# 创建环境描述配置
env_config = create_env_description_config(
    detail_level='full',        # full/room/brief
    show_properties=True,       # 是否显示物体属性
    only_discovered=False       # 是否只显示已发现内容
)

# 在智能体配置中使用
agent_config = {
    'env_description': env_config,
    'llm_config': 'llm_config',
    # 其他配置...
}
```

## 动作系统API

### ActionHandler

动作处理器是执行智能体命令的主要接口。

#### 执行命令

```python
# 基本命令执行
status, message, result = action_handler.process_command(
    agent_id="robot_1",
    command_str="GOTO main_workbench_area"
)

# 检查执行状态
if status == ActionStatus.SUCCESS:
    print(f"成功: {message}")

    # 检查任务验证结果（如果启用）
    if result and 'task_verification' in result:
        verification = result['task_verification']
        summary = verification.get('completion_summary', {})
        completed = summary.get('completed_tasks', 0)
        total = summary.get('total_tasks', 0)
        print(f"任务进度: {completed}/{total}")
elif status == ActionStatus.FAILURE:
    print(f"失败: {message}")
elif status == ActionStatus.INVALID:
    print(f"无效命令: {message}")
```

#### 动作注册

```python
# 注册单个动作类
action_handler.register_action_class("custom_action", CustomActionClass)

# 批量注册动作类
action_classes = {
    "action1": ActionClass1,
    "action2": ActionClass2
}
action_handler.register_action_classes(action_classes)
```

### 支持的动作类型

#### 基础动作
```python
# 移动动作
status, msg, result = action_handler.process_command("robot_1", "GOTO main_workbench_area")
status, msg, result = action_handler.process_command("robot_1", "GOTO oscilloscope_1")

# 抓取和放置
status, msg, result = action_handler.process_command("robot_1", "GRAB dac_chip_1")
status, msg, result = action_handler.process_command("robot_1", "PLACE dac_chip_1 IN plastic_bin_1")
status, msg, result = action_handler.process_command("robot_1", "PLACE book_1 ON table_1")

# 探索
status, msg, result = action_handler.process_command("robot_1", "EXPLORE")
status, msg, result = action_handler.process_command("robot_1", "EXPLORE main_workbench_area")
```

#### 属性动作

**不需要工具的动作（场景全局可用）**:
```python
# 设备操作（仅当场景abilities包含这些动作时可用）
status, msg, result = action_handler.process_command("robot_1", "TURN_ON oscilloscope_1")
status, msg, result = action_handler.process_command("robot_1", "TURN_OFF oscilloscope_1")
status, msg, result = action_handler.process_command("robot_1", "CONNECT cable_1")

# 容器操作
status, msg, result = action_handler.process_command("robot_1", "OPEN plastic_bin_1")
status, msg, result = action_handler.process_command("robot_1", "CLOSE plastic_bin_1")
```

**需要工具的动作（智能体特定，实时注册）**:
```python
# 先拿起工具
status, msg, result = action_handler.process_command("robot_1", "GRAB butter_knife_1")

# 现在可以使用工具相关动作
status, msg, result = action_handler.process_command("robot_1", "SPREAD butter_1")

# 放下工具后，相关动作自动取消注册
status, msg, result = action_handler.process_command("robot_1", "PLACE butter_knife_1 ON table_1")
```

#### 合作动作
```python
# 合作抓取重物
status, msg, result = action_handler.process_command(
    "robot_1", "CORP_GRAB robot_1,robot_2 heavy_box_1"
)

# 合作移动
status, msg, result = action_handler.process_command(
    "robot_1", "CORP_GOTO robot_1,robot_2 storage_room"
)

# 合作放置
status, msg, result = action_handler.process_command(
    "robot_1", "CORP_PLACE robot_1,robot_2 heavy_box_1 IN storage_area"
)
```

### 动作描述API

获取智能体当前支持的所有动作的实时描述：

```python
# 获取单个智能体支持的动作描述
description = engine.get_agent_supported_actions_description(["robot_1"])
print(description)

# 获取多个智能体的联合动作描述
dual_description = engine.get_agent_supported_actions_description(["robot_1", "robot_2"])
print(dual_description)

# 获取三个智能体的联合动作描述
multi_description = engine.get_agent_supported_actions_description(["robot_1", "robot_2", "robot_3"])
print(multi_description)

# 或者通过action_handler获取
description = action_handler.get_agent_supported_actions_description(["robot_1"])
dual_description = action_handler.get_agent_supported_actions_description(["robot_1", "robot_2"])
```

**单个智能体返回格式**（不显示合作动作）:
```
=== SUPPORTED ACTIONS FOR ROBOT_1 ===

== Basic Actions ==
GOTO <object_id>
  - Move to a specific location or object
  - Example: GOTO main_workbench_area

GRAB <object_id>
  - Pick up an object that is nearby
  - Example: GRAB cup_1

== Attribute Actions (No Tools Required) ==
OPEN <object_id>
  - Opens an object such as a container or device
  - Example: OPEN device_1

== Agent-Specific Actions (Tools Required) ==
SPREAD <object_id>
  - Spreads a substance using a spreading tool
  - Example: SPREAD device_1

=== END OF ACTIONS ===
```

**多智能体返回格式**（显示合作动作）:
```
=== SUPPORTED ACTIONS FOR ROBOT_1 & ROBOT_2 ===

== Basic Actions ==
GOTO <object_id>
  - Move to a specific location or object
  - Example: GOTO main_workbench_area

== Agent-Specific Actions (Tools Required) ==
SPREAD <object_id>
  - Spreads a substance using a spreading tool
  - Available to: robot_1 & robot_2
  - Example: SPREAD device_1

== Cooperative Actions ==
CORP_GRAB robot_1,robot_2 <object_id>
  - Two agents cooperatively grab a heavy object
  - Example: CORP_GRAB robot_1,robot_2 heavy_box_1

== Cooperative Attribute Actions ==
CORP_SPREAD robot_1,robot_2 <object_id>
  - Spreads a substance using a spreading tool (cooperative)
  - Example: CORP_SPREAD robot_1,robot_2 device_1

=== END OF ACTIONS ===

== Cooperative Actions ==
CORP_GRAB <agent1,agent2> <object_id>
  - Multiple agents cooperatively grab a heavy object
  - Example: CORP_GRAB agent_1,agent_2 heavy_box_1
```

**特点**:
- **实时更新**: 拿起/放下工具时描述立即更新
- **完整覆盖**: 包括所有类型的动作
- **英文描述**: 提供清晰的命令格式和功能说明
- **使用示例**: 每个动作都包含具体的使用示例

## 任务验证API

### TaskVerifier

任务验证器提供任务完成状态的检查和验证功能。

```python
from embodied_simulator.utils.task_verifier import TaskVerifier

# 创建任务验证器
verifier = TaskVerifier(verify_data, world_state)

# 验证所有任务
results = verifier.verify_all_tasks()

# 获取完成摘要
summary = verifier.get_completion_summary()
print(f"总进度: {summary['completion_rate']:.1%}")
print(f"已完成任务: {summary['completed_tasks']}/{summary['total_tasks']}")

# 验证特定任务
task_result = verifier.verify_task("task_id")
```

### 验证模式配置

```python
# 在配置中设置验证模式
config = {
    'task_verification': {
        'mode': 'step_by_step',           # 逐步验证
        'return_subtask_status': True     # 返回子任务状态
    }
}

# 或者设置为全局验证
config = {
    'task_verification': {
        'mode': 'global'                  # 仅在done命令时验证
    }
}

# 或者禁用验证
config = {
    'task_verification': {
        'mode': 'disabled'                # 禁用验证
    }
}
```

## 可视化API

### VisualizationManager

可视化管理器提供Web界面的启动、停止和控制功能。

#### 基本控制

```python
# 检查可视化状态
if engine.visualization_manager:
    status = engine.get_visualization_status()
    print(f"可视化状态: {status}")

    # 获取可视化URL
    url = engine.get_visualization_url()
    print(f"访问地址: {url}")

    # 停止可视化
    engine.stop_visualization()

    # 重启可视化
    engine.restart_visualization()
```

#### 配置可视化

```python
# 在引擎配置中启用可视化
config = {
    'visualization': {
        'enabled': True,
        'web_server': {
            'host': 'localhost',
            'port': 8080,
            'auto_open_browser': True
        },
        'request_interval': 2000  # 前端更新间隔(毫秒)
    }
}

engine = SimulationEngine(config=config)
```

### 可视化REST API

可视化系统提供以下REST API接口：

| 端点 | 方法 | 描述 |
|------|------|------|
| `/` | GET | 主页面 |
| `/api/data` | GET | 获取完整可视化数据 |
| `/api/rooms` | GET | 获取房间列表 |
| `/api/room/{room_id}` | GET | 获取特定房间数据 |
| `/api/agents` | GET | 获取智能体数据 |
| `/api/objects` | GET | 获取物体数据 |
| `/api/config` | GET | 获取配置信息 |

#### API使用示例

```python
import requests

# 获取完整数据
response = requests.get('http://localhost:8080/api/data')
data = response.json()

# 获取房间列表
response = requests.get('http://localhost:8080/api/rooms')
rooms = response.json()

# 获取智能体数据
response = requests.get('http://localhost:8080/api/agents')
agents = response.json()
```

## 配置API

### 配置文件加载

```python
# 从YAML文件加载配置
import yaml
with open('data/simulator_config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 创建引擎时传入配置
engine = SimulationEngine(config=config, task_abilities=abilities)
```

### 主要配置选项

```python
config = {
    # 探索模式
    'explore_mode': 'thorough',  # normal/thorough

    # 任务验证配置
    'task_verification': {
        'enabled': True,
        'mode': 'step_by_step',           # step_by_step/global/disabled
        'return_subtask_status': True
    },

    # 可视化配置
    'visualization': {
        'enabled': True,
        'web_server': {
            'host': 'localhost',
            'port': 8080,
            'auto_open_browser': True
        },
        'request_interval': 2000          # 前端更新间隔(毫秒)
    }
}
```

## 状态码和枚举

### ActionStatus

```python
from embodied_simulator.core import ActionStatus

ActionStatus.SUCCESS    # 动作执行成功
ActionStatus.FAILURE    # 动作执行失败
ActionStatus.INVALID    # 无效的动作命令
```

### ObjectType

```python
from embodied_simulator.core import ObjectType

ObjectType.ROOM         # 房间
ObjectType.FURNITURE    # 家具
ObjectType.ITEM         # 物品
ObjectType.AGENT        # 智能体
```

### ActionType

```python
from embodied_simulator.core import ActionType

ActionType.BASIC        # 基础动作
ActionType.ATTRIBUTE    # 属性动作
ActionType.COOPERATION  # 合作动作
```

## 错误处理

### 标准错误处理模式

所有API调用都返回状态码和消息，便于错误处理：

```python
status, message, result = action_handler.process_command(agent_id, command)

if status == ActionStatus.SUCCESS:
    print(f"成功: {message}")

    # 检查额外结果信息
    if result:
        # 位置变化信息
        if 'new_location_id' in result:
            print(f"新位置: {result['new_location_id']}")

        # 任务验证信息
        if 'task_verification' in result:
            verification = result['task_verification']
            summary = verification.get('completion_summary', {})
            completed = summary.get('completed_tasks', 0)
            total = summary.get('total_tasks', 0)
            print(f"任务进度: {completed}/{total}")

elif status == ActionStatus.FAILURE:
    print(f"执行失败: {message}")
    # 处理失败情况

elif status == ActionStatus.INVALID:
    print(f"无效命令: {message}")
    # 处理无效命令
```

### 异常处理

```python
try:
    # 初始化模拟器
    success = engine.initialize_with_data(data)
    if not success:
        raise RuntimeError("模拟器初始化失败")

    # 执行动作
    status, message, result = action_handler.process_command(agent_id, command)

except Exception as e:
    print(f"发生异常: {e}")
    # 记录错误日志
    import traceback
    traceback.print_exc()
```

## 完整使用示例

### 基本工作流程

```python
from embodied_simulator.core import SimulationEngine, ActionStatus
from embodied_simulator.utils.data_loader import default_data_loader

def main():
    try:
        # 1. 加载数据
        scene_data, task_data, verify_data = default_data_loader.load_complete_scenario("00001")

        # 2. 创建引擎
        config = {
            'visualization': {'enabled': True},
            'task_verification': {'mode': 'step_by_step'}
        }
        engine = SimulationEngine(
            config=config,
            task_abilities=task_data.get("abilities", [])
        )

        # 3. 初始化模拟器
        success = engine.initialize_with_data({
            'scene': scene_data,
            'task': task_data,
            'verify': verify_data
        })

        if not success:
            print("初始化失败")
            return

        # 4. 获取智能体
        agents = engine.agent_manager.get_all_agents()
        agent_id = list(agents.keys())[0]

        # 5. 执行任务
        commands = [
            "GOTO main_workbench_area",
            "EXPLORE main_workbench_area",
            "GRAB oscilloscope_1",
            "TURN_ON oscilloscope_1"
        ]

        for command in commands:
            status, message, result = engine.action_handler.process_command(
                agent_id, command
            )

            print(f"命令: {command}")
            print(f"结果: {status.name} - {message}")

            if result and 'task_verification' in result:
                verification = result['task_verification']
                summary = verification.get('completion_summary', {})
                print(f"任务进度: {summary.get('completed_tasks', 0)}/{summary.get('total_tasks', 0)}")

            print("-" * 50)

        # 6. 获取可视化URL
        if engine.visualization_manager:
            url = engine.get_visualization_url()
            print(f"可视化界面: {url}")

    except Exception as e:
        print(f"执行失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 7. 清理资源
        if engine and engine.visualization_manager:
            engine.stop_visualization()

if __name__ == "__main__":
    main()
```
