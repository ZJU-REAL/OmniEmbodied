OmniSimulator API Reference
============================

This section provides comprehensive API documentation for the OmniSimulator text-based simulation engine.

.. toctree::
   :maxdepth: 2

Core Engine
-----------

SimulationEngine
^^^^^^^^^^^^^^^^

.. autoclass:: OmniSimulator.core.engine.SimulationEngine
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

   .. method:: __init__(config=None)

      Initialize the simulation engine with optional configuration.

      :param config: Configuration dictionary or None for defaults
      :type config: dict or None

   .. method:: initialize_with_task(task_file)

      Initialize simulation with a specific task file.

      :param task_file: Path to task JSON file
      :type task_file: str
      :returns: True if initialization successful
      :rtype: bool

   .. method:: process_command(command)

      Process a text command and return the result.

      :param command: Natural language command
      :type command: str
      :returns: Command execution result
      :rtype: dict

Environment Management
-----------------------

EnvironmentManager
^^^^^^^^^^^^^^^^^^

.. autoclass:: OmniSimulator.environment.environment_manager.EnvironmentManager
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

   .. method:: get_room(room_id)

      Retrieve room information by ID.

      :param room_id: Unique room identifier
      :type room_id: str
      :returns: Room object or None if not found
      :rtype: Room or None

Room
^^^^

.. autoclass:: OmniSimulator.environment.room.Room
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

   .. attribute:: room_id
      :type: str

      Unique identifier for the room.

   .. attribute:: name
      :type: str

      Human-readable room name.

   .. method:: get_objects_in_room(room_id)

      Get all objects currently in the specified room.

      :param room_id: Room identifier
      :type room_id: str
      :returns: List of objects in the room
      :rtype: list

   .. method:: move_object(object_id, target_location)

      Move an object to a new location.

      :param object_id: Object to move
      :type object_id: str
      :param target_location: Destination location
      :type target_location: str
      :returns: True if move successful
      :rtype: bool

Action System
-------------

ActionManager
^^^^^^^^^^^^^

.. autoclass:: OmniSimulator.action.action_manager.ActionManager
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

   .. method:: register_action(action_class)

      Register a new action class with the system.

      :param action_class: Action class to register
      :type action_class: class

   .. method:: execute_action(agent, action_type, **kwargs)

      Execute an action for the specified agent.

      :param agent: Agent performing the action
      :type agent: Agent
      :param action_type: Type of action to perform
      :type action_type: str
      :returns: Action execution result
      :rtype: dict

   .. method:: validate_action(agent, action_type, **kwargs)

      Validate if an action can be performed.

      :param agent: Agent attempting the action
      :type agent: Agent
      :param action_type: Type of action to validate
      :type action_type: str
      :returns: Validation result
      :rtype: dict

BaseAction
^^^^^^^^^^

.. autoclass:: OmniSimulator.action.actions.base_action.BaseAction
   :members:
   :undoc-members:
   :show-inheritance:

   .. method:: validate()
      :abstractmethod:

      Validate if the action can be performed.

      :returns: True if action is valid
      :rtype: bool

   .. method:: execute()
      :abstractmethod:

      Execute the action.

      :returns: Action execution result
      :rtype: dict

Action Types
^^^^^^^^^^^^

Basic Actions
"""""""""""""

.. autoclass:: OmniSimulator.action.actions.basic_actions.GotoAction
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: OmniSimulator.action.actions.basic_actions.GrabAction  
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: OmniSimulator.action.actions.basic_actions.PlaceAction
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: OmniSimulator.action.actions.attribute_actions.AttributeAction
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: OmniSimulator.action.actions.basic_actions.LookAction
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: OmniSimulator.action.actions.basic_actions.ExploreAction
   :members:
   :undoc-members:
   :show-inheritance:

Agent System
------------

Agent
^^^^^

