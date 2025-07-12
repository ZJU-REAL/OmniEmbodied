# Embodied Agent Framework

A Large Language Model (LLM) based agent framework for controlling agents in text-based embodied task simulators to execute various tasks. Supports three modes: single agent, centralized multi-agent, and decentralized multi-agent.

## Project Overview

This framework provides a powerful runtime environment for LLM-based embodied agents, seamlessly integrating with text-based embodied task simulators. Main features include:

- **Multiple Interaction Modes**: Choose different agent collaboration approaches based on task complexity
- **Unified LLM Interface**: Support for multiple LLM providers, including local deployment and API services
- **Dynamic Prompt System**: Prompts separated from code, supporting variable injection and template management
- **Flexible Configuration Management**: Centralized configuration using YAML files
- **Simulator Bridge Layer**: Simplify simulator interactions with natural language description capabilities

## Feature Highlights

- **Multiple Agent Modes**:
  - Single Agent: Complete tasks independently with chain-of-thought reasoning support
  - Centralized Multi-Agent: One central LLM coordinates multiple execution agents with collaborative actions
  - Decentralized Multi-Agent: Multiple agents with their own LLMs collaborate with personalized configurations
- **Advanced Prompt System**:
  - Configuration file management of prompt templates with dynamic variable injection
  - Detailed proximity relationships and action command guidelines
  - Chain-of-Thought reasoning support
- **Flexible LLM Support**: Support for multiple LLM providers (OpenAI, Azure OpenAI, vLLM, etc.)
- **Intelligent Environment Perception**:
  - Natural language environment description functionality
  - Multi-level environment information (full/room/brief)
  - Dynamic object state tracking
- **Comprehensive Configuration System**: Use YAML files to manage configurations for different modes with log level control
- **Powerful Communication Mechanism**: Support for inter-agent messaging, broadcasting, and negotiation
- **Enhanced Execution Control**:
  - History management and failure retry mechanisms
  - Simulator bridge layer to simplify interactions
  - Action state tracking and feedback
- **Extensible Architecture**: Easy to implement different agent strategies and collaboration modes

## Installation

### Prerequisites

- Python 3.8+
- Text-based embodied task simulator (can be used standalone, but recommended with simulator)

### Installation Steps

```bash
# Clone repository
git clone https://github.com/your_username/embodied_framework.git

# Install dependencies
cd embodied_framework
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Environment Variable Configuration

Set appropriate API keys based on your LLM provider:

```bash
# OpenAI
export OPENAI_API_KEY="your_openai_api_key"

# Azure OpenAI
export AZURE_OPENAI_API_KEY="your_azure_api_key"
export AZURE_OPENAI_RESOURCE="your_resource_name"
export AZURE_OPENAI_DEPLOYMENT="your_deployment_id"
```

## Usage

### Single Agent Mode

```python
from embodied_framework import LLMAgent, ConfigManager, SimulatorBridge

# Step 1: Load configuration
config_manager = ConfigManager()
llm_config = config_manager.get_config("llm_config")
agent_config = config_manager.get_config("single_agent_config")

# Step 2: Initialize simulator bridge
bridge = SimulatorBridge()
bridge.initialize_with_task('data/default/default_task.json')

# Output task information
task_description = bridge.get_task_description()
print(f"Task: {task_description}")

# Step 3: Create LLM agent
agent_id = "agent_1"
agent = LLMAgent(bridge, agent_id, agent_config)

# Step 4: Execute task
status, message, result = agent.step()
print(f"Execution result: {message}")

# Get agent state
state = agent.get_state()
inventory = [item.get("name") for item in state.get("inventory", [])]
print(f"Current inventory: {inventory}")
```

### Centralized Multi-Agent Mode

```python
from embodied_framework import Coordinator, WorkerAgent, ConfigManager, SimulatorBridge

# Initialize simulator bridge
bridge = SimulatorBridge()
bridge.initialize_with_task('data/default/default_task.json')

# Load configuration
config_manager = ConfigManager()
centralized_config = config_manager.get_config('centralized_config')

# Create coordinator
coordinator = Coordinator(bridge, 'coordinator', centralized_config.get('coordinator'))

