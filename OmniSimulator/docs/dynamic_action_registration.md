# 动态动作注册系统

## 概述

本文档描述了最新实现的动态动作注册系统，该系统根据场景配置和智能体能力实时注册动作，实现了高效的动作管理和实时能力绑定。

## 核心设计原则

### 1. 场景驱动的注册策略
- **场景注册**: 只注册场景JSON中`abilities`字段包含的不需要工具的动作
- **实时动态注册**: 需要工具的动作根据智能体拿起的工具实时注册/取消注册
- **智能体特定**: 每个智能体维护独立的动作集合

### 2. 实时能力绑定
- 智能体拿起工具时自动获得相应能力并注册对应动作
- 智能体放下工具时自动失去相应能力并取消注册对应动作
- 支持多个工具的动态切换和能力叠加

### 3. 基于数据驱动
- 测试场景和任务从`data`文件夹读取，作为标准样本使用
- 支持场景数据、任务数据和验证数据的完整加载
- 动作描述从CSV文件中读取，支持英文描述

## 主要组件

### 1. DataLoader (utils/data_loader.py)
负责从data文件夹加载各种数据：

```python
# 加载完整场景
scene_data, task_data, verify_data = data_loader.load_complete_scenario("00001")

# 获取任务能力
abilities = data_loader.get_task_abilities("00001")

# 获取任务命令
commands = data_loader.get_task_commands("00001", "tool_use")
```

**主要功能**:
- 加载场景数据 (`*_scene.json`)
- 加载任务数据 (`*_task.json`)
- 加载验证数据 (`*_verify.json`)
- 提取任务能力和命令
- 验证数据完整性

### 2. 增强的ActionManager类
新增了场景驱动和实时动态注册方法：

```python
# 创建ActionManager时传递场景abilities
action_manager = ActionManager(
    world_state,
    env_manager,
    agent_manager,
    scene_abilities=scene_abilities
)

# 获取智能体支持的动作描述（实时更新）
description = action_manager.get_agent_supported_actions_description([agent_id])
```

**关键方法**:
- `_register_scene_no_tool_actions()`: 根据场景abilities注册不需要工具的动作
- `register_ability_action()`: 为智能体注册能力相关动作
- `unregister_ability_action()`: 为智能体取消注册能力相关动作
- `get_agent_supported_actions_description()`: 获取智能体支持的实时动作描述

### 3. 更新的SimulationEngine
支持场景驱动的初始化和实时动作描述：

```python
# 创建引擎并初始化（自动从场景数据提取abilities）
engine = SimulationEngine(config=config)
data = {'scene': scene_data, 'task': task_data}
engine.initialize_with_data(data)

# 获取智能体支持的实时动作描述
description = engine.get_agent_supported_actions_description([agent_id])
```

**新增功能**:
- 自动从场景数据提取abilities并传递给ActionManager
- 支持实时获取智能体动作描述
- 动作描述会实时反映智能体当前能力状态

### 4. 验证和近邻管理系统
新增了完整的验证框架：

#### ActionValidator (utils/action_validators.py)
```python
# 验证物体存在性和发现状态
result = ActionValidator.validate_object_exists_and_discovered(env_manager, "object_id")

# 验证智能体容量
result = ActionValidator.validate_agent_capacity(agent)

# 验证完整的抓取动作
result = ActionValidator.validate_grab_action(env_manager, agent, "object_id")
```

#### ProximityManager (utils/proximity_manager.py)
```python
# 更新智能体近邻关系
proximity_manager.update_agent_proximity(agent, target_object_id)

# 检查智能体是否靠近物体
is_near = proximity_manager.is_agent_near_object(agent, object_id)
```

### 4. 实时动作描述系统
提供智能体当前支持动作的完整英文描述：

```python
# 获取智能体支持的动作描述
description = engine.get_agent_supported_actions_description([agent_id])
print(description)
```

**输出示例**:
```
=== SUPPORTED ACTIONS ===

== Basic Actions ==
GOTO <object_id>
  - Move to a specific location or object
  - Example: GOTO main_workbench_area

== Attribute Actions (No Tools Required) ==
OPEN <object_id>
  - Opens an object such as a container or device
  - Example: OPEN device_1

== Agent-Specific Actions (Tools Required) ==
SPREAD <object_id>
  - Spreads a substance using a spreading tool
  - Example: SPREAD device_1
```

**关键特性**:
- **实时更新**: 拿起/放下工具时动作描述立即更新
- **完整覆盖**: 包括基础动作、属性动作、合作动作
- **英文描述**: 提供清晰的命令格式和功能说明
- **使用示例**: 每个动作都包含具体的使用示例

## 数据文件结构

