Basic Simulation Examples
==========================

This section provides step-by-step examples for getting started with OmniEmbodied simulations. These examples progress from simple single-agent scenarios to more complex multi-agent interactions.

Example 1: Your First Simulation
---------------------------------

Let's start with the simplest possible simulation using OmniSimulator directly.

**Setup:**

.. code-block:: python

   from OmniSimulator.core.engine import SimulationEngine
   from OmniSimulator.agent.agent import Agent

   # Initialize the simulation engine
   engine = SimulationEngine()
   
   print("✅ Simulation engine initialized")

**Load a Simple Scenario:**

.. code-block:: python

   # Load a basic kitchen scenario
   scenario_data = {
       "rooms": {
           "kitchen": {
               "description": "A simple kitchen",
               "objects": ["table", "apple", "knife"],
               "connections": []
           }
       },
       "agents": {
           "agent_1": {
               "initial_room": "kitchen",
               "inventory": []
           }
       }
   }
   
   # Load the scenario
   engine.load_scenario_from_data(scenario_data)
   print("✅ Scenario loaded")

**Create and Register Agent:**

.. code-block:: python

   # Create a simple agent
   agent = Agent(agent_id="agent_1", initial_room="kitchen")
   engine.register_agent(agent)
   
   print(f"✅ Agent {agent.agent_id} registered in {agent.get_current_room().name}")

**Execute Basic Actions:**

.. code-block:: python

   # Look around the environment
   result = engine.execute_action("agent_1", "look_around")
   if result.success:
       print("Agent observations:")
       print(f"  Current room: {result.new_state['current_room']}")
       print(f"  Visible objects: {result.new_state['visible_objects']}")
   
   # Take an object
   result = engine.execute_action("agent_1", "take", {"target": "apple"})
   if result.success:
       print("✅ Successfully took the apple")
   else:
       print(f"❌ Failed to take apple: {result.error}")
   
   # Check inventory
   result = engine.execute_action("agent_1", "inventory")
   print(f"Agent inventory: {result.new_state['inventory']}")

**Expected Output:**

.. code-block:: text

   ✅ Simulation engine initialized
   ✅ Scenario loaded
   ✅ Agent agent_1 registered in kitchen
   Agent observations:
     Current room: kitchen
     Visible objects: ['table', 'apple', 'knife']
   ✅ Successfully took the apple
   Agent inventory: ['apple']

Example 2: Using Pre-built Scenarios
-------------------------------------

Now let's use one of the included scenario files.

**Load from File:**

.. code-block:: python

   from OmniSimulator.core.engine import SimulationEngine
   import json

   # Initialize engine
   engine = SimulationEngine()

   # Load a pre-built scenario
   scenario_path = "data/eval/single-independent/scene/00001_scene.json"
   engine.load_scenario(scenario_path)

   # Also load the corresponding task
   task_path = "data/eval/single-independent/task/00001_task.json"
   with open(task_path, 'r') as f:
       task_data = json.load(f)
   
   print(f"Loaded scenario: {scenario_path}")
   print(f"Task description: {task_data.get('description', 'No description')}")

**Register Agent and Execute Task:**

.. code-block:: python

   # Register agent from scenario
   agent_config = task_data['agents'][0]  # Get first agent
   agent = Agent(
       agent_id=agent_config['agent_id'],
       initial_room=agent_config['initial_room']
   )
   engine.register_agent(agent)

   # Execute task steps
   max_steps = 20
   step_count = 0
   
   while step_count < max_steps:
       # Get current observations
       result = engine.execute_action(agent.agent_id, "look_around")
       
       if not result.success:
           print(f"Failed to get observations: {result.error}")
           break
       
       observations = result.new_state
       print(f"\nStep {step_count + 1}:")
       print(f"  Room: {observations['current_room']}")
       print(f"  Objects: {observations['visible_objects']}")
       
       # Simple strategy: try to take first available object
       if observations['visible_objects']:
           target = observations['visible_objects'][0]
           result = engine.execute_action(agent.agent_id, "take", {"target": target})
           
           if result.success:
               print(f"  ✅ Took {target}")
           else:
               print(f"  ❌ Failed to take {target}: {result.error}")
       else:
           print("  No objects visible")
           break
       
       step_count += 1

Example 3: Framework-Based Evaluation
--------------------------------------

Now let's use the OmniEmbodied Framework for more sophisticated evaluation.

**Simple Evaluation Setup:**

.. code-block:: python

   from evaluation.evaluation_interface import EvaluationInterface

   # Use the evaluation interface for testing
   print("✅ Evaluation interface ready")

**Run Single Scenario:**

