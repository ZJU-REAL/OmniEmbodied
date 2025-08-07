# Task Filtering Feature Usage Guide

## Overview

The task filtering feature allows you to filter evaluation tasks based on task types and agent counts, enabling more precise evaluation analysis. This feature supports both configuration file setup and command-line parameter methods.

## Supported Filtering Conditions

### 1. Task Category Filtering (categories)

Filter based on the task's `task_category` field:

- `direct_command` - Direct command tasks
- `attribute_reasoning` - Attribute reasoning tasks  
- `tool_use` - Tool usage tasks
- `spatial_reasoning` - Spatial reasoning tasks
- `compound_reasoning` - Compound reasoning tasks
- `explicit_collaboration` - Explicit collaboration tasks
- `implicit_collaboration` - Implicit collaboration tasks
- `compound_collaboration` - Compound collaboration tasks

### 2. Agent Count Filtering (agent_count)

Filter based on the number of agents in the scenario:

- `single` - Only evaluate single-agent tasks (agents_config length equals 1)
- `multi` - Only evaluate multi-agent tasks (agents_config length greater than 1)
- `all` - No agent count restriction (default value)

## 配置方法

### 方法1：配置文件配置

在配置文件的`parallel_evaluation.scenario_selection.task_filter`部分添加筛选条件：

```yaml
parallel_evaluation:
  scenario_selection:
    mode: 'range'
    range:
      start: '00001'
      end: '00010'

    # 任务筛选配置 (与场景选择取交集)
    # 说明：任务筛选用于根据任务特征进一步筛选要评测的场景
    # 只有包含符合筛选条件任务的场景才会被评测
    task_filter:
      # 任务类别筛选 (可选)
      # 说明：根据任务的task_category字段筛选任务
      # 用法：取消注释并指定要筛选的类别列表
      categories: ['direct_command', 'attribute_reasoning']

      # 智能体数量筛选 (可选)
      # 说明：根据任务设计时的智能体数量筛选任务
      # 注意：这里指的是任务文件中agents_config的数量，不是评测时使用的智能体模式
      # 重要说明：
      #   - 如果设置为'single'，单智能体模式只会评测原本就是单智能体的任务
      #   - 如果设置为'multi'，单智能体模式会尝试完成原本设计给多智能体的任务
      #   - 如果设置为'all'，单智能体模式可能会遇到需要协作的任务（可能失败）
      # 推荐配置：
      #   - 单智能体配置文件建议使用 agent_count: 'single'
      #   - 多智能体配置文件建议使用 agent_count: 'multi'
      agent_count: 'single'
```

**配置文件说明**：
- `single_agent_config.yaml`: 推荐使用 `agent_count: 'single'`
- `centralized_config.yaml`: 推荐使用 `agent_count: 'multi'`
- `decentralized_config.yaml`: 推荐使用 `agent_count: 'multi'`

### 方法2：命令行参数

```bash
# 按任务类别筛选
python -m evaluation.evaluator \
  --config single_agent_config \
  --agent-type single \
  --task-type sequential \
  --scenarios 00001-00010 \
  --task-categories direct_command attribute_reasoning \
  --suffix filtered_tasks

# 按智能体数量筛选
python -m evaluation.evaluator \
  --config single_agent_config \
  --agent-type single \
  --task-type sequential \
  --scenarios all \
  --agent-count-filter single \
  --suffix single_agent_only

# 组合筛选
python -m evaluation.evaluator \
  --config centralized_config \
  --agent-type multi \
  --task-type combined \
  --scenarios all \
  --task-categories direct_command tool_use \
  --agent-count-filter multi \
  --suffix multi_agent_tools
```

### 方法3：Python API

