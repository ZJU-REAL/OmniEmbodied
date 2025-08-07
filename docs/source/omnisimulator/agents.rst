Agent Interface
===============

The agent interface in OmniSimulator provides a clean, comprehensive API for integrating AI systems with the simulation environment. It handles agent state management, action execution, observation processing, and multi-agent coordination.

.. toctree::
   :maxdepth: 2

Overview
--------

The agent system is designed to support various AI architectures while providing consistent interfaces for:

- **State Management**: Track agent position, inventory, and status
- **Action Execution**: Interface with the action system
- **Observation Processing**: Receive and interpret environmental feedback
- **Multi-Agent Coordination**: Support for collaboration and communication
- **Memory Management**: Maintain action history and learned information

Core Components
---------------

Agent Class
^^^^^^^^^^^

The ``Agent`` class provides the primary interface for AI systems to interact with the simulation:

**Key Features**:

- Clean, consistent API across all agent types
- Automatic state synchronization with the simulation
- Built-in observation and feedback processing
- Support for both single-agent and multi-agent scenarios

.. code-block:: python

   from OmniSimulator.agent.agent import Agent

   # Create agent instance
   agent = Agent(
       agent_id="explorer_001",
       name="Explorer",
       location_id="kitchen"
   )

   # Get current location and inventory
   print(f"Agent location: {agent.location_id}")
   print(f"Agent inventory: {agent.inventory}")

   # Note: Action execution is typically handled by the SimulationEngine
   # rather than directly through the Agent class

Agent Manager
^^^^^^^^^^^^^

The ``AgentManager`` coordinates multiple agents within a single simulation:

- **Agent Registration**: Add and remove agents from the simulation
- **State Coordination**: Ensure consistent multi-agent states
- **Communication Routing**: Handle inter-agent messages
- **Resource Management**: Prevent agent conflicts over resources

.. code-block:: python

   from OmniSimulator.agent.agent_manager import AgentManager

   # Initialize agent manager
   agent_manager = AgentManager(world_state, env_manager)

   # Register multiple agents
   agent_manager.register_agent("worker_1", initial_room="kitchen")
   agent_manager.register_agent("worker_2", initial_room="living_room")

   # Get all active agents
   active_agents = agent_manager.get_active_agents()

Agent State Management
----------------------

Agent State Properties
^^^^^^^^^^^^^^^^^^^^^^

Each agent maintains comprehensive state information:

**Core State**:

- ``agent_id``: Unique identifier
- ``location``: Current room and position
- ``inventory``: Objects carried by the agent
- ``status``: Current activity status
- ``capabilities``: Agent abilities and constraints

**Extended State**:

- ``action_history``: Record of executed actions
- ``observations``: Current environmental perceptions
- ``memory``: Learned information and experiences
- ``goals``: Current objectives and tasks
- ``relationships``: Connections with other agents

.. code-block:: python

   # Access agent properties directly
   location = agent.location_id
   inventory = agent.inventory
   max_carry = agent.max_grasp_limit
   current_weight = agent.current_weight
   
   # Agent abilities and properties
   abilities = agent.abilities
   properties = agent.properties
   near_objects = agent.near_objects

State Synchronization
^^^^^^^^^^^^^^^^^^^^

Agent state automatically synchronizes with the simulation environment:

.. code-block:: python

   # Actions are executed through the SimulationEngine
   # Agent state is updated by the simulation system
   
   # Check if agent can grab more objects
   can_grab = agent.can_grab()
   print(f"Can grab more objects: {can_grab}")
   
   # Check carrying capacity for an object
   object_properties = {"weight": 2.5}
   can_carry, reason = agent.can_carry(object_properties)
   print(f"Can carry object: {can_carry}, Reason: {reason}")

Observation System
------------------

Environmental Perception
^^^^^^^^^^^^^^^^^^^^^^^^

Agents receive rich observational data about their environment:

**Visual Observations**:

- Objects visible in current location
- Spatial relationships and layouts
- State changes from actions
- Presence of other agents

**Action Feedback**:

- Success/failure status of actions
- Detailed results and consequences
- Error messages and suggestions
- Environmental changes caused by actions

.. code-block:: python

   # Get current observations
   observations = agent.get_observations()
   
   # Visual observations
   visible_objects = observations['visible_objects']
   room_description = observations['room_description']
   other_agents = observations['other_agents_present']
   
   # Action feedback
   last_action_result = observations['last_action_result']
   environmental_changes = observations['recent_changes']

Observation Processing
^^^^^^^^^^^^^^^^^^^^^^

The agent interface processes raw simulation data into structured observations:

