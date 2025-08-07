OmniSimulator
=============

OmniSimulator is the core simulation engine of OmniEmbodied, providing a rich and flexible environment for embodied AI agents. It handles environment simulation, agent-environment interactions, action execution, and state management.

.. toctree::
   :maxdepth: 2

   overview

Overview
--------

OmniSimulator provides:

🌍 **Rich Environments**
   Detailed room-based environments with realistic object interactions and spatial relationships.

🎯 **Action System** 
   Comprehensive action framework supporting movement, manipulation, observation, and communication.

🤖 **Agent Management**
   Multi-agent support with flexible agent architectures and coordination mechanisms.

✅ **Task Verification**
   Built-in task completion verification with step-by-step progress tracking.

🔧 **Extensible Design**
   Modular architecture allowing easy customization and extension of components.

Key Features
------------

Environment Simulation
^^^^^^^^^^^^^^^^^^^^^^^

- **Room-based layouts** with realistic spatial constraints
- **Object persistence** and state tracking across interactions  
- **Dynamic discovery** system for progressive environment exploration
- **Multi-agent coordination** with shared and private observations

Action Framework
^^^^^^^^^^^^^^^^

- **Basic actions**: Movement (go, approach), manipulation (take, place)
- **Observation actions**: Look, examine, inventory management
- **Communication actions**: Agent-to-agent messaging and coordination
- **Tool usage**: Specialized actions for different object types

Agent Integration
^^^^^^^^^^^^^^^^^

- **Flexible agent interfaces** supporting various AI architectures
- **State management** with configurable history and memory systems
- **Error handling** and graceful failure recovery
- **Performance monitoring** and detailed logging

Quick Start
-----------

Here's a minimal example of using OmniSimulator:

.. code-block:: python

   from OmniSimulator.core.engine import SimulationEngine
   from OmniSimulator.agent.agent import Agent

   # Initialize the simulation engine
   engine = SimulationEngine()

   # Load a scenario
   scenario_data = engine.load_scenario("00001")
   
   # Create and register an agent
   agent = Agent(agent_id="agent_1", agent_config=config)
   engine.register_agent(agent)

   # Run simulation
   results = engine.run_simulation(max_steps=100)

For more detailed examples, see :doc:`../examples/index`.

Configuration
-------------

OmniSimulator behavior is controlled through YAML configuration files:

.. code-block:: yaml

   # simulator_config.yaml
   simulator:
     global_observation: false
   
   task_verification:
     enabled: true
     mode: "step_by_step"
     return_subtask_status: true

See :doc:`configuration` for complete configuration options.

Components
----------

The simulator consists of several key components:

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Component
     - Description
   * - :doc:`environments`
     - Environment and room management, object placement and discovery
   * - :doc:`actions`
     - Action execution, validation, and effects
   * - :doc:`objects`  
     - Object definitions, properties, and interactions
   * - :doc:`agents`
     - Agent interfaces, state management, and coordination
   * - :doc:`task_verification`
     - Task completion checking and progress tracking

Advanced Topics
---------------

For advanced usage and customization:

- :doc:`../developer/extending` - Creating custom components
- :doc:`../developer/architecture` - Understanding the system design  
- :doc:`../api/simulator` - Complete API reference
- :doc:`../troubleshooting` - Common issues and solutions

The following sections provide detailed documentation for each component of OmniSimulator. 