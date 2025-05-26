# 智能体框架 (Agent Framework)

基于大语言模型(LLM)的智能体框架，用于控制[文本具身任务模拟器](../README.md)中的智能体执行各种任务。支持单智能体、中心化多智能体和去中心化多智能体三种模式。

## 功能特点

- **多种智能体模式**：
  - 单智能体：独立完成任务
  - 中心化多智能体：一个中央LLM协调多个执行智能体
  - 去中心化多智能体：多个拥有自己LLM的智能体相互协作
- **灵活的LLM支持**：支持多种LLM提供商（OpenAI、Azure OpenAI等）
- **完善的配置系统**：使用YAML文件管理不同模式的配置
- **强大的通信机制**：支持智能体间消息传递和协商
- **可扩展的架构**：便于实现不同的智能体策略和协作模式

## 安装方法

```bash
# 首先安装embodied_simulator（项目所在的主仓库）
cd sim
pip install -e .

# 然后安装embodied_framework
cd embodied_framework
pip install -e .
```

## 使用方法

### 单智能体模式

```python
from embodied_simulator import SimulationEngine
from embodied_framework import LLMAgent, ConfigManager

# 初始化模拟引擎
simulator = SimulationEngine()
simulator.initialize('data/scenes/default_scene.json')

# 加载配置
config_manager = ConfigManager()
agent_config = config_manager.get_config('single_agent_config')

# 创建LLM智能体
agent = LLMAgent(simulator, 'agent_1', agent_config)

# 设置任务
agent.set_task("找到厨房，打开冰箱，取出苹果")

# 执行一步
status, message, result = agent.step()
print(f"执行结果: {message}")
```

### 中心化多智能体模式

```python
from embodied_simulator import SimulationEngine
from embodied_framework import Coordinator, WorkerAgent, ConfigManager

# 初始化模拟引擎
simulator = SimulationEngine()
simulator.initialize('data/scenes/default_scene.json')

# 加载配置
config_manager = ConfigManager()
centralized_config = config_manager.get_config('centralized_config')

# 创建协调器
coordinator = Coordinator(simulator, 'coordinator', centralized_config.get('coordinator'))

# 创建工作智能体
worker = WorkerAgent(simulator, 'worker_1', centralized_config.get('worker_agents'))
coordinator.add_worker(worker)

# 设置任务
coordinator.set_task("找到厨房，打开冰箱，取出苹果")

# 执行一步协调
status, message, results = coordinator.step()
```

### 去中心化多智能体模式

```python
from embodied_simulator import SimulationEngine
from embodied_framework import AutonomousAgent, CommunicationManager, ConfigManager

# 初始化模拟引擎
simulator = SimulationEngine()
simulator.initialize('data/scenes/default_scene.json')

# 创建通信管理器
comm_manager = CommunicationManager()
comm_manager.start_processing()

# 加载配置
config_manager = ConfigManager()
decentralized_config = config_manager.get_config('decentralized_config')

# 创建自主智能体
agent1 = AutonomousAgent(simulator, 'agent_1', decentralized_config.get('autonomous_agent'), 
                        comm_manager=comm_manager)
agent2 = AutonomousAgent(simulator, 'agent_2', decentralized_config.get('autonomous_agent'), 
                        comm_manager=comm_manager)

# 注册到通信管理器
comm_manager.register_agent('agent_1', agent1, agent1.receive_message)
comm_manager.register_agent('agent_2', agent2, agent2.receive_message)

# 设置任务
agent1.set_task("探索房子，找到厨房，并告知agent_2")
agent2.set_task("等待agent_1找到厨房，然后打开冰箱，取出苹果")

# 执行步骤
agent1.step()
agent2.step()
```

### 配置LLM

在`config/defaults/llm_config.yaml`中配置LLM提供商：

```yaml
# 使用OpenAI
provider: openai
openai:
  model: gpt-3.5-turbo
  api_key: "sk-..." # 最好使用环境变量OPENAI_API_KEY

# 使用Azure OpenAI
provider: azure_openai
azure_openai:
  resource_name: "your-resource"
  deployment_id: "your-deployment"
  api_key: "..." # 最好使用环境变量AZURE_OPENAI_API_KEY
```

## 提示词配置

框架使用配置文件管理提示词模板，使得提示词与代码分离，便于修改和维护。提示词配置文件位于`config/defaults/prompts_config.yaml`。

### 提示词配置结构

提示词配置按照不同的模式（单智能体、中心化、去中心化）进行组织：

