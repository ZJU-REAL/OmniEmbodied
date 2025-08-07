OmniEmbodied Framework API
===========================

This section provides detailed API documentation for all core framework components.

.. toctree::
   :maxdepth: 2

Evaluation Framework
--------------------

EvaluationManager
^^^^^^^^^^^^^^^^^

The central coordinator for evaluation activities.

.. autoclass:: evaluation.evaluation_manager.EvaluationManager
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

   .. method:: __init__(config_file, agent_type, task_type, scenario_selection, custom_suffix=None)

      Initialize the evaluation manager.

      :param str config_file: Configuration file identifier (e.g., "single_agent_config")
      :param str agent_type: Type of agent ("single" or "multi")
      :param str task_type: Type of task ("independent" or "collaborative")
      :param dict scenario_selection: Scenario selection configuration
      :param str custom_suffix: Optional suffix for result files

   .. method:: run_evaluation()

      Execute the evaluation process.

      :returns: Evaluation results dictionary
      :rtype: dict

EvaluationInterface
^^^^^^^^^^^^^^^^^^^

High-level interface for running evaluations.

.. autofunction:: evaluation.evaluation_interface.EvaluationInterface.run_evaluation

   Execute evaluation with specified parameters.

   :param str config_file: Configuration file identifier
   :param str agent_type: Agent type ("single" or "multi")
   :param str task_type: Task type ("independent" or "collaborative")
   :param dict scenario_selection: Scenario selection parameters
   :param str custom_suffix: Optional result file suffix
   :returns: Evaluation results
   :rtype: dict

ScenarioSelector
^^^^^^^^^^^^^^^^

Manages scenario selection and filtering.

.. autoclass:: evaluation.scenario_selector.ScenarioSelector
   :members:
   :undoc-members:
   :show-inheritance:

   .. method:: get_scenario_list(config, scenario_selection)

      Get filtered list of scenarios.

      :param dict config: Configuration dictionary
      :param dict scenario_selection: Selection criteria
      :returns: List of selected scenarios
      :rtype: list

TaskExecutor
^^^^^^^^^^^^

Executes individual tasks within scenarios.

.. autoclass:: evaluation.task_executor.TaskExecutor
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

   .. method:: execute_task(scenario_data, task_config)

      Execute a single task.

      :param dict scenario_data: Scenario information
      :param dict task_config: Task configuration
      :returns: Task execution result
      :rtype: dict

Agent Framework
---------------

Single Agent
^^^^^^^^^^^^

LLMAgent for single-agent scenarios.

.. autoclass:: modes.single_agent.llm_agent.LLMAgent
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

   .. method:: __init__(simulator, agent_id, config=None)

      Initialize LLM agent.

      :param SimulationEngine simulator: Simulation engine instance
      :param str agent_id: Unique agent identifier
      :param dict config: Optional agent configuration

   .. method:: decide_action(observation, available_actions)

      Decide next action based on observation.

      :param str observation: Current observation text
      :param list available_actions: Available action types
      :returns: Selected action details
      :rtype: dict

Multi-Agent System
^^^^^^^^^^^^^^^^^^

CentralizedAgent for coordinated multi-agent scenarios.

.. autoclass:: modes.centralized.centralized_agent.CentralizedAgent
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

   .. method:: __init__(simulator, agent_id, config=None)

      Initialize centralized agent coordinator.

      :param SimulationEngine simulator: Simulation engine instance
      :param str agent_id: Coordinator agent identifier
      :param dict config: Optional coordination configuration

LLM Integration
---------------

LLM Factory
^^^^^^^^^^^

Factory function for creating LLM instances.

.. Note: LLM factory function documentation temporarily disabled due to import issues.
   :no-index:

   Create LLM client from configuration.

   :param dict llm_config: LLM configuration dictionary
   :returns: Configured LLM client instance
   :rtype: object

The configuration format for different LLM providers:

.. code-block:: python

   # OpenAI API configuration
   llm_config = {
       "mode": "api",
       "api": {
           "provider": "openai",
           "model": "gpt-4",
           "api_key": "your-api-key"
       }
   }
   
   # Anthropic API configuration  
   llm_config = {
       "mode": "api", 
       "api": {
           "provider": "anthropic",
           "model": "claude-3-sonnet",
           "api_key": "your-api-key"
       }
   }

BaseLLM
^^^^^^^

Base class for LLM implementations.

.. autoclass:: llm.base_llm.BaseLLM
   :members:
   :undoc-members:
   :show-inheritance:

APILLM
^^^^^^

API-based LLM client implementation.

.. autoclass:: llm.api_llm.APILLM
   :members:
   :undoc-members:
   :show-inheritance:

   .. method:: generate(messages, **kwargs)

      Generate response from messages.

      :param list messages: List of message dictionaries
      :param kwargs: Additional generation parameters
      :returns: Generated response text
      :rtype: str

Configuration System
---------------------

ConfigManager
^^^^^^^^^^^^^

Manages configuration loading and merging.

