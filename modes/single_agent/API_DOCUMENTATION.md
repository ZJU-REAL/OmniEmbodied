# Single Agent API Documentation

## 概述

单智能体模式使用单个LLM智能体来执行所有任务。智能体需要能够独立分析环境、制定计划并执行动作。

## 必须实现的接口

### 核心类：LLMAgent

**文件位置**：`modes/single_agent/llm_agent.py`

**继承关系**：`LLMAgent(BaseAgent)`

### 必须实现的方法

#### 1. `__init__(self, simulator: SimulationEngine, agent_id: str, config: Dict[str, Any])`
**功能**：初始化单智能体
**参数**：
- `simulator`: 模拟器实例
- `agent_id`: 智能体ID（通常为"agent_1"）
- `config`: 配置字典

**实现要求**：
- 调用父类初始化
- 初始化LLM实例
- 设置提示词管理器
- 初始化对话历史

#### 2. `decide_action(self) -> str`
**功能**：决定下一步动作（核心方法）
**返回值**：动作命令字符串

**支持的动作格式**：
- `"EXPLORE"` - 探索环境
- `"GRAB object_name"` - 抓取物体
- `"PLACE object_name location"` - 放置物体
- `"DONE"` - 完成任务

**实现要求**：
- 构建包含环境信息的提示词
- 调用LLM生成响应
- 解析响应提取动作命令
- 记录LLM交互到轨迹记录器

#### 3. `set_task(self, task_description: str) -> None`
**功能**：设置当前任务描述
**参数**：
- `task_description`: 任务描述文本

**实现要求**：
- 保存任务描述到实例变量
- 可选：重置相关状态

#### 4. `set_trajectory_recorder(self, recorder) -> None`
**功能**：设置轨迹记录器用于记录LLM交互
**参数**：
- `recorder`: 轨迹记录器实例

**实现要求**：
- 保存记录器引用
- 在LLM交互时调用记录器方法

#### 5. `reset(self) -> None`
**功能**：重置智能体状态
**使用场景**：
- Sequential模式：场景间重置
- Independent模式：任务间重置

**实现要求**：
- 清空对话历史
- 重置失败计数器
- 清空动作历史
- 重置环境描述缓存

#### 6. `get_mode_name(self) -> str`
**功能**：返回模式名称
**返回值**：`"single_agent"`

### 可选实现的方法

#### 1. `get_llm_interaction_info(self) -> Dict[str, Any]`
**功能**：获取最后一次LLM交互的详细信息
**返回值**：包含prompt、response、model_info的字典

#### 2. `update_chat_history(self, user_message: str, assistant_message: str) -> None`
**功能**：更新对话历史
**参数**：
- `user_message`: 用户消息
- `assistant_message`: 助手回复

## 配置文件结构

**文件位置**：`config/baseline/single_agent_config.yaml`

```yaml
agent_config:
  agent_class: "modes.single_agent.llm_agent.LLMAgent"
  max_failures: 3
  max_history: 50

llm_config:
  model_name: "gpt-4"
  temperature: 0.1
  max_tokens: 1000

execution:
  max_total_steps: 200
  max_steps_per_task: 50
  timeout_seconds: 900

history:
  max_history_length: 10  # -1 表示不限制

environment_description:
  detail_level: "full"  # "full", "medium", "minimal"
  update_frequency: 1   # 每N步更新一次
```

## 使用示例

```python
from modes.single_agent.llm_agent import LLMAgent
from OmniSimulator import SimulationEngine

# 初始化
simulator = SimulationEngine()
config = load_config('single_agent_config')
agent = LLMAgent(simulator, "agent_1", config)

# 设置任务
agent.set_task("请找到红色的苹果并将其放到桌子上")

# 设置轨迹记录器
agent.set_trajectory_recorder(trajectory_recorder)

# 执行循环
for step in range(max_steps):
    action = agent.decide_action()
    status, message, result = agent.step()
    
    if "DONE" in action:
        break

# 重置（用于下一个任务）
agent.reset()
```

## 注意事项

1. **LLM交互记录**：每次调用LLM时必须记录到轨迹记录器
2. **错误处理**：需要处理LLM响应解析失败的情况
3. **历史管理**：合理管理对话历史长度，避免token超限
4. **状态重置**：确保reset()方法彻底清理状态
5. **线程安全**：如果支持并行，需要考虑线程安全
