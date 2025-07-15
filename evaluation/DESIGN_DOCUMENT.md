# 评测器重构设计方案

## 1. 项目背景与需求分析

### 1.1 当前系统分析
当前评测系统具有以下特点：

#### 1.1.1 评测模式支持
- **单场景评测模式**：
  - `single_sequential`：单智能体逐个评测，每个子任务独立执行
  - `single_combined`：单智能体混合评测，所有子任务拼接执行
  - `single_independent`：单智能体独立评测，每个子任务在全新环境中执行
  - `multi_sequential`：多智能体逐个评测，每个子任务独立执行
  - `multi_combined`：多智能体混合评测，所有子任务拼接执行
  - `multi_independent`：多智能体独立评测，每个子任务在全新环境中执行

- **并行场景评测模式**：
  - `parallel_single_*`：单智能体场景级并行评测
  - `parallel_multi_*`：多智能体场景级并行评测

#### 1.1.2 Baseline配置
- `single_agent_config`：单智能体基线配置
- `centralized_config`：中心化多智能体基线配置
- `decentralized_config`：去中心化多智能体基线配置

#### 1.1.3 并行评测支持
- **场景选择模式**：
  - `all`：评测所有可用场景
  - `range`：评测指定范围的场景（如00001-00010）
  - `list`：评测指定列表的场景
- **并行配置**：支持最大并行场景数配置
- **输出管理**：独立的轨迹保存和汇总报告生成

#### 1.1.4 轨迹记录系统
- **详细轨迹**：完整的执行过程记录（trajectory.json）
- **简洁轨迹**：关键执行信息记录（compact_trajectory.json）
- **LLM交互记录**：按子任务分类的QA记录（llm_qa.json）
- **实时CSV记录**：子任务执行日志的实时保存（subtask_execution_log.csv）
- **执行日志**：详细的执行日志文件（execution.log）

### 1.2 重构需求
根据您的要求，重构评测器需要：
1. **仅重构评测器部分**：不修改baseline代码，保持现有baseline实现
2. **保持现有功能**：继承当前评测器的所有功能和配置
3. **优化架构设计**：提供更清晰的模块化结构
4. **保持兼容性**：确保与现有配置文件和输出格式兼容

## 2. 重构设计方案

### 2.1 简化架构设计

基于您的要求，采用简洁明了的架构，避免过度分化：

```
evaluation/
├── __init__.py
├── DESIGN_DOCUMENT.md          # 本设计文档
├── evaluation_manager.py       # 统一评测管理器（主要逻辑）
├── scenario_selector.py        # 场景选择器（支持all/range/list）
├── trajectory_manager.py       # 轨迹管理器（基于现有TrajectoryRecorder）
├── independent_executor.py     # Independent模式执行器（重新实现）
└── evaluator.py               # 主入口脚本（重构后）
```

**设计原则**：
- **统一并行实现**：所有评测都使用并行框架，单场景时并行数为1
- **简化模块结构**：避免过多子文件夹和子模式
- **统一输出目录**：每次运行都在一个父文件夹下，不论什么模式
- **代码复用**：最大化复用现有TaskEvaluator和相关组件

### 2.2 统一输出目录结构

#### 2.2.1 运行命名规则（简化）
```
统一格式：{timestamp}_{agent_type}_{task_type}_{custom_suffix}
示例：
- 20250716_012148_single_independent_demo
- 20250716_012148_multi_sequential_baseline_test
- 20250716_012148_single_combined_experiment1
```

**说明**：
- 移除scenario_id，因为每次运行可能包含多个场景或场景范围
- 统一命名格式，不区分单场景和多场景
- custom_suffix可以用来标识具体的实验或测试内容

#### 2.2.2 统一输出目录结构（所有模式）
```
output/
├── {run_name}/                 # 每次运行的统一父文件夹
│   ├── run_summary.json        # 运行摘要（包含所有场景信息）
│   ├── evaluation_log.log      # 主评测日志
│   ├── subtask_execution_log.csv # 所有场景的CSV记录（合并）
│   ├── trajectories/           # 所有轨迹文件
│   │   ├── {scenario_id}_trajectory.json
│   │   └── ... (所有场景的轨迹)
│   ├── logs/                   # 所有执行日志
│   │   ├── {scenario_id}_execution.json
│   │   └── ... (所有场景的执行日志JSON)
│   └── llm_qa/                 # 所有LLM交互记录
│       ├── {scenario_id}_llm_qa.json
│       └── ... (所有场景的LLM记录)
```

**关键特点**：
- **统一父文件夹**：不论单场景还是多场景，都在同一个运行文件夹下
- **简化轨迹文件**：只保留trajectory.json，移除compact版本
- **JSON格式日志**：logs目录保存结构化的执行日志JSON文件
- **Independent模式**：所有子任务的轨迹都保存在同一个运行文件夹中
- **并行实现**：单场景时并行数为1，多场景时根据配置设置并行数
- **文件合并**：CSV文件合并所有场景的记录，便于统一分析

### 2.3 简化核心类设计

#### 2.3.1 EvaluationManager（统一评测管理器）
```python
class EvaluationManager:
    """统一评测管理器 - 所有评测都通过并行框架实现"""

    def __init__(self, config_file: str, agent_type: str, task_type: str,
                 scenario_id: str = None, custom_suffix: str = None):
        """
        Args:
            config_file: 配置文件名（如'single_agent_config'）
            agent_type: 智能体类型（'single'或'multi'）
            task_type: 任务类型（'sequential', 'combined', 'independent'）
            scenario_id: 单场景ID（如果指定，则只评测该场景）
            custom_suffix: 自定义后缀
        """
        self.parallel_count = 1 if scenario_id else self._get_parallel_count()
        self.scenario_list = self._determine_scenarios(scenario_id)

    def run_evaluation(self) -> Dict[str, Any]:
        """统一评测入口 - 使用并行框架（并行数可能为1）"""
        return self._run_parallel_evaluation()

    def _run_parallel_evaluation(self) -> Dict[str, Any]:
        """并行评测实现 - 复用现有并行逻辑"""

    def _execute_single_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """执行单个场景 - 复用现有TaskEvaluator"""
```