# Create worker agent
worker = WorkerAgent(bridge, 'worker_1', centralized_config.get('worker_agents'))
coordinator.add_worker(worker)

# Set task
coordinator.set_task("Find the kitchen, open the refrigerator, take out an apple")

# Execute one coordination step
status, message, results = coordinator.step()
```

### Decentralized Multi-Agent Mode

```python
from embodied_framework import AutonomousAgent, CommunicationManager, ConfigManager, SimulatorBridge

# Initialize simulator bridge
bridge = SimulatorBridge()
bridge.initialize_with_task('data/default/default_task.json')

# Create communication manager
comm_manager = CommunicationManager()
comm_manager.start_processing()

# Load configuration
config_manager = ConfigManager()
decentralized_config = config_manager.get_config('decentralized_config')

# Create autonomous agents
agent1 = AutonomousAgent(bridge, 'agent_1', decentralized_config.get('autonomous_agent'),
                       comm_manager=comm_manager)
agent2 = AutonomousAgent(bridge, 'agent_2', decentralized_config.get('autonomous_agent'),
                       comm_manager=comm_manager)

# Register with communication manager
comm_manager.register_agent('agent_1', agent1, agent1.receive_message)
comm_manager.register_agent('agent_2', agent2, agent2.receive_message)

# Set tasks
agent1.set_task("Explore the house, find the kitchen, and inform agent_2")
agent2.set_task("Wait for agent_1 to find the kitchen, then open the refrigerator and take out an apple")

# Execute steps
agent1.step()
agent2.step()
```

### Using Simulator Bridge to Simplify Interactions

```python
from embodied_framework.utils.simulator_bridge import SimulatorBridge

# Initialize simulator bridge
bridge = SimulatorBridge()

# Initialize with task file
bridge.initialize_with_task('data/default/default_task.json')

# Get task information
task_description = bridge.get_task_description()
agents_config = bridge.get_agents_config()

# Get scene information
rooms = bridge.get_rooms()
for room in rooms:
    objects = bridge.get_objects_in_room(room['id'])

# Find objects
red_objects = bridge.find_objects_by_property('color', 'red')
heavy_objects = bridge.find_objects_by_property('weight', lambda w: w > 10)

# Use natural language description functionality
agent_id = "agent_1"
agent_description = bridge.describe_agent_natural_language(agent_id)
print(f"Agent description: {agent_description}")

# Describe room
room_id = "kitchen"
room_description = bridge.describe_room_natural_language(room_id)
print(f"Room description: {room_description}")

# Describe entire environment
env_description = bridge.describe_environment_natural_language()
print(f"Environment description: {env_description}")
```

## Configuration System

### LLM Configuration

Configure LLM providers in `config/defaults/llm_config.yaml`:

```yaml
# LLM inference mode settings
mode: "api"  # Options: "api" or "vllm"

# API call configuration
api:
  provider: "openai"  # Options: "openai" or "custom"

  # Using OpenAI
  openai:
    model: "gpt-3.5-turbo"
    api_key: "sk-..."  # Best to use environment variable OPENAI_API_KEY
    temperature: 0.7
    max_tokens: 1000

  # Using custom endpoint (e.g., DeepSeek, Qwen, etc.)
  custom:
    model: "deepseek-chat"
    api_key: "sk-..."  # Or use environment variable CUSTOM_LLM_API_KEY
    endpoint: "https://api.deepseek.com"
    temperature: 0.1
    max_tokens: 4096

# VLLM local inference configuration
vllm:
  model_path: "/path/to/model"  # Local model path
  temperature: 0.1
  max_tokens: 4096
  tensor_parallel_size: 1
  gpu_memory_utilization: 0.9

# LLM parameter configuration
parameters:
  # Whether to send complete conversation history to LLM
  send_history: false  # true=send complete history, false=send only summary
