Quick Start
===========

This guide will help you run your first evaluation with OmniEmbodied in just a few minutes.

Prerequisites
-------------

Make sure you have completed the :doc:`installation` process before proceeding.

Configuration Setup
--------------------

Before running evaluations, you need to configure the LLM service and observation mode. OmniEmbodied supports various LLM providers including DeepSeek, OpenAI API and local vLLM deployments.

Configure LLM Service
^^^^^^^^^^^^^^^^^^^^^^

1. **Edit the LLM configuration file**:

   .. code-block:: bash

      vim config/baseline/llm_config.yaml  # Edit the LLM configuration

2. **For DeepSeek API** (Recommended for quick start):

   .. code-block:: yaml

      # config/baseline/llm_config.yaml
      api:
        provider: "deepseekv3"
        providers:
          deepseekv3:
            api_key: "your-api-key-here"  # Replace with your actual API key
            model: "deepseek-chat"
            temperature: 0.3
            max_tokens: 2048

3. **For vLLM Server Deployment** (For local models):

   .. code-block:: yaml

      # config/baseline/llm_config.yaml
      provider: "custom"
      model_name: "your-model-name"  # e.g., "Qwen2.5-7B-Instruct"
      
      api_config:
        base_url: "http://localhost:8000/v1"  # vLLM server endpoint
        api_key: "EMPTY"  # vLLM doesn't require real API key
        timeout: 60
        max_retries: 3
      
      model_config:
        temperature: 0.1
        max_tokens: 2000
        top_p: 0.9

3. **Start vLLM Server** (if using local deployment):

   .. code-block:: bash

      # Install vLLM (if not already installed)
      pip install vllm

      # Start vLLM server with your model
      python -m vllm.entrypoints.openai.api_server \
          --model /path/to/your/model \
          --host 0.0.0.0 \
          --port 8000

4. **For OpenAI API** (alternative):

   .. code-block:: yaml

      # config/baseline/llm_config.yaml
      provider: "openai"
      model_name: "gpt-4"
      
      api_config:
        api_key: "${OPENAI_API_KEY}"  # Set as environment variable
        timeout: 30
        max_retries: 3
      
      model_config:
        temperature: 0.1
        max_tokens: 2000

   Set your API key:

   .. code-block:: bash

      export OPENAI_API_KEY="your-api-key-here"

Global Observation Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For scripts ending with ``-wg.sh`` (with global observation), you need to configure:

.. code-block:: yaml

   # config/simulator/simulator_config.yaml
   global_observation: true  # Enable global observation mode

This enables agents to have complete visibility of the environment from the start.

Running Your First Evaluation
------------------------------

OmniEmbodied provides ready-to-use shell scripts for different evaluation scenarios.

Quick Start Example
^^^^^^^^^^^^^^^^^^^

Run a basic evaluation with DeepSeek:

.. code-block:: bash

   # Run basic evaluation (without global observation)
   bash scripts/deepseekv3-wo.sh

Single Agent Evaluation
^^^^^^^^^^^^^^^^^^^^^^^^

Run single-agent tasks with different models:

.. code-block:: bash

   # Run Qwen 7B single-agent evaluation (with global observation)
   bash scripts/qwen7b-wg.sh

   # Run Qwen 7B single-agent evaluation (without global observation)  
   bash scripts/qwen7b-wo.sh

The script will:

- Load the configured LLM service
- Run evaluation on single-agent scenarios (00001 to 00800)
- Save results with timestamp to ``output/`` directory
- Generate detailed logs and trajectory files

Multi-Agent Evaluation
^^^^^^^^^^^^^^^^^^^^^^^

Run multi-agent collaborative tasks:

.. code-block:: bash

   # Run DeepSeek R1 multi-agent evaluation
   bash deepseekr1-wg.sh

   # Run Llama 8B multi-agent evaluation
   bash llama8b-wg.sh

Understanding Script Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each script contains key configuration parameters:

.. code-block:: bash

   #!/bin/bash
   # Example: qwen7b-wg.sh
   
   # Model configuration
   MODEL_NAME="qwen7b"
   DATASET_TYPE="single"          # single or multi agent
   GUIDANCE="wg"                  # wg (with guidance) or wo (without guidance)
   
   # Evaluation range
   START_SCENARIO="00001"
   END_SCENARIO="00800"
   
   # Parallel processing
   MAX_PARALLEL=5                 # Number of concurrent scenarios
   
   # Configuration file
   CONFIG_FILE="single_agent_config"  # ConfigManager will resolve the full path

**Key Parameters:**