#### 2.3.2 ScenarioSelector（场景选择器）
```python
class ScenarioSelector:
    """场景选择器 - 简化实现"""

    @staticmethod
    def get_scenario_list(config: Dict[str, Any], scenario_id: str = None) -> List[str]:
        """
        获取要评测的场景列表

        Args:
            config: 配置文件
            scenario_id: 指定的单场景ID（优先级最高）

        Returns:
            List[str]: 场景ID列表
        """
        if scenario_id:
            return [scenario_id]  # 单场景模式

        # 多场景模式，从配置读取
        scenario_selection = config.get('parallel_evaluation', {}).get('scenario_selection', {})
        mode = scenario_selection.get('mode', 'range')

        if mode == 'all':
            return self._get_all_scenarios()
        elif mode == 'range':
            return self._get_range_scenarios(scenario_selection.get('range', {}))
        elif mode == 'list':
            return scenario_selection.get('list', ['00001'])
```

#### 2.3.3 TrajectoryManager（轨迹管理器）
```python
class TrajectoryManager:
    """轨迹管理器 - 基于现有TrajectoryRecorder，支持多场景统一管理"""

    def __init__(self, output_dir: str, run_name: str):
        """
        Args:
            output_dir: 统一输出目录
            run_name: 运行名称
        """
        self.output_dir = output_dir
        self.run_name = run_name
        self.csv_file = os.path.join(output_dir, "subtask_execution_log.csv")
        self.scenario_recorders = {}  # 各场景的TrajectoryRecorder

    def get_scenario_recorder(self, scenario_id: str) -> TrajectoryRecorder:
        """获取或创建场景专用记录器"""

    def merge_csv_records(self):
        """合并所有场景的CSV记录到统一文件"""

    def generate_run_summary(self) -> Dict[str, Any]:
        """生成运行摘要，包含所有场景的统计信息"""

    def save_execution_log(self, scenario_id: str, execution_data: Dict[str, Any]):
        """保存场景执行日志JSON文件"""
```

### 2.4 输出文件格式详解

#### 2.4.1 轨迹文件格式（按场景保存）
```json
// trajectories/{scenario_id}_trajectory.json - 每个场景一个轨迹文件
[
  // Sequential和Independent模式：多个任务轨迹
  {
    "action_sequence": [
      {
        "action_index": 0,  // 动作编号从0开始
        "action_command": "EXPLORE",
        "execution_status": "SUCCESS",  // SUCCESS, FAILURE, INVALID
        "result_message": "robot_1 thoroughly explored Filter Simulation Station and discovered 11 new objects",
        "agent_id": "agent_1"
      },
      {
        "action_index": 1,
        "action_command": "GRAB oscilloscope_probe_set_1",
        "execution_status": "INVALID",
        "result_message": "Object not discovered: Oscilloscope Probe Set",
        "agent_id": "agent_1"
      },
      // ... 更多动作
      {
        "action_index": 19,
        "action_command": "DONE",  // 模型认为任务完成
        "execution_status": "SUCCESS",
        "result_message": "Task completion declared by agent",
        "agent_id": "agent_1"
      }
    ],
    "subtask_completions": [
      // 模拟器检测到的实际任务完成情况
      {
        "subtask_index": 1,  // 子任务编号从1开始
        "completed_at": 15   // 在第15步完成（步数从1开始）
      }
      // 如果任务未完成，此数组为空
    ]
  },
  {
    "action_sequence": [...],  // 第二个任务的动作序列
    "subtask_completions": []  // 此任务未完成
  }
  // ... 更多任务（Sequential和Independent模式）
]
```

#### 2.4.2 Combined模式的特殊格式
```json
// Combined模式：只有一个大任务轨迹
[
  {
    "action_sequence": [
      // 所有子任务的动作序列合并在一起
      {
        "action_index": 0,
        "action_command": "EXPLORE",
        "execution_status": "SUCCESS",
        "result_message": "...",
        "agent_id": "agent_1"
      },
      // ... 大量动作
      {
        "action_index": 45,
        "action_command": "DONE",
        "execution_status": "SUCCESS",
        "result_message": "All tasks completed",
        "agent_id": "agent_1"
      }
    ],
    "subtask_completions": [
      // 记录各个子任务在哪一步完成
      {
        "subtask_index": 1,
        "completed_at": 7   // 第1个子任务在第7步完成
      },
      {
        "subtask_index": 2,
        "completed_at": 15  // 第2个子任务在第15步完成
      },
      {
        "subtask_index": 3,
        "completed_at": 28  // 第3个子任务在第28步完成
      }
      // 未完成的子任务不会出现在这里
    ]
  }
]
```

#### 2.4.3 LLM QA记录格式（按场景组织）

**Sequential和Independent模式**：
```json
// llm_qa/{scenario_id}_llm_qa.json - 每个场景一个QA文件
[
  {
    "qa_interactions": [
      {
        "interaction_index": 0,
        "timestamp": "2025-01-16T01:21:48.123456",
        "prompt": "You are an intelligent agent...\nCurrent task: Place the oscilloscope probe set...",
        "response": "Thought: I need to explore the environment first to find the oscilloscope probe set.\nAction: EXPLORE",
        "tokens_used": {
          "prompt_tokens": 1250,
          "completion_tokens": 45,
          "total_tokens": 1295
        },
        "response_time_ms": 1250,
        "extracted_action": "EXPLORE"
      }
      // ... 第一个任务的所有交互
    ]
  },
  {
    "qa_interactions": [...]  // 第二个任务的QA记录
  }
  // ... 更多任务的QA记录
]
```

**Combined模式**：
```json
// llm_qa/{scenario_id}_llm_qa.json - Combined模式为一个整体的长QA序列
[
  {
    "qa_interactions": [
      {
        "interaction_index": 0,
        "timestamp": "2025-01-16T01:21:48.123456",
        "prompt": "You are an intelligent agent...\nCombined tasks: 1. Place the oscilloscope... 2. Connect the cable... 3. Measure the signal...",
        "response": "Thought: I need to start with the first task...\nAction: EXPLORE",
        "tokens_used": {
          "prompt_tokens": 2150,
          "completion_tokens": 45,
          "total_tokens": 2195
        },
        "response_time_ms": 1250,
        "extracted_action": "EXPLORE"
      },
      {
        "interaction_index": 1,
        "timestamp": "2025-01-16T01:21:52.456789",
        "prompt": "...",
        "response": "...",
        "tokens_used": {...},
        "response_time_ms": 980,
        "extracted_action": "GRAB oscilloscope_probe_set_1"
      }
      // ... 所有子任务的交互合并在一个长序列中
    ]
  }
]
```

