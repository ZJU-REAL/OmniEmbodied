# 智能体框架 (Embodied Agent Framework)

基于大语言模型(LLM)的智能体框架，用于控制文本具身任务模拟器中的智能体执行各种任务。支持单智能体、中心化多智能体和去中心化多智能体三种模式。

## 项目概述

本框架为基于LLM的具身智能体提供了强大的运行环境，可以无缝集成到文本具身任务模拟器中。主要特性包括：

- **多种交互模式**：根据任务的复杂性选择不同的智能体协作方式
- **统一的LLM接口**：支持多种LLM提供商，包括本地部署和API服务
- **动态提示词系统**：提示词与代码分离，支持变量注入和模板化管理
- **灵活的配置管理**：使用YAML文件进行集中式配置
- **模拟器桥接层**：简化与模拟器的交互，提供自然语言描述能力

## 功能特点

- **多种智能体模式**：
  - 单智能体：独立完成任务，支持思维链推理
  - 中心化多智能体：一个中央LLM协调多个执行智能体，支持协作动作
  - 去中心化多智能体：多个拥有自己LLM的智能体相互协作，支持个性化配置
- **先进的提示词系统**：
  - 配置文件管理提示词模板，支持动态变量注入
  - 详细的近邻关系和动作命令指南
  - 支持思维链推理（Chain-of-Thought）
- **灵活的LLM支持**：支持多种LLM提供商（OpenAI、Azure OpenAI、vLLM等）
- **智能的环境感知**：
  - 自然语言环境描述功能
  - 多层次环境信息（完整/房间/简要）
  - 动态物体状态跟踪
- **完善的配置系统**：使用YAML文件管理不同模式的配置，支持日志级别控制
- **强大的通信机制**：支持智能体间消息传递、广播和协商
- **增强的执行控制**：
  - 历史记录管理和失败重试机制
  - 模拟器桥接层简化交互
  - 动作状态跟踪和反馈
- **可扩展的架构**：便于实现不同的智能体策略和协作模式

## 安装方法

### 前提条件

- Python 3.8+
- 文本具身任务模拟器 (可单独使用，但推荐与模拟器结合)

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/你的用户名/embodied_framework.git

# 安装依赖
cd embodied_framework
pip install -r requirements.txt

# 安装为开发模式
pip install -e .
```

### 环境变量配置

根据您使用的LLM提供商，设置相应的API密钥：

```bash
# OpenAI
export OPENAI_API_KEY="your_openai_api_key"

# Azure OpenAI
export AZURE_OPENAI_API_KEY="your_azure_api_key"
export AZURE_OPENAI_RESOURCE="your_resource_name"
export AZURE_OPENAI_DEPLOYMENT="your_deployment_id"
```

## 使用方法

### 单智能体模式

```python
from embodied_framework import LLMAgent, ConfigManager, SimulatorBridge

# 步骤1: 加载配置
config_manager = ConfigManager()
llm_config = config_manager.get_config("llm_config")
agent_config = config_manager.get_config("single_agent_config")

# 步骤2: 初始化模拟器桥接
bridge = SimulatorBridge()
bridge.initialize_with_task('data/default/default_task.json')

# 输出任务信息
task_description = bridge.get_task_description()
print(f"任务: {task_description}")

# 步骤3: 创建LLM智能体
agent_id = "agent_1"
agent = LLMAgent(bridge, agent_id, agent_config)

# 步骤4: 执行任务
status, message, result = agent.step()
print(f"执行结果: {message}")

# 获取智能体状态
state = agent.get_state()
inventory = [item.get("name") for item in state.get("inventory", [])]
print(f"当前库存: {inventory}")
```

### 中心化多智能体模式

```python
from embodied_framework import Coordinator, WorkerAgent, ConfigManager, SimulatorBridge

# 初始化模拟器桥接
bridge = SimulatorBridge()
bridge.initialize_with_task('data/default/default_task.json')

# 加载配置
config_manager = ConfigManager()
centralized_config = config_manager.get_config('centralized_config')

# 创建协调器
coordinator = Coordinator(bridge, 'coordinator', centralized_config.get('coordinator'))

# 创建工作智能体
worker = WorkerAgent(bridge, 'worker_1', centralized_config.get('worker_agents'))
coordinator.add_worker(worker)

# 设置任务
coordinator.set_task("找到厨房，打开冰箱，取出苹果")

# 执行一步协调
status, message, results = coordinator.step()
```

### 去中心化多智能体模式

```python
from embodied_framework import AutonomousAgent, CommunicationManager, ConfigManager, SimulatorBridge

