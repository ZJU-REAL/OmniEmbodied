# 动态动作注册系统

## 概述

本文档描述了新实现的动态动作注册系统，该系统根据任务配置动态注册动作，避免了之前一次性注册所有动作的问题。

## 核心设计原则

### 1. 分层注册策略
- **全局注册**: 不需要工具的动作在系统初始化时全局注册
- **动态注册**: 需要工具的动作根据任务的`abilities`字段动态注册

### 2. 基于数据驱动
- 测试场景和任务从`data`文件夹读取，作为标准样本使用
- 支持场景数据、任务数据和验证数据的完整加载

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

### 2. 增强的AttributeAction类
新增了任务特定的动作注册方法：

```python
# 全局注册不需要工具的动作
AttributeAction.register_global_no_tool_actions(action_manager)

# 根据任务abilities动态注册需要工具的动作
AttributeAction.register_task_specific_actions(action_manager, task_abilities)
```

**关键方法**:
- `register_global_no_tool_actions()`: 注册所有不需要工具的动作
- `register_task_specific_actions()`: 根据任务能力注册特定动作
- `get_available_actions_for_abilities()`: 获取能力对应的可用动作

### 3. 更新的SimulationEngine
支持基于任务能力的初始化：

```python
# 创建带有任务能力的引擎
engine = SimulationEngine(task_abilities=["clean", "open", "turn_on"])

# 或者后续更新能力
engine.update_task_abilities(new_abilities)
```

**新增功能**:
- 构造函数接受`task_abilities`参数
- 自动注册任务特定的动作
- 支持运行时更新能力

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

## 数据文件结构

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
    "clean",
    "open", 
    "plug_in",
    "turn_on",
    "turn_off"
  ],
  "single_agent_tasks": {
    "direct_command": [...],
    "tool_use": [...]
  },
  "scene_id": "00001"
}
```

### 场景文件格式 (data/scene/*.json)
```json
{
  "description": "场景描述",
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

### 1. 创建基于任务的仿真环境
```python
from embodied_simulator.utils.data_loader import default_data_loader
from embodied_simulator.core import SimulationEngine

# 加载任务数据
task_data = default_data_loader.load_task("00001")
abilities = task_data.get("abilities", [])

# 创建引擎
engine = SimulationEngine(task_abilities=abilities)

# 初始化环境
scene_data = default_data_loader.load_scene("00001")
engine.initialize_with_data({
    'scene': scene_data,
    'task': task_data
})
```

### 2. 执行任务命令
```python
# 获取任务命令
commands = default_data_loader.get_task_commands("00001", "direct_command")

# 执行命令
for command in commands:
    if "Turn on" in command and "oscilloscope_1" in command:
        status, message, _ = engine.process_command("robot_1", "TURN_ON oscilloscope_1")
        print(f"执行结果: {status}, 消息: {message}")
```

## 优势

### 1. 性能优化
- 只注册任务需要的动作，减少内存占用
- 避免不必要的动作验证开销

### 2. 灵活性
- 支持不同任务的不同动作集合
- 运行时动态调整可用动作

### 3. 可维护性
- 基于数据驱动，易于添加新场景和任务
- 清晰的分层架构，便于扩展

### 4. 测试完整性
- 基于真实数据的测试，更接近实际使用场景
- 全面的边界情况测试，提高系统稳定性

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