#### 2.4.4 执行日志格式（按场景保存）
```json
// logs/{scenario_id}_execution.json - 每个场景的执行日志（只记录完成情况）
{
  "scenario_id": "00001",
  "evaluation_mode": "independent",
  "start_time": "2025-01-16T01:21:48.123456",
  "end_time": "2025-01-16T01:25:30.654321",
  "total_duration_seconds": 222.53,
  "tasks": [
    {
      "task_index": 1,
      "task_description": "Place the oscilloscope probe set with id 'oscilloscope_probe_set_1' onto the 'rack_mounted_signal_analyzer_1'.",
      "task_category": "direct_command",  // direct_command, tool_use, exploration, attribute_reasoning等
      "status": "completed",  // completed, failed, timeout
      "total_steps": 20,
      "start_time": "2025-01-16T01:21:48.123456",
      "end_time": "2025-01-16T01:22:15.789012",
      "duration_seconds": 27.67,
      "llm_interactions": 5,
      "completion_analysis": {
        "model_claimed_completion": true,   // 模型是否声明完成
        "actually_completed": true,         // 是否实际完成
        "completion_accuracy": "correct",   // correct/premature/missed
        "done_step": 20,                   // DONE命令步数（-1表示未输出DONE）
        "actual_completion_step": 15       // 实际完成步数（-1表示未完成）
      }
    },
    {
      "task_index": 2,
      "task_description": "Connect the analyzer cable to the signal generator.",
      "task_category": "tool_use",
      "status": "failed",
      "total_steps": 15,
      "start_time": "2025-01-16T01:22:16.000000",
      "end_time": "2025-01-16T01:22:35.123456",
      "duration_seconds": 19.12,
      "llm_interactions": 4,
      "completion_analysis": {
        "model_claimed_completion": true,
        "actually_completed": false,
        "completion_accuracy": "premature",
        "done_step": 15,
        "actual_completion_step": -1
      }
    }
    // ... 更多任务
  ]
}
```

#### 2.4.5 运行摘要格式（按任务类型统计）
```json
// run_summary.json - 每次运行的统一摘要（按任务类型分别统计成功率）
{
  "run_info": {
    "run_name": "20250716_012148_single_independent_demo",
    "start_time": "2025-01-16T01:21:48.123456",
    "end_time": "2025-01-16T01:25:30.654321",
    "total_duration": 222.53,
    "evaluation_mode": "independent",
    "agent_type": "single",
    "parallel_count": 2,
    "total_scenarios": 4,
    "scenario_range": "00001-00004"  // 或者 "00001,00003,00005" 或者 "all"
  },
  "task_category_statistics": {
    "direct_command": {
      "total_tasks": 8,
      "completed_tasks": 6,  // 模拟器客观评估的实际完成数
      "completion_rate": 0.75,  // 基于模拟器评估的客观完成率
      "model_claimed_tasks": 7,  // 模型声明完成的任务数
      "completion_accuracy": 0.857  // 模型声明的准确率 (6/7)
    },
    "tool_use": {
      "total_tasks": 6,
      "completed_tasks": 4,  // 模拟器客观评估
      "completion_rate": 0.667,  // 客观完成率
      "model_claimed_tasks": 5,
      "completion_accuracy": 0.8  // 模型准确率 (4/5)
    },
    "exploration": {
      "total_tasks": 4,
      "completed_tasks": 3,  // 模拟器客观评估
      "completion_rate": 0.75,  // 客观完成率
      "model_claimed_tasks": 4,
      "completion_accuracy": 0.75  // 模型准确率 (3/4)
    },
    "attribute_reasoning": {
      "total_tasks": 2,
      "completed_tasks": 2,  // 模拟器客观评估
      "completion_rate": 1.0,  // 客观完成率
      "model_claimed_tasks": 2,
      "completion_accuracy": 1.0  // 模型准确率 (2/2)
    }
  },
  "overall_summary": {
    "total_scenarios": 4,
    "total_tasks": 20,
    "total_completed_tasks": 15,  // 模拟器客观评估的实际完成数
    "overall_completion_rate": 0.75,  // 客观完成率 (15/20)
    "total_model_claimed_tasks": 18,  // 模型声明完成的任务数
    "overall_completion_accuracy": 0.833,  // 模型声明准确率 (15/18)
    "average_duration_per_scenario": 55.6,
    "parallel_efficiency": 1.85,
    "total_llm_interactions": 88,
    "average_interactions_per_task": 4.4
  }
}
```

#### 2.4.6 CSV合并格式（所有场景统一）
```csv
timestamp,scenario_id,task_index,task_description,task_category,agent_type,status,task_executed,subtask_completed,model_claimed_done,actual_completion_step,done_command_step,total_steps,successful_steps,failed_steps,command_success_rate,start_time,end_time,duration_seconds,llm_interactions
2025-01-16T01:21:48,00001,1,Place oscilloscope probe set with id 'oscilloscope_probe_set_1' onto the 'rack_mounted_signal_analyzer_1',direct_command,single_agent,completed,True,True,True,15,20,20,18,2,90.00%,2025-01-16T01:21:48,2025-01-16T01:22:15,27.67,5
2025-01-16T01:22:16,00001,2,Connect the analyzer cable to the signal generator,tool_use,single_agent,failed,True,False,True,-1,15,15,12,3,80.00%,2025-01-16T01:22:16,2025-01-16T01:22:35,19.12,4
2025-01-16T01:23:01,00002,1,Explore the laboratory environment,exploration,single_agent,completed,True,True,False,-1,-1,25,20,5,80.00%,2025-01-16T01:23:01,2025-01-16T01:23:45,44.23,8
```

**关键字段说明**：
- `task_index`: 任务编号（从1开始）
- `task_executed`: 任务是否执行完成（达到最大步数或DONE）
- `subtask_completed`: 模拟器客观评估的实际完成状态（以此为准计算完成率）
- `model_claimed_done`: 模型是否输出了DONE命令
- `actual_completion_step`: 模拟器检测到实际完成的步数（-1表示未完成）
- `done_command_step`: DONE命令的步数（-1表示未输出DONE）

**完成率计算说明**：
- 任务完成率以模拟器的客观评估为准（`subtask_completed`字段）
- 模拟器会根据任务目标和当前环境状态判断任务是否真正完成
- 模型的DONE声明只是模型的主观判断，不作为完成率计算依据

## 3. 统一并行实现策略

### 3.1 并行框架统一
- **核心思想**：所有评测都使用并行框架，单场景时并行数为1
- **实现方式**：基于现有的并行评测逻辑，统一处理单场景和多场景
- **配置驱动**：通过配置文件的`parallel_evaluation.max_parallel_scenarios`控制并行数

