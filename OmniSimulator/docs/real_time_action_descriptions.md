# 实时动作描述系统

## 概述

实时动作描述系统是Embodied Simulator的一个重要功能，它能够实时生成智能体当前支持的所有动作的完整英文描述，包括命令格式、功能说明和使用示例。该系统会根据智能体的能力变化（如拿起或放下工具）实时更新动作列表。

## 核心特性

### 🔄 实时更新
- 智能体拿起工具时，自动添加工具相关动作的描述
- 智能体放下工具时，自动移除工具相关动作的描述
- 描述内容始终反映智能体当前的真实能力状态

### 📝 完整覆盖
- **基础动作**: GOTO, GRAB, PLACE, LOOK, EXPLORE
- **属性动作**: 基于场景配置的不需要工具的动作
- **智能体特定动作**: 需要工具的动作，实时注册/取消注册
- **合作动作**: 多智能体协作动作

### 🌍 英文描述
- 提供清晰的英文命令格式
- 包含详细的功能说明
- 每个动作都有具体的使用示例

### 🤝 多智能体支持（更新功能）
- 支持单个智能体和多个智能体的动作描述
- 单智能体模式不显示合作动作，避免混淆
- 多智能体模式显示具体的合作动作格式
- 智能优化避免重复动作显示
- 显示智能体特定动作的可用性信息

## API使用

### 基本用法

```python
from embodied_simulator.core import SimulationEngine
from embodied_simulator.utils.data_loader import default_data_loader

# 初始化模拟器
scene_data, task_data = default_data_loader.load_complete_scenario("00001")
engine = SimulationEngine()
engine.initialize_with_data({'scene': scene_data, 'task': task_data})

# 获取智能体
agents = engine.agent_manager.get_all_agents()
agent_id = list(agents.keys())[0]

# 获取单个智能体的动作描述（不显示合作动作）
description = engine.get_agent_supported_actions_description([agent_id])
print(description)

# 获取多个智能体的联合动作描述（显示合作动作）
agents = list(engine.agent_manager.get_all_agents().keys())
if len(agents) >= 2:
    dual_description = engine.get_agent_supported_actions_description([agents[0], agents[1]])
    print(dual_description)
```

### 单个智能体输出示例

```
=== SUPPORTED ACTIONS FOR AGENT_1 ===

== Basic Actions ==
GOTO <object_id>
  - Move to a specific location or object
  - Example: GOTO main_workbench_area

GRAB <object_id>
  - Pick up an object that is nearby
  - Example: GRAB cup_1

PLACE <object_id> <in|on> <container_id>
  - Place a held object into or onto another object
  - Example: PLACE cup_1 on table_1

LOOK <object_id>
  - Examine an object to get detailed information
  - Example: LOOK table_1

EXPLORE
  - Explore current room to discover objects
  - Example: EXPLORE

=== END OF ACTIONS ===
```

### 多智能体输出示例（显示合作动作）

```
=== SUPPORTED ACTIONS FOR AGENT_1 & AGENT_2 ===

== Basic Actions ==
GOTO <object_id>
  - Move to a specific location or object
  - Example: GOTO main_workbench_area

== Agent-Specific Actions (Tools Required) ==
SPREAD <object_id>
  - Spreads a substance using a spreading tool
  - Available to: agent_1 & agent_2
  - Example: SPREAD device_1

== Cooperative Actions ==
CORP_GRAB agent_1,agent_2 <object_id>
  - Two agents cooperatively grab a heavy object
  - Example: CORP_GRAB agent_1,agent_2 heavy_box_1

== Cooperative Attribute Actions ==
CORP_SPREAD agent_1,agent_2 <object_id>
  - Spreads a substance using a spreading tool (cooperative)
  - Example: CORP_SPREAD agent_1,agent_2 device_1

=== END OF ACTIONS ===
```

## 多智能体功能详解

### 函数签名

```python
def get_agent_supported_actions_description(self, agent_ids: List[str]) -> str:
    """
    获取智能体支持的所有动作的字符串描述

    Args:
        agent_ids: 智能体ID列表，支持单个或多个智能体

    Returns:
        str: 包含所有支持动作的描述字符串（英文）
    """
```

### 使用方式

```python
# 单个智能体（不显示合作动作）
description = engine.get_agent_supported_actions_description(["agent_1"])

# 多个智能体（显示合作动作）
dual_description = engine.get_agent_supported_actions_description(["agent_1", "agent_2"])

# 三个智能体
multi_description = engine.get_agent_supported_actions_description(["agent_1", "agent_2", "agent_3"])
```

### 功能差异

| 特性 | 单个智能体 | 多个智能体 |
|------|------------|------------|
| 参数格式 | `["agent_1"]` | `["agent_1", "agent_2", ...]` |
| 标题格式 | `=== SUPPORTED ACTIONS FOR AGENT_1 ===` | `=== SUPPORTED ACTIONS FOR AGENT_1 & AGENT_2 ===` |
| 合作动作显示 | 不显示合作动作 | 显示具体的合作动作格式 |
| 合作动作格式 | 无 | `CORP_GRAB agent_1,agent_2 <object_id>` |
| 智能体特定动作 | 只显示该智能体的动作 | 显示所有智能体的联合动作并标注可用性 |
| 重复动作处理 | 不适用 | 智能合并，避免重复显示 |

### 优化特性