.. code-block:: python

   # Evaluate a single scenario using the interface
   try:
       result = EvaluationInterface.run_evaluation(
           config_file="single_agent_config",
           agent_type="single",
           task_type="independent",
           scenario_selection={
               "dataset_type": "single", 
               "scenario_range": {"start": "00001", "end": "00001"}
           }
       )
       
       print(f"\n📊 Evaluation Results:")
       print(f"  Success rate: {result.get('success_rate', 0):.2%}")
       print(f"  Total scenarios: {result.get('total_scenarios', 0)}")
       
   except Exception as e:
       print(f"❌ Evaluation failed: {str(e)}")

**Run Multiple Scenarios:**

.. code-block:: python

   # Evaluate multiple scenarios using the interface  
   print(f"\n🔄 Evaluating multiple scenarios...")
   
   try:
       result = EvaluationInterface.run_evaluation(
           config_file="single_agent_config",
           agent_type="single",
           task_type="independent",
           scenario_selection={
               "dataset_type": "single",
               "scenario_range": {"start": "00001", "end": "00003"}
           }
       )
       
       print(f"\n📈 Batch Results:")
       print(f"  Success rate: {result.get('success_rate', 0):.2%}")
       print(f"  Total scenarios: {result.get('total_scenarios', 0)}")
   
   except Exception as e:
       print(f"❌ Batch evaluation failed: {str(e)}")

Example 4: Configuration Customization
---------------------------------------

Let's explore different configuration options for customized evaluation.

**Create Custom Configuration:**

.. code-block:: python

   # Create custom evaluation configuration
   custom_config = {
       "agent_config": {
           "agent_class": "modes.single_agent.llm_agent.LLMAgent",
           "max_history": 15,
           "max_steps_per_task": 25
       },
       
       "llm_config": {
           "provider": "vllm",
           "model_name": "Qwen2.5-7B-Instruct",
           "endpoint": "http://localhost:8000/v1",
           "temperature": 0.1,
           "max_tokens": 1000
       },
       
       "evaluation": {
           "dataset_type": "single",
           "task_filter": {
               "categories": ["direct_command", "attribute_reasoning"]
           }
       },
       
       "logging": {
           "level": "DEBUG",
           "show_llm_details": False
       }
   }

**Save and Use Custom Configuration:**

.. code-block:: python

   import yaml
   from pathlib import Path

   # Save custom configuration
   config_path = Path("custom_eval_config.yaml")
   with open(config_path, 'w') as f:
       yaml.dump(custom_config, f, default_flow_style=False)
   
   print(f"✅ Saved configuration to {config_path}")

   # Use custom configuration
   config_manager = ConfigManager()
   loaded_config = config_manager.load_config(config_path.stem)
   
   evaluator = EvaluationManager(loaded_config)
   print("✅ Evaluator initialized with custom config")

Example 5: Multi-Agent Collaboration
-------------------------------------

Let's set up a simple multi-agent scenario.

**Multi-Agent Setup:**

.. code-block:: python

   from modes.centralized.centralized_agent import CentralizedAgent

   # Load multi-agent configuration
   config = config_manager.load_config("centralized_config")
   
   # Create centralized agent system
   coordinator = CentralizedAgent(
       coordinator_id="mission_control",
       worker_count=2,
       config=config["agent_config"]
   )
   
   print("✅ Multi-agent system initialized")
   print(f"  Coordinator: {coordinator.coordinator_id}")
   print(f"  Workers: {len(coordinator.workers)}")

**Collaborative Task Execution:**

.. code-block:: python

   # Define a collaborative task
   collaborative_task = {
       "description": "Clean the living room together",
       "subtasks": [
           {"agent": "worker_1", "task": "vacuum the floor"},
           {"agent": "worker_2", "task": "dust the furniture"}
       ]
   }

   # Execute collaborative task
   print(f"\n🤝 Starting collaborative task:")
   print(f"  {collaborative_task['description']}")

   try:
       # Plan task distribution
       plan = coordinator.plan_task_distribution(collaborative_task['description'])
       print(f"  📋 Task plan created: {len(plan['subtasks'])} subtasks")
       
       # Execute coordination
       result = coordinator.coordinate_execution()
       
       if result.coordination_success:
           print("  ✅ Collaboration successful!")
           for worker_id, worker_result in result.worker_results.items():
               status = "✅" if worker_result['success'] else "❌"
               print(f"    {worker_id}: {status}")
       else:
           print(f"  ❌ Collaboration failed: {result.coordination_message}")
   
   except Exception as e:
       print(f"❌ Collaboration error: {str(e)}")

Example 6: Error Handling and Debugging
----------------------------------------

Let's explore proper error handling and debugging techniques.

**Robust Evaluation with Error Handling:**

