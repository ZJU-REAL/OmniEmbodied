# 并行任务评测器使用指南

## 概述

并行任务评测器 (`ParallelTaskEvaluator`) 支持多个任务的并行评测，每个任务使用完全独立的模拟器实例，确保完全隔离，避免任何资源竞争和状态污染。

## 主要特性

- **完全隔离**：每个任务使用独立的模拟器实例、智能体实例和配置副本
- **灵活配置**：支持多种任务选择模式和并行执行参数
- **健壮性**：单任务失败不影响其他任务，支持重试机制
- **独立轨迹**：每个任务的轨迹独立保存，便于分析
- **资源管理**：自动清理资源，避免内存泄漏

## 配置说明

### 启用并行评测

在配置文件中设置：

```yaml
parallel_evaluation:
  enabled: true
```

### 并行执行配置

```yaml
parallel_evaluation:
  # 并行执行模式: 'thread' (线程) 或 'process' (进程)
  execution_mode: 'thread'
  
  # 最大并行任务数量 (0表示使用CPU核心数)
  max_parallel_tasks: 4
```

### 任务选择配置

#### 1. 所有任务模式
```yaml
task_selection:
  mode: 'all'
```

#### 2. 范围模式
```yaml
task_selection:
  mode: 'range'
  range:
    start_index: 0  # 起始任务索引
    end_index: 5    # 结束任务索引 (-1表示到最后)
```

#### 3. 指定列表模式
```yaml
task_selection:
  mode: 'list'
  task_indices: [0, 2, 4, 6]  # 指定任务索引列表
```

#### 4. 按类别模式
```yaml
task_selection:
  mode: 'category'
  categories: ['direct_command', 'tool_use']  # 指定任务类别
```

### 故障处理配置

```yaml
failure_handling:
  # 单个任务失败时是否继续其他任务
  continue_on_task_failure: true
  
  # 最大重试次数
  max_retries: 1
  
  # 重试延迟时间(秒)
  retry_delay: 5.0
```

## 使用方法

### 1. 命令行使用

```bash
# 使用并行模式评测
python evaluation/evaluator.py --mode parallel --scenario 00001

# 使用自定义配置
python evaluation/evaluator.py --mode parallel --config my_parallel_config.yaml --scenario 00001
```

### 2. 程序化使用

```python
from utils.parallel_task_evaluator import ParallelTaskEvaluator

# 创建并行评测器
evaluator = ParallelTaskEvaluator(
    config_file='single_agent_config',
    agent_type='single',
    task_type='sequential',
    scenario_id='00001',
    custom_suffix='my_test'
)

# 运行并行评测
results = evaluator.run_parallel_evaluation()

# 查看结果
print(f"完成任务: {results['summary']['completed_tasks']}")
print(f"总耗时: {results['run_info']['total_duration']:.2f}秒")
print(f"并行效率: {results['summary']['parallel_efficiency']:.2f}")
```

## 输出结构

并行评测会创建以下文件结构：

```
output/
├── parallel_run_20250701_143022_single_sequential_scenario_00001_test/
│   ├── parallel_results.json           # 详细结果
│   ├── run_summary.json               # 运行摘要
│   ├── parallel_execution.log         # 主日志文件
│   ├── task_00000/                    # 任务0独立目录
│   │   ├── trajectory.json
│   │   ├── compact_trajectory.json
│   │   └── task_00000_execution.log
│   ├── task_00001/                    # 任务1独立目录
│   │   ├── trajectory.json
│   │   ├── compact_trajectory.json
│   │   └── task_00001_execution.log
│   └── ...
```

## 结果分析

### 主要指标

- **完成率**：`completed_tasks / total_tasks`
- **平均执行时间**：所有任务的平均执行时间
- **并行效率**：理论串行时间 / 实际并行时间
- **成功率**：成功完成的任务比例

### 结果文件

1. **parallel_results.json**：包含所有任务的详细执行结果
2. **run_summary.json**：运行摘要和统计信息
3. **task_xxxxx/trajectory.json**：每个任务的详细轨迹

## 最佳实践

1. **资源配置**：根据系统资源合理设置 `max_parallel_tasks`
2. **任务选择**：使用范围或类别模式进行有针对性的评测
3. **故障处理**：启用 `continue_on_task_failure` 确保评测完整性
4. **日志分析**：查看各任务的独立日志文件进行问题诊断
5. **性能监控**：关注并行效率指标，优化并行度设置

## 注意事项

- 每个任务使用完全独立的模拟器实例，确保无状态污染
- 并行度过高可能导致系统资源不足，建议根据硬件配置调整
- 任务间启动有延迟机制，避免同时初始化造成资源竞争
- 支持优雅中断，接收信号时会保存当前所有任务状态
