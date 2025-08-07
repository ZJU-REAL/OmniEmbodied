Data Structures Reference
==========================

This section documents the data structures returned by various API calls in the OmniEmbodied Framework.

Evaluation Results
------------------

EvaluationInterface.run_evaluation() Response
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``EvaluationInterface.run_evaluation()`` method returns a structured dictionary with the following format:

.. code-block:: python

   {
       "runinfo": {
           "run_id": str,              # Unique run identifier
           "model_name": str,          # Model name (e.g., "vllm:Qwen2.5-7B-Instruct")
           "agent_type": str,          # Agent type ("single" or "multi")
           "task_mode": str,           # Task mode ("independent", "sequential", "combined")
           "start_time": str,          # ISO format timestamp
           "end_time": str,            # ISO format timestamp
           "total_scenarios": int,     # Total number of scenarios evaluated
           "config_file": str,         # Configuration file used
           "status": str,              # Status ("completed", "failed", "interrupted")
           "duration_seconds": float,  # Total evaluation duration
           "note": str                 # Optional additional notes
       },
       "overall_summary": {
           "success_rate": float,      # Overall success rate (0.0 to 1.0)
           "total_scenarios": int,     # Total scenarios processed
           "successful_scenarios": int, # Number of successful scenarios
           "failed_scenarios": int,    # Number of failed scenarios
           "average_steps": float,     # Average steps per scenario
           "average_duration": float,  # Average duration per scenario (seconds)
           "total_llm_calls": int,     # Total LLM API calls made
           "error_distribution": {     # Error type distribution
               "timeout": int,
               "max_steps": int,
               "action_failed": int,
               "other": int
           }
       },
       "task_category_statistics": {   # Performance by task category
           "direct_command": {
               "success_rate": float,
               "scenario_count": int,
               "average_steps": float
           },
           "attribute_reasoning": {
               "success_rate": float, 
               "scenario_count": int,
               "average_steps": float
           },
           # ... other task categories
       }
   }

**Usage Example:**

.. code-block:: python

   result = EvaluationInterface.run_evaluation(
       config_file="single_agent_config",
       agent_type="single", 
       task_type="independent",
       scenario_selection={"scenario_range": {"start": "00001", "end": "00010"}}
   )
   
   # Access run information
   print(f"Run ID: {result['runinfo']['run_id']}")
   print(f"Success Rate: {result['overall_summary']['success_rate']:.2%}")
   
   # Access task-specific performance
   for category, stats in result['task_category_statistics'].items():
       print(f"{category}: {stats['success_rate']:.2%} success rate")

Scenario Selection Configuration  
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``scenario_selection`` parameter accepts the following structure:

.. code-block:: python

   {
       "dataset_type": str,           # "single", "multi", or "mixed"
       "mode": str,                   # "all", "range", or "list"
       
       # For range mode
       "scenario_range": {
           "start": str,              # Starting scenario ID (e.g., "00001")
           "end": str                 # Ending scenario ID (e.g., "00100")
       },
       
       # For list mode
       "scenario_list": [str],        # List of specific scenario IDs
       
       # Task filtering options
       "task_filter": {
           "categories": [str],       # Task categories to include
           "difficulty_levels": [str], # Difficulty levels to include
           "exclude_scenarios": [str] # Specific scenarios to exclude
       }
   }

**Available Task Categories:**

- ``"direct_command"`` - Simple command following
- ``"attribute_reasoning"`` - Object attribute-based reasoning
- ``"tool_use"`` - Tool manipulation tasks
- ``"spatial_reasoning"`` - Spatial relationship understanding
- ``"multi_step_reasoning"`` - Complex multi-step tasks
- ``"explicit_collaboration"`` - Direct multi-agent collaboration
- ``"implicit_collaboration"`` - Indirect multi-agent coordination
- ``"compound_collaboration"`` - Complex collaborative scenarios

Agent Configuration Structures
-------------------------------

Single Agent Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   {
       "agent_config": {
           "agent_class": str,        # "modes.single_agent.llm_agent.LLMAgent"
           "max_history": int,        # Maximum conversation history length
           "max_steps_per_task": int, # Maximum steps per task
           "timeout_per_action": int, # Timeout per action (seconds)
           "retry_failed_actions": bool, # Whether to retry failed actions
       },
       
       "llm_config": {
           "mode": str,               # "api" or "vllm"
           "api": {                   # For API mode
               "provider": str,       # "openai", "anthropic", etc.
               "model": str,          # Model name
               "temperature": float,  # Generation temperature
               "max_tokens": int,     # Maximum tokens per response
               "api_key": str         # API key
           },
           "vllm": {                  # For vLLM mode
               "model": str,          # Model name or path
               "endpoint": str        # vLLM server endpoint
           }
       },
       
       "execution": {
           "max_total_steps": int,    # Maximum total steps per evaluation
           "max_steps_per_task": int, # Maximum steps per individual task
           "step_timeout": int        # Timeout per step (seconds)
       }
   }

Multi-Agent Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   {
       "agent_config": {
           "agent_class": str,        # "modes.centralized.centralized_agent.CentralizedAgent"
           "coordination_mode": str,  # "centralized" or "decentralized"
           "agent_count": int,        # Number of agents
           "communication_enabled": bool, # Enable inter-agent communication
           "shared_memory": bool      # Enable shared memory between agents
       },
       
       # Same LLM and execution configurations as single agent
       "llm_config": { ... },
       "execution": { ... }
   }

