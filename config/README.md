# 配置系统使用指南

## 概述

本项目采用了全新的分层配置系统，支持配置继承、环境变量替换、命令行参数覆盖等高级功能。

## 配置文件结构

```
config/
├── baseline/                    # 基础配置
│   ├── base_config.yaml        # 系统默认配置
│   ├── llm_config.yaml         # LLM配置
│   ├── single_agent_config.yaml # 单智能体配置
│   ├── centralized_config.yaml # 中心化智能体配置
│   └── prompts_config.yaml     # 提示词配置
├── simulator/                  # 模拟器配置
│   └── simulator_config.yaml
└── data_generation/            # 数据生成配置
    ├── task_gen_config.yaml
    └── ...
```

## 核心特性

### 1. 配置继承

通过 `extends` 关键字实现配置继承：

```yaml
# single_agent_config.yaml
extends: "base_config"

# 智能体特定配置
agent_config:
  agent_class: "modes.single_agent.llm_agent.LLMAgent"
  max_failures: 3
```

### 2. 环境变量支持

使用 `${VAR_NAME}` 语法（环境变量必须存在，否则报错）：

```yaml
api:
  custom:
    api_key: "${CUSTOM_LLM_API_KEY}"
    endpoint: "${CUSTOM_LLM_ENDPOINT}"
```

### 3. 命令行参数覆盖

支持通过命令行参数覆盖配置文件中的任何值：

```bash
# 修改LLM模型和参数
python examples/centralized_agent_example.py \
    --llm-provider custom \
    --llm-model deepseek-coder \
    --llm-temperature 0.15

# 修改执行参数
python examples/centralized_agent_example.py \
    --max-total-steps 600 \
    --max-steps-per-task 50

# 使用通用覆盖语法
python examples/centralized_agent_example.py \
    --config-override "api.custom.temperature=0.2" \
    --config-override "execution.max_total_steps=500"
```

## 使用方法

### 基本使用

```python
from config.config_manager import get_config_manager
from config.config_utils import (
    get_llm_config, get_agent_config,
    get_data_dir, get_scene_dir, get_task_dir,
    list_available_datasets, get_default_dataset
)

# 获取配置管理器
config_manager = get_config_manager()

# 加载配置
llm_config = get_llm_config()
agent_config = get_agent_config('single_agent')

# 获取特定配置值（配置项必须存在，否则抛出KeyError）
model_name = config_manager.get_config_section('llm_config', 'api.custom.model')

# 获取数据集目录
source_dir = get_data_dir('base_config', 'source')  # 源数据集目录
eval_dir = get_data_dir('base_config', 'eval_single')  # 单智能体评测数据集
sft_dir = get_data_dir('base_config', 'sft_multi')  # 多智能体SFT训练数据集

# 获取特定数据集的场景和任务目录
eval_scene_dir = get_scene_dir('base_config', 'eval_single')
eval_task_dir = get_task_dir('base_config', 'eval_single')

# 获取默认数据集
default_dataset = get_default_dataset('centralized_config')
print(f"默认数据集: {default_dataset}")

# 列出可用数据集
datasets = list_available_datasets('base_config')
print(f"可用数据集: {datasets}")
```

### 运行时配置覆盖

```python
# 设置运行时覆盖
config_manager.set_runtime_override('llm_config', 'api.custom.temperature', 0.2)
config_manager.set_runtime_override('agent_config', 'execution.max_total_steps', 500)

# 从字典设置覆盖
overrides = {
    'api': {
        'custom': {
            'model': 'deepseek-coder',
            'temperature': 0.15
        }
    }
}
config_manager.set_runtime_overrides_from_dict('llm_config', overrides)
```

### 命令行参数集成

```python
from config.config_override import ConfigOverrideParser, create_config_aware_parser

# 创建支持配置覆盖的参数解析器
parser = create_config_aware_parser(description='我的应用')

# 添加应用特定参数
parser.add_argument('--mode', type=str, help='运行模式')

# 解析参数并应用覆盖
args = parser.parse_args()
ConfigOverrideParser.apply_config_overrides(args, 'my_config')
```

## 配置优先级

配置值的优先级从高到低为：

1. **命令行参数覆盖** (最高优先级)
2. **运行时覆盖**
3. **配置文件中的值**
4. **继承的基础配置值**

**注意：配置系统不提供默认值，所有必需的配置项都必须明确定义，否则会抛出异常。**

## 常用命令行参数

### LLM配置覆盖
- `--llm-provider`: LLM提供商 (openai, volcengine, bailian, custom)
- `--llm-model`: 模型名称
- `--llm-temperature`: 温度参数
- `--llm-max-tokens`: 最大token数
- `--llm-api-key`: API密钥
- `--llm-endpoint`: API端点

### 执行配置覆盖
- `--max-total-steps`: 最大总执行步数
- `--max-steps-per-task`: 每个任务的最大步数
- `--timeout-seconds`: 超时时间

### 智能体配置覆盖
- `--max-failures`: 最大失败次数
- `--max-history`: 最大历史记录长度

### 提示词配置覆盖
- `--system-prompt`: 系统提示词
- `--coordinator-prompt`: 协调器提示词
- `--worker-prompt`: 工作智能体提示词
- `--prompt-file`: 从JSON文件加载提示词

### 数据集配置覆盖
- `--dataset`: 选择使用的数据集 (source, eval_single, eval_multi, sft_single, sft_multi)
- `--dataset-dir`: 自定义数据集目录路径（覆盖选定数据集的路径）

## 示例

查看 `examples/config_usage_example.py` 了解完整的使用示例。

运行配置覆盖示例：

```bash
# 显示配置摘要
python examples/centralized_agent_example.py --show-config

# 使用配置覆盖运行
python examples/centralized_agent_example.py \
    --llm-model deepseek-coder \
    --llm-temperature 0.15 \
    --max-total-steps 600 \
    --coordinator-prompt "你是一个高效的任务协调器"

# 使用数据集覆盖
python examples/centralized_agent_example.py \
    --dataset sft_single \
    --suffix "sft_training_test"

# 使用自定义数据集目录
python examples/centralized_agent_example.py \
    --dataset eval_multi \
    --dataset-dir "/path/to/custom/eval/multi" \
    --suffix "custom_eval"
```