### 3.2 以场景为单位的并行执行框架
```python
# 以场景为单位的并行执行流程
def run_evaluation():
    scenarios = determine_scenarios()  # 获取要评测的场景列表
    parallel_count = min(len(scenarios), config.max_parallel_scenarios)

    # 以场景为单位并行执行，而不是任务为单位
    with ProcessPoolExecutor(max_workers=parallel_count) as executor:
        # 每个worker处理一个完整的场景（包含该场景的所有任务）
        future_to_scenario = {
            executor.submit(execute_complete_scenario, scenario_id): scenario_id
            for scenario_id in scenarios
        }

        scenario_results = {}
        for future in as_completed(future_to_scenario):
            scenario_id = future_to_scenario[future]
            try:
                scenario_results[scenario_id] = future.result()
            except Exception as exc:
                logger.error(f'场景 {scenario_id} 执行失败: {exc}')
                scenario_results[scenario_id] = {'status': 'failed', 'error': str(exc)}

    # 统一结果处理和文件组织
    return aggregate_results(scenario_results)

def execute_complete_scenario(scenario_id: str) -> Dict[str, Any]:
    """
    执行完整场景（包含该场景的所有任务）
    - 一个场景的所有任务在同一个进程中顺序执行
    - 避免任务级别的并行，确保场景内任务的连续性
    """
    scenario_executor = ScenarioExecutor(scenario_id)
    return scenario_executor.execute_all_tasks()
```

**并行粒度说明**：
- **场景级并行**：多个场景可以并行执行
- **任务级顺序**：同一场景内的任务顺序执行，保持历史连续性
- **资源隔离**：每个场景在独立的进程中执行，避免相互干扰

### 3.3 任务完成状态跟踪
- **DONE命令检测**：监控模型输出的DONE命令及其步数
- **模拟器状态检测**：实时从模拟器获取任务实际完成状态
- **完成准确性分析**：比较模型声明与实际完成的差异
- **实时记录**：每个动作后立即更新完成状态到轨迹文件

### 3.4 Independent模式特殊处理
- **子任务轨迹**：Independent模式的所有子任务轨迹都保存在同一个运行文件夹中
- **轨迹聚合**：使用现有的IndependentTaskExecutor聚合机制
- **统一输出**：最终聚合到场景级别的轨迹文件中

### 3.5 实时数据保存策略

#### 3.5.1 实时保存策略

**立即写入磁盘**：
- **轨迹文件**：每个动作执行后立即保存到`trajectories/{scenario_id}_trajectory.json`
- **CSV记录**：每个子任务完成后立即追加到`subtask_execution_log.csv`
- **QA记录**：每次LLM交互后立即保存到`llm_qa/{scenario_id}_llm_qa.json`
- **执行日志**：每个任务完成后立即更新`logs/{scenario_id}_execution.json`
- **运行摘要**：程序结束时或中断时保存`run_summary.json`

**数据安全优先**：
- **无缓冲机制**：不使用内存缓冲，每次操作都直接写入磁盘
- **立即刷新**：每次写入后立即调用flush()确保数据写入磁盘
- **原子操作**：使用临时文件+重命名确保写入的原子性
- **中断保护**：程序中断时数据已经保存，无需额外处理

**Independent模式处理**：
- **子任务轨迹**：每个子任务执行完成后立即保存到场景轨迹文件
- **实时追加**：不等待所有子任务完成，边执行边保存
- **增量更新**：场景轨迹文件采用增量追加方式，确保数据不丢失

#### 3.5.2 中断保护机制
```python
# 信号处理器确保中断时保存数据
def signal_handler(signum, frame):
    logger.info("🛑 接收到中断信号，正在保存数据...")

    # 立即保存所有场景的轨迹文件
    for scenario_id, recorder in scenario_recorders.items():
        recorder.save_trajectory_immediately()
        recorder.save_qa_immediately()
        recorder.save_execution_log_immediately()

    # 保存CSV文件（如果有缓存数据）
    flush_csv_buffer()

    # 生成并保存运行摘要
    generate_and_save_run_summary()

    logger.info("✅ 数据保存完成，程序退出")
    sys.exit(0)

# 注册信号处理器
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```

#### 3.5.3 并发保护机制
- **CSV文件锁**：多场景并行时使用文件锁保护CSV写入
- **场景独立**：各场景的轨迹、QA、执行日志文件独立保存，无需锁定
- **原子操作**：使用临时文件+重命名确保文件写入的原子性

```python
# CSV写入的文件锁保护
import fcntl

def append_to_csv_with_lock(csv_file, row_data):
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # 排他锁
        try:
            writer = csv.writer(f)
            writer.writerow(row_data)
            f.flush()  # 立即刷新到磁盘
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # 释放锁
```

#### 3.5.4 实时写入机制
```python
class TrajectoryManager:
    """轨迹管理器 - 每次操作都立即写入磁盘"""

    def __init__(self, scenario_id: str, output_dir: str):
        self.scenario_id = scenario_id
        self.trajectory_file = os.path.join(output_dir, f"trajectories/{scenario_id}_trajectory.json")
        self.qa_file = os.path.join(output_dir, f"llm_qa/{scenario_id}_llm_qa.json")
        self.execution_log_file = os.path.join(output_dir, f"logs/{scenario_id}_execution.json")
        self.lock = threading.Lock()

        # 确保目录存在
        os.makedirs(os.path.dirname(self.trajectory_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.qa_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.execution_log_file), exist_ok=True)

    def append_action(self, action_data: Dict):
        """添加动作并立即写入磁盘"""
        with self.lock:
            # 读取现有轨迹数据
            trajectory_data = self.load_trajectory_data()

            # 追加新动作
            if not trajectory_data:
                trajectory_data = [{"action_sequence": [], "subtask_completions": []}]

            trajectory_data[-1]["action_sequence"].append(action_data)

            # 立即写入磁盘
            self.save_trajectory_immediately(trajectory_data)

    def update_subtask_completion(self, subtask_index: int, completed_at: int):
        """更新子任务完成状态并立即写入磁盘"""
        with self.lock:
            trajectory_data = self.load_trajectory_data()

            if trajectory_data:
                # 更新最后一个任务的完成状态
                trajectory_data[-1]["subtask_completions"].append({
                    "subtask_index": subtask_index,
                    "completed_at": completed_at
                })

                # 立即写入磁盘
                self.save_trajectory_immediately(trajectory_data)

    def append_qa_interaction(self, qa_data: Dict):
        """添加QA交互并立即写入磁盘"""
        with self.lock:
            # 读取现有QA数据
            qa_data_list = self.load_qa_data()

            # 追加新交互
            if not qa_data_list:
                qa_data_list = [{"qa_interactions": []}]

            qa_data_list[-1]["qa_interactions"].append(qa_data)

            # 立即写入磁盘
            self.save_qa_immediately(qa_data_list)

    def save_trajectory_immediately(self, trajectory_data: List[Dict]):
        """立即保存轨迹数据到磁盘"""
        temp_file = self.trajectory_file + '.tmp'
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(trajectory_data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())  # 强制写入磁盘

            # 原子性重命名
            os.rename(temp_file, self.trajectory_file)
        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise e

    def save_qa_immediately(self, qa_data: List[Dict]):
        """立即保存QA数据到磁盘"""
        temp_file = self.qa_file + '.tmp'
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(qa_data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())  # 强制写入磁盘

            # 原子性重命名
            os.rename(temp_file, self.qa_file)
        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise e

    def load_trajectory_data(self) -> List[Dict]:
        """加载现有轨迹数据"""
        if os.path.exists(self.trajectory_file):
            with open(self.trajectory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def load_qa_data(self) -> List[Dict]:
        """加载现有QA数据"""
        if os.path.exists(self.qa_file):
            with open(self.qa_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
```