```

### Agent Configuration

Agent configurations for various modes are located in the `config/defaults/` directory:
- `single_agent_config.yaml`: Single agent configuration
- `centralized_config.yaml`: Centralized multi-agent configuration
- `decentralized_config.yaml`: Decentralized multi-agent configuration

## Prompt System

The framework uses configuration files to manage prompt templates, separating prompts from code for easy modification and maintenance. The prompt configuration file is located at `config/defaults/prompts_config.yaml`.

### Prompt Configuration Structure

Prompt configurations are organized by different modes (single agent, centralized, decentralized):

```yaml
# Single agent mode prompts
single_agent:
  system: |
    # System prompt
  task_template: |
    # Task prompt template with variable substitution support

# Centralized multi-agent mode prompts
centralized:
  coordinator_system: |
    # Coordinator system prompt
  coordinator_template: |
    # Coordinator task prompt template

# Decentralized multi-agent mode prompts
decentralized:
  autonomous_system: |
    # Autonomous agent system prompt template
  autonomous_template: |
    # Autonomous agent task prompt template
```

### Using Prompt Manager

The framework provides a `PromptManager` class for loading and formatting prompt templates:

```python
from embodied_framework.utils import PromptManager

# Create prompt manager
prompt_manager = PromptManager("prompts_config")

# Get prompt template
system_prompt = prompt_manager.get_prompt_template("single_agent", "system")

# Format prompt template
formatted_prompt = prompt_manager.get_formatted_prompt(
    "single_agent",
    "task_template",
    task_description="Find the kitchen, open the refrigerator, take out an apple",
    current_location="living room",
    nearby_objects="table, sofa, TV",
    inventory="none"
)
```

### Environment Information Injection

The prompt system automatically injects environment descriptions into prompts through the `{environment_description}` placeholder:

```yaml
# In prompts_config.yaml
single_agent:
  task_template: |
    {environment_description}

    Current task:
    {task_description}

    Action history:
    {history_summary}
```

The detail level of environment descriptions is controlled by configuration files, ensuring LLMs receive appropriate environmental context information.

### Dynamic Action Injection

The `{dynamic_actions_description}` in system prompts automatically injects the list of currently available actions:

```yaml
single_agent:
  system: |
    You are an agent executing tasks in a text-based embodied environment.

    {dynamic_actions_description}

    Please choose appropriate actions based on the current environment state.
```

### Custom Prompts

To customize prompts, simply modify the corresponding templates in the `config/defaults/prompts_config.yaml` file without modifying code. This makes prompt tuning simpler and more flexible.

## Architecture Design

### Core Components

- `BaseAgent`: Base class for all agents, providing basic functionality
- `ConfigManager`: Manages YAML configuration files
- `PromptManager`: Manages prompt templates
- `SimulatorBridge`: Simplifies interactions with simulator
- `LLMFactory`: Creates different LLM instances based on configuration

### Agent Modes

- `single_agent`: Single agent implementation
- `centralized`: Centralized multi-agent implementation
- `decentralized`: Decentralized multi-agent implementation

### Directory Structure

```
embodied_framework/
├── core/                   # Core components
│   ├── base_agent.py       # Base agent abstract class
│   ├── agent_manager.py    # Agent manager
│   ├── agent_factory.py    # Agent factory functions
├── modes/                  # Different mode implementations
│   ├── single_agent/       # Single agent mode
│       ├── llm_agent.py    # LLM-based agent
│   ├── centralized/        # Centralized multi-agent
│       ├── coordinator.py  # Central coordinator
│       ├── worker_agent.py # Execution agent
│       ├── planner.py      # Task planning component
│   ├── decentralized/      # Decentralized multi-agent
│       ├── autonomous_agent.py # Autonomous agent
│       ├── communication.py    # Inter-agent communication
│       ├── negotiation.py      # Negotiation mechanism
├── llm/                    # LLM interfaces
│   ├── base_llm.py         # LLM base class
│   ├── llm_factory.py      # LLM factory functions
│   ├── api_llm.py          # API-based LLM implementation
│   ├── vllm_llm.py         # Local vLLM implementation
├── config/                 # Configuration system
│   ├── config_manager.py   # Configuration manager
│   ├── defaults/           # Default configuration files
├── utils/                  # Utility functions
│   ├── logger.py           # Logging utilities
│   ├── simulator_bridge.py # Simulator bridge
│   ├── prompt_manager.py   # Prompt management
│   ├── data_loader.py      # Data loading utilities
├── examples/               # Example scripts
```

## Example Scripts

The project includes multiple example scripts to help you get started quickly:

- `examples/single_agent_example.py`: Single agent example
- `examples/centralized_example.py`: Centralized multi-agent example
- `examples/decentralized_example.py`: Decentralized multi-agent example
- `examples/simulator_bridge_demo.py`: Simulator bridge usage example

## Advanced Features

### Natural Language Environment Description

The simulator bridge layer (`SimulatorBridge`) provides powerful natural language description functionality to help agents better understand the environment:

```python
# Get natural language descriptions
bridge = SimulatorBridge()
bridge.initialize_with_task('data/default/default_task.json')

