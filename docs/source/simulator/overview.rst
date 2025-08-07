Simulator Overview
==================

OmniSimulator is a comprehensive simulation engine designed for embodied AI research. It provides realistic environments where intelligent agents can perform complex tasks requiring perception, reasoning, and action.

Core Concepts
-------------

Environment Model
^^^^^^^^^^^^^^^^^

OmniSimulator uses a **room-based environment model** where:

- **Rooms** represent distinct spaces with defined boundaries
- **Objects** have properties, states, and locations within rooms
- **Agents** can move between rooms and interact with objects
- **Spatial relationships** define object positions and accessibility

.. code-block:: python

   # Example environment structure
   {
     "rooms": {
       "living_room": {
         "objects": ["sofa", "tv", "coffee_table"],
         "connections": ["kitchen", "hallway"]
       },
       "kitchen": {
         "objects": ["refrigerator", "stove", "sink"],
         "connections": ["living_room"]
       }
     }
   }

Agent-Environment Interaction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Agents interact with the environment through a **structured action interface**:

1. **Observation**: Agents perceive their environment and receive state information
2. **Planning**: Agents process observations and plan their next actions  
3. **Action Execution**: The simulator executes actions and updates the world state
4. **Feedback**: Agents receive feedback about action success and environmental changes

.. mermaid::

   graph LR
       A[Agent] -->|Action| S[Simulator]
       S -->|Observation| A
       S -->|Updates| E[Environment]
       E -->|State| S

State Management
^^^^^^^^^^^^^^^^

The simulator maintains comprehensive state information:

**Environment State**:
- Object locations and properties
- Room connections and layouts
- Agent positions and inventories

**Agent State**:
- Current location and orientation
- Inventory contents
- Action history and memory
- Task progress and objectives

**Task State**:
- Subtask completion status
- Goal conditions and requirements
- Success/failure criteria

Action System
-------------

Actions are the primary interface between agents and the environment. OmniSimulator supports several categories of actions:

Basic Movement
^^^^^^^^^^^^^^

.. code-block:: python

   # Movement actions
   agent.execute_action("go", {"target": "kitchen"})
   agent.execute_action("approach", {"target": "refrigerator"})

Object Manipulation  
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Manipulation actions
   agent.execute_action("take", {"target": "apple"})
   agent.execute_action("place", {"target": "apple", "location": "table"})
   agent.execute_action("open", {"target": "refrigerator"})

Observation and Inspection
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Observation actions
   agent.execute_action("look_around")
   agent.execute_action("examine", {"target": "book"})
   agent.execute_action("inventory")

Communication (Multi-agent)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Communication actions
   agent.execute_action("tell", {
       "target": "agent_2", 
       "message": "I found the key in the drawer"
   })

Task Verification
-----------------

OmniSimulator includes a sophisticated task verification system that:

**Tracks Progress**:
- Monitors subtask completion in real-time
- Provides feedback on task success/failure
- Maintains detailed execution logs

**Validates Actions**:
- Checks action preconditions before execution
- Ensures physical constraints are respected
- Handles error conditions gracefully

**Supports Different Modes**:
- ``step_by_step``: Continuous monitoring and feedback
- ``global``: End-of-task verification only
- ``disabled``: No automatic verification

Multi-Agent Support
--------------------

OmniSimulator natively supports multiple agents operating in the same environment:

**Shared Environment**:
- All agents operate in the same world state
- Actions by one agent affect the environment for all agents
- Object locations and states are globally consistent

**Agent Coordination**:
- Agents can communicate through explicit messaging
- Shared observations of environmental changes
- Coordination primitives for collaborative tasks

**Conflict Resolution**:
- Actions that would conflict are handled gracefully
- Resource contention (e.g., same object) is managed
- Fair scheduling of agent actions

Performance and Scalability
----------------------------

The simulator is designed for efficient operation:

**Optimized State Updates**:
- Incremental state changes rather than full world updates
- Efficient spatial indexing for object queries
- Lazy evaluation of complex computations

**Memory Management**:
- Configurable history length to control memory usage
- Efficient storage of action traces and state changes
- Garbage collection of unused state information

**Parallelization Support**:
- Thread-safe operations for concurrent agent execution
- Parallel scenario execution for batch evaluation
- Distributed simulation capabilities (future feature)

Extension Points
----------------

OmniSimulator is designed to be extensible:

**Custom Actions**:
- Define new action types with custom logic
- Implement domain-specific behaviors
- Add validation rules and preconditions

**Custom Objects**:
- Create new object types with unique properties
- Define interaction rules and state transitions
- Implement specialized object behaviors

**Custom Environments**:
- Design new room layouts and configurations
- Add environmental dynamics and changes
- Implement domain-specific constraints

**Custom Agents**:
- Integrate different AI architectures
- Implement custom decision-making algorithms
- Add specialized perception and planning modules

For detailed information on extending the simulator, see :doc:`../developer/extending`.

Configuration
-------------

The simulator behavior is controlled through configuration files:

.. code-block:: yaml

   # Basic simulator configuration
   simulator:
     global_observation: false  # Whether all objects are initially visible
     explore_mode: thorough     # Exploration behavior (normal/thorough)
   
   task_verification:
     enabled: true              # Enable task completion checking
     mode: "step_by_step"       # Verification mode
     return_subtask_status: true # Return progress information
   
   logging:
     level: "INFO"              # Logging verbosity
     log_actions: true          # Log all agent actions
     log_state_changes: true    # Log environment state changes

See :doc:`configuration` for complete configuration options.

Next Steps
----------

To learn more about specific components:

- :doc:`architecture` - Detailed system architecture
- :doc:`environments` - Environment and room management
- :doc:`actions` - Complete action reference
- :doc:`objects` - Object system and properties
- :doc:`agents` - Agent interfaces and integration
- :doc:`task_verification` - Task completion verification

For practical examples, see :doc:`../examples/index`. 