### 场景文件格式 (data/scene/*.json)
```json
{
  "description": "场景描述",
  "abilities": [
    "open",
    "close",
    "turn_on",
    "turn_off",
    "connect"
  ],
  "rooms": [...],
  "objects": [
    {
      "id": "precision_screwdriver_1",
      "properties": {
        "provides_abilities": ["screw"]
      }
    }
  ]
}
```

### 任务文件格式 (data/task/*.json)
```json
{
  "agents_config": [
    {
      "name": "robot_1",
      "max_grasp_limit": 1,
      "max_weight": 25.0
    }
  ],
  "abilities": [
    "extinguish",
    "freeze",
    "recharge",
    "spread",
    "stir",
    "toast",
    "unlock"
  ],
  "single_agent_tasks": {
    "direct_command": [...],
    "tool_use": [...]
  },
  "scene_id": "00001"
}
```



## 测试框架

### 1. 基于数据的测试环境
```python
# 创建基于真实数据的测试环境
builder = create_data_based_test_environment("00001")

# 获取智能体和执行命令
agent = builder.get_agent("robot_1")
status, message, _ = builder.execute_command(agent.id, "TURN_ON oscilloscope_1")
```

### 2. 全面的测试覆盖
- **数据加载测试**: 验证场景、任务数据的正确加载
- **环境创建测试**: 验证基于数据的环境正确创建
- **动作执行测试**: 测试真实场景中的动作执行
- **边界情况测试**: 测试各种异常和边界情况

## 使用示例

### 1. 创建基于场景的仿真环境
```python
from embodied_simulator.utils.data_loader import default_data_loader
from embodied_simulator.core import SimulationEngine

# 加载完整场景数据
scene_data, task_data = default_data_loader.load_complete_scenario("00001")

# 创建引擎（自动从场景数据提取abilities）
config = {
    'visualization': {'enabled': False},
    'task_verification': {'enabled': False}
}
engine = SimulationEngine(config=config)

# 初始化环境
data = {'scene': scene_data, 'task': task_data}
success = engine.initialize_with_data(data)
```

### 2. 实时动作描述功能
```python
# 获取智能体
agents = engine.agent_manager.get_all_agents()
agent_id = list(agents.keys())[0]

# 获取初始动作描述
initial_description = engine.get_agent_supported_actions_description([agent_id])
print("初始支持的动作:")
print(initial_description)

# 拿起工具
engine.process_command(agent_id, "goto steel_workbench_1")
engine.process_command(agent_id, "grab butter_knife_1")

# 获取更新后的动作描述
updated_description = engine.get_agent_supported_actions_description([agent_id])
print("拿起工具后支持的动作:")
print(updated_description)
# 现在包含 SPREAD <object_id> 动作

# 放下工具
engine.process_command(agent_id, "place butter_knife_1 on steel_workbench_1")

# 获取最终动作描述
final_description = engine.get_agent_supported_actions_description([agent_id])
print("放下工具后支持的动作:")
print(final_description)
# SPREAD 动作被移除
```

## 优势

### 1. 性能优化
- 只注册场景需要的不需要工具的动作，减少内存占用
- 智能体特定动作实时注册/取消注册，避免不必要的动作验证开销
- 动作描述按需生成，提高响应速度

### 2. 实时性和灵活性
- 支持智能体能力的实时变化
- 动作描述实时反映当前状态
- 支持多个工具的动态切换和能力叠加
- 运行时动态调整可用动作

### 3. 用户体验
- 提供完整的英文动作描述和使用示例
- 实时更新的动作列表，便于用户了解当前可用操作
- 清晰的命令格式说明，降低使用门槛

### 4. 可维护性
- 基于场景数据驱动，易于添加新场景和任务
- 清晰的分层架构，便于扩展
- 动作描述从CSV文件读取，易于维护和更新

### 5. 测试完整性
- 基于真实数据的测试，更接近实际使用场景
- 全面的边界情况测试，提高系统稳定性
- 实时功能测试，确保动态注册机制正常工作

## 扩展指南

### 1. 添加新的动作类型
1. 在`attribute_actions.csv`中添加动作配置
2. 设置`requires_tool`字段
3. 在任务文件的`abilities`中包含新动作

### 2. 添加新的场景
1. 创建`*_scene.json`文件
2. 创建对应的`*_task.json`文件
3. 可选创建`*_verify.json`验证文件

### 3. 自定义验证逻辑
继承`ActionValidator`类并重写相关方法，或者添加新的验证方法。

## 总结

动态动作注册系统通过分层注册策略和数据驱动的方法，实现了高效、灵活的动作管理。系统不仅提高了性能，还增强了可维护性和扩展性，为复杂的多智能体仿真提供了坚实的基础。