.. code-block:: python

   import logging
   from typing import List, Dict, Any

   def robust_evaluation(scenario_ids: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
       """Run evaluation with comprehensive error handling."""
       
       # Setup logging
       logging.basicConfig(level=logging.INFO)
       logger = logging.getLogger(__name__)
       
       results = {
           'successful_scenarios': [],
           'failed_scenarios': [],
           'errors': {},
           'summary': {}
       }
       
       try:
           evaluator = EvaluationManager(config)
           logger.info(f"Starting evaluation of {len(scenario_ids)} scenarios")
           
           for scenario_id in scenario_ids:
               try:
                   # Evaluate single scenario
                   scenario_results = evaluator.evaluate_scenarios([scenario_id])
                   
                   if scenario_results.detailed_results[0]['success']:
                       results['successful_scenarios'].append(scenario_id)
                       logger.info(f"✅ {scenario_id}: SUCCESS")
                   else:
                       results['failed_scenarios'].append(scenario_id)
                       logger.warning(f"❌ {scenario_id}: FAILED")
               
               except Exception as scenario_error:
                   results['failed_scenarios'].append(scenario_id)
                   results['errors'][scenario_id] = str(scenario_error)
                   logger.error(f"💥 {scenario_id}: ERROR - {scenario_error}")
           
           # Calculate summary
           total = len(scenario_ids)
           successful = len(results['successful_scenarios'])
           results['summary'] = {
               'total_scenarios': total,
               'successful': successful,
               'failed': total - successful,
               'success_rate': successful / total if total > 0 else 0.0
           }
           
       except Exception as e:
           logger.error(f"💥 Evaluation setup failed: {str(e)}")
           results['setup_error'] = str(e)
       
       return results

   # Run robust evaluation
   test_scenarios = ["00001", "00002", "invalid_scenario", "00003"]
   config = config_manager.load_config("single_agent_config")

   results = robust_evaluation(test_scenarios, config)

   print("\n📊 Robust Evaluation Results:")
   print(f"  Total scenarios: {results['summary']['total_scenarios']}")
   print(f"  Successful: {len(results['successful_scenarios'])}")
   print(f"  Failed: {len(results['failed_scenarios'])}")
   print(f"  Success rate: {results['summary']['success_rate']:.2%}")

   if results['errors']:
       print("\n❌ Errors encountered:")
       for scenario, error in results['errors'].items():
           print(f"  {scenario}: {error}")

Example 7: Performance Monitoring
----------------------------------

Let's add performance monitoring to our simulations.

**Performance-Monitored Evaluation:**

.. code-block:: python

   import time
   import psutil
   import os
   from contextlib import contextmanager

   @contextmanager
   def performance_monitor():
       """Context manager for monitoring performance."""
       process = psutil.Process(os.getpid())
       
       start_time = time.time()
       start_memory = process.memory_info().rss / 1024 / 1024  # MB
       
       print(f"🔍 Starting performance monitoring...")
       print(f"  Initial memory: {start_memory:.1f} MB")
       
       try:
           yield
       finally:
           end_time = time.time()
           end_memory = process.memory_info().rss / 1024 / 1024  # MB
           
           duration = end_time - start_time
           memory_delta = end_memory - start_memory
           
           print(f"\n📈 Performance Summary:")
           print(f"  Duration: {duration:.2f} seconds")
           print(f"  Memory usage: {end_memory:.1f} MB ({memory_delta:+.1f} MB)")
           print(f"  CPU usage: {process.cpu_percent():.1f}%")

   # Use performance monitoring
   with performance_monitor():
       # Run evaluation
       config = config_manager.load_config("single_agent_config")
       evaluator = EvaluationManager(config)
       
       results = evaluator.evaluate_scenarios(["00001", "00002", "00003"])
       print(f"Evaluated {results.total_scenarios} scenarios")

Next Steps
----------

Now that you've learned the basics, explore more advanced topics:

**More Examples:**
- :doc:`configuration_examples` - Advanced configuration patterns
- :doc:`custom_agents` - Building custom agents
- :doc:`evaluation_workflows` - Complex evaluation setups

**Detailed Guides:**
- :doc:`../user_guide/task_types` - Understanding task categories
- :doc:`../user_guide/evaluation_framework` - Comprehensive evaluation
- :doc:`../framework/index` - Framework components overview

**API Reference:**
- :doc:`../api/omnisimulator` - OmniSimulator API
- :doc:`../api/framework` - Framework API
- :doc:`../api/config` - Configuration reference

**Troubleshooting:**
If you encounter issues:
1. Check the :doc:`../troubleshooting` guide
2. Enable debug logging: ``logging.basicConfig(level=logging.DEBUG)``
3. Verify your configuration files are valid YAML
4. Ensure all required dependencies are installed

Happy simulating! 🚀 