# Describe agent state
agent_desc = bridge.describe_agent_natural_language("agent_1")

# Describe specific room
kitchen_desc = bridge.describe_room_natural_language("kitchen")

# Describe entire environment
env_desc = bridge.describe_environment_natural_language(
    sim_config={
        "nlp_show_object_properties": True,  # Show object properties
        "nlp_only_show_discovered": False    # Show all content, not just discovered
    }
)
```

These descriptions can be used as part of prompts to help LLMs better understand and reason about environmental situations.

### Task File Initialization

The framework supports using task files to initialize simulation environments, which is the most recommended initialization method:

```python
from embodied_framework.utils.simulator_bridge import SimulatorBridge

# Initialize simulator bridge
bridge = SimulatorBridge()

# Initialize with task file
task_file = "data/default/default_task.json"
success = bridge.initialize_with_task(task_file)

if success:
    # Task initialization successful
    task_description = bridge.get_task_description()
    print(f"Task: {task_description}")

    # Get agent information configured in task
    agents_config = bridge.get_agents_config()
    print(f"Task configured {len(agents_config)} agents")
else:
    print("Task initialization failed")
```

Task files contain scene settings, agent configurations, and task objectives, allowing you to quickly set up a complete simulation environment.

### Inter-Agent Communication

Decentralized multi-agent mode supports inter-agent communication. Agents can use the following command formats:
- `MSG<ReceiverID>: <Message Content>` - Send message to specific agent
- `BROADCAST: <Message Content>` - Broadcast message to all agents

### Personalized Agent Configuration

Decentralized mode supports configuring personality and skills for each agent:

```yaml
decentralized:
  autonomous_agent:
    personality: "cooperative, efficient, cautious"
    skills: ["exploration", "interaction", "analysis"]
    use_cot: true  # Enable chain-of-thought reasoning
    max_chat_history: 10
```

### Environment Description Configuration

The framework supports flexible environment description configuration, directly affecting the completeness of room information injected into prompts:

```yaml
env_description:
  detail_level: "full"  # full/room/brief - Control room information scope
  show_object_properties: true  # Whether to show detailed object properties
  only_show_discovered: false   # Whether to show only discovered content
```

#### Detail Level Description

- **`detail_level: "full"`** - Complete environment description
  - Shows information for **all rooms**
  - Includes environment overview, room details, and agent status
  - Suitable for tasks requiring global planning

- **`detail_level: "room"`** - Current room description (default)
  - Shows only information for **the room the agent is currently in**
  - Reduces prompt length, suitable for local operation tasks

- **`detail_level: "brief"`** - Brief description
  - Shows only agent's own state
  - Minimal environment information

#### Object Information Control

- **`show_object_properties: true`** - Show detailed object properties (size, weight, brand, etc.)
- **`only_show_discovered: false`** - Show all objects, including unexplored ones
- **`only_show_discovered: true`** - Show only discovered objects (more realistic for exploration scenarios)

#### Configuration Examples

```yaml
# Omniscient perspective configuration - suitable for planning tasks
env_description:
  detail_level: "full"
  show_object_properties: true
  only_show_discovered: false

# Exploration mode configuration - suitable for exploration tasks
env_description:
  detail_level: "room"
  show_object_properties: true
  only_show_discovered: true

# Lightweight mode configuration - suitable for simple tasks
env_description:
  detail_level: "brief"
  show_object_properties: false
  only_show_discovered: true
