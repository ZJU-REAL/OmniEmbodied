# Decentralized Multi-Agent API Documentation

## 概述

去中心化多智能体模式使用多个自主智能体，每个智能体都具有独立的决策能力。智能体之间通过通信协商任务分配，无需中央协调器。

## 架构设计

```
AutonomousAgent 1 ←→ AutonomousAgent 2
        ↕                    ↕
AutonomousAgent 3 ←→ AutonomousAgent N

每个智能体都能：
├── 自主决策
├── 与其他智能体通信
├── 协商任务分配
└── 独立执行任务
```

## 必须实现的接口

### 核心类1：AutonomousAgent

**文件位置**：`modes/decentralized/autonomous_agent.py`

**继承关系**：`AutonomousAgent(BaseAgent)`

#### 必须实现的方法

##### 1. `__init__(self, simulator: SimulationEngine, agent_id: str, config: Dict[str, Any])`
**功能**：初始化自主智能体
**参数**：
- `simulator`: 模拟器实例
- `agent_id`: 智能体ID（如"agent_1", "agent_2"等）
- `config`: 配置字典

**实现要求**：
- 调用父类初始化
- 初始化LLM实例
- 初始化通信管理器
- 设置协商策略

##### 2. `decide_action(self) -> str`
**功能**：自主决策动作（核心方法）
**返回值**：动作命令字符串

**实现逻辑**：
1. 检查是否有新的通信消息
2. 分析当前任务状态
3. 决定是否需要与其他智能体协商
4. 执行自主决策
5. 返回动作命令

##### 3. `communicate_with_peers(self, message: Dict[str, Any]) -> Dict[str, Any]`
**功能**：与其他智能体通信
**参数**：
- `message`: 要发送的消息

**消息格式**：
```python
{
    "sender_id": "agent_1",
    "receiver_id": "agent_2",  # 或 "broadcast" 表示广播
    "message_type": "task_negotiation",  # "task_negotiation", "status_update", "help_request"
    "content": {
        "task_id": "task_1",
        "proposal": "我可以处理这个任务"
    },
    "timestamp": "2024-01-01T12:00:00"
}
```

##### 4. `negotiate_task_allocation(self, available_tasks: List[Dict]) -> Dict[str, Any]`
**功能**：协商任务分配
**参数**：
- `available_tasks`: 可用任务列表

**返回值**：协商结果
```python
{
    "accepted_tasks": ["task_1", "task_3"],
    "rejected_tasks": ["task_2"],
    "proposals": [
        {
            "task_id": "task_4",
            "agent_id": "agent_2",
            "reason": "agent_2更适合处理这个任务"
        }
    ]
}
```

##### 5. `set_peer_agents(self, peer_agents: List['AutonomousAgent']) -> None`
**功能**：设置对等智能体列表
**参数**：
- `peer_agents`: 其他智能体实例列表

##### 6. `set_task(self, task_description: str) -> None`
**功能**：设置任务
**参数**：
- `task_description`: 任务描述

##### 7. `set_trajectory_recorder(self, recorder) -> None`
**功能**：设置轨迹记录器

##### 8. `reset(self) -> None`
**功能**：重置智能体状态
**实现要求**：
- 清空通信历史
- 重置协商状态
- 清空任务分配记录

##### 9. `get_mode_name(self) -> str`
**返回值**：`"decentralized"`

#### 可选实现的方法

##### 1. `get_agent_capabilities(self) -> List[str]`
**功能**：获取智能体能力列表

##### 2. `evaluate_task_suitability(self, task: Dict[str, Any]) -> float`
**功能**：评估任务适合度（0-1分数）

##### 3. `handle_conflict_resolution(self, conflict: Dict[str, Any]) -> Dict[str, Any]`
**功能**：处理任务冲突

### 核心类2：CommunicationManager

**文件位置**：`modes/decentralized/communication.py`

#### 必须实现的方法

