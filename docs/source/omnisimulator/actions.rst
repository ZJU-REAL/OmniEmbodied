Action System
=============

The action system in OmniSimulator provides a comprehensive framework for agent interactions with the environment. It handles action parsing, validation, execution, and state management for both single and multi-agent scenarios.

.. toctree::
   :maxdepth: 2

Overview
--------

The action system is designed around object-oriented principles with clear separation of concerns:

- **Action Management**: Central coordination of all action types
- **Action Validation**: Ensures actions are physically and logically possible
- **Action Execution**: Modifies environment state based on agent actions
- **Multi-Agent Coordination**: Handles collaborative and corporate actions

Core Components
---------------

Action Manager
^^^^^^^^^^^^^^

The ``ActionManager`` serves as the central hub for all action operations:

**Key Responsibilities**:

- Parse action commands and create action objects
- Validate actions against current world state
- Execute actions and update environment
- Manage corporate (collaborative) action states
- Register and manage custom action types

.. code-block:: python

   from OmniSimulator.action.action_manager import ActionManager

   # Initialize with core managers
   action_manager = ActionManager(
       world_state=world_state,
       env_manager=env_manager,
       agent_manager=agent_manager
   )

   # Execute an action
   result = action_manager.execute_action(
       agent_id="agent_001",
       action_command="GRAB red_apple"
   )

   if result.success:
       print(f"Action executed: {result.message}")
   else:
       print(f"Action failed: {result.error_message}")

Action Types
^^^^^^^^^^^^

OmniSimulator supports multiple categories of actions:

**Basic Movement Actions**:

- ``GOTO``: Move agent to a specific location
- ``EXPLORE``: Systematic exploration of rooms and areas

**Object Manipulation**:

- ``GRAB``: Pick up objects from the environment
- ``PLACE``: Put down objects in specific locations
- ``LOOK``: Examine objects and get detailed information

**Collaborative Actions**:

- ``CORP_GRAB``: Coordinated object pickup requiring multiple agents
- ``CORP_GOTO``: Synchronized movement of multiple agents
- ``CORP_PLACE``: Collaborative object placement

**Attribute-Based Actions**:

- Dynamic actions based on object properties (clean, heat, cool, etc.)
- Tool-based actions requiring specific equipment
- Context-sensitive actions that adapt to object types

Basic Actions
^^^^^^^^^^^^^

**GOTO Action**:

Moves agents between rooms and to specific locations within rooms.

.. code-block:: python

   # Move to a room
   result = action_manager.execute_action(
       agent_id="explorer",
       action_command="GOTO kitchen"
   )

   # Move to specific location in room
   result = action_manager.execute_action(
       agent_id="explorer", 
       action_command="GOTO kitchen_table"
   )

**GRAB Action**:

Allows agents to pick up objects from the environment.

.. code-block:: python

   # Grab object by name
   result = action_manager.execute_action(
       agent_id="collector",
       action_command="GRAB red_apple"
   )

   # Grab from specific location
   result = action_manager.execute_action(
       agent_id="collector",
       action_command="GRAB apple FROM kitchen_table"
   )

**PLACE Action**:

Places objects from agent inventory into the environment.

.. code-block:: python

   # Place object at location
   result = action_manager.execute_action(
       agent_id="organizer",
       action_command="PLACE red_apple ON kitchen_table"
   )

   # Place in container
   result = action_manager.execute_action(
       agent_id="organizer",
       action_command="PLACE apple IN fruit_basket"
   )

**LOOK Action**:

Provides detailed information about objects and locations.

.. code-block:: python

   # Look at specific object
   result = action_manager.execute_action(
       agent_id="investigator",
       action_command="LOOK red_apple"
   )

   # Look around current room
   result = action_manager.execute_action(
       agent_id="investigator",
       action_command="LOOK"
   )

**EXPLORE Action**:

Systematic exploration of areas to discover objects and spatial relationships.