.. autoclass:: config.config_manager.ConfigManager
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

   .. method:: __init__(config_dir=None)

      Initialize configuration manager.

      :param str config_dir: Directory containing configuration files

   .. method:: load_config(config_name, config_override=None)

      Load configuration by name.

      :param str config_name: Configuration identifier (e.g., "single_agent_config")
      :param dict config_override: Optional override values
      :returns: Merged configuration dictionary
      :rtype: dict

Configuration structure for different components:

.. code-block:: yaml

   # Agent configuration
   agent_config:
     max_history: 20
     temperature: 0.7
     action_timeout: 30
   
   # LLM configuration
   llm_config:
     mode: "api"
     api:
       provider: "openai"
       model: "gpt-4"
   
   # Evaluation configuration
   evaluation:
     max_steps: 50
     timeout: 300
     parallel_scenarios: 5

Utilities
---------

Logger
^^^^^^

Basic logging utilities.

.. autoclass:: utils.logger.ColorizedFormatter
   :members:
   :undoc-members:
   :show-inheritance:

.. autofunction:: utils.logger.get_logger

   Get logger instance by name.

   :param str name: Logger name
   :returns: Logger instance
   :rtype: logging.Logger

.. autofunction:: utils.logger.setup_logging

   Setup logging configuration.

   :param str name: Logger name
   :param str level: Logging level
   :param str log_file: Optional log file path
   :param bool console_output: Enable console output
   :returns: Configured logger
   :rtype: logging.Logger

Data Generation Logger
^^^^^^^^^^^^^^^^^^^^^^

Specialized logging utilities for data generation.

.. autofunction:: data_generation.utils.logger.get_logger

   Get data generation logger instance.

.. autofunction:: data_generation.utils.logger.log_raw_response

   Log raw LLM responses.

   :param str generator_type: Type of generator
   :param str item_id: Item identifier
   :param int thread_id: Thread identifier
   :param str response: Response text

.. autofunction:: data_generation.utils.logger.log_processing

   Log processing messages.

   :param logging.Logger logger: Logger instance
   :param str message: Message to log

.. autofunction:: data_generation.utils.logger.log_success

   Log success messages.

   :param logging.Logger logger: Logger instance
   :param str message: Success message

Data Generation Framework
-------------------------

BaseGenerator
^^^^^^^^^^^^^

Base class for data generators.

.. autoclass:: data_generation.generators.base_generator.BaseGenerator
   :members:
   :undoc-members:
   :show-inheritance:

   .. method:: __init__(generator_type, config_override=None)

      Initialize base generator.

      :param str generator_type: Type of generator
      :param dict config_override: Optional configuration overrides

   .. method:: generate(num_items)

      Generate specified number of items.

      :param int num_items: Number of items to generate
      :returns: Generated items
      :rtype: list

TaskGenerator
^^^^^^^^^^^^^

Generates task definitions.

.. autoclass:: data_generation.generators.task_generator.TaskGenerator
   :members:
   :undoc-members:
   :show-inheritance:

SceneGenerator
^^^^^^^^^^^^^^

Generates scene descriptions.

.. autoclass:: data_generation.generators.scene_generator.SceneGenerator
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
--------------

Basic Evaluation
^^^^^^^^^^^^^^^^^

.. code-block:: python

   from evaluation.evaluation_interface import EvaluationInterface
   
   # Run single-agent evaluation
   result = EvaluationInterface.run_evaluation(
       config_file="single_agent_config",  # ConfigManager resolves full path
       agent_type="single",
       task_type="independent",
       scenario_selection={
           "dataset_type": "single",
           "scenario_range": {"start": "00001", "end": "00050"}
       }
   )
   
   print(f"Success rate: {result.get('success_rate', 0):.2%}")

LLM Integration
^^^^^^^^^^^^^^^

.. code-block:: python

   from llm.llm_factory import create_llm_from_config
   
   # Create LLM instance
   llm_config = {
       "mode": "api",
       "api": {
           "provider": "openai",
           "model": "gpt-4",
           "api_key": "your-api-key"
       }
   }
   
   llm = create_llm_from_config(llm_config)
   response = llm.generate([{"role": "user", "content": "Hello!"}])

Custom Agent
^^^^^^^^^^^^

.. code-block:: python

   from modes.single_agent.llm_agent import LLMAgent
   from OmniSimulator.core.engine import SimulationEngine
   
   # Initialize simulation
   engine = SimulationEngine()
   
   # Create custom agent
   agent = LLMAgent(
       simulator=engine,
       agent_id="custom_agent",
       config={
           "temperature": 0.7,
           "max_history": 20
       }
   )

Configuration Management
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from config.config_manager import ConfigManager
   
   # Load configuration
   config_manager = ConfigManager()
   config = config_manager.load_config(
       "single_agent_config",  # Short name - automatically resolved
       config_override={
           "evaluation": {"max_steps": 100}
       }
   )

For more examples and detailed tutorials, see :doc:`../examples/basic_simulation`. 