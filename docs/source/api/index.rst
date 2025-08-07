API Reference
=============

This section provides complete API documentation for all OmniEmbodied components.

.. toctree::
   :maxdepth: 2

   framework
   omnisimulator
   data_structures

Core Modules
------------

.. autosummary::
   :toctree: _autosummary
   :template: module.rst

   OmniSimulator
   evaluation
   core
   llm
   modes
   config
   data_generation

Quick API Overview
------------------

**Core Simulation**:

.. autosummary::
   :toctree: _autosummary

   OmniSimulator.core.engine.SimulationEngine
   OmniSimulator.agent.agent.Agent

**Environment and Actions**:

.. autosummary::
   :toctree: _autosummary

   OmniSimulator.environment.environment_manager.EnvironmentManager
   OmniSimulator.action.action_manager.ActionManager
   OmniSimulator.environment.room.Room

**Evaluation Framework**:

.. autosummary::
   :toctree: _autosummary

   evaluation.evaluation_manager.EvaluationManager
   evaluation.task_executor.TaskExecutor

**Agent Modes**:

.. autosummary::
   :toctree: _autosummary

   modes.single_agent.llm_agent.LLMAgent
   modes.centralized.centralized_agent.CentralizedAgent

**Configuration Management**:

.. autosummary::
   :toctree: _autosummary

   config.config_manager.ConfigManager

**LLM Integration**:

.. autosummary::
   :toctree: _autosummary



Usage Examples
--------------

Evaluation
^^^^^^^^^^

.. code-block:: python

   from evaluation.evaluation_interface import EvaluationInterface

   # Run evaluation
   result = EvaluationInterface.run_evaluation(
       config_file="single_agent_config",
       agent_type="single",
       task_type="independent",
       scenario_selection={
           "mode": "range",
           "range": {"start": "00001", "end": "00010"}
       }
   )

   print(f"Success rate: {result['overall_summary']['success_rate']:.2%}")

Basic Simulation
^^^^^^^^^^^^^^^^

.. code-block:: python

   from OmniSimulator.core.engine import SimulationEngine

   # Initialize simulation
   engine = SimulationEngine(config_file="simulator_config")
   engine.initialize_with_task(task_file="example_task.json")

   # Process commands
   result = engine.process_command("go to living room")
   print(result)

Custom Agent
^^^^^^^^^^^^

.. code-block:: python

   from modes.single_agent.llm_agent import LLMAgent
   from OmniSimulator.core.engine import SimulationEngine

   # Create simulation
   simulator = SimulationEngine()
   
   # Create agent
   agent = LLMAgent(
       simulator=simulator,
       agent_id="agent_1", 
       config={"model": "gpt-4"}
   )

   # Agent reasoning step
   step_result = agent.decide_action()
   print(step_result) 