.. code-block:: python

   # Explore current room
   result = action_manager.execute_action(
       agent_id="scout",
       action_command="EXPLORE"
   )

   # Explore specific area
   result = action_manager.execute_action(
       agent_id="scout",
       action_command="EXPLORE kitchen_counter"
   )

Collaborative Actions
^^^^^^^^^^^^^^^^^^^^

Corporate actions enable multi-agent coordination for tasks requiring teamwork.

**Corporate GRAB**:

Coordinated pickup of heavy or large objects requiring multiple agents.

.. code-block:: python

   # Initiate corporate grab (first agent)
   result = action_manager.execute_action(
       agent_id="worker_1",
       action_command="CORP_GRAB heavy_sofa"
   )

   # Join corporate grab (second agent) 
   result = action_manager.execute_action(
       agent_id="worker_2",
       action_command="CORP_GRAB heavy_sofa"
   )

**Corporate GOTO**:

Synchronized movement ensuring agents move together.

.. code-block:: python

   # Coordinate movement between agents
   result = action_manager.execute_action(
       agent_id="leader",
       action_command="CORP_GOTO living_room WITH worker_2"
   )

**Corporate PLACE**:

Collaborative placement of objects requiring coordination.

.. code-block:: python

   # Place heavy object with coordination
   result = action_manager.execute_action(
       agent_id="mover_1",
       action_command="CORP_PLACE heavy_sofa ON rug"
   )

Attribute-Based Actions
^^^^^^^^^^^^^^^^^^^^^^

Dynamic actions that adapt based on object properties and available tools.

**Tool-Required Actions**:

Actions that need specific equipment to execute.

.. code-block:: python

   # Clean action (requires cleaning tool)
   result = action_manager.execute_action(
       agent_id="cleaner",
       action_command="CLEAN dirty_plate"
   )

   # Heat action (requires heating device)
   result = action_manager.execute_action(
       agent_id="cook", 
       action_command="HEAT cold_soup"
   )

**Context-Sensitive Actions**:

Actions that behave differently based on object types.

.. code-block:: python

   # Action adapts to object properties
   result = action_manager.execute_action(
       agent_id="helper",
       action_command="ACTIVATE electronic_device"
   )

Action Validation
-----------------

The action system performs comprehensive validation before execution:

**Spatial Validation**:

- Agent must be in correct location for action
- Target objects must be accessible
- Spatial relationships must allow the action

**Physical Validation**:

- Objects must have appropriate properties
- Agent capabilities must match action requirements
- Physical constraints (size, weight) must be satisfied

**State Validation**:

- Object states must allow the action
- Prerequisites must be met
- Conflicts with other actions resolved

.. code-block:: python

   # Validation occurs automatically
   result = action_manager.execute_action(
       agent_id="agent_001",
       action_command="GRAB heavy_anvil"  # May fail if agent lacks strength
   )

   if not result.success:
       print(f"Validation failed: {result.error_message}")
       print(f"Error type: {result.error_type}")

Action Results and Feedback
---------------------------

Every action returns comprehensive feedback:

**Success Results**:

.. code-block:: python

   class ActionResult:
       success: bool = True
       message: str = "Action completed successfully"
       new_state: Dict = {...}           # Updated world state
       observations: List[str] = [...]   # What the agent observes
       changes: Dict = {...}             # Specific state changes

**Failure Results**:

.. code-block:: python

   class ActionResult:
       success: bool = False
       error_message: str = "Cannot grab object: not in same room"
       error_type: str = "SPATIAL_ERROR"
       suggestions: List[str] = ["Move to kitchen first"]

Dynamic Action Registration
---------------------------

Register custom actions for specific scenarios:

**Scene-Based Registration**:

Actions are registered based on scene capabilities and object types.

.. code-block:: python

   # Register tool-based actions for specific agents
   ActionManager.register_ability_action("CLEAN", "cleaning_robot")
   ActionManager.register_ability_action("REPAIR", "maintenance_bot")

**Custom Action Development**:

Create new action types by extending the base action class:

