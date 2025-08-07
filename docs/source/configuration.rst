Configuration
=============

OmniEmbodied uses a flexible YAML-based configuration system that allows you to customize every aspect of the simulation, evaluation, and agent behavior.

Overview
--------

The configuration system is hierarchical and supports:

- **Base configurations** that can be extended
- **Configuration inheritance** with override capabilities  
- **Environment variable substitution**
- **Dynamic configuration validation**
- **Profile-based settings** for different scenarios

Configuration Files
--------------------

The main configuration files are located in the ``config/`` directory:

.. code-block:: text

   config/
   ├── baseline/
   │   ├── base_config.yaml           # Base configuration template
   │   ├── single_agent_config.yaml   # Single agent scenarios
   │   ├── centralized_config.yaml    # Multi-agent centralized control
   │   └── llm_config.yaml            # LLM-specific settings
   ├── data_generation/
   │   ├── clue_gen_config.yaml       # Clue generation settings
   │   ├── scene_gen_config.yaml      # Scene generation settings
   │   └── task_gen_config.yaml       # Task generation settings
   └── simulator/
       └── simulator_config.yaml      # Core simulator settings

Important Configuration Notes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**For Global Observation Mode**: Scripts ending with ``-wg.sh`` require:

1. Runtime parameter: ``--observation-mode global``
2. Simulator configuration: ``global_observation: true`` in ``config/simulator/simulator_config.yaml``

Base Configuration Structure
----------------------------

Here's the basic structure of a configuration file:

.. code-block:: yaml

   # Configuration inheritance
   extends: "base_config"

   # Dataset configuration
   dataset:
     default: "eval_single"             # Dataset to use

   # Logging settings  
   logging:
     level: "INFO"                      # DEBUG, INFO, WARNING, ERROR
     show_llm_details: true             # Show LLM API details

   # Agent configuration
   agent_config:
     agent_class: "modes.single_agent.llm_agent.LLMAgent"
     max_history: 20                    # Maximum conversation history
     
     environment_description:
       detail_level: 'full'             # full, basic, minimal
       show_object_properties: true
       only_show_discovered: true
       include_other_agents: true
       update_frequency: 0              # 0 = every step

   # Execution settings
   execution:
     max_total_steps: 400               # Maximum steps per simulation
     max_steps_per_task: 35             # Maximum steps per individual task

   # Evaluation settings
   evaluation:
     task_type: 'independent'           # independent, collaborative
     default_scenario: '00002'          # Default scenario ID

   # LLM configuration
   llm_config:
     model_name: "gpt-4"               # Model to use
     temperature: 0.1                  # Sampling temperature
     max_tokens: 2000                  # Maximum response length
     api_key_env: "OPENAI_API_KEY"     # Environment variable for API key

Configuration Sections
-----------------------

Dataset Configuration
^^^^^^^^^^^^^^^^^^^^^

Controls which dataset to use for evaluation:

.. code-block:: yaml

   dataset:
     default: "eval_single"             # Options: eval_single, eval_multi, 
                                        #          sft_single, sft_multi, source

Agent Configuration
^^^^^^^^^^^^^^^^^^^

Defines agent behavior and capabilities:

.. code-block:: yaml

   agent_config:
     agent_class: "modes.single_agent.llm_agent.LLMAgent"
     max_history: 20
     
     # How the agent perceives the environment
     environment_description:
       detail_level: 'full'             # full, basic, minimal
       show_object_properties: true     # Include object states
       only_show_discovered: true       # Only show discovered objects
       include_other_agents: true       # Include other agent positions
       update_frequency: 0              # Update frequency (0 = always)

Execution Configuration
^^^^^^^^^^^^^^^^^^^^^^^

Controls simulation execution parameters:

.. code-block:: yaml

   execution:
     max_total_steps: 400               # Total simulation steps
     max_steps_per_task: 35             # Steps per individual task
     timeout_seconds: 300               # Timeout for individual actions

Evaluation Configuration
^^^^^^^^^^^^^^^^^^^^^^^^

Defines evaluation parameters and scenarios:

.. code-block:: yaml

   evaluation:
     task_type: 'independent'           # Task execution mode
     default_scenario: '00002'          # Default scenario
     
   # Parallel evaluation settings
   parallel_evaluation:
     enabled: true
     scenario_parallelism:
       max_parallel_scenarios: 5       # Maximum concurrent scenarios
       
     scenario_selection:
       mode: 'all'                      # all, range, list
       range:
         start: '00001'
         end: '01000'
       list: ['00001', '00002', '00004']

LLM Configuration
^^^^^^^^^^^^^^^^^

Configures large language model integration:

.. code-block:: yaml

   llm_config:
     model_name: "gpt-4"               # Model identifier
     temperature: 0.1                  # Sampling temperature (0.0-2.0)
     max_tokens: 2000                  # Maximum response tokens
     top_p: 1.0                        # Nucleus sampling parameter
     frequency_penalty: 0.0            # Frequency penalty (0.0-2.0)
     presence_penalty: 0.0             # Presence penalty (0.0-2.0)
     
     # API configuration
     api_key_env: "OPENAI_API_KEY"     # Environment variable name
     api_base: null                    # Custom API base URL
     timeout: 30                       # Request timeout in seconds
     max_retries: 3                    # Maximum retry attempts

Simulator Configuration
^^^^^^^^^^^^^^^^^^^^^^^

Controls core simulator behavior:

.. code-block:: yaml

   simulator:
     global_observation: false         # Whether all objects are initially visible
     explore_mode: thorough            # normal, thorough
   
   task_verification:
     enabled: true                     # Enable task verification
     mode: "step_by_step"              # step_by_step, global, disabled
     return_subtask_status: true       # Return subtask completion status