#### 3.5.5 原子文件写入
```python
# 确保文件写入的原子性
def save_json_atomically(file_path, data):
    temp_file = file_path + '.tmp'
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())  # 强制写入磁盘

        # 原子性重命名
        os.rename(temp_file, file_path)
    except Exception as e:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise e
```

## 4. 轨迹格式和任务完成机制

### 4.1 轨迹文件组织原则
- **按场景保存**：每个场景生成独立的轨迹文件（trajectory.json, compact_trajectory.json）
- **QA按场景组织**：每个场景生成独立的LLM QA文件（{scenario_id}_llm_qa.json）
- **统一CSV合并**：所有场景的CSV记录合并到一个文件中
- **实时保存**：每个动作执行后立即保存，确保数据不丢失

### 4.2 任务编号和步数规则
- **任务编号**：从1开始（task_index: 1, 2, 3, ...）
- **动作编号**：从0开始（action_index: 0, 1, 2, ...）
- **步数计算**：从1开始（completed_at: 1, 2, 3, ...）
- **子任务编号**：从1开始（subtask_index: 1, 2, 3, ...）

### 4.3 DONE命令与任务完成的区分
```python
# 处理DONE命令的逻辑
def handle_done_command(action_step):
    # 1. 记录模型的DONE声明
    record_model_completion_claim(action_step)

    # 2. 从模拟器获取实际完成状态
    actual_completion = simulator.check_task_completion()

    # 3. 更新轨迹记录
    update_trajectory_with_completion_analysis(
        model_claimed=True,
        actually_completed=actual_completion,
        done_step=action_step,
        actual_completion_step=get_actual_completion_step()
    )

    # 4. 实时保存到CSV
    save_to_csv_immediately()
```

### 4.4 不同评测模式的轨迹差异

- **Sequential模式**：
  - 轨迹包含多个任务的执行记录
  - 每个任务有独立的`action_sequence`和`subtask_completions`
  - **子任务间不清空历史**，场景间清空历史
  - 智能体可以利用前面子任务的执行经验

- **Combined模式**：
  - 轨迹只有一个大任务的执行记录
  - 所有子任务的动作合并在一个`action_sequence`中
  - `subtask_completions`记录各子任务在哪一步完成
  - 所有子任务在同一个连续的对话中执行

- **Independent模式**：
  - 轨迹包含多个任务的执行记录（类似Sequential）
  - 但每个任务在完全独立的环境实例中执行
  - 每个子任务都是全新开始，无法利用前面的经验
  - 最终聚合所有子任务结果到场景级别文件

### 4.5 实时状态跟踪机制
```python
# 实时跟踪任务完成状态
class TaskCompletionTracker:
    def __init__(self):
        self.completion_states = {}
        self.done_commands = {}

    def track_action(self, action, step_number):
        # 检查是否为DONE命令
        if action.command == "DONE":
            self.done_commands[current_task] = step_number

        # 从模拟器检查实际完成状态
        completion_status = simulator.check_subtask_completion()
        if completion_status.newly_completed:
            self.completion_states[completion_status.subtask_index] = step_number

        # 立即更新轨迹文件
        self.update_trajectory_immediately()
```

## 5. 重新实现策略

### 5.1 废弃现有组件，重新实现
- **废弃TaskEvaluator**：参考现有实现但重新编写，避免直接使用
- **废弃IndependentTaskExecutor**：重新实现Independent模式的聚合机制
- **废弃现有TrajectoryRecorder**：基于其思路重新实现TrajectoryManager
- **保留配置系统**：继续使用现有的ConfigManager和配置文件格式

### 5.2 新实现的核心组件

#### 5.2.1 新的任务执行器
```python
class TaskExecutor:
    """新的任务执行器 - 替代原有TaskEvaluator"""

    def __init__(self, config_file: str, agent_type: str, task_type: str):
        """初始化执行器"""

    def execute_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """执行单个场景的评测"""

    def execute_sequential_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """执行Sequential模式任务"""

    def execute_combined_tasks(self, tasks: List[Dict]) -> Dict:
        """执行Combined模式任务"""

    def execute_independent_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """执行Independent模式任务（新实现）"""
```

#### 5.2.2 新的Independent模式实现
```python
class IndependentModeExecutor:
    """Independent模式执行器 - 在evaluation目录重新实现"""

    def __init__(self, config_file: str, agent_type: str, scenario_id: str):
        """
        初始化Independent模式执行器
        - 如需参考原IndependentTaskExecutor，在当前evaluation目录重新实现
        - 不直接引用utils/independent_task_executor.py
        """
        self.config_file = config_file
        self.agent_type = agent_type
        self.scenario_id = scenario_id
        self.trajectory_manager = TrajectoryManager(...)

    def execute_independent_evaluation(self, tasks: List[Dict]) -> Dict:
        """
        执行Independent评测
        - 每个子任务在完全独立的环境中执行
        - 实时保存每个子任务的轨迹，不等到最终汇总
        """
        subtask_results = []

        for i, task in enumerate(tasks):
            # 为每个子任务创建独立的执行环境
            subtask_result = self.execute_single_subtask(task, i + 1)

            # 立即保存子任务轨迹到场景文件
            self.save_subtask_trajectory_immediately(subtask_result, i + 1)

            subtask_results.append(subtask_result)

        # 聚合所有子任务结果
        return self.aggregate_subtask_results(subtask_results)

    def execute_single_subtask(self, subtask: Dict, subtask_index: int) -> Dict:
        """
        执行单个子任务
        - 创建全新的TaskExecutor实例
        - 完全独立的环境和智能体状态
        """

    def save_subtask_trajectory_immediately(self, subtask_result: Dict, subtask_index: int):
        """
        立即保存子任务轨迹
        - 不等到所有子任务完成
        - 实时追加到场景轨迹文件
        """

    def aggregate_subtask_results(self, subtask_results: List[Dict]) -> Dict:
        """聚合子任务结果到场景级别"""
```