.. autoclass:: OmniSimulator.agent.agent.Agent
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

   .. method:: __init__(agent_id, name, location_id)

      Initialize a new agent.

      :param agent_id: Unique agent identifier
      :type agent_id: str
      :param name: Human-readable agent name
      :type name: str
      :param location_id: Initial location
      :type location_id: str

   .. attribute:: location_id
      :type: str

      Current location of the agent.

   .. attribute:: inventory
      :type: list

      List of objects currently carried by the agent.

   .. method:: can_grab(object_id)

      Check if the agent can grab a specific object.

      :param object_id: Object to check
      :type object_id: str
      :returns: True if object can be grabbed
      :rtype: bool

   .. method:: can_carry(object_id)

      Check if the agent can carry a specific object.

      :param object_id: Object to check
      :type object_id: str
      :returns: True if object can be carried
      :rtype: bool

AgentManager
^^^^^^^^^^^^

.. autoclass:: OmniSimulator.agent.agent_manager.AgentManager
   :members:
   :undoc-members:
   :show-inheritance:

   .. method:: get_agent(agent_id)

      Retrieve an agent by ID.

      :param agent_id: Agent identifier
      :type agent_id: str
      :returns: Agent object or None
      :rtype: Agent or None

   .. method:: get_all_agents()

      Get all active agents.

      :returns: List of all agents
      :rtype: list

Utilities
---------

DataLoader
^^^^^^^^^^

.. autoclass:: OmniSimulator.utils.data_loader.DataLoader
   :members:
   :undoc-members:
   :show-inheritance:

   .. method:: load_task(task_file)

      Load task data from file.

      :param task_file: Path to task file
      :type task_file: str
      :returns: Task data dictionary
      :rtype: dict

Task Verifier
^^^^^^^^^^^^^

.. automodule:: OmniSimulator.utils.task_verifier
   :members:
   :undoc-members:

.. autoclass:: OmniSimulator.utils.task_verifier.TaskVerifier
   :members:
   :undoc-members:
   :show-inheritance:

Core Types and Enums
--------------------

ObjectType
^^^^^^^^^^

.. autoclass:: OmniSimulator.core.enums.ObjectType
   :members:
   :undoc-members:

ActionType
^^^^^^^^^^

.. autoclass:: OmniSimulator.core.enums.ActionType
   :members:
   :undoc-members:

ActionStatus
^^^^^^^^^^^^

.. autoclass:: OmniSimulator.core.enums.ActionStatus
   :members:
   :undoc-members:

Usage Examples
--------------

Basic Simulation Setup
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from OmniSimulator.core.engine import SimulationEngine
   
   # Initialize simulation engine
   engine = SimulationEngine()
   
   # Load a task
   success = engine.initialize_with_task("path/to/task.json")
   
   if success:
       # Process commands
       result = engine.process_command("go to living room")
       print(result)

Agent Interaction
^^^^^^^^^^^^^^^^^

.. code-block:: python

   from OmniSimulator.agent.agent import Agent
   from OmniSimulator.core.engine import SimulationEngine
   
   # Create simulation
   engine = SimulationEngine()
   
   # Create an agent
   agent = Agent(agent_id="agent_1", name="Assistant", location_id="living_room")
   
   # Check agent capabilities
   can_grab = agent.can_grab("cup")
   can_carry = agent.can_carry("table")
   
   print(f"Agent location: {agent.location_id}")
   print(f"Agent inventory: {agent.inventory}")

Action Execution
^^^^^^^^^^^^^^^^

.. code-block:: python

   from OmniSimulator.action.action_manager import ActionManager
   from OmniSimulator.core.enums import ActionType
   
   # Initialize action manager
   action_manager = ActionManager()
   
   # Validate and execute action
   validation = action_manager.validate_action(
       agent=agent,
       action_type="goto",
       target="kitchen"
   )
   
   if validation.get('valid'):
       result = action_manager.execute_action(
           agent=agent,
           action_type="goto",
           target="kitchen"
       )
       print(f"Action result: {result}")

Environment Queries
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from OmniSimulator.environment.environment_manager import EnvironmentManager
   
   # Initialize environment manager
   env_manager = EnvironmentManager()
   
   # Get room information
   room = env_manager.get_room("living_room")
   objects = env_manager.get_objects_in_room("living_room")
   
   print(f"Room: {room.name}")
   print(f"Objects in room: {[obj.name for obj in objects]}")

For comprehensive tutorials and examples, see :doc:`../examples/basic_simulation`. 