1. **单智能体简化**: 单智能体模式不显示合作动作，避免混淆
2. **避免重复**: 相同的基础动作只显示一次
3. **智能合并**: 智能体特定动作会合并显示，并标注哪些智能体可用
4. **具体示例**: 合作动作使用具体的智能体ID作为示例
5. **参数验证**: 完善的参数验证和错误处理
6. **自动去重**: 自动去除重复的智能体ID



TURN_OFF <object_id>
  - Turns off a device or equipment
  - Example: TURN_OFF device_1

CONNECT <object_id>
  - Connects a device or cable
  - Example: CONNECT device_1

== Agent-Specific Actions (Tools Required) ==
SPREAD <object_id>
  - Spreads a substance using a spreading tool
  - Example: SPREAD device_1

== Cooperative Actions ==
CORP_GRAB <agent1,agent2> <object_id>
  - Multiple agents cooperatively grab a heavy object
  - Example: CORP_GRAB agent_1,agent_2 heavy_box_1

CORP_GOTO <agent1,agent2> <location_id>
  - Multiple agents move together while carrying an object
  - Example: CORP_GOTO agent_1,agent_2 storage_area

CORP_PLACE <agent1,agent2> <object_id> <in|on> <container_id>
  - Multiple agents cooperatively place a heavy object
  - Example: CORP_PLACE agent_1,agent_2 heavy_box_1 on table_1

== Cooperative Attribute Actions ==
CORP_SPREAD <agent1,agent2> <object_id>
  - Spreads a substance using a spreading tool (cooperative)
  - Example: CORP_SPREAD agent_1,agent_2 device_1

=== END OF ACTIONS ===
```

## 实时更新演示

### 场景1: 拿起工具获得新能力

```python
# 初始状态 - 查看当前支持的动作
initial_description = engine.get_agent_supported_actions_description([agent_id])
print("=== 初始状态 ===")
print(initial_description)

# 移动到工具位置
engine.process_command(agent_id, "goto steel_workbench_1")

# 拿起工具
engine.process_command(agent_id, "grab butter_knife_1")

# 查看更新后的动作描述
updated_description = engine.get_agent_supported_actions_description([agent_id])
print("=== 拿起工具后 ===")
print(updated_description)
# 现在包含 SPREAD <object_id> 动作
```

### 场景2: 放下工具失去能力

```python
# 放下工具
engine.process_command(agent_id, "place butter_knife_1 on steel_workbench_1")

# 查看最终的动作描述
final_description = engine.get_agent_supported_actions_description([agent_id])
print("=== 放下工具后 ===")
print(final_description)
# SPREAD 动作被移除，回到初始状态
```

### 场景3: 多工具切换

```python
# 拿起第一个工具
engine.process_command(agent_id, "grab butter_knife_1")
description1 = engine.get_agent_supported_actions_description([agent_id])
print("拿起butter_knife后的动作:", "SPREAD" in description1)

# 放下第一个工具，拿起第二个工具
engine.process_command(agent_id, "place butter_knife_1 on steel_workbench_1")
engine.process_command(agent_id, "grab mixing_spoon_1")
description2 = engine.get_agent_supported_actions_description([agent_id])
print("拿起mixing_spoon后的动作:", "STIR" in description2)
print("是否还有SPREAD动作:", "SPREAD" in description2)  # False
```

## 技术实现

### 动作分类机制

系统根据以下规则对动作进行分类：

1. **基础动作**: 硬编码的核心动作，所有智能体都支持
2. **场景属性动作**: 从场景JSON的`abilities`字段读取，只注册不需要工具的动作
3. **智能体特定动作**: 根据智能体当前持有的工具动态注册
4. **合作动作**: 基础合作动作和属性合作动作

### 描述生成流程

1. **收集动作**: 从全局动作类和智能体特定动作类中收集所有可用动作
2. **分类整理**: 按动作类型进行分类和排序
3. **读取描述**: 从CSV配置文件中读取动作的英文描述
4. **格式化输出**: 生成结构化的英文描述文本

### 实时更新机制

1. **工具拿起**: `agent.add_ability_from_object()` → `ActionManager.register_ability_action()`
2. **工具放下**: `agent.remove_ability_from_object()` → `ActionManager.unregister_ability_action()`
3. **描述查询**: 每次调用都实时查询当前注册的动作

## 配置和扩展

### 添加新的动作描述

在`action/actions/attribute_actions.csv`文件中添加新的动作配置：

```csv
action_name,attribute,expected_value,requires_tool,description
new_action,some_attr,true,true,"Performs a new action on the object"
```

### 自定义描述格式

可以通过修改`ActionManager.get_agent_supported_actions_description()`方法来自定义输出格式。

## 应用场景

### 1. 智能体指导
为智能体提供当前可用操作的完整列表，帮助决策和规划。

### 2. 用户界面
在可视化界面中显示智能体当前支持的动作，提升用户体验。

### 3. API文档生成
动态生成智能体API文档，确保文档与实际能力同步。

### 4. 调试和测试
快速了解智能体当前状态，便于调试和测试。

## 总结

实时动作描述系统是Embodied Simulator的一个创新功能，它将静态的动作列表转变为动态的、实时更新的能力描述。这不仅提高了系统的可用性，也为智能体的自主决策和人机交互提供了重要支持。

通过场景驱动的注册机制和实时能力绑定，系统能够准确反映智能体的当前状态，为用户提供最新、最准确的操作指南。
