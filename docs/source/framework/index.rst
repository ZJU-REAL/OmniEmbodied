OmniEmbodied Framework
======================

The OmniEmbodied Framework is a comprehensive evaluation and training system built on top of OmniSimulator. It provides LLM integration, multi-agent coordination, and standardized benchmarking for embodied AI research.

.. toctree::
   :maxdepth: 2

   evaluation
   agents
   data_generation

What is the OmniEmbodied Framework?
-----------------------------------

The OmniEmbodied Framework extends OmniSimulator with:

📊 **Evaluation System**
   Comprehensive benchmarking tools with standardized tasks, metrics, and analysis.

🤖 **Agent Implementations**
   Ready-to-use agent architectures including single-agent and multi-agent coordination modes.

💬 **LLM Integration**
   Seamless integration with OpenAI, Anthropic, vLLM, and other language model providers.

📈 **Data Generation**
   Automated tools for creating training datasets, evaluation scenarios, and synthetic data.

🔧 **Configuration Management**
   Flexible YAML-based configuration system supporting complex experimental setups.

Core Components
---------------

Evaluation Framework
^^^^^^^^^^^^^^^^^^^^

The evaluation system provides:

- **Standardized Tasks**: 1400+ curated scenarios across multiple difficulty levels
- **Task Categories**: Direct commands, reasoning, collaboration, and tool use
- **Performance Metrics**: Success rates, efficiency measures, and error analysis
- **Comparative Analysis**: Tools for comparing different agent architectures

.. code-block:: python

   from evaluation.evaluation_interface import EvaluationInterface

   # Configure evaluation parameters
   result = EvaluationInterface.run_evaluation(
       config_file="single_agent_config",  # Will resolve to config/baseline/single_agent_config.yaml
       agent_type="single",
       task_type="independent", 
       scenario_selection={
           "dataset_type": "single",
           "scenario_range": {"start": "00001", "end": "00003"}
       }
   )
   
   # Analyze results
   print(f"Success rate: {result.get('success_rate', 0):.2%}")
   print(f"Total scenarios: {result.get('total_scenarios', 0)}")

Agent Modes
^^^^^^^^^^^

The framework includes multiple agent architectures:

**Single Agent Mode**:
- Individual agents complete tasks independently
- Support for chain-of-thought reasoning
- Configurable memory and history management

**Centralized Multi-Agent Mode**:
- Central coordinator manages multiple worker agents
- Hierarchical task decomposition and assignment
- Coordinated action planning and execution

**Decentralized Multi-Agent Mode** (Future):
- Autonomous agents with peer-to-peer communication
- Negotiation and consensus mechanisms
- Distributed problem solving

.. code-block:: python

   from modes.single_agent.llm_agent import LLMAgent
   from modes.centralized.centralized_agent import CentralizedAgent

   # Single agent
   single_agent = LLMAgent(
       agent_id="solo_explorer",
       config=single_agent_config
   )
   
   # Centralized multi-agent
   coordinator = CentralizedAgent(
       coordinator_id="mission_control", 
       worker_count=3,
       config=centralized_config
   )

LLM Integration
^^^^^^^^^^^^^^^

The framework supports various language model providers:

- **OpenAI Models**: GPT-3.5, GPT-4, GPT-4-Turbo
- **Anthropic Models**: Claude-3 family
- **Local Models**: vLLM, HuggingFace Transformers
- **Custom Endpoints**: Any OpenAI-compatible API

.. code-block:: python

   from llm.llm_factory import create_llm_from_config

   # OpenAI integration
   openai_llm = create_llm_from_config({
       "mode": "api",
       "api": {
           "provider": "openai", 
           "model": "gpt-4",
           "temperature": 0.1,
           "api_key": "your-key"
       }
   })
   
   # vLLM local deployment
   vllm_llm = create_llm_from_config({
       "mode": "vllm",
       "model": "Qwen2.5-7B-Instruct",
       "endpoint": "http://localhost:8000/v1"
   })

Key Features
------------

Comprehensive Benchmarking
^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Task Taxonomy**: 8 distinct task categories covering different AI capabilities
- **Difficulty Levels**: Progressive complexity from basic to advanced reasoning
- **Evaluation Protocols**: Standardized procedures for reproducible research
- **Performance Analysis**: Detailed breakdowns by task type and error mode

Multi-Modal Agent Support
^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Text-Based Reasoning**: Natural language understanding and generation
- **Symbolic Manipulation**: Logical reasoning and problem solving
- **Spatial Reasoning**: Understanding of physical relationships and constraints
- **Tool Usage**: Interaction with objects and environmental elements

