# 动作系统文档

## 概述

动作系统是Embodied Simulator的核心组件，负责处理智能体的所有行为。系统支持多种类型的动作，采用动态注册机制，根据任务需求灵活加载相应的动作能力。

## 目录
- [动作分类](#动作分类)
- [基础动作](#基础动作)
- [属性动作](#属性动作)
- [合作动作](#合作动作)
- [能力系统](#能力系统)
- [动作验证](#动作验证)
- [扩展指南](#扩展指南)

## 动作分类

### 🔧 动态注册机制
- **场景注册**: 只注册场景JSON中`abilities`字段包含的不需要工具的动作
- **智能体动态注册**: 需要工具的动作根据智能体拿起的工具实时注册/取消注册
- **实时更新**: 动作描述实时反映智能体当前能力状态

### 📊 动作类型统计
- **基础动作**: 5种 (GOTO, GRAB, PLACE, LOOK, EXPLORE)
- **属性动作**: 217种 (通过CSV配置，按场景和能力动态加载)
- **合作动作**: 基础合作动作 + 属性合作动作

### 🎯 执行模式
- **同步执行**: 动作立即执行并返回结果
- **实时能力绑定**: 拿起/放下工具时自动更新可用动作
- **验证集成**: 可选的任务验证功能
- **错误处理**: 完善的错误反馈机制

## 基础动作

### GOTO
移动到指定位置（房间或物体）。智能体会自动更新近邻关系。

```bash
GOTO main_workbench_area    # 移动到房间
GOTO plastic_bin_1          # 移动到物体附近
GOTO oscilloscope_1         # 移动到设备附近
```

**特性**:
- 自动路径规划
- 更新近邻关系
- 支持房间和物体目标

### GRAB
抓取物体。必须先靠近物体，且物体必须可抓取。

```bash
GRAB dac_chip_1            # 抓取芯片
GRAB cleaning_cloth_1      # 抓取清洁布（获得清洁能力）
```

**限制**:
- 必须在物体附近（near关系）
- 智能体库存未满
- 物体未被其他智能体持有
- 容器类物体必须为空才能抓取

### PLACE
放置物体到指定位置。

```bash
PLACE dac_chip_1 IN plastic_bin_1     # 放入容器
PLACE book_1 ON table_1               # 放在表面
PLACE cleaning_cloth_1 ON bedside_table_1  # 放在床头柜上
```

**特性**:
- 支持IN和ON两种放置关系
- 自动更新物体位置和关系
- 维护智能体近邻关系

### EXPLORE
探索房间，发现未知物体。

```bash
EXPLORE                        # 探索当前房间
EXPLORE main_workbench_area    # 探索指定房间
```

**功能**:
- 发现房间内的隐藏物体
- 更新物体的发现状态
- 返回发现的物体数量

## 属性动作

属性动作通过CSV文件配置，支持动态添加。这些动作基于物体的属性状态进行操作。

### 配置文件
位置：`action/actions/attribute_actions.csv`

格式：
```csv
action_name,attribute,expected_value,requires_tool,description
open,is_open,false,false,"Opens a container or door"
clean,dirty,true,true,"Cleans a dirty object"
turn_on,is_on,false,false,"Turns on a device"
plug_in,is_plugged_in,false,false,"Plugs in a device"
```

### 不需要工具的动作
只有场景JSON中`abilities`字段包含的动作才会被注册：

```bash
# 以001号场景为例，只注册以下5个不需要工具的动作：
OPEN plastic_bin_1          # 打开容器
CLOSE plastic_bin_1         # 关闭容器
TURN_ON oscilloscope_1      # 开启设备
TURN_OFF oscilloscope_1     # 关闭设备
CONNECT cable_1             # 连接设备
```

**特点**:
- 基于场景配置，只注册场景支持的动作
- 基于物体当前属性状态
- 自动验证前置条件
- 场景内全局可用，无需特殊能力

### 需要工具的动作
智能体必须先拿起相应工具，动作会实时注册/取消注册：

```bash
# 需要先拿起 precision_screwdriver_1
SCREW component_1

# 需要先拿起 cleaning_cloth_1
CLEAN workbench_1

# 需要先拿起 repair_kit_1
REPAIR broken_device_1

# 需要先拿起 butter_knife_1
SPREAD butter_1

# 需要先拿起 mixing_spoon_1
STIR mixture_1
```

**工具能力映射**:
- `cleaning_cloth_1` → 提供 `clean` 能力
- `precision_screwdriver_1` → 提供 `screw` 能力
- `butter_knife_1` → 提供 `spread` 能力
- `mixing_spoon_1` → 提供 `stir` 能力

**实时动态能力系统**:
- 智能体抓取工具时自动获得能力并注册对应动作
- 放下工具时失去相应能力并取消注册对应动作
- 能力与库存物品实时同步
- 支持多个工具的动态切换

## 合作动作

多智能体协作动作，用于处理需要多个智能体配合的任务，特别是搬运重物。

### CORP_GRAB
合作抓取重物。需要指定参与的智能体和目标物体。

```bash
CORP_GRAB robot_1,robot_2 heavy_box_1
```

**前置条件**:
- 所有指定智能体都在物体附近
- 物体需要合作才能搬运（weight > single_agent_capacity）
- 所有智能体库存为空
- 物体未被其他智能体持有

### CORP_GOTO
合作移动到目标位置。所有参与的智能体一起移动。

```bash
CORP_GOTO robot_1,robot_2 storage_room
```

**特性**:
- 所有智能体同步移动
- 保持合作状态
- 更新所有智能体的位置

### CORP_PLACE
合作放置物体到指定位置。

```bash
CORP_PLACE robot_1,robot_2 heavy_box_1 IN storage_area
CORP_PLACE robot_1,robot_2 heavy_box_1 ON large_table_1
```

**后置效果**:
- 物体放置到目标位置
- 所有智能体释放合作状态
- 更新物体和智能体的近邻关系

### 合作流程
典型的合作搬运流程：

1. `CORP_GRAB` - 多个智能体合作抓取重物
2. `CORP_GOTO` - 合作移动到目标位置
3. `CORP_PLACE` - 合作放置物体

## 能力系统

智能体通过持有特定物体获得能力：

```python
# 物体提供能力
{
    "id": "toolbox_1",
    "properties": {
        "provides_abilities": ["repair", "fix"]
    }
}

# 智能体抓取工具箱后获得repair能力
# 可以执行repair动作
```

## 近邻关系

所有动作都依赖近邻关系：

1. 智能体必须先`goto`靠近目标
2. 只能与`near_objects`中的物体交互
3. 抓取物体后自动near该物体
4. 放置物体后仍然near该物体

## 动作验证

每个动作执行前都会进行验证：

1. 目标存在性检查
2. 近邻关系检查
3. 能力要求检查
4. 状态条件检查
5. 约束条件检查

## 实时动作描述功能

### 获取智能体支持的动作描述

系统提供了实时获取智能体当前支持的所有动作描述的功能：

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

== Cooperative Actions ==
CORP_GRAB <agent1,agent2> <object_id>
  - Multiple agents cooperatively grab a heavy object
  - Example: CORP_GRAB agent_1,agent_2 heavy_box_1
```

**特点**:
- **实时更新**: 动作描述会实时反映智能体当前的能力状态
- **完整覆盖**: 包括基础动作、属性动作、智能体特定动作和合作动作
- **英文描述**: 提供清晰的英文命令格式和功能说明
- **使用示例**: 每个动作都包含具体的使用示例

### 实时更新演示

```python
# 初始状态 - 只有基础动作和场景不需要工具的动作
initial_description = engine.get_agent_supported_actions_description([agent_id])

# 拿起工具 - 自动添加工具相关动作
engine.process_command(agent_id, "grab butter_knife_1")
updated_description = engine.get_agent_supported_actions_description([agent_id])
# 现在包含 SPREAD <object_id> 动作

# 放下工具 - 自动移除工具相关动作
engine.process_command(agent_id, "place butter_knife_1 on table_1")
final_description = engine.get_agent_supported_actions_description([agent_id])
# SPREAD 动作被移除，回到初始状态
```

## 扩展指南

### 1. 添加新的属性动作

**步骤1**: 在CSV文件中添加配置
```csv
# action/actions/attribute_actions.csv
action_name,attribute,expected_value,requires_tool,description
repair,broken,true,true,"Repairs a broken object"
```

**步骤2**: 确保物体具有相应属性
```json
{
  "id": "broken_device_1",
  "properties": {
    "broken": true
  }
}
```

**步骤3**: 在任务中包含能力
```json
{
  "abilities": ["repair"]
}
```

### 2. 创建自定义动作类

**步骤1**: 继承BaseAction
```python
from embodied_simulator.action.actions.base_action import BaseAction
from embodied_simulator.core import ActionStatus

class CustomAction(BaseAction):
    def execute(self, agent, target_id=None, **kwargs):
        """
        执行自定义动作

        Args:
            agent: 执行动作的智能体
            target_id: 目标物体ID
            **kwargs: 额外参数

        Returns:
            Tuple[ActionStatus, str, Dict]: (状态, 消息, 额外数据)
        """
        try:
            # 验证前置条件
            if not self._validate_preconditions(agent, target_id):
                return ActionStatus.FAILURE, "前置条件不满足", {}

            # 执行动作逻辑
            result = self._perform_action(agent, target_id)

            # 更新世界状态
            self._update_world_state(agent, target_id, result)

            return ActionStatus.SUCCESS, "动作执行成功", {"result": result}

        except Exception as e:
            return ActionStatus.FAILURE, f"执行失败: {e}", {}

    def _validate_preconditions(self, agent, target_id):
        """验证前置条件"""
        # 实现验证逻辑
        return True

    def _perform_action(self, agent, target_id):
        """执行具体动作"""
        # 实现动作逻辑
        return {}

    def _update_world_state(self, agent, target_id, result):
        """更新世界状态"""
        # 实现状态更新
        pass
```

**步骤2**: 注册动作
```python
# 在ActionManager中注册
action_manager.register_action_class("custom", CustomAction)

# 或在ActionHandler中注册
action_handler.register_action_class("custom", CustomAction)
```

### 3. 扩展合作动作

```python
class CustomCooperationAction(BaseAction):
    def execute(self, agent, target_id=None, **kwargs):
        # 解析参与的智能体
        agent_ids = kwargs.get('agent_ids', [])

        # 验证所有智能体都可用
        for agent_id in agent_ids:
            agent_obj = self.agent_manager.get_agent(agent_id)
            if not agent_obj:
                return ActionStatus.FAILURE, f"智能体 {agent_id} 不存在", {}

        # 执行合作逻辑
        # ...

        return ActionStatus.SUCCESS, "合作动作完成", {}
```

### 4. 动作验证扩展

```python
from embodied_simulator.utils.action_validators import ActionValidator

class CustomValidator(ActionValidator):
    @staticmethod
    def validate_custom_condition(env_manager, agent, target_id):
        """
        自定义验证条件

        Returns:
            Tuple[bool, str]: (是否通过, 错误消息)
        """
        # 实现验证逻辑
        if condition_met:
            return True, ""
        else:
            return False, "自定义条件不满足"
```

### 5. 配置文件扩展

**扩展属性动作配置**:
```csv
# 添加新的动作类型
action_name,attribute,expected_value,requires_tool,description,category
scan,scannable,true,true,"Scans an object for information","diagnostic"
analyze,analyzable,true,true,"Analyzes object composition","diagnostic"
```

**扩展工具能力映射**:
```json
{
  "id": "scanner_tool_1",
  "properties": {
    "provides_abilities": ["scan", "analyze"]
  }
}
```

## 最佳实践

### 1. 动作设计原则

- **单一职责**: 每个动作只做一件事
- **幂等性**: 重复执行相同动作应该产生相同结果
- **原子性**: 动作要么完全成功，要么完全失败
- **可逆性**: 尽可能提供撤销机制

### 2. 错误处理

```python
def execute(self, agent, target_id=None, **kwargs):
    try:
        # 动作逻辑
        pass
    except SpecificException as e:
        return ActionStatus.FAILURE, f"特定错误: {e}", {}
    except Exception as e:
        return ActionStatus.FAILURE, f"未知错误: {e}", {}
```

### 3. 状态管理

```python
def execute(self, agent, target_id=None, **kwargs):
    # 保存原始状态
    original_state = self._save_state()

    try:
        # 执行动作
        result = self._perform_action()
        return ActionStatus.SUCCESS, "成功", result
    except Exception as e:
        # 恢复原始状态
        self._restore_state(original_state)
        return ActionStatus.FAILURE, f"失败: {e}", {}
```

### 4. 性能优化

- **缓存验证结果**: 避免重复验证
- **批量操作**: 合并相似的操作
- **延迟计算**: 按需计算复杂结果

## 调试和测试

### 1. 动作测试

```python
def test_custom_action():
    # 创建测试环境
    engine = create_test_environment()

    # 执行动作
    status, message, result = engine.action_handler.process_command(
        "test_agent", "CUSTOM target_object"
    )

    # 验证结果
    assert status == ActionStatus.SUCCESS
    assert "成功" in message
    assert result is not None
```

### 2. 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 添加调试输出
def execute(self, agent, target_id=None, **kwargs):
    print(f"执行动作: {self.__class__.__name__}")
    print(f"智能体: {agent.id}, 目标: {target_id}")

    # 动作逻辑
    # ...
```

## 常见问题

### Q: 如何添加需要多个工具的动作？

A: 在验证阶段检查智能体是否拥有所有必需的能力：

```python
def _validate_preconditions(self, agent, target_id):
    required_abilities = ["ability1", "ability2"]
    for ability in required_abilities:
        if ability not in agent.abilities:
            return False
    return True
```

### Q: 如何实现条件动作（基于环境状态）？

A: 在动作执行前检查环境条件：

```python
def execute(self, agent, target_id=None, **kwargs):
    # 检查环境条件
    if not self._check_environment_condition():
        return ActionStatus.FAILURE, "环境条件不满足", {}

    # 继续执行
    # ...
```

### Q: 如何处理动作的副作用？

A: 在动作执行后更新相关的世界状态：

```python
def _update_world_state(self, agent, target_id, result):
    # 更新目标物体状态
    target_obj = self.env_manager.get_object_by_id(target_id)
    target_obj.properties.update(result.get("property_changes", {}))

    # 更新智能体状态
    agent.update_status(result.get("agent_changes", {}))

    # 触发相关事件
    self._trigger_side_effects(agent, target_id, result)
```
