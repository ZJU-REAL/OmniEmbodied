# Centralized Multi-Agent API Documentation

## 概述

中心化多智能体模式使用一个协调器(Coordinator)统一管理多个工作智能体(Worker)。协调器负责任务分解、规划和调度，工作智能体执行具体的子任务。

## 架构设计

```
Coordinator (协调器)
├── 任务分解与规划
├── 工作智能体管理
├── 统一决策与调度
└── 结果聚合

Workers (工作智能体)
├── Worker 1: 执行分配的子任务
├── Worker 2: 执行分配的子任务
└── Worker N: 执行分配的子任务
```

## 必须实现的接口

### 核心类1：CentralizedCoordinator

**文件位置**：`modes/centralized/coordinator.py`

**继承关系**：`CentralizedCoordinator(BaseAgent)`

#### 必须实现的方法

##### 1. `__init__(self, simulator: SimulationEngine, agent_id: str, config: Dict[str, Any])`
**功能**：初始化协调器
**参数**：
- `simulator`: 模拟器实例
- `agent_id`: 协调器ID（通常为"coordinator"）
- `config`: 配置字典

**实现要求**：
- 调用父类初始化
- 初始化LLM实例（用于规划）
- 初始化工作智能体字典
- 设置任务分解器和规划器

##### 2. `decide_action(self) -> str`
**功能**：协调器统一决策（核心方法）
**返回值**：当前执行的动作命令

**实现逻辑**：
1. 收集所有worker状态
2. 分析当前任务进度
3. 决定下一步行动
4. 分配任务给合适的worker
5. 返回当前执行的动作

##### 3. `add_worker(self, worker_id: str, worker_config: Dict[str, Any]) -> None`
**功能**：添加工作智能体
**参数**：
- `worker_id`: 工作智能体ID
- `worker_config`: 工作智能体配置

**实现要求**：
- 创建WorkerAgent实例
- 添加到工作智能体字典
- 设置worker的协调器引用

##### 4. `set_task(self, task_description: str) -> None`
**功能**：设置任务并分解给workers
**参数**：
- `task_description`: 任务描述

**实现要求**：
- 分析任务复杂度
- 分解为子任务
- 分配给合适的workers

##### 5. `set_trajectory_recorder(self, recorder) -> None`
**功能**：设置轨迹记录器
**实现要求**：
- 设置协调器的记录器
- 为所有workers设置记录器

##### 6. `reset(self) -> None`
**功能**：重置协调器和所有workers状态
**实现要求**：
- 重置协调器状态
- 重置所有workers状态
- 清空任务分配记录

##### 7. `get_mode_name(self) -> str`
**返回值**：`"centralized"`

#### 可选实现的方法

##### 1. `get_worker_status(self) -> Dict[str, Any]`
**功能**：获取所有工作智能体状态

##### 2. `reassign_task(self, failed_worker_id: str, task: Dict[str, Any]) -> bool`
**功能**：重新分配失败的任务

### 核心类2：WorkerAgent

**文件位置**：`modes/centralized/worker_agent.py`

**继承关系**：`WorkerAgent(BaseAgent)`

#### 必须实现的方法

##### 1. `__init__(self, simulator: SimulationEngine, agent_id: str, config: Dict[str, Any])`
**功能**：初始化工作智能体

##### 2. `execute_assigned_task(self, task_assignment: Dict[str, Any]) -> str`
**功能**：执行协调器分配的任务
**参数**：
- `task_assignment`: 任务分配信息

**任务分配格式**：
```python
{
    "task_id": "subtask_1",
    "description": "找到红色苹果",
    "priority": 1,
    "deadline": "2024-01-01T12:00:00",
    "resources": ["vision", "manipulation"]
}
```

##### 3. `report_status(self) -> Dict[str, Any]`
**功能**：向协调器报告状态
**返回值**：状态信息字典

**状态格式**：
```python
{
    "worker_id": "worker_1",
    "status": "busy",  # "idle", "busy", "failed"
    "current_task": "subtask_1",
    "progress": 0.6,
    "last_action": "GRAB apple_1",
    "capabilities": ["vision", "manipulation"]
}
```

##### 4. `reset(self) -> None`
**功能**：重置工作智能体状态

#### 可选实现的方法

##### 1. `set_coordinator(self, coordinator) -> None`
**功能**：设置协调器引用

##### 2. `request_help(self, help_type: str) -> bool`
**功能**：向协调器请求帮助

## 配置文件结构

**文件位置**：`config/baseline/centralized_config.yaml`

```yaml
coordinator_config:
  agent_class: "modes.centralized.coordinator.CentralizedCoordinator"
  max_workers: 3
  planning_strategy: "hierarchical"  # "hierarchical", "sequential"
  task_allocation_method: "capability_based"  # "round_robin", "capability_based"

worker_config:
  agent_class: "modes.centralized.worker_agent.WorkerAgent"
  specialization: "general"  # "general", "vision", "manipulation"
  max_concurrent_tasks: 1

llm_config:
  model_name: "gpt-4"
  temperature: 0.1

execution:
  max_total_steps: 300
  max_steps_per_task: 50
  coordination_interval: 5  # 每N步进行一次协调
```

## 使用示例

```python
from modes.centralized.coordinator import CentralizedCoordinator
from modes.centralized.worker_agent import WorkerAgent

# 初始化协调器
coordinator = CentralizedCoordinator(simulator, "coordinator", config)

# 添加工作智能体
for i in range(3):
    worker_id = f"worker_{i+1}"
    coordinator.add_worker(worker_id, worker_config)

# 设置任务
coordinator.set_task("团队协作找到所有水果并分类放置")

# 执行循环
for step in range(max_steps):
    action = coordinator.decide_action()
    status, message, result = coordinator.step()
    
    if "DONE" in action:
        break

# 重置
coordinator.reset()
```

## 通信协议

### 协调器 -> Worker
```python
{
    "type": "task_assignment",
    "task": {
        "task_id": "subtask_1",
        "description": "找到红色苹果",
        "priority": 1
    }
}
```

### Worker -> 协调器
```python
{
    "type": "status_report",
    "worker_id": "worker_1",
    "status": "completed",
    "result": {
        "success": True,
        "message": "已找到红色苹果"
    }
}
```

## 注意事项

1. **任务分解**：协调器需要智能地分解复杂任务
2. **负载均衡**：合理分配任务给不同workers
3. **故障处理**：处理worker失败的情况
4. **同步机制**：确保协调器和workers状态同步
5. **资源管理**：避免workers之间的资源冲突

## 实现参考

参考`modes/single_agent/llm_agent.py`的实现模式：
- LLM集成方式
- 配置管理方式
- 轨迹记录方式
- 提示词管理方式

协调器应该类似单智能体，但需要额外的任务分解和工作智能体管理能力。
