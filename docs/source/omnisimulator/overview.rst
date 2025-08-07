OmniSimulator Overview
======================

OmniSimulator is a powerful, text-based simulation engine designed specifically for embodied AI research. It provides a realistic environment where intelligent agents can perceive, reason, and act in complex scenarios.

Architecture Overview
---------------------

OmniSimulator follows a modular, layered architecture:

.. code-block:: text

   ┌─────────────────────────────────────────────┐
   │         Simulation Engine (Core)            │
   │  ┌─────────────────────────────────────────┐ │
   │  │        Task Verification System         │ │
   │  └─────────────────────────────────────────┘ │
   │  ┌─────────────┐ ┌─────────────┐ ┌────────┐ │
   │  │ Environment │ │   Action    │ │ Agent  │ │
   │  │  Manager    │ │  Manager    │ │   API  │ │
   │  └─────────────┘ └─────────────┘ └────────┘ │
   │  ┌─────────────────────────────────────────┐ │
   │  │           State Management              │ │
   │  └─────────────────────────────────────────┘ │
   └─────────────────────────────────────────────┘

Core Design Principles
----------------------

**Realism and Consistency**
   The simulator maintains physical consistency, ensuring that agent actions have realistic consequences and the environment behaves predictably.

**Extensibility**
   Modular design allows easy addition of new action types, object behaviors, and environment features without modifying core systems.

**Multi-Agent Support**
   Native support for multiple agents operating simultaneously in shared environments with proper conflict resolution.

**Task-Oriented**
   Built-in task definition and verification systems for goal-oriented agent evaluation and training.

Environment Model
-----------------

Room-Based World Structure
^^^^^^^^^^^^^^^^^^^^^^^^^^

OmniSimulator uses a room-based environment model where:

- **Rooms** are discrete spaces with defined properties and connections
- **Objects** exist within rooms and can have containment relationships
- **Agents** navigate between rooms and interact with objects
- **Spatial relationships** define accessibility and positioning

.. code-block:: json

   {
     "rooms": {
       "living_room": {
         "description": "A comfortable living space with furniture",
         "connections": ["kitchen", "hallway"],
         "objects": ["sofa", "coffee_table", "tv", "remote"]
       },
       "kitchen": {
         "description": "A modern kitchen with appliances",
         "connections": ["living_room"],
         "objects": ["refrigerator", "stove", "sink", "counter"]
       }
     }
   }

Object System
^^^^^^^^^^^^^

Objects in OmniSimulator have rich properties and states:

**Static Properties:**
- Physical attributes (size, weight, material)
- Visual properties (color, shape, brand)
- Functional capabilities (can_open, can_contain)

**Dynamic States:**
- Current status (open/closed, on/off, clean/dirty)
- Location and containment relationships
- Accessibility and visibility

.. code-block:: json

   {
     "object_id": "refrigerator_1",
     "name": "refrigerator",
     "properties": {
       "size": "large",
       "color": "white",
       "brand": "Samsung",
       "can_open": true,
       "can_contain": true
     },
     "states": {
       "is_open": false,
       "is_on": true,
       "temperature": "cold",
       "contents": ["apple", "milk", "cheese"]
     },
     "location": "kitchen"
   }

Action System
-------------

Comprehensive Action Framework
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

OmniSimulator provides a rich set of actions organized into categories:

**Movement Actions:**
- ``go <room>`` - Move to a different room
- ``approach <object>`` - Move closer to an object

**Manipulation Actions:**
- ``take <object>`` - Pick up an object
- ``place <object> <location>`` - Put object down or in container
- ``open <object>`` - Open doors, containers, etc.
- ``close <object>`` - Close opened objects

**Observation Actions:**
- ``look_around`` - Observe current environment
- ``examine <object>`` - Inspect object details
- ``inventory`` - Check carried items

**Communication Actions:** (Multi-agent)
- ``tell <agent> <message>`` - Send message to specific agent
- ``broadcast <message>`` - Message all agents

Action Validation and Execution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Every action goes through a validation and execution pipeline:

1. **Precondition Checking**: Verify action is possible given current state
2. **Parameter Validation**: Ensure all required parameters are provided
3. **Physics Constraints**: Check physical feasibility (size, weight, etc.)
4. **State Updates**: Modify environment and agent states
5. **Feedback Generation**: Provide detailed success/failure information

.. code-block:: python

   # Example action execution
   result = engine.execute_action(
       agent_id="agent_1",
       action_type="take",
       parameters={"target": "red_apple"}
   )
   
   if result.success:
       print(f"Success: {result.message}")
       # State automatically updated
   else:
       print(f"Failed: {result.error}")
       print(f"Suggestions: {result.suggestions}")

Agent Integration
-----------------

Flexible Agent Interface
^^^^^^^^^^^^^^^^^^^^^^^^^

OmniSimulator provides clean APIs for integrating various agent architectures:

**Observation Interface:**
- Rich environmental descriptions
- Configurable detail levels
- Dynamic state updates

**Action Interface:**
- Unified action execution
- Comprehensive error handling
- Action history tracking

**State Management:**
- Agent inventory tracking
- Location and status monitoring
- Memory and history management