.. code-block:: python

   # Raw observation processing
   def process_observations(self, raw_obs):
       processed = {
           'objects': self._categorize_objects(raw_obs['objects']),
           'spatial': self._analyze_spatial_relations(raw_obs['layout']),
           'changes': self._detect_state_changes(raw_obs['previous'], raw_obs['current'])
       }
       return processed

   # Get processed observations
   observations = agent.get_processed_observations()

Action Interface
----------------

Action Execution
^^^^^^^^^^^^^^^^

Agents can execute actions through multiple interfaces:

**Direct Action Execution**:

.. code-block:: python

   # Execute action with parameters
   result = agent.execute_action(
       action_type="GRAB",
       parameters={"target": "red_apple", "location": "kitchen_table"}
   )

   # Execute action from command string
   result = agent.execute_action_command("GRAB red_apple FROM kitchen_table")

**Batch Action Processing**:

.. code-block:: python

   # Execute multiple actions in sequence
   action_sequence = [
       "GOTO kitchen",
       "GRAB apple",
       "GOTO living_room", 
       "PLACE apple ON coffee_table"
   ]
   
   results = agent.execute_action_sequence(action_sequence)
   
   # Check if all actions succeeded
   all_success = all(result.success for result in results)

Action Validation
^^^^^^^^^^^^^^^^^

Actions are validated before execution:

.. code-block:: python

   # Validate action without executing
   validation_result = agent.validate_action("GRAB heavy_object")
   
   if not validation_result.is_valid:
       print(f"Action not valid: {validation_result.reason}")
       print(f"Suggestions: {validation_result.suggestions}")
   
   # Get available actions in current state
   available_actions = agent.get_available_actions()

Multi-Agent Features
--------------------

Agent Communication
^^^^^^^^^^^^^^^^^^^

Agents can communicate with each other through the simulation:

.. code-block:: python

   # Send message to another agent
   agent.send_message(
       target_agent_id="worker_2",
       message="I found the target object in the kitchen",
       message_type="information"
   )

   # Receive messages
   messages = agent.get_messages()
   for message in messages:
       sender = message['sender']
       content = message['content']
       timestamp = message['timestamp']

Collaborative Actions
^^^^^^^^^^^^^^^^^^^^

Support for actions requiring multiple agents:

.. code-block:: python

   # Initiate collaborative action
   result = agent.initiate_collaboration(
       action_type="CORP_GRAB",
       parameters={"target": "heavy_sofa"},
       required_agents=["worker_2"]
   )
   
   # Join collaborative action
   result = agent.join_collaboration(
       collaboration_id="corp_grab_001"
   )

Agent Coordination
^^^^^^^^^^^^^^^^^^

Coordinate with other agents to avoid conflicts:

.. code-block:: python

   # Request exclusive access to resource
   access_granted = agent.request_resource_access("kitchen_table")
   
   if access_granted:
       result = agent.execute_action("PLACE object ON kitchen_table")
       agent.release_resource_access("kitchen_table")

Integration Patterns
--------------------

Simple Agent Integration
^^^^^^^^^^^^^^^^^^^^^^^

Basic integration for rule-based or scripted agents:

.. code-block:: python

   class SimpleAgent:
       def __init__(self, agent_id):
           self.sim_agent = Agent(agent_id)
           self.goals = []
           
       def act(self):
           observations = self.sim_agent.get_observations()
           action = self.choose_action(observations)
           result = self.sim_agent.execute_action(action)
           return result
           
       def choose_action(self, observations):
           # Simple rule-based decision making
           if self.needs_exploration():
               return "EXPLORE"
           elif self.sees_target_object(observations):
               return f"GRAB {self.target_object}"
           else:
               return "LOOK"

LLM Agent Integration
^^^^^^^^^^^^^^^^^^^^

Integration pattern for language model-based agents:

.. code-block:: python

   class LLMAgent:
       def __init__(self, agent_id, llm_interface):
           self.sim_agent = Agent(agent_id)
           self.llm = llm_interface
           
       def act(self):
           # Get current state and observations
           state = self.sim_agent.get_current_state()
           observations = self.sim_agent.get_observations()
           
           # Generate action using LLM
           prompt = self.create_action_prompt(state, observations)
           llm_response = self.llm.generate(prompt)
           action = self.parse_action_from_response(llm_response)
           
           # Execute action
           result = self.sim_agent.execute_action(action)
           
           # Update agent memory
           self.update_memory(action, result)
           
           return result

Multi-Agent Coordination Patterns
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Patterns for coordinating multiple agents:

.. code-block:: python

   class CoordinatedAgentSystem:
       def __init__(self, agent_ids):
           self.agents = {
               agent_id: Agent(agent_id) 
               for agent_id in agent_ids
           }
           self.coordinator = self.agents[agent_ids[0]]  # First agent as coordinator
           
       def execute_collaborative_task(self, task):
           # Coordinator plans the task
           plan = self.coordinator.plan_collaborative_task(task)
           
           # Assign subtasks to agents
           assignments = self.assign_subtasks(plan)
           
           # Execute in coordination
           results = {}
           for agent_id, subtask in assignments.items():
               agent = self.agents[agent_id]
               results[agent_id] = agent.execute_action_sequence(subtask)
               
           return results

Configuration and Customization
-------------------------------

Agent Configuration
^^^^^^^^^^^^^^^^^^

Configure agent behavior and capabilities:

.. code-block:: yaml

   agent_config:
     capabilities:
       max_carry_weight: 10        # Maximum weight agent can carry
       movement_speed: 1.0         # Movement speed multiplier
       observation_range: 5        # Range for observing objects
       
     behavior:
       exploration_strategy: "systematic"  # How agent explores
       memory_retention: 100       # Number of actions to remember
       communication_enabled: true # Whether agent can communicate
       
     restrictions:
       forbidden_actions: []       # Actions agent cannot perform
       required_tools: []          # Tools needed for certain actions
       location_restrictions: []   # Areas agent cannot access

Performance Optimization
^^^^^^^^^^^^^^^^^^^^^^^

Optimize agent operations for large-scale simulations:

.. code-block:: yaml

   performance:
     observation_caching: true     # Cache observation processing
     action_batching: true         # Batch multiple actions
     memory_management:
       max_history_size: 1000      # Limit stored action history
       compress_old_data: true     # Compress old observations
       
     multi_agent_optimization:
       parallel_processing: true   # Process agents in parallel
       communication_batching: true # Batch inter-agent messages

Debugging and Monitoring
------------------------

Agent State Inspection
^^^^^^^^^^^^^^^^^^^^^^

Tools for debugging agent behavior:

.. code-block:: python

   # Get detailed agent state
   debug_state = agent.get_debug_state()
   
   # Inspect action history
   history = agent.get_action_history(limit=10)
   for action in history:
       print(f"{action.timestamp}: {action.command} -> {action.result}")
   
   # Monitor agent performance
   performance_stats = agent.get_performance_stats()
   print(f"Success rate: {performance_stats['success_rate']:.2%}")
   print(f"Average action time: {performance_stats['avg_action_time']:.3f}s")

Logging and Tracing
^^^^^^^^^^^^^^^^^^^

Comprehensive logging for agent activities:

.. code-block:: python

   # Enable detailed logging
   agent.enable_debug_logging(level="DEBUG")
   
   # Get execution trace
   trace = agent.get_execution_trace()
   
   # Export agent session for analysis
   session_data = agent.export_session_data()

Error Handling
--------------

Exception Management
^^^^^^^^^^^^^^^^^^^

Handle various error conditions gracefully:

.. code-block:: python

   try:
       result = agent.execute_action("GRAB non_existent_object")
   except AgentActionError as e:
       print(f"Action error: {e.message}")
       print(f"Error type: {e.error_type}")
       print(f"Suggestions: {e.suggestions}")
   except AgentStateError as e:
       print(f"State error: {e.message}")
       # Attempt to recover agent state
       agent.recover_state()

Recovery Mechanisms
^^^^^^^^^^^^^^^^^^

Automatic recovery from common errors:

.. code-block:: python

   # Configure automatic error recovery
   agent.configure_error_recovery(
       max_retries=3,
       recovery_strategies={
           "SPATIAL_ERROR": "attempt_navigation",
           "STATE_ERROR": "refresh_observations", 
           "COMMUNICATION_ERROR": "retry_with_delay"
       }
   )

Best Practices
--------------

**Agent Design**:

- Keep agent state minimal and focused
- Use observations rather than direct world state access
- Implement proper error handling for all actions
- Design agents to be stateless where possible

**Performance Optimization**:

- Cache expensive operations like pathfinding
- Batch multiple simple actions when appropriate
- Use efficient data structures for agent memory
- Monitor and profile agent performance regularly

**Multi-Agent Coordination**:

- Implement proper synchronization for shared resources
- Use communication efficiently to avoid overhead
- Design agents to handle coordination failures gracefully
- Test coordination patterns with varying agent counts

**Debugging and Maintenance**:

- Use comprehensive logging for complex agent behaviors
- Implement agent state validation and consistency checks
- Create reproducible test scenarios for agent debugging
- Monitor agent performance metrics in production

API Reference
-------------

For complete API documentation, see:

- :class:`OmniSimulator.agent.agent.Agent`
- :class:`OmniSimulator.agent.agent_manager.AgentManager`
- :module:`OmniSimulator.core.state` 