```

### Custom Agent Behavior

You can implement custom agent behavior by inheriting from base classes:

```python
from embodied_framework.core import BaseAgent

class MyCustomAgent(BaseAgent):
    def __init__(self, simulator, agent_id, config=None):
        super().__init__(simulator, agent_id, config)
        # Custom initialization code

    def decide_action(self):
        # Custom decision logic
        return "GOTO kitchen"
```

## Environment Variables

- `OPENAI_API_KEY` - OpenAI API key
- `AZURE_OPENAI_API_KEY` - Azure OpenAI API key
- `AZURE_OPENAI_RESOURCE` - Azure OpenAI resource name
- `AZURE_OPENAI_DEPLOYMENT` - Azure OpenAI deployment ID

## Frequently Asked Questions

### How to Switch LLM Providers?

Modify the `provider` field in `config/defaults/llm_config.yaml` to switch LLM providers.

### How to Add New LLM Implementation?

1. Create a new LLM implementation class in the `llm` directory, inheriting from `BaseLLM`
2. Add corresponding instantiation code in `llm_factory.py`
3. Add new provider configuration in the configuration file

### How to Optimize Prompts?

Directly edit prompt templates in the `config/defaults/prompts_config.yaml` file without modifying code. The prompt system supports:
- Dynamic variable injection (such as task descriptions, environment states, history records)
- Chain-of-thought reasoning prompts
- Dedicated prompt templates for different modes

### How to Configure History Message Sending?

The framework supports two ways of passing historical information, configured through `parameters.send_history` in `config/defaults/llm_config.yaml`:

**Method 1: Send Complete Conversation History (`send_history: true`)**
- LLM can see complete conversation context, including all historical user inputs and assistant replies
- Advantages: More accurate understanding, better context coherence
- Disadvantages: Consumes more tokens, may exceed model context length limits
- Use cases: Short conversations, tasks requiring precise context understanding

**Method 2: Send History Summary (`send_history: false`, default)**
- Only sends system messages and latest user messages, historical information passed through `history_summary` in prompts
- Advantages: Saves tokens, avoids context length issues, better performance
- Disadvantages: May lose some historical details
- Use cases: Long conversations, limited token budget, most task scenarios

```yaml
# Configure in llm_config.yaml
parameters:
  send_history: false  # Recommended setting
```

### How to Debug Agent Behavior?

1. Adjust log level to DEBUG: Set `logging.level: debug` in configuration file
2. Use environment description functionality to view agent's perceived environment state
3. Review execution history to analyze decision-making process
4. Utilize chain-of-thought reasoning functionality to understand agent's reasoning process
5. Enable `send_history: true` to see if LLM needs more historical context

## Changelog

### v1.2.0 (Latest Version)

**Major Feature Enhancements**
- 🚀 **Prompt System Refactoring**: Comprehensive optimization of prompt configuration with detailed proximity relationships and action guidelines
- 🧠 **Chain-of-Thought Reasoning Support**: All mode agents now support Chain-of-Thought reasoning
- 🌍 **Enhanced Environment Perception**: New multi-level environment description functionality (full/room/brief)
- 🤖 **Personalized Agents**: Decentralized mode supports personality and skill configuration
- 📊 **Improved Logging System**: Support for debug-level logging for easier troubleshooting

**Code Improvements**
- Optimized `BaseAgent` class with enhanced history management and state retrieval
- Improved example scripts with more detailed error handling and debugging information
- Enhanced `PromptManager` class with dynamic environment description injection support
- Improved centralized coordinator's collaborative action support
- Optimized decentralized agent communication and decision-making mechanisms

**Configuration Optimizations**
- Simplified prompt configuration file structure
- Added environment description detail level control
- Support for chain-of-thought reasoning toggle configuration
- Optimized log level configuration

## Contributing Guide

Welcome to contribute code, report issues, or make suggestions! Please follow these steps:

1. Fork this repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add some amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Submit Pull Request

## License

This project is licensed under the MIT License - see LICENSE file for details

## Acknowledgments

- Thanks to all contributors and users
- This project is built on various open source tools and libraries