- ``MODEL_NAME``: Identifier for the model being evaluated
- ``DATASET_TYPE``: ``single`` for single-agent, ``multi`` for multi-agent tasks
- ``GUIDANCE``: ``wg`` includes task guidance, ``wo`` tests pure reasoning
- ``START_SCENARIO/END_SCENARIO``: Range of scenarios to evaluate
- ``MAX_PARALLEL``: Controls concurrent evaluation processes

Monitoring Evaluation Progress
------------------------------

During evaluation, you'll see output like:

.. code-block:: text

   [INFO] Starting evaluation: qwen7b_single_00001_to_00800_wg
   [INFO] Configuration loaded: single_agent_config (resolved to config/baseline/single_agent_config.yaml)
   [INFO] LLM service connected: http://localhost:8000/v1
   [INFO] Processing scenario 00001/00800...
   [INFO] Task: "Find the red apple in the kitchen"
   [INFO] Agent completed task in 12 steps - SUCCESS
   [INFO] Processing scenario 00002/00800...
   ...
   [INFO] Evaluation completed. Results saved to: 
   output/20241220_143052_qwen7b_single_00001_to_00800_wg.json

Understanding Results
---------------------

The evaluation generates several output files:

**Result Files:**
- ``{timestamp}_{model}_{type}_{range}_{guidance}.json`` - Main results
- ``trajectory_logs/`` - Detailed step-by-step agent actions
- ``error_logs/`` - Failed scenarios and error analysis

**Key Metrics:**
- **Success Rate**: Percentage of successfully completed tasks
- **Average Steps**: Mean number of actions per task
- **Task Categories**: Performance breakdown by task type
- **Error Analysis**: Common failure modes and patterns

**Sample Results:**

.. code-block:: json

   {
     "model_name": "qwen7b",
     "dataset_type": "single", 
     "guidance": "wg",
     "total_scenarios": 800,
     "completed_scenarios": 782,
     "success_rate": 0.847,
     "average_steps": 8.3,
     "task_breakdown": {
       "direct_command": {"success_rate": 0.92, "count": 200},
       "attribute_reasoning": {"success_rate": 0.85, "count": 200},
       "tool_use": {"success_rate": 0.78, "count": 200},
       "compound_reasoning": {"success_rate": 0.73, "count": 200}
     }
   }

Common Configuration Options
----------------------------

You can customize evaluations by modifying configuration files:

**Agent Behavior** (configured via ``single_agent_config``):

.. code-block:: yaml

   agent_config:
     max_history: 20              # Conversation history length
     max_steps_per_task: 35       # Maximum actions per task
     
   environment_description:
     detail_level: 'full'         # full, basic, minimal
     show_object_properties: true # Include object attributes
     update_frequency: 0          # Update every step

**Execution Control**:

.. code-block:: yaml

   execution:
     max_total_steps: 400         # Total simulation steps
     timeout_seconds: 300         # Per-action timeout
     
   parallel_evaluation:
     max_parallel_scenarios: 5    # Concurrent evaluations

**Task Filtering**:

.. code-block:: yaml

   scenario_selection:
     task_filter:
       categories:                # Select specific task types
         - "direct_command" 
         - "attribute_reasoning"

Troubleshooting
---------------

**LLM Service Connection Issues:**

.. code-block:: bash

   # Test vLLM server connectivity
   curl -X POST http://localhost:8000/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d '{"model":"your-model","messages":[{"role":"user","content":"Hello"}]}'

**Common Issues:**

- **"Connection refused"**: vLLM server not running or wrong port
- **"Model not found"**: Check model name in configuration matches vLLM server
- **"Out of memory"**: Reduce ``max_parallel_scenarios`` or use smaller model
- **Slow evaluation**: Check network latency to LLM service

**Debug Mode:**

Enable detailed logging for troubleshooting:

.. code-block:: yaml

   logging:
     level: "DEBUG"
     show_llm_details: true

Next Steps
----------

Once you've run your first evaluation:

**Explore Results:**
- Analyze performance by task category
- Compare different models and configurations
- Review trajectory logs for agent behavior insights

**Advanced Usage:**
- :doc:`user_guide/evaluation_framework` - Systematic evaluation strategies
- :doc:`user_guide/configuration` - Advanced configuration patterns
- :doc:`examples/index` - More evaluation examples

**Customize Evaluations:**
- :doc:`developer/extending` - Create custom agents
- :doc:`api/omnisimulator` - Use simulation API directly
- :doc:`user_guide/task_types` - Understand task categories

The quick start focuses on getting evaluations running quickly. For deeper understanding of the system components, see the detailed documentation sections. 