Configuration Inheritance
--------------------------

Configurations can extend other configurations using the ``extends`` keyword:

.. code-block:: yaml

   # specialized_config.yaml
   extends: "base_config"
   
   # Override specific settings
   agent_config:
     max_history: 50                   # Override base setting
     
   # Add new settings
   custom_setting:
     value: "specialized"

This allows you to:

- Create base configurations with common settings
- Override specific values in derived configurations
- Maintain consistency across different scenarios
- Reduce duplication in configuration files

Environment Variables
---------------------

Configuration files support environment variable substitution:

.. code-block:: yaml

   llm_config:
     api_key_env: "${OPENAI_API_KEY}"   # Direct substitution
     model_name: "${MODEL_NAME:-gpt-4}" # With default value
     max_tokens: "${MAX_TOKENS:2000}"   # Integer with default

Set environment variables before running:

.. code-block:: bash

   export OPENAI_API_KEY="your-api-key"
   export MODEL_NAME="gpt-4-turbo"
   export MAX_TOKENS="4000"

Task Filtering Configuration
----------------------------

You can filter tasks based on various criteria:

.. code-block:: yaml

   parallel_evaluation:
     scenario_selection:
       task_filter:
         # Filter by task categories
         categories:
           - "direct_command"
           - "attribute_reasoning"
           - "tool_use"
         
         # Filter by agent count
         agent_count: "single"          # single, multi, all

Available task categories:

- ``direct_command``: Simple command-following tasks
- ``attribute_reasoning``: Tasks requiring reasoning about object properties
- ``tool_use``: Tasks involving tool manipulation
- ``spatial_reasoning``: Tasks requiring spatial understanding
- ``compound_reasoning``: Complex multi-step reasoning tasks
- ``explicit_collaboration``: Tasks requiring explicit agent coordination
- ``implicit_collaboration``: Tasks with implicit coordination requirements
- ``compound_collaboration``: Complex collaborative tasks

Data Generation Configuration
-----------------------------

Configuration for automated data generation:

.. code-block:: yaml

   # data_generation/test_dataset_config.yaml
   source:
     data_dir: "data/data-all"          # Source data directory
     task_subdir: "task"
     scene_subdir: "scene"
   
   output:
     output_dir: "data/eval/single-independent"
     task_subdir: "task" 
     scene_subdir: "scene"
   
   task_filter:
     agent_mode: "single"               # single, multi, all
     task_categories:
       - "direct_command"
       - "attribute_reasoning"
     count_per_category: 200            # Target count per category
   
   agent_selection:
     strategy: "max_weight"             # max_weight, first, random
   
   scene_processing:
     create_scene_links: true           # Create symlinks vs copy files

Configuration Validation
-------------------------

The system automatically validates configuration files and will report errors for:

- **Missing required fields**
- **Invalid data types** 
- **Unknown configuration keys**
- **Invalid value ranges**
- **Circular inheritance dependencies**

Example validation error:

.. code-block:: text

   ConfigurationError: Invalid configuration in 'agent_config.max_history'
   Expected: int >= 1
   Got: 0
   File: config/my_config.yaml, line 15

Best Practices
--------------

**Organization**:

- Use the ``extends`` mechanism to avoid duplication
- Group related settings in logical sections
- Use descriptive names for custom configurations

**Security**:

- Never commit API keys or sensitive information
- Use environment variables for secrets
- Set appropriate file permissions on configuration files

**Documentation**:

- Comment configuration files extensively
- Document any non-obvious setting choices
- Maintain a changelog for configuration changes

**Testing**:

- Test configuration changes with small scenarios first
- Validate configurations before deploying
- Keep backup copies of working configurations

Common Configuration Patterns
------------------------------

**Development vs Production**:

.. code-block:: yaml

   # development_config.yaml
   extends: "base_config"
   
   logging:
     level: "DEBUG"
     show_llm_details: true
   
   execution:
     max_total_steps: 50              # Shorter for quick testing
   
   llm_config:
     temperature: 0.0                 # Deterministic for debugging

.. code-block:: yaml

   # production_config.yaml  
   extends: "base_config"
   
   logging:
     level: "INFO"
     show_llm_details: false
   
   execution:
     max_total_steps: 400
   
   llm_config:
     temperature: 0.1

**Model Comparison**:

.. code-block:: yaml

   # gpt4_config.yaml
   extends: "base_config"
   llm_config:
     model_name: "gpt-4"
     temperature: 0.1

.. code-block:: yaml

   # claude_config.yaml
   extends: "base_config"
   llm_config:
     model_name: "claude-3-sonnet"
     temperature: 0.1
     api_key_env: "ANTHROPIC_API_KEY"

Troubleshooting
---------------

**Configuration not loading**:

- Check YAML syntax with ``python -c "import yaml; yaml.safe_load(open('config.yaml'))"``)
- Verify file paths are correct
- Ensure proper indentation (spaces, not tabs)

**Invalid settings**:

- Check configuration documentation for valid values
- Look for typos in configuration keys
- Verify data types match expectations

**Environment variables not working**:

- Confirm environment variables are set: ``echo $VARIABLE_NAME``
- Use proper syntax: ``${VARIABLE_NAME}`` or ``${VARIABLE_NAME:-default}``
- Check for shell escaping issues

For more troubleshooting tips, see :doc:`troubleshooting`.

Next Steps
----------

- Explore :doc:`examples/index` for configuration examples
- Learn about :doc:`simulator/configuration` for simulator-specific settings
- See :doc:`user_guide/index` for advanced configuration techniques 