Error Handling
--------------

Exception Types
^^^^^^^^^^^^^^^

The framework raises the following custom exceptions:

**ConfigurationError**

.. code-block:: python

   class ConfigurationError(Exception):
       """Raised when configuration is invalid or incomplete."""
       pass

**EvaluationError**

.. code-block:: python

   class EvaluationError(Exception):
       """Raised when evaluation fails."""
       pass

**ScenarioNotFoundError**

.. code-block:: python

   class ScenarioNotFoundError(Exception):
       """Raised when a specified scenario cannot be found."""
       pass

Error Response Format
^^^^^^^^^^^^^^^^^^^^^

When an error occurs during evaluation, the response includes error information:

.. code-block:: python

   {
       "runinfo": {
           "status": "failed",
           "error_type": str,         # Type of error that occurred
           "error_message": str,      # Human-readable error message
           "failed_scenario": str,    # Scenario that caused failure (if applicable)
           # ... other runinfo fields
       },
       "error_details": {
           "traceback": str,          # Full error traceback (if debug enabled)
           "context": dict            # Additional context information
       }
   }

**Common Error Types:**

- ``"configuration_error"`` - Invalid or missing configuration
- ``"scenario_not_found"`` - Specified scenario file not found
- ``"llm_connection_error"`` - Cannot connect to LLM service
- ``"timeout_error"`` - Evaluation timed out
- ``"resource_error"`` - Insufficient system resources

Trajectory Data Structures
---------------------------

Individual Step Data
^^^^^^^^^^^^^^^^^^^^

Each step in a trajectory contains:

.. code-block:: python

   {
       "step_number": int,            # Step index (starting from 1)
       "timestamp": str,              # ISO format timestamp
       "agent_id": str,               # Agent identifier
       "action": {
           "action_type": str,        # Action name (e.g., "MOVE", "GRAB")
           "parameters": dict,        # Action parameters
           "raw_command": str         # Original command string
       },
       "observation": {
           "current_room": str,       # Current room name
           "visible_objects": [str],  # List of visible objects
           "inventory": [str],        # Agent's inventory
           "status_message": str      # Status description
       },
       "result": {
           "success": bool,           # Whether action succeeded
           "message": str,            # Result message
           "error": str               # Error message (if failed)
       },
       "llm_interaction": {           # LLM-specific data
           "prompt": str,             # Full prompt sent to LLM
           "response": str,           # LLM response
           "token_count": int,        # Tokens used
           "processing_time": float   # LLM response time
       }
   }

Complete Trajectory Structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   {
       "scenario_id": str,            # Scenario identifier
       "agent_type": str,             # Agent type used
       "task_description": str,       # Task description
       "start_time": str,             # Evaluation start time
       "end_time": str,               # Evaluation end time
       "final_status": str,           # "success", "failure", "timeout"
       "total_steps": int,            # Total steps taken
       "total_llm_calls": int,        # Total LLM API calls
       "steps": [                     # List of step data
           # ... step objects as described above
       ],
       "summary": {
           "task_completed": bool,     # Whether task was completed
           "efficiency_score": float,  # Efficiency metric (0.0 to 1.0)  
           "error_count": int,         # Number of failed actions
           "unique_actions_used": [str] # List of unique actions performed
       }
   }

Usage Examples
--------------

Working with Evaluation Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Run evaluation and process results
   result = EvaluationInterface.run_evaluation(
       config_file="single_agent_config",
       agent_type="single",
       task_type="independent", 
       scenario_selection={
           "scenario_range": {"start": "00001", "end": "00050"}
       }
   )
   
   # Extract key metrics
   runinfo = result['runinfo']
   summary = result['overall_summary']
   
   print(f"Evaluation: {runinfo['run_id']}")
   print(f"Model: {runinfo['model_name']}")
   print(f"Duration: {runinfo['duration_seconds']:.1f}s")
   print(f"Success Rate: {summary['success_rate']:.2%}")
   print(f"Average Steps: {summary['average_steps']:.1f}")
   
   # Analyze performance by task category
   for category, stats in result['task_category_statistics'].items():
       print(f"\n{category.replace('_', ' ').title()}:")
       print(f"  Success Rate: {stats['success_rate']:.2%}")
       print(f"  Scenarios: {stats['scenario_count']}")
       print(f"  Avg Steps: {stats['average_steps']:.1f}")

Error Handling Best Practices
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   try:
       result = EvaluationInterface.run_evaluation(
           config_file="single_agent_config",
           agent_type="single",
           task_type="independent",
           scenario_selection={"scenario_range": {"start": "00001", "end": "00010"}}
       )
       
       # Check if evaluation completed successfully
       if result['runinfo']['status'] == 'completed':
           print(f"Success! {result['overall_summary']['success_rate']:.2%} success rate")
       else:
           print(f"Evaluation ended with status: {result['runinfo']['status']}")
           
   except ConfigurationError as e:
       print(f"Configuration error: {e}")
       # Handle configuration issues
       
   except ScenarioNotFoundError as e:
       print(f"Scenario not found: {e}")
       # Handle missing scenarios
       
   except EvaluationError as e:
       print(f"Evaluation failed: {e}")
       # Handle evaluation failures
       
   except Exception as e:
       print(f"Unexpected error: {e}")
       # Handle other errors

See Also
--------

- :doc:`framework` - Framework API reference
- :doc:`../framework/evaluation` - Evaluation system guide
- :doc:`../examples/basic_simulation` - Usage examples 