Experimental Infrastructure
^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Parallel Execution**: Concurrent evaluation across multiple scenarios
- **Result Management**: Organized storage and retrieval of experimental data
- **Configuration Versioning**: Track and reproduce experimental conditions  
- **Error Analysis**: Detailed logging and failure mode investigation

Getting Started with the Framework
-----------------------------------

**Quick Evaluation**:

.. code-block:: bash

   # Configure your LLM (see quickstart guide)
   vim config/baseline/llm_config.yaml
   
   # Run evaluation using provided scripts
   cd scripts/
   bash qwen7b-wg.sh  # Single-agent with guidance
   bash deepseekr1-wg.sh  # Multi-agent evaluation

**Custom Evaluation**:

.. code-block:: python

   from evaluation.evaluation_interface import EvaluationInterface

   # Run evaluation using the interface
   result = EvaluationInterface.run_evaluation(
       config_file="single_agent_config",
       agent_type="single",
       task_type="independent",
       scenario_selection={
           "dataset_type": "single", 
           "scenario_range": {"start": "00001", "end": "00100"},
           "task_filter": {
               "categories": ["direct_command", "tool_use"]
           }
       }
   )
   
   print(f"Evaluation completed: {result.get('success_rate', 0):.2%} success rate")

Framework Architecture
----------------------

The framework layers on top of OmniSimulator:

.. code-block:: text

   ┌─────────────────────────────────────────────┐
   │           Evaluation & Training             │
   │  ┌─────────────────┐ ┌─────────────────────┐ │
   │  │    Benchmark    │ │   Data Generation   │ │
   │  │     Suite       │ │      Tools          │ │
   │  └─────────────────┘ └─────────────────────┘ │
   └─────────────────────────────────────────────┘
   ┌─────────────────────────────────────────────┐
   │              Agent Modes                    │
   │  ┌─────────────┐ ┌─────────────┐ ┌────────┐ │
   │  │   Single    │ │ Centralized │ │ Custom │ │
   │  │   Agent     │ │Multi-Agent  │ │ Modes  │ │
   │  └─────────────┘ └─────────────┘ └────────┘ │
   └─────────────────────────────────────────────┘
   ┌─────────────────────────────────────────────┐
   │             LLM Integration                 │
   │  ┌─────────────┐ ┌─────────────┐ ┌────────┐ │
   │  │   OpenAI    │ │  Anthropic  │ │  vLLM  │ │
   │  └─────────────┘ └─────────────┘ └────────┘ │
   └─────────────────────────────────────────────┘
   ┌─────────────────────────────────────────────┐
   │              OmniSimulator                  │
   └─────────────────────────────────────────────┘

Configuration System
--------------------

The framework uses hierarchical YAML configuration:

.. code-block:: yaml

   # Base configuration
   extends: "base_config"
   
   # Agent setup
   agent_config:
     agent_class: "modes.single_agent.llm_agent.LLMAgent"
     max_history: 20
     
   # LLM configuration  
   llm_config:
     provider: "vllm"
     model_name: "Qwen2.5-7B-Instruct"
     endpoint: "http://localhost:8000/v1"
     temperature: 0.1
     
   # Evaluation setup
   evaluation:
     dataset_type: "single"
     scenario_range: {"start": "00001", "end": "00800"}
     max_parallel: 5

Data and Scenarios
------------------

The framework includes extensive datasets:

**Evaluation Datasets**:
- **Single-Agent**: 800 scenarios across 4 task categories
- **Multi-Agent**: 600 collaborative scenarios
- **Progressive Difficulty**: From basic commands to complex reasoning

**Task Categories**:
- Direct Command Following
- Attribute-Based Reasoning  
- Tool Use and Manipulation
- Spatial Reasoning
- Compound Multi-Step Reasoning
- Explicit Collaboration
- Implicit Collaboration
- Compound Collaboration

Performance and Optimization
----------------------------

The framework is optimized for research workflows:

**Efficient Evaluation**:
- Parallel scenario processing
- Intelligent caching and reuse
- Optimized LLM API usage

**Resource Management**:
- Configurable memory limits
- Automatic cleanup and garbage collection
- Progress tracking and resumption

**Result Analysis**:
- Automated statistical analysis
- Comparative performance metrics
- Error categorization and analysis

Next Steps
----------

To learn more about the Framework components:

- :doc:`evaluation` - Evaluation system and benchmarking
- :doc:`agents` - Agent implementations and customization
- :doc:`llm_integration` - Language model integration guide
- :doc:`data_generation` - Dataset creation and management
- :doc:`configuration` - Advanced configuration patterns

For practical usage:

- :doc:`../examples/evaluation_workflows` - Evaluation examples
- :doc:`../examples/custom_agents` - Creating custom agents
- :doc:`../examples/llm_integration` - LLM integration examples 