.. code-block:: python

   from OmniSimulator.action.actions.base_action import BaseAction

   class CustomAction(BaseAction):
       def __init__(self, action_command, world_state, env_manager):
           super().__init__(action_command, world_state, env_manager)
           
       def is_valid(self) -> bool:
           # Implement validation logic
           return self._validate_custom_requirements()
           
       def execute(self) -> ActionResult:
           # Implement execution logic
           return self._perform_custom_action()

Configuration and Customization
-------------------------------

**Action Configuration**:

Control action behavior through YAML configuration:

.. code-block:: yaml

   actions:
     basic_actions:
       grab:
         max_weight: 10       # Maximum weight for single agent
         requires_tools: false
       
     corporate_actions:
       corp_grab:
         min_agents: 2        # Minimum agents required
         max_weight: 50       # Weight limit for corporate actions
         
     attribute_actions:
       clean:
         requires_tool: true
         tool_types: ["cleaning_cloth", "sponge"]

**Performance Tuning**:

Optimize action execution for large simulations:

.. code-block:: yaml

   action_performance:
     parallel_validation: true     # Validate multiple actions in parallel
     cache_validations: true       # Cache validation results
     max_action_history: 100       # Limit stored action history

Error Handling and Debugging
-----------------------------

**Common Error Types**:

- ``SPATIAL_ERROR``: Agent or object location issues
- ``PHYSICAL_ERROR``: Physical constraint violations  
- ``STATE_ERROR``: Invalid object or agent states
- ``PERMISSION_ERROR``: Action not allowed for agent
- ``TOOL_ERROR``: Required tools not available

**Debugging Tools**:

.. code-block:: python

   # Enable detailed action logging
   action_manager.enable_debug_logging()

   # Get action execution trace
   trace = action_manager.get_last_action_trace()
   
   # Validate environment state before actions
   validation_result = action_manager.validate_world_state()

**Action Replay**:

Record and replay action sequences for testing:

.. code-block:: python

   # Record action sequence
   action_manager.start_recording()
   # ... execute actions ...
   recording = action_manager.stop_recording()
   
   # Replay actions
   replay_result = action_manager.replay_actions(recording)

Multi-Agent Coordination
------------------------

**Corporate Action Lifecycle**:

1. **Initiation**: First agent starts corporate action
2. **Recruitment**: Additional agents join the action
3. **Validation**: Check all agents meet requirements
4. **Execution**: Coordinate simultaneous execution
5. **Completion**: Update all participating agents

**Conflict Resolution**:

Handle competing actions between agents:

- **Priority Systems**: Assign action priorities
- **Mutual Exclusion**: Prevent conflicting simultaneous actions
- **Negotiation Protocols**: Allow agents to resolve conflicts

**Communication Integration**:

Corporate actions integrate with agent communication:

.. code-block:: python

   # Actions can trigger inter-agent communication
   result = action_manager.execute_action(
       agent_id="coordinator",
       action_command="CORP_GRAB table WITH helper_bot"
   )
   
   # Automatically sends coordination messages between agents

Best Practices
--------------

**Action Design**:

- Keep actions atomic and well-defined
- Provide clear error messages and suggestions
- Design actions to be composable and reusable
- Consider physical plausibility in all actions

**Performance Optimization**:

- Cache expensive validation operations
- Use lazy evaluation for complex state checks
- Batch similar actions when possible
- Profile action execution for bottlenecks

**Error Recovery**:

- Implement graceful failure modes
- Provide alternative action suggestions
- Support action rollback for critical failures
- Log sufficient detail for debugging

**Multi-Agent Considerations**:

- Design actions to scale with agent count
- Avoid global state dependencies where possible
- Implement proper synchronization for corporate actions
- Consider communication overhead in distributed scenarios

API Reference
-------------

For complete API documentation, see:

- :class:`OmniSimulator.action.action_manager.ActionManager`
- :class:`OmniSimulator.action.actions.base_action.BaseAction`
- :module:`OmniSimulator.action.actions.basic_actions`
- :module:`OmniSimulator.action.actions.corporate_actions`
- :module:`OmniSimulator.action.actions.attribute_actions` 