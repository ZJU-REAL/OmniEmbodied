# 配置文件使用说明

## 概述

本目录包含三个主要的评测配置文件，每个文件针对不同的智能体模式进行了优化配置。

## 配置文件说明

### 1. single_agent_config.yaml
**用途**：单智能体模式评测配置
- **智能体类型**：单个LLM智能体
- **适用场景**：个体任务执行、基础能力评测
- **推荐任务筛选**：`agent_count: 'single'` (只评测单智能体任务)

### 2. centralized_config.yaml
**用途**：中心化多智能体模式评测配置
- **智能体类型**：协调器 + 工作智能体
- **适用场景**：需要统一协调的多智能体任务
- **推荐任务筛选**：`agent_count: 'multi'` (专注于协作任务)

### 3. decentralized_config.yaml
**用途**：去中心化多智能体模式评测配置
- **智能体类型**：多个自主智能体
- **适用场景**：需要自主协作的多智能体任务
- **推荐任务筛选**：`agent_count: 'multi'` (专注于协作任务)

## 关键配置项详解

### 场景选择 (scenario_selection)

```yaml
scenario_selection:
  mode: 'range'  # 'all', 'range', 'list'
  range:
    start: '00001'  # 起始场景ID
    end: '00010'    # 结束场景ID
  # list: ['00001', '00003', '00005']  # 指定场景列表
```

**说明**：
- 首先根据此配置确定基础场景列表
- 然后应用任务筛选进一步过滤

### 任务筛选 (task_filter)

#### 任务类别筛选 (categories)

```yaml
task_filter:
  categories: ['direct_command', 'attribute_reasoning']
```

**支持的任务类别**：
- `direct_command`: 直接命令任务
- `attribute_reasoning`: 属性推理任务
- `tool_use`: 工具使用任务
- `spatial_reasoning`: 空间推理任务
- `compound_reasoning`: 复合推理任务
- `explicit_collaboration`: 显式协作任务
- `implicit_collaboration`: 隐式协作任务
- `compound_collaboration`: 复合协作任务

#### 智能体数量筛选 (agent_count)

```yaml
task_filter:
  agent_count: 'single'  # 'single', 'multi', 'all'
```

**重要概念区分**：
- **任务设计时的智能体数量**：任务文件中`agents_config`的长度
- **评测时的智能体模式**：`--agent-type`参数指定的模式

**选项说明**：
- `single`: 只评测设计为单智能体的任务 (agents_config长度=1)
- `multi`: 只评测设计为多智能体的任务 (agents_config长度>1)
- `all`: 不限制智能体数量

## 配置组合建议

### 推荐配置组合

1. **单智能体基础评测**
   ```yaml
   # single_agent_config.yaml
   task_filter:
     agent_count: 'single'
   ```

2. **多智能体协作评测**
   ```yaml
   # centralized_config.yaml 或 decentralized_config.yaml
   task_filter:
     categories: ['explicit_collaboration', 'implicit_collaboration']
     agent_count: 'multi'
   ```

3. **特定任务类型评测**
   ```yaml
   task_filter:
     categories: ['direct_command', 'tool_use']
     agent_count: 'all'
   ```

### 研究性配置组合

1. **跨模式能力测试**
   ```yaml
   # single_agent_config.yaml
   task_filter:
     agent_count: 'multi'  # 单智能体尝试多智能体任务
   ```

2. **多智能体系统泛化能力**
   ```yaml
   # centralized_config.yaml
   task_filter:
     agent_count: 'single'  # 多智能体系统完成单智能体任务
   ```

## 使用示例

### 命令行使用

```bash
# 使用配置文件中的设置
python -m evaluation.evaluator \
  --config single_agent_config \
  --agent-type single \
  --task-type sequential

# 覆盖配置文件设置
python -m evaluation.evaluator \
  --config single_agent_config \
  --agent-type single \
  --task-type sequential \
  --task-categories direct_command \
  --agent-count-filter single
```

### Python API使用

```python
from evaluation.evaluation_interface import run_filtered_evaluation

# 使用配置文件设置
results = run_filtered_evaluation(
    config_file='single_agent_config',
    agent_type='single',
    task_type='sequential'
)

# 覆盖配置文件设置
results = run_filtered_evaluation(
    config_file='single_agent_config',
    agent_type='single',
    task_type='sequential',
    task_categories=['direct_command'],
    agent_count_filter='single'
)
```

## 注意事项

1. **配置优先级**：命令行参数 > 配置文件设置 > 默认值
2. **筛选逻辑**：场景选择与任务筛选取交集
3. **性能考虑**：任务筛选需要读取任务文件，会有轻微性能影响
4. **兼容性**：所有筛选功能都是可选的，不影响现有评测流程

## 故障排除

### 常见问题

1. **筛选后没有场景**
   - 检查筛选条件是否过于严格
   - 确认场景中包含指定类别的任务
   - 验证智能体数量筛选条件

2. **配置不生效**
   - 检查YAML语法是否正确
   - 确认缩进格式正确
   - 验证配置项名称拼写

3. **任务类别不匹配**
   - 检查任务文件中的`task_category`字段
   - 确认类别名称大小写正确
   - 验证任务文件格式

通过合理配置这些参数，你可以精确控制评测范围，提高评测效率和分析精度。