### 5.3 确认的设计要求

#### ✅ **已确认的要求**
1. **轨迹格式简化**：只保存action_sequence和subtask_completions
2. **执行日志JSON**：logs目录保存结构化的任务执行信息
3. **统一并行实现**：所有评测都使用并行框架
4. **实时保存策略**：所有文件都及时保存，支持中断保护
5. **Combined模式QA**：QA记录与轨迹逻辑一致，为一个整体长序列
6. **run_summary格式**：按任务类型统计成功率，不保存逐场景信息
7. **重新实现**：废弃现有组件，参考但不直接使用

### 5.4 任务完成评估机制

#### 5.4.1 完成状态的权威来源
- **模拟器评估**：任务完成的唯一权威标准
- **客观判断**：基于任务目标和环境状态的客观评估
- **实时检测**：每个动作执行后立即检查完成状态

#### 5.4.2 Sequential模式的历史管理
- **子任务间保持历史**：在同一场景内，子任务间不清空对话历史
- **场景间清空历史**：不同场景之间完全独立，清空所有历史
- **经验利用**：智能体可以利用前面子任务的执行经验来完成后续子任务

#### 5.4.3 完成率计算逻辑
```python
def calculate_completion_rates(task_results):
    """计算任务完成率 - 以模拟器评估为准"""

    category_stats = defaultdict(lambda: {'total': 0, 'completed': 0, 'claimed': 0})

    for task in task_results:
        category = task['task_category']
        category_stats[category]['total'] += 1

        # 以模拟器的客观评估为准
        if task['simulator_completion_status']:  # 模拟器判断是否完成
            category_stats[category]['completed'] += 1

        # 记录模型声明情况（用于准确率分析）
        if task['model_claimed_done']:
            category_stats[category]['claimed'] += 1

    # 计算完成率和准确率
    for category in category_stats:
        stats = category_stats[category]
        stats['completion_rate'] = stats['completed'] / stats['total']
        if stats['claimed'] > 0:
            stats['completion_accuracy'] = stats['completed'] / stats['claimed']
        else:
            stats['completion_accuracy'] = 0.0

    return category_stats
```

### 5.5 并发保护机制设计

#### 5.5.1 需要保护的资源
- **CSV文件**：多场景并行写入时需要文件锁保护
- **运行摘要**：多场景完成时需要同步更新统计信息
- **日志文件**：主评测日志需要线程安全写入

#### 5.5.2 不需要保护的资源
- **轨迹文件**：各场景独立文件，无并发冲突
- **QA文件**：各场景独立文件，无并发冲突
- **执行日志JSON**：各场景独立文件，无并发冲突

#### 5.5.3 高效的并发保护策略
```python
# 1. 实时CSV写入器
class CSVWriter:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.lock = threading.Lock()

        # 确保目录存在
        os.makedirs(os.path.dirname(csv_file), exist_ok=True)

    def append_row(self, row_data):
        """立即写入CSV数据到磁盘"""
        with self.lock:
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row_data)
                f.flush()  # 立即刷新到磁盘
                os.fsync(f.fileno())  # 强制写入磁盘

# 2. 场景级并行管理器
class ScenarioParallelManager:
    """场景级并行执行管理器"""

    def __init__(self, max_parallel_scenarios: int):
        self.max_parallel_scenarios = max_parallel_scenarios
        self.scenario_stats = {}
        self.stats_lock = threading.Lock()

    def execute_scenarios_parallel(self, scenarios: List[str]) -> Dict[str, Any]:
        """以场景为单位并行执行"""
        parallel_count = min(len(scenarios), self.max_parallel_scenarios)

        with ProcessPoolExecutor(max_workers=parallel_count) as executor:
            # 每个worker处理一个完整场景
            future_to_scenario = {
                executor.submit(self.execute_single_scenario, scenario_id): scenario_id
                for scenario_id in scenarios
            }

            results = {}
            for future in as_completed(future_to_scenario):
                scenario_id = future_to_scenario[future]
                try:
                    results[scenario_id] = future.result()
                    logger.info(f"✅ 场景 {scenario_id} 执行完成")
                except Exception as exc:
                    logger.error(f"❌ 场景 {scenario_id} 执行失败: {exc}")
                    results[scenario_id] = {'status': 'failed', 'error': str(exc)}

        return results

    def execute_single_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """执行单个场景的所有任务"""
        # 在同一个进程中顺序执行该场景的所有任务
        # 保持任务间的历史连续性
        scenario_executor = ScenarioTaskExecutor(scenario_id)
        return scenario_executor.run_all_tasks()

# 3. 运行摘要的实时更新
class RunSummaryManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.task_stats = defaultdict(lambda: {'total': 0, 'completed': 0, 'claimed': 0})

    def update_task_stats(self, task_category, simulator_completed, model_claimed):
        """立即更新任务统计"""
        with self.lock:
            self.task_stats[task_category]['total'] += 1
            if simulator_completed:  # 以模拟器评估为准
                self.task_stats[task_category]['completed'] += 1
            if model_claimed:
                self.task_stats[task_category]['claimed'] += 1
```

### 5.3 实时保存策略确认
**问题5**: 数据保存时机：
- 每个动作执行后立即保存轨迹文件
- 每个子任务完成后立即保存CSV记录
- 每次LLM交互后立即保存QA记录
- 是否需要调整保存频率？

**问题6**: 文件锁和并发处理：
- 多场景并行时使用文件锁保护CSV写入
- 各场景的轨迹文件独立保存，无需锁定
- 是否需要其他并发保护机制？

### 5.4 代码架构确认
**问题7**: 简化架构的合理性：
- 4个核心文件的架构是否足够简洁
- 是否需要进一步简化或适当增加模块
- 代码复用策略是否合适？