```python
from evaluation.evaluation_interface import run_filtered_evaluation

# 使用便利函数
results = run_filtered_evaluation(
    config_file='single_agent_config',
    agent_type='single',
    task_type='sequential',
    scenarios='all',
    task_categories=['direct_command'],
    agent_count_filter='single',
    suffix='direct_command_single'
)

# 使用完整接口
from evaluation.evaluation_interface import EvaluationInterface

scenario_selection = {
    'mode': 'range',
    'range': {'start': '00001', 'end': '00010'},
    'task_filter': {
        'categories': ['direct_command', 'attribute_reasoning'],
        'agent_count': 'all'
    }
}

results = EvaluationInterface.run_evaluation(
    config_file='single_agent_config',
    agent_type='single',
    task_type='sequential',
    scenario_selection=scenario_selection,
    custom_suffix='filtered_evaluation'
)
```

## 筛选逻辑

### 场景与任务筛选的交集

任务筛选与场景选择取**交集**：

1. **场景筛选**：首先根据`mode`、`range`、`list`选择基础场景列表
2. **任务筛选**：然后对每个场景检查是否包含符合筛选条件的任务
3. **最终结果**：只有包含符合条件任务的场景才会被评测

### 筛选算法

对于每个场景：

```python
# 智能体数量检查
agents_count = len(task_data['agents_config'])
if agent_count_filter == 'single' and agents_count != 1:
    continue  # 跳过此场景
elif agent_count_filter == 'multi' and agents_count <= 1:
    continue  # 跳过此场景

# 任务类别检查
if categories_filter:
    task_categories = [task['task_category'] for task in task_data['tasks']]
    if not any(category in categories_filter for category in task_categories):
        continue  # 跳过此场景

# 通过筛选，包含此场景
```

## 使用示例

### 示例1：只评测直接命令任务

```bash
python -m evaluation.evaluator \
  --config single_agent_config \
  --agent-type single \
  --task-type sequential \
  --scenarios all \
  --task-categories direct_command \
  --suffix direct_command_only
```

### 示例2：只评测单智能体任务

```bash
python -m evaluation.evaluator \
  --config single_agent_config \
  --agent-type single \
  --task-type sequential \
  --scenarios all \
  --agent-count-filter single \
  --suffix single_agent_tasks
```

### 示例3：评测多智能体的协作任务

```bash
python -m evaluation.evaluator \
  --config centralized_config \
  --agent-type multi \
  --task-type combined \
  --scenarios all \
  --task-categories explicit_collaboration implicit_collaboration \
  --agent-count-filter multi \
  --suffix collaboration_tasks
```

### 示例4：使用配置文件筛选

修改`config/baseline/single_agent_config.yaml`：

```yaml
parallel_evaluation:
  scenario_selection:
    mode: 'all'
    task_filter:
      categories: ['direct_command']
      agent_count: 'all'
```

然后运行：

```bash
python -m evaluation.evaluator \
  --config single_agent_config \
  --agent-type single \
  --task-type sequential \
  --suffix config_filtered
```

## 日志输出

筛选过程会在日志中显示详细信息：

```
2025-07-16 07:27:52,772 - evaluation.scenario_selector - INFO - 任务筛选结果: 5 -> 3 个场景
2025-07-16 07:27:52,772 - evaluation.scenario_selector - INFO -   类别筛选: ['direct_command']
2025-07-16 07:27:52,772 - evaluation.scenario_selector - INFO -   智能体数量筛选: single
```

## 注意事项

1. **配置优先级**：命令行参数会覆盖配置文件中的设置
2. **筛选严格性**：如果筛选条件过于严格，可能导致没有场景通过筛选
3. **性能影响**：任务筛选需要读取所有任务文件，对性能有轻微影响
4. **兼容性**：筛选功能向后兼容，不影响现有的评测流程

## 故障排除

### 问题1：筛选后没有场景

**现象**：`任务筛选结果: X -> 0 个场景`

**解决方案**：
- 检查筛选条件是否过于严格
- 确认场景中确实包含指定类别的任务
- 验证智能体数量筛选条件是否正确

### 问题2：筛选条件不生效

**现象**：筛选前后场景数量相同

**解决方案**：
- 确认配置文件格式正确
- 检查命令行参数拼写
- 验证任务文件中的`task_category`字段

通过任务筛选功能，你可以更精确地评测特定类型的任务，提高评测效率和分析精度。