```yaml
# 单智能体模式的提示词
single_agent:
  system: |
    # 系统提示词
  task_template: |
    # 任务提示词模板，支持变量替换
  
# 中心化多智能体模式的提示词
centralized:
  coordinator_system: |
    # 协调器系统提示词
  coordinator_template: |
    # 协调器任务提示词模板
  
# 去中心化多智能体模式的提示词
decentralized:
  autonomous_system: |
    # 自主智能体系统提示词模板
  autonomous_template: |
    # 自主智能体任务提示词模板
```

### 使用提示词管理器

框架提供了`PromptManager`类用于加载和格式化提示词模板：

```python
from embodied_framework.utils import PromptManager

# 创建提示词管理器
prompt_manager = PromptManager("prompts_config")

# 获取提示词模板
system_prompt = prompt_manager.get_prompt_template("single_agent", "system")

# 格式化提示词模板
formatted_prompt = prompt_manager.get_formatted_prompt(
    "single_agent",
    "task_template",
    task_description="找到厨房，打开冰箱，取出苹果",
    current_location="客厅",
    nearby_objects="桌子，沙发，电视",
    inventory="无"
)
```

### 自定义提示词

要自定义提示词，只需修改`config/defaults/prompts_config.yaml`文件中的相应模板，而无需修改代码。这使得提示词调优变得更加简单和灵活。

## 目录结构

```
embodied_framework/
├── core/                   # 核心组件
│   ├── base_agent.py       # 基础智能体抽象类
│   ├── agent_manager.py    # 智能体管理器
│   ├── agent_factory.py    # 智能体工厂函数
├── single_agent/           # 单智能体实现
│   ├── basic_agent.py      # 基本智能体
│   ├── llm_agent.py        # 基于LLM的智能体
├── centralized/            # 中心化多智能体
│   ├── coordinator.py      # 中央协调器
│   ├── worker_agent.py     # 执行智能体
│   ├── planner.py          # 任务规划组件
├── decentralized/          # 去中心化多智能体
│   ├── autonomous_agent.py # 自主智能体
│   ├── communication.py    # 智能体间通信
│   ├── negotiation.py      # 协商机制
├── llm/                    # LLM接口
│   ├── base_llm.py         # LLM基类
│   ├── llm_factory.py      # LLM工厂函数
│   ├── providers/          # 不同提供商的实现
│       ├── openai_llm.py 
│       ├── azure_openai_llm.py
├── config/                 # 配置系统
│   ├── config_manager.py   # 配置管理器
│   ├── defaults/           # 默认配置
│       ├── llm_config.yaml
│       ├── single_agent_config.yaml
│       ├── centralized_config.yaml
│       ├── decentralized_config.yaml
├── utils/                  # 工具函数
│   ├── logger.py           # 日志工具
├── examples/               # 示例脚本
│   ├── single_agent_example.py
│   ├── centralized_example.py
│   ├── decentralized_example.py
```

## 示例

请参考`examples/`目录下的示例脚本了解如何使用不同模式的智能体完成任务。

## 环境变量

- `OPENAI_API_KEY` - OpenAI API密钥
- `AZURE_OPENAI_API_KEY` - Azure OpenAI API密钥
- `AZURE_OPENAI_RESOURCE` - Azure OpenAI资源名称
- `AZURE_OPENAI_DEPLOYMENT` - Azure OpenAI部署ID

## 贡献指南

欢迎贡献代码、报告问题或提出建议！请遵循以下步骤：

1. Fork本仓库
2. 创建功能分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add some amazing feature'`
4. 推送到分支：`git push origin feature/amazing-feature`
5. 提交Pull Request

## 许可证

本项目采用MIT许可证 - 详见LICENSE文件

## 架构简化

为了避免重复实现模拟器已有的功能，框架引入了SimulatorBridge桥接层。这个桥接层直接与模拟器交互，统一提供场景、任务和智能体相关的功能，从而简化了代码结构：

```python
from embodied_simulator import SimulationEngine
from embodied_framework.utils.simulator_bridge import SimulatorBridge

# 初始化模拟器和桥接器
simulator = SimulationEngine()
bridge = SimulatorBridge(simulator)

# 使用任务文件初始化
bridge.initialize_with_task('data/default/default_task.json')

# 获取任务信息
task_description = bridge.get_task_description()
agents_config = bridge.get_agents_config()

# 获取场景信息
rooms = bridge.get_rooms()
for room in rooms:
    objects = bridge.get_objects_in_room(room['id'])
    
# 查找物体
red_objects = bridge.find_objects_by_property('color', 'red')
heavy_objects = bridge.find_objects_by_property('weight', lambda w: w > 10)
```

这种设计有以下优势：
1. 减少代码冗余，避免重复实现模拟器已有的功能
2. 简化API，提供统一的接口进行场景和任务管理
3. 更好的可维护性，当模拟器更新时，只需更新桥接层即可 