**问题8**: 兼容性保证：
- 保持与现有TaskEvaluator的完全兼容
- 保持现有配置文件格式不变
- 保持命令行接口不变
- 是否有其他兼容性要求？

### 5.5 功能增强确认
**问题9**: 任务完成分析功能：
- 增加完成准确性分析
- 区分模型声明和实际完成
- 提供更详细的统计信息
- 是否需要其他分析功能？

**问题10**: 测试验证要求：
- 确保所有评测模式的轨迹格式正确
- 验证DONE命令和实际完成的正确区分
- 测试并行保存的数据一致性
- 是否有其他特定测试要求？

## 5. 简化实现计划

### 阶段1：核心文件创建（1-2天）
1. **evaluation_manager.py**：统一评测管理器
   - 集成现有TaskEvaluator功能
   - 实现统一的并行框架调用
   - 处理单场景和多场景的统一逻辑

2. **scenario_selector.py**：场景选择器
   - 实现all/range/list三种选择模式
   - 处理单场景和多场景的场景列表生成

3. **trajectory_manager.py**：轨迹管理器
   - 基于现有TrajectoryRecorder
   - 支持多场景的统一文件管理
   - 实现简化轨迹格式和执行日志JSON生成
   - 实现CSV合并和运行摘要生成
   - 支持Independent模式的实时轨迹保存

4. **independent_executor.py**：Independent模式执行器
   - 在evaluation目录重新实现（不直接引用utils中的代码）
   - 可参考原IndependentTaskExecutor的思路
   - 实现实时轨迹保存，不等待最终汇总

5. **evaluator.py**：重构主入口
   - 简化命令行处理逻辑
   - 统一调用EvaluationManager

### 阶段2：功能集成和测试（2-3天）
1. **功能验证**：
   - 测试所有评测模式（sequential、combined、independent）
   - 测试单场景和多场景评测
   - 验证输出格式和文件组织

2. **兼容性测试**：
   - 确保与现有配置文件兼容
   - 验证命令行接口不变
   - 检查输出结果与现有系统一致

3. **性能测试**：
   - 测试并行效率
   - 验证实时保存功能
   - 检查内存使用情况

### 阶段3：文档和优化（1天）
1. **代码优化**：清理和注释
2. **使用文档**：更新使用说明
3. **示例验证**：确保所有示例正常工作

## 6. 预期效果

### 6.1 代码简化
- **文件数量**：从当前的复杂结构简化为4个核心文件
- **代码复用**：最大化复用现有组件，减少重复代码
- **维护性**：清晰的模块划分，便于后续维护

### 6.2 功能统一
- **并行框架**：所有评测都使用统一的并行实现
- **输出格式**：统一的输出目录结构和文件组织
- **用户体验**：保持现有的使用方式，无需学习成本

### 6.3 扩展性
- **新模式添加**：可以轻松添加新的评测模式
- **配置扩展**：支持新的配置选项和场景选择方式
- **记录增强**：可以方便地增加新的记录功能

## 7. Baseline使用接口设计

### 7.1 统一评测接口
```python
# evaluation/evaluation_interface.py
class EvaluationInterface:
    """为baseline提供的统一评测接口"""

    @staticmethod
    def run_evaluation(config_file: str, agent_type: str, task_type: str,
                      scenario_selection: Dict[str, Any] = None,
                      custom_suffix: str = None) -> Dict[str, Any]:
        """
        统一评测入口

        Args:
            config_file: 配置文件名 ('single_agent_config', 'centralized_config', 'decentralized_config')
            agent_type: 智能体类型 ('single', 'multi')
            task_type: 任务类型 ('sequential', 'combined', 'independent')
            scenario_selection: 场景选择配置
                {
                    'mode': 'range',  # 'all', 'range', 'list'
                    'range': {'start': '00001', 'end': '00010'},
                    'list': ['00001', '00003', '00005']
                }
            custom_suffix: 自定义后缀

        Returns:
            Dict: 评测结果摘要
        """
        from .evaluation_manager import EvaluationManager

        manager = EvaluationManager(
            config_file=config_file,
            agent_type=agent_type,
            task_type=task_type,
            scenario_selection=scenario_selection,
            custom_suffix=custom_suffix
        )

        return manager.run_evaluation()
```

### 7.2 Baseline使用示例

#### 7.2.1 单智能体baseline使用
```python
# baseline/single_agent_baseline.py
from evaluation.evaluation_interface import EvaluationInterface

def run_single_agent_evaluation():
    """单智能体baseline评测示例"""

    # Sequential模式评测
    sequential_results = EvaluationInterface.run_evaluation(
        config_file='single_agent_config',
        agent_type='single',
        task_type='sequential',
        scenario_selection={
            'mode': 'range',
            'range': {'start': '00001', 'end': '00010'}
        },
        custom_suffix='baseline_test'
    )

    # Combined模式评测
    combined_results = EvaluationInterface.run_evaluation(
        config_file='single_agent_config',
        agent_type='single',
        task_type='combined',
        scenario_selection={
            'mode': 'list',
            'list': ['00001', '00003', '00005', '00007', '00009']
        },
        custom_suffix='combined_baseline'
    )

    # Independent模式评测
    independent_results = EvaluationInterface.run_evaluation(
        config_file='single_agent_config',
        agent_type='single',
        task_type='independent',
        scenario_selection={'mode': 'all'},
        custom_suffix='independent_baseline'
    )

    return {
        'sequential': sequential_results,
        'combined': combined_results,
        'independent': independent_results
    }

if __name__ == '__main__':
    results = run_single_agent_evaluation()
    print("🎉 单智能体baseline评测完成!")
    for mode, result in results.items():
        completion_rate = result['overall_summary']['overall_completion_rate']
        print(f"📊 {mode}模式完成率: {completion_rate:.2%}")
```

#### 7.2.2 多智能体baseline使用
```python
# baseline/multi_agent_baseline.py
from evaluation.evaluation_interface import EvaluationInterface

def run_centralized_evaluation():
    """中心化多智能体baseline评测"""
    return EvaluationInterface.run_evaluation(
        config_file='centralized_config',
        agent_type='multi',
        task_type='sequential',
        scenario_selection={
            'mode': 'range',
            'range': {'start': '00001', 'end': '00020'}
        },
        custom_suffix='centralized_baseline'
    )

def run_decentralized_evaluation():
    """去中心化多智能体baseline评测"""
    return EvaluationInterface.run_evaluation(
        config_file='decentralized_config',
        agent_type='multi',
        task_type='independent',
        scenario_selection={'mode': 'all'},
        custom_suffix='decentralized_baseline'
    )

if __name__ == '__main__':
    print("🚀 运行中心化多智能体评测...")
    centralized_results = run_centralized_evaluation()

    print("🚀 运行去中心化多智能体评测...")
    decentralized_results = run_decentralized_evaluation()

    print("🎉 多智能体baseline评测完成!")
    print(f"📊 中心化完成率: {centralized_results['overall_summary']['overall_completion_rate']:.2%}")
    print(f"📊 去中心化完成率: {decentralized_results['overall_summary']['overall_completion_rate']:.2%}")
```