.. code-block:: python

   from OmniSimulator.agent.agent import Agent
   
   # Create agent
   agent = Agent("explorer", initial_room="entrance")
   
   # Get observations
   obs = agent.get_observations()
   print(f"Current room: {obs['current_room']}")
   print(f"Visible objects: {obs['visible_objects']}")
   print(f"Inventory: {obs['inventory']}")
   
   # Execute action
   result = agent.execute_action("examine", {"target": "mysterious_box"})

Multi-Agent Coordination
^^^^^^^^^^^^^^^^^^^^^^^^^

OmniSimulator handles multiple agents with:

- **Shared Environment**: All agents see consistent world state
- **Action Scheduling**: Fair and conflict-free action execution
- **Communication**: Message passing between agents
- **Conflict Resolution**: Handling competing actions gracefully

Task Verification System
-------------------------

Built-in Task Management
^^^^^^^^^^^^^^^^^^^^^^^^^

OmniSimulator includes sophisticated task verification:

**Task Definition:**
- Clear goal specifications
- Subtask decomposition
- Success criteria definition

**Progress Tracking:**
- Real-time completion monitoring
- Subtask status updates
- Detailed progress reports

**Verification Modes:**
- ``step_by_step``: Continuous monitoring with feedback
- ``global``: Final state verification only
- ``disabled``: No automatic verification

.. code-block:: yaml

   # Task definition example
   task:
     id: "cooking_task"
     description: "Prepare a simple meal"
     subtasks:
       - id: "gather_ingredients"
         condition: "agent has [bread, cheese, tomato]"
       - id: "use_stove"
         condition: "stove.state == 'on'"
       - id: "complete_cooking"
         condition: "sandwich in agent.inventory"

Performance Characteristics
---------------------------

Scalability and Efficiency
^^^^^^^^^^^^^^^^^^^^^^^^^^^

OmniSimulator is designed for research-scale simulations:

**Performance Metrics:**
- Support for 10+ concurrent agents
- 100+ objects per environment
- 1000+ actions per simulation
- Sub-second action execution

**Memory Management:**
- Efficient state representation
- Configurable history retention
- Garbage collection of unused objects

**Optimization Features:**
- Incremental state updates
- Lazy evaluation of complex queries
- Caching of frequently accessed data

Configuration and Customization
-------------------------------

Flexible Configuration System
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

OmniSimulator behavior is controlled through YAML configuration:

.. code-block:: yaml

   # Basic configuration
   simulator:
     global_observation: false    # All objects visible initially
     explore_mode: thorough       # Exploration behavior
     physics_enabled: true        # Enable physics constraints
   
   task_verification:
     enabled: true               # Enable task checking
     mode: "step_by_step"       # Verification mode
     return_subtask_status: true # Return progress info
   
   logging:
     level: "INFO"              # Logging verbosity
     log_actions: true          # Log agent actions
     log_state_changes: true    # Log world changes

Extension Points
^^^^^^^^^^^^^^^^

OmniSimulator supports customization through:

**Custom Actions:** Add domain-specific behaviors
**Custom Objects:** Define new object types with unique properties
**Custom Environments:** Create specialized world configurations
**Custom Verification:** Implement domain-specific task checking

Integration with OmniEmbodied Framework
---------------------------------------

OmniSimulator serves as the foundation for the OmniEmbodied Framework, providing:

- **Simulation Engine**: Core simulation capabilities
- **Agent Interface**: Clean APIs for agent integration
- **Task System**: Built-in task definition and verification
- **Data Generation**: Foundation for creating training scenarios

The framework extends OmniSimulator with:
- LLM-based agents
- Evaluation benchmarks
- Multi-agent coordination
- Automated data generation

Use Cases and Applications
--------------------------

Research Applications
^^^^^^^^^^^^^^^^^^^^^

**Embodied AI Research:**
- Agent perception and reasoning
- Planning and decision-making
- Learning from interaction

**Multi-Agent Systems:**
- Coordination and collaboration
- Communication protocols
- Distributed problem-solving

**Human-AI Interaction:**
- Natural language interfaces
- Task-oriented dialogue
- Instructional following

Educational Applications
^^^^^^^^^^^^^^^^^^^^^^^^

**AI Education:**
- Demonstrate AI concepts interactively
- Hands-on learning with realistic scenarios
- Progressive difficulty for skill building

**Research Training:**
- Platform for student projects
- Standardized evaluation environment
- Reproducible experimental conditions

Getting Started
---------------

To begin using OmniSimulator:

1. **Installation**: Follow the :doc:`../installation` guide
2. **Basic Usage**: Try the :doc:`../examples/basic_simulation` tutorial
3. **API Reference**: Explore the :doc:`api_reference` documentation
4. **Advanced Topics**: Learn about :doc:`../developer/extending` OmniSimulator

Next Steps
----------

Learn more about specific OmniSimulator components:

- :doc:`environments` - Environment system details
- :doc:`actions` - Action system and custom actions
- :doc:`agents` - Agent interfaces and integration
- :doc:`objects` - Object system and properties
- :doc:`task_verification` - Task verification system

For practical usage:
- :doc:`../examples/omnisimulator_tutorial` - Comprehensive tutorial
- :doc:`../developer/extending` - Customization guide
- :doc:`../api/omnisimulator` - Complete API reference 