# 初始化模拟器桥接
bridge = SimulatorBridge()
bridge.initialize_with_task('data/default/default_task.json')

# 创建通信管理器
comm_manager = CommunicationManager()
comm_manager.start_processing()

# 加载配置
config_manager = ConfigManager()
decentralized_config = config_manager.get_config('decentralized_config')

# 创建自主智能体
agent1 = AutonomousAgent(bridge, 'agent_1', decentralized_config.get('autonomous_agent'), 
                       comm_manager=comm_manager)
agent2 = AutonomousAgent(bridge, 'agent_2', decentralized_config.get('autonomous_agent'), 
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

### 使用模拟器桥接简化交互

```python
from embodied_framework.utils.simulator_bridge import SimulatorBridge

# 初始化模拟器桥接器
bridge = SimulatorBridge()

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

# 使用自然语言描述功能
agent_id = "agent_1"
agent_description = bridge.describe_agent_natural_language(agent_id)
print(f"智能体描述: {agent_description}")

# 描述房间
room_id = "kitchen"
room_description = bridge.describe_room_natural_language(room_id)
print(f"房间描述: {room_description}")

# 描述整个环境
env_description = bridge.describe_environment_natural_language()
print(f"环境描述: {env_description}")
```

## 配置系统

### LLM配置

在`config/defaults/llm_config.yaml`中配置LLM提供商：

```yaml
# LLM推理方式设置
mode: "api"  # 可选值: "api" 或 "vllm"

# API调用方式配置
api:
  provider: "openai"  # 可选值: "openai" 或 "custom"

  # 使用OpenAI
  openai:
    model: "gpt-3.5-turbo"
    api_key: "sk-..."  # 最好使用环境变量OPENAI_API_KEY
    temperature: 0.7
    max_tokens: 1000

  # 使用自定义端点（如DeepSeek、通义千问等）
  custom:
    model: "deepseek-chat"
    api_key: "sk-..."  # 或使用环境变量CUSTOM_LLM_API_KEY
    endpoint: "https://api.deepseek.com"
    temperature: 0.1
    max_tokens: 4096

# VLLM本地推理配置
vllm:
  model_path: "/path/to/model"  # 本地模型路径
  temperature: 0.1
  max_tokens: 4096
  tensor_parallel_size: 1
  gpu_memory_utilization: 0.9

# LLM参数配置
parameters:
  # 是否发送完整的对话历史给LLM
  send_history: false  # true=发送完整历史，false=只发送摘要
```

### 智能体配置

各种模式的智能体配置位于`config/defaults/`目录下：
- `single_agent_config.yaml`：单智能体配置
- `centralized_config.yaml`：中心化多智能体配置
- `decentralized_config.yaml`：去中心化多智能体配置

## 提示词系统

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

### 环境信息注入

提示词系统会自动将环境描述注入到提示词中，通过`{environment_description}`占位符实现：

```yaml
# 在 prompts_config.yaml 中
single_agent:
  task_template: |
    {environment_description}

    当前任务：
    {task_description}

    历史行动：
    {history_summary}
```

环境描述的详细程度由配置文件控制，确保LLM获得适当的环境上下文信息。

### 动态动作注入

系统提示词中的`{dynamic_actions_description}`会自动注入当前可用的动作列表：

```yaml
single_agent:
  system: |
    你是一个在文本具身环境中执行任务的智能体。

    {dynamic_actions_description}

    请根据当前环境状态选择合适的动作。
```

### 自定义提示词

要自定义提示词，只需修改`config/defaults/prompts_config.yaml`文件中的相应模板，而无需修改代码。这使得提示词调优变得更加简单和灵活。

## 架构设计

### 核心组件

- `BaseAgent`: 所有智能体的基类，提供基本功能
- `ConfigManager`: 管理YAML配置文件
- `PromptManager`: 管理提示词模板
- `SimulatorBridge`: 简化与模拟器的交互
- `LLMFactory`: 根据配置创建不同的LLM实例

### 智能体模式

- `single_agent`: 单智能体实现
- `centralized`: 中心化多智能体实现
- `decentralized`: 去中心化多智能体实现

### 目录结构

```
embodied_framework/
├── core/                   # 核心组件
│   ├── base_agent.py       # 基础智能体抽象类
│   ├── agent_manager.py    # 智能体管理器
│   ├── agent_factory.py    # 智能体工厂函数
├── modes/                  # 不同模式的实现
│   ├── single_agent/       # 单智能体模式
│       ├── llm_agent.py    # 基于LLM的智能体
│   ├── centralized/        # 中心化多智能体
│       ├── coordinator.py  # 中央协调器
│       ├── worker_agent.py # 执行智能体
│       ├── planner.py      # 任务规划组件
│   ├── decentralized/      # 去中心化多智能体
│       ├── autonomous_agent.py # 自主智能体
│       ├── communication.py    # 智能体间通信
│       ├── negotiation.py      # 协商机制
├── llm/                    # LLM接口
│   ├── base_llm.py         # LLM基类
│   ├── llm_factory.py      # LLM工厂函数
│   ├── api_llm.py          # API型LLM实现
│   ├── vllm_llm.py         # 本地vLLM实现
├── config/                 # 配置系统
│   ├── config_manager.py   # 配置管理器
│   ├── defaults/           # 默认配置文件
├── utils/                  # 工具函数
│   ├── logger.py           # 日志工具
│   ├── simulator_bridge.py # 模拟器桥接
│   ├── prompt_manager.py   # 提示词管理
│   ├── data_loader.py      # 数据加载工具
├── examples/               # 示例脚本
```

## 示例脚本

项目内置了多个示例脚本，帮助您快速上手：

- `examples/single_agent_example.py`: 单智能体示例
- `examples/centralized_example.py`: 中心化多智能体示例
- `examples/decentralized_example.py`: 去中心化多智能体示例
- `examples/simulator_bridge_demo.py`: 模拟器桥接使用示例

## 高级功能

### 自然语言环境描述

模拟器桥接层(`SimulatorBridge`)提供了强大的自然语言描述功能，可以帮助智能体更好地理解环境：

```python
# 获取自然语言描述
bridge = SimulatorBridge()
bridge.initialize_with_task('data/default/default_task.json')

# 描述智能体状态
agent_desc = bridge.describe_agent_natural_language("agent_1")

# 描述特定房间
kitchen_desc = bridge.describe_room_natural_language("kitchen")

# 描述整个环境
env_desc = bridge.describe_environment_natural_language(
    sim_config={
        "nlp_show_object_properties": True,  # 显示物体属性
        "nlp_only_show_discovered": False    # 显示全部内容，不仅是已发现的
    }
)
```

这些描述可以作为提示词的一部分，帮助LLM更好地理解和推理环境中的情况。

### 任务文件初始化

框架支持使用任务文件初始化模拟环境，这是最推荐的初始化方式：

```python
from embodied_framework.utils.simulator_bridge import SimulatorBridge

# 初始化模拟器桥接
bridge = SimulatorBridge()

# 使用任务文件初始化
task_file = "data/default/default_task.json"
success = bridge.initialize_with_task(task_file)

if success:
    # 任务初始化成功
    task_description = bridge.get_task_description()
    print(f"任务: {task_description}")
    
    # 获取任务配置的智能体信息
    agents_config = bridge.get_agents_config()
    print(f"任务配置了 {len(agents_config)} 个智能体")
else:
    print("任务初始化失败")
```

任务文件包含了场景设置、智能体配置和任务目标等信息，使用它可以快速设置完整的模拟环境。

### 智能体间通信

去中心化多智能体模式支持智能体间通信，智能体可以使用以下命令格式：
- `MSG<接收者ID>: <消息内容>` - 发送消息到特定智能体
- `BROADCAST: <消息内容>` - 广播消息给所有智能体

### 个性化智能体配置

去中心化模式支持为每个智能体配置个性和技能：

```yaml
decentralized:
  autonomous_agent:
    personality: "合作、高效、谨慎"
    skills: ["探索", "交互", "分析"]
    use_cot: true  # 启用思维链推理
    max_chat_history: 10
```

### 环境描述配置

框架支持灵活的环境描述配置，直接影响提示词中注入的房间信息完整性：

```yaml
env_description:
  detail_level: "full"  # full/room/brief - 控制房间信息范围
  show_object_properties: true  # 是否显示物体详细属性
  only_show_discovered: false   # 是否只显示已发现的内容
```

#### 详细程度说明

- **`detail_level: "full"`** - 完整环境描述
  - 显示**所有房间**的信息
  - 包含环境概述、房间详情和智能体状态
  - 适用于需要全局规划的任务

- **`detail_level: "room"`** - 当前房间描述（默认）
  - 只显示**智能体当前所在房间**的信息
  - 减少提示词长度，适用于局部操作任务

- **`detail_level: "brief"`** - 简要描述
  - 只显示智能体自身状态
  - 最简化的环境信息

#### 物体信息控制

- **`show_object_properties: true`** - 显示物体的详细属性（尺寸、重量、品牌等）
- **`only_show_discovered: false`** - 显示所有物体，包括未探索发现的
- **`only_show_discovered: true`** - 只显示已发现的物体（更符合现实探索场景）

#### 配置示例

```yaml
# 全知视角配置 - 适用于规划任务
env_description:
  detail_level: "full"
  show_object_properties: true
  only_show_discovered: false

# 探索模式配置 - 适用于探索任务
env_description:
  detail_level: "room"
  show_object_properties: true
  only_show_discovered: true

# 轻量模式配置 - 适用于简单任务
env_description:
  detail_level: "brief"
  show_object_properties: false
  only_show_discovered: true
```

### 自定义智能体行为

可以通过继承基础类来实现自定义智能体行为：

```python
from embodied_framework.core import BaseAgent

class MyCustomAgent(BaseAgent):
    def __init__(self, simulator, agent_id, config=None):
        super().__init__(simulator, agent_id, config)
        # 自定义初始化代码
        
    def decide_action(self):
        # 自定义决策逻辑
        return "GOTO kitchen"
```

## 环境变量

- `OPENAI_API_KEY` - OpenAI API密钥
- `AZURE_OPENAI_API_KEY` - Azure OpenAI API密钥
- `AZURE_OPENAI_RESOURCE` - Azure OpenAI资源名称
- `AZURE_OPENAI_DEPLOYMENT` - Azure OpenAI部署ID

## 常见问题

### 如何切换LLM提供商？

修改`config/defaults/llm_config.yaml`中的`provider`字段即可切换LLM提供商。

### 如何添加新的LLM实现？

1. 在`llm`目录中创建新的LLM实现类，继承`BaseLLM`
2. 在`llm_factory.py`中添加对应的实例化代码
3. 在配置文件中添加新的提供商配置

### 如何优化提示词？

直接编辑`config/defaults/prompts_config.yaml`文件中的提示词模板，无需修改代码。提示词系统支持：
- 动态变量注入（如任务描述、环境状态、历史记录）
- 思维链推理提示
- 不同模式的专用提示词模板

### 如何配置历史消息发送？

框架支持两种历史信息传递方式，通过`config/defaults/llm_config.yaml`中的`parameters.send_history`配置：

**方式1：发送完整对话历史（`send_history: true`）**
- LLM能看到完整的对话上下文，包括所有历史的用户输入和助手回复
- 优点：理解更准确，上下文连贯性更好
- 缺点：消耗更多token，可能超出模型上下文长度限制
- 适用场景：短对话、需要精确上下文理解的任务

**方式2：发送历史摘要（`send_history: false`，默认）**
- 只发送system消息和最新的用户消息，历史信息通过`history_summary`在提示词中传递
- 优点：节省token，避免上下文长度问题，性能更好
- 缺点：可能丢失部分历史细节
- 适用场景：长对话、token预算有限、大部分任务场景

```yaml
# 在 llm_config.yaml 中配置
parameters:
  send_history: false  # 推荐设置
```

### 如何调试智能体行为？

1. 调整日志级别到DEBUG：在配置文件中设置`logging.level: debug`
2. 使用环境描述功能查看智能体感知的环境状态
3. 查看执行历史记录分析决策过程
4. 利用思维链推理功能了解智能体的推理过程
5. 启用`send_history: true`查看LLM是否需要更多历史上下文

## 更新日志

### v1.2.0 (最新版本)

**主要功能增强**
- 🚀 **提示词系统重构**：全面优化提示词配置，增加详细的近邻关系和动作指南
- 🧠 **思维链推理支持**：所有模式的智能体现在支持Chain-of-Thought推理
- 🌍 **增强环境感知**：新增多层次环境描述功能（完整/房间/简要）
- 🤖 **个性化智能体**：去中心化模式支持个性和技能配置
- 📊 **改进日志系统**：支持调试级别日志，便于问题排查

**代码改进**
- 优化`BaseAgent`类，增强历史记录管理和状态获取
- 改进示例脚本，添加更详细的错误处理和调试信息
- 增强`PromptManager`类，支持动态环境描述注入
- 完善中心化协调器的协作动作支持
- 优化去中心化智能体的通信和决策机制

**配置优化**
- 简化提示词配置文件结构
- 增加环境描述详细级别控制
- 支持思维链推理开关配置
- 优化日志级别配置

## 贡献指南

欢迎贡献代码、报告问题或提出建议！请遵循以下步骤：

1. Fork本仓库
2. 创建功能分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add some amazing feature'`
4. 推送到分支：`git push origin feature/amazing-feature`
5. 提交Pull Request

## 许可证

本项目采用MIT许可证 - 详见LICENSE文件

## 致谢

- 感谢所有贡献者和使用者
- 本项目基于多种开源工具和库构建 