#### 7.2.3 简化的命令行接口
```python
# baseline/run_baseline.py
import argparse
from evaluation.evaluation_interface import EvaluationInterface

def main():
    parser = argparse.ArgumentParser(description='Baseline评测工具')
    parser.add_argument('--config', required=True,
                       choices=['single_agent_config', 'centralized_config', 'decentralized_config'],
                       help='配置文件名')
    parser.add_argument('--agent-type', required=True,
                       choices=['single', 'multi'],
                       help='智能体类型')
    parser.add_argument('--task-type', required=True,
                       choices=['sequential', 'combined', 'independent'],
                       help='任务类型')
    parser.add_argument('--scenarios', default='all',
                       help='场景选择: all, 00001-00010, 00001,00003,00005')
    parser.add_argument('--suffix', default='baseline',
                       help='自定义后缀')

    args = parser.parse_args()

    # 解析场景选择
    scenario_selection = parse_scenario_selection(args.scenarios)

    # 运行评测
    results = EvaluationInterface.run_evaluation(
        config_file=args.config,
        agent_type=args.agent_type,
        task_type=args.task_type,
        scenario_selection=scenario_selection,
        custom_suffix=args.suffix
    )

    print("🎉 评测完成!")
    print(f"📊 总体完成率: {results['overall_summary']['overall_completion_rate']:.2%}")
    print(f"📁 结果保存在: output/{results['run_info']['run_name']}/")

def parse_scenario_selection(scenarios_str):
    """解析场景选择字符串"""
    if scenarios_str == 'all':
        return {'mode': 'all'}
    elif '-' in scenarios_str:
        start, end = scenarios_str.split('-')
        return {
            'mode': 'range',
            'range': {'start': start, 'end': end}
        }
    elif ',' in scenarios_str:
        scenario_list = scenarios_str.split(',')
        return {
            'mode': 'list',
            'list': scenario_list
        }
    else:
        return {
            'mode': 'list',
            'list': [scenarios_str]
        }

if __name__ == '__main__':
    main()
```

### 7.3 使用示例命令
```bash
# 单智能体Sequential模式评测
python baseline/run_baseline.py --config single_agent_config --agent-type single --task-type sequential --scenarios 00001-00010 --suffix test1

# 多智能体Independent模式评测
python baseline/run_baseline.py --config decentralized_config --agent-type multi --task-type independent --scenarios all --suffix experiment1

# 特定场景列表评测
python baseline/run_baseline.py --config centralized_config --agent-type multi --task-type combined --scenarios 00001,00005,00010 --suffix selected_scenes

# 单个场景快速测试
python baseline/run_baseline.py --config single_agent_config --agent-type single --task-type sequential --scenarios 00001 --suffix quick_test
```

### 7.4 批量对比评测
```python
# baseline/comparison_runner.py
from evaluation.evaluation_interface import EvaluationInterface
import json
from datetime import datetime

def run_baseline_comparison():
    """运行所有baseline的对比评测"""

    # 定义评测配置
    evaluation_configs = [
        {
            'name': 'single_sequential',
            'config_file': 'single_agent_config',
            'agent_type': 'single',
            'task_type': 'sequential'
        },
        {
            'name': 'single_combined',
            'config_file': 'single_agent_config',
            'agent_type': 'single',
            'task_type': 'combined'
        },
        {
            'name': 'single_independent',
            'config_file': 'single_agent_config',
            'agent_type': 'single',
            'task_type': 'independent'
        },
        {
            'name': 'multi_centralized',
            'config_file': 'centralized_config',
            'agent_type': 'multi',
            'task_type': 'sequential'
        },
        {
            'name': 'multi_decentralized',
            'config_file': 'decentralized_config',
            'agent_type': 'multi',
            'task_type': 'independent'
        }
    ]

    # 统一场景选择
    scenario_selection = {
        'mode': 'range',
        'range': {'start': '00001', 'end': '00010'}
    }

    # 运行所有评测
    comparison_results = {}
    for config in evaluation_configs:
        print(f"🚀 运行 {config['name']} 评测...")

        result = EvaluationInterface.run_evaluation(
            config_file=config['config_file'],
            agent_type=config['agent_type'],
            task_type=config['task_type'],
            scenario_selection=scenario_selection,
            custom_suffix=f"comparison_{config['name']}"
        )

        comparison_results[config['name']] = result
        print(f"✅ {config['name']} 评测完成")

    # 保存对比结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    comparison_file = f"output/baseline_comparison_{timestamp}.json"

    with open(comparison_file, 'w', encoding='utf-8') as f:
        json.dump(comparison_results, f, ensure_ascii=False, indent=2)

    print(f"📊 对比结果已保存到: {comparison_file}")
    return comparison_results

if __name__ == '__main__':
    results = run_baseline_comparison()

    # 打印对比摘要
    print("\n📊 Baseline对比摘要:")
    print("-" * 60)
    for name, result in results.items():
        completion_rate = result['overall_summary']['overall_completion_rate']
        accuracy = result['overall_summary']['overall_completion_accuracy']
        print(f"{name:20} | 完成率: {completion_rate:6.2%} | 准确率: {accuracy:6.2%}")
```

这个设计为baseline提供了非常方便的使用接口，包括：

## 🎯 **核心特性**

### 1. **统一接口**
- 一个`EvaluationInterface.run_evaluation()`方法搞定所有评测
- 支持所有配置文件和评测模式
- 灵活的场景选择配置

### 2. **丰富示例**
- 单智能体baseline使用示例
- 多智能体baseline使用示例
- 命令行工具
- 批量对比评测

### 3. **易于集成**
- 一行代码启动评测
- 标准化的返回结果格式
- 详细的使用文档和命令示例

### 4. **灵活配置**
- 支持all/range/list三种场景选择模式
- 自定义后缀标识不同实验
- 完整的命令行参数支持