##### 1. `__init__(self, agent_id: str)`
**功能**：初始化通信管理器
**参数**：
- `agent_id`: 所属智能体ID

##### 2. `send_message(self, target_agent_id: str, message: Dict[str, Any]) -> bool`
**功能**：发送消息给目标智能体
**参数**：
- `target_agent_id`: 目标智能体ID
- `message`: 消息内容

##### 3. `receive_messages(self) -> List[Dict[str, Any]]`
**功能**：接收消息
**返回值**：消息列表

##### 4. `broadcast_message(self, message: Dict[str, Any]) -> bool`
**功能**：广播消息给所有智能体
**参数**：
- `message`: 消息内容

## 配置文件结构

**文件位置**：`config/baseline/decentralized_config.yaml`

```yaml
agent_config:
  agent_class: "modes.decentralized.autonomous_agent.AutonomousAgent"
  num_agents: 3
  negotiation_strategy: "auction_based"  # "auction_based", "consensus", "priority_based"
  cooperation_level: "high"  # "low", "medium", "high"

communication_config:
  protocol: "direct"  # "direct", "broadcast", "gossip"
  timeout: 5.0
  max_message_queue: 100
  retry_attempts: 3

llm_config:
  model_name: "gpt-4"
  temperature: 0.2  # 稍高一些以增加多样性

execution:
  max_total_steps: 400
  max_steps_per_task: 60
  negotiation_rounds: 3
```

## 使用示例

```python
from modes.decentralized.autonomous_agent import AutonomousAgent

# 创建多个自主智能体
agents = []
for i in range(3):
    agent_id = f"agent_{i+1}"
    agent = AutonomousAgent(simulator, agent_id, config)
    agents.append(agent)

# 设置对等关系
for agent in agents:
    peers = [a for a in agents if a != agent]
    agent.set_peer_agents(peers)

# 设置任务
task_description = "团队自主协作完成复杂任务"
for agent in agents:
    agent.set_task(task_description)

# 执行循环（每个智能体独立执行）
for step in range(max_steps):
    for agent in agents:
        action = agent.decide_action()
        status, message, result = agent.step()
        
        if "DONE" in action:
            break

# 重置所有智能体
for agent in agents:
    agent.reset()
```

## 通信协议

### 任务协商消息
```python
{
    "message_type": "task_negotiation",
    "content": {
        "task_id": "task_1",
        "action": "bid",  # "bid", "accept", "reject", "counter_offer"
        "bid_value": 0.8,
        "capabilities": ["vision", "manipulation"],
        "estimated_time": 30
    }
}
```

### 状态更新消息
```python
{
    "message_type": "status_update",
    "content": {
        "agent_status": "busy",
        "current_task": "task_1",
        "progress": 0.6,
        "available_capacity": 0.4
    }
}
```

### 帮助请求消息
```python
{
    "message_type": "help_request",
    "content": {
        "problem_type": "stuck",
        "current_situation": "无法找到目标物体",
        "requested_help": "需要其他智能体协助搜索"
    }
}
```

## 协商策略

### 1. 拍卖机制 (auction_based)
- 任务发布者广播任务
- 智能体提交竞标
- 选择最优竞标者

### 2. 共识机制 (consensus)
- 所有智能体参与讨论
- 通过投票达成共识
- 分配任务给合适的智能体

### 3. 优先级机制 (priority_based)
- 根据智能体优先级分配
- 高优先级智能体优先选择
- 剩余任务分配给其他智能体

## 注意事项

1. **通信开销**：合理控制通信频率和消息大小
2. **死锁避免**：防止智能体间的循环等待
3. **一致性保证**：确保智能体间状态一致
4. **故障恢复**：处理智能体失效的情况
5. **负载均衡**：避免某个智能体过载

## 实现参考

参考`modes/single_agent/llm_agent.py`的实现模式：
- LLM集成方式
- 配置管理方式
- 轨迹记录方式
- 提示词管理方式

自主智能体应该在单智能体基础上增加通信和协商能力。
