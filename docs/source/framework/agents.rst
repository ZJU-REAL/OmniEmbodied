Agent Modes
===========

The OmniEmbodied Framework provides multiple agent architectures to support different research scenarios and coordination patterns. Each mode offers distinct advantages for different types of embodied AI tasks.

.. toctree::
   :maxdepth: 2

Overview
--------

Agent modes in OmniEmbodied are designed to support various coordination patterns:

- **Single Agent Mode**: Individual agents operating independently
- **Centralized Multi-Agent Mode**: Central coordinator managing multiple worker agents
- **Decentralized Multi-Agent Mode**: Autonomous agents with peer-to-peer coordination (future)

Each mode integrates seamlessly with the evaluation system and supports all LLM providers.

Single Agent Mode
-----------------

Architecture
^^^^^^^^^^^^

The single agent mode provides a straightforward interface for individual agent tasks:

**Key Components**:

- **LLM Integration**: Direct connection to language models for decision-making
- **Action Planning**: Sequential action generation based on observations
- **Memory Management**: Conversation history and experience tracking
- **Task Execution**: Independent task completion without coordination

**Use Cases**:

- Individual task completion scenarios
- Baseline performance measurement
- Agent capability evaluation
- Simple interaction testing

Implementation
^^^^^^^^^^^^^^

The ``LLMAgent`` class provides the core single agent functionality:

.. code-block:: python

   from modes.single_agent.llm_agent import LLMAgent
   from OmniSimulator.core.engine import SimulationEngine

   # Initialize simulation environment
   simulator = SimulationEngine()
   
   # Create single agent
   agent = LLMAgent(
       simulator=simulator,
       agent_id="solo_worker",
       config=agent_config
   )
   
   # Set task
   agent.set_task("Find the red apple in the kitchen and place it on the table")
   
   # Execute steps
   while not agent.is_task_completed():
       action = agent.generate_action()
       result = agent.execute_action(action)
       
       if not result.success:
           print(f"Action failed: {result.message}")
           break

Configuration
^^^^^^^^^^^^^

Configure single agent behavior:

.. code-block:: yaml

   # single_agent_config.yaml
   agent_config:
     agent_class: "modes.single_agent.llm_agent.LLMAgent"
     max_history: 20              # Conversation history length
     
   # LLM settings
   llm_config:
     provider: "openai"
     model: "gpt-4"
     temperature: 0.1
     max_tokens: 512
     
   # Prompt configuration
   prompt_config:
     template: "single_agent_v1"  # Prompt template version
     system_prompt_key: "system_prompt"
     use_chain_of_thought: true   # Enable reasoning traces

Prompt Management
^^^^^^^^^^^^^^^^^

Single agents use specialized prompts for task execution:

.. code-block:: python

   # Agent automatically selects appropriate prompts
   agent.set_task("Clean the kitchen thoroughly")
   
   # System prompt includes:
   # - Role definition
   # - Available actions
   # - Task completion criteria
   # - Response format requirements

   # Task-specific prompts adapt to:
   # - Current environment state
   # - Action history
   # - Task progress
   # - Error recovery

Centralized Multi-Agent Mode
----------------------------

Architecture
^^^^^^^^^^^^

The centralized mode uses a single LLM to coordinate multiple agents:

**Control Structure**:

- **Central Coordinator**: Single LLM making decisions for all agents
- **Agent Proxies**: Individual agents executing coordinator commands
- **State Synchronization**: Unified world state across all agents
- **Action Coordination**: Prevents conflicts and ensures collaboration

**Advantages**:

- Consistent decision-making across agents
- Optimal resource allocation
- Reduced communication overhead
- Simplified coordination logic

.. code-block:: python

   from modes.centralized.centralized_agent import CentralizedAgent

   # Create centralized coordinator
   coordinator = CentralizedAgent(
       simulator=simulator,
       agent_id="mission_control",
       config=centralized_config
   )
   
   # Coordinator manages multiple agent proxies
   # Each proxy represents a physical agent in the simulation
   managed_agents = ["agent_1", "agent_2", "agent_3"]
   coordinator.set_managed_agents(managed_agents)

Coordination Patterns
^^^^^^^^^^^^^^^^^^^^^^

**Task Decomposition**:

The coordinator breaks complex tasks into subtasks:

.. code-block:: python

   # Example coordination decision
   coordinator.set_task("Prepare dinner for the family")
   
   # Coordinator might plan:
   # Agent 1: "Go to refrigerator and get vegetables"
   # Agent 2: "Find cooking pot in kitchen cabinet"  
   # Agent 3: "Set the dining table with plates and utensils"
   
   # Execute coordinated plan
   action = coordinator.generate_action()  # Returns multi-agent action
   result = coordinator.execute_action(action)

**Resource Management**:

Prevents conflicts and ensures efficient resource usage:

.. code-block:: python

   # Coordinator automatically handles:
   # - Agent spatial positioning
   # - Object access conflicts
   # - Tool sharing between agents
   # - Sequential vs parallel task execution

**Communication Optimization**:

Reduces inter-agent communication through centralized planning:

.. code-block:: python

   # Traditional multi-agent: Multiple communication rounds
   # Centralized: Single decision point with full information

Configuration
^^^^^^^^^^^^^

Centralized multi-agent configuration:

.. code-block:: yaml

   # centralized_config.yaml
   agent_config:
     agent_class: "modes.centralized.centralized_agent.CentralizedAgent"
     managed_agents: ["agent_1", "agent_2"]  # Agents under coordination
     coordination_strategy: "optimal"         # Planning strategy
     
   # Multi-agent specific settings
   multi_agent:
     max_agents: 3                    # Maximum agents to coordinate
     coordination_timeout: 30         # Max time for coordination decisions
     conflict_resolution: "priority"  # How to handle conflicts
     
   # Prompt settings for coordination
   prompt_config:
     template: "centralized_v1"       # Coordination-specific prompts
     include_all_agent_states: true  # Include all agent info in prompts
     action_format: "multi_agent"     # Multi-agent action format

Advanced Coordination
^^^^^^^^^^^^^^^^^^^^^

**Dynamic Task Assignment**:

.. code-block:: python

   class AdvancedCentralizedAgent(CentralizedAgent):
       def generate_action(self):
           # Analyze current state
           agent_states = self.get_all_agent_states()
           task_priorities = self.analyze_task_priorities()
           
           # Dynamic assignment based on:
           # - Agent capabilities
           # - Current positions
           # - Task urgency
           # - Resource availability
           
           return self.optimize_agent_assignments(agent_states, task_priorities)

**Performance Monitoring**:

.. code-block:: python

   # Monitor coordination effectiveness
   coordination_metrics = coordinator.get_coordination_metrics()
   
   print(f"Agent utilization: {coordination_metrics['agent_utilization']}")
   print(f"Task completion rate: {coordination_metrics['completion_rate']}")
   print(f"Coordination overhead: {coordination_metrics['overhead_time']}")

Decentralized Multi-Agent Mode (Future)
---------------------------------------

Planned Architecture
^^^^^^^^^^^^^^^^^^^^^

Future decentralized mode will support:

**Autonomous Agents**:

- Independent LLM instances for each agent
- Peer-to-peer communication protocols
- Distributed decision-making
- Emergent coordination patterns

**Communication Framework**:

- Message passing between agents
- Negotiation and consensus mechanisms
- Information sharing protocols
- Conflict resolution strategies

**Planned Features**:

.. code-block:: python

   # Future decentralized agent example
   from modes.decentralized.autonomous_agent import AutonomousAgent
   
   # Each agent has independent reasoning
   agent_1 = AutonomousAgent("worker_1", llm_config_1)
   agent_2 = AutonomousAgent("worker_2", llm_config_2)
   
   # Agents communicate directly
   agent_1.send_message(agent_2.id, "I found the target object")
   response = agent_2.receive_messages()
   
   # Distributed task planning
   joint_plan = agent_1.negotiate_plan(agent_2, shared_task)

Agent Integration Patterns
--------------------------

Custom Agent Development
^^^^^^^^^^^^^^^^^^^^^^^^^

Extend base agent classes for custom behaviors:

.. code-block:: python

   from core.base_agent import BaseAgent

   class CustomAgent(BaseAgent):
       def __init__(self, simulator, agent_id, config):
           super().__init__(simulator, agent_id, config)
           self.custom_state = {}
           
       def generate_action(self):
           # Implement custom decision logic
           observations = self.get_observations()
           return self.custom_planning_algorithm(observations)
           
       def custom_planning_algorithm(self, observations):
           # Custom planning logic
           if self.needs_exploration():
               return self.explore_strategy()
           elif self.has_clear_objective():
               return self.direct_action_strategy()
           else:
               return self.reasoning_strategy()

Hybrid Agent Systems
^^^^^^^^^^^^^^^^^^^^

Combine different agent types:

.. code-block:: python

   class HybridAgentSystem:
       def __init__(self):
           # Mix of agent types
           self.coordinator = CentralizedAgent(...)
           self.specialist = CustomAgent(...)
           self.backup = LLMAgent(...)
           
       def execute_task(self, task):
           # Use different agents for different subtasks
           if task.requires_coordination():
               return self.coordinator.execute_task(task)
           elif task.needs_specialist_knowledge():
               return self.specialist.execute_task(task)
           else:
               return self.backup.execute_task(task)

Performance Comparison
----------------------

Agent Mode Trade-offs
^^^^^^^^^^^^^^^^^^^^^

**Single Agent Mode**:

*Advantages*:
- Simple implementation and debugging
- No coordination overhead
- Clear responsibility assignment
- Fast decision making

*Disadvantages*:
- Limited to individual tasks
- No collaboration benefits
- May be inefficient for complex tasks
- Single point of failure

**Centralized Multi-Agent Mode**:

*Advantages*:
- Optimal coordination
- Consistent decision-making
- Efficient resource allocation
- Good performance on collaborative tasks

*Disadvantages*:
- Single point of failure (coordinator)
- Scalability limitations
- Higher computational requirements
- Communication bottleneck

**Decentralized Multi-Agent Mode** (Planned):

*Advantages*:
- Fault tolerance and robustness
- Scalable to many agents
- Emergent behaviors possible
- Distributed processing

*Disadvantages*:
- Communication complexity
- Potential coordination failures
- Higher system complexity
- Difficult debugging and monitoring

Benchmarking Results
^^^^^^^^^^^^^^^^^^^^^

Based on evaluation across 1400+ scenarios:

.. code-block:: text

   Success Rate by Agent Mode:
   
   Single Agent:     78.5% ± 2.1%
   Centralized:      85.2% ± 1.8%
   
   Average Steps by Task Type:
   
   Direct Commands:
   - Single Agent:   8.2 ± 1.4
   - Centralized:    7.1 ± 1.2
   
   Collaboration Tasks:
   - Single Agent:   N/A (not applicable)
   - Centralized:    14.8 ± 2.3

Best Practices
--------------

Mode Selection
^^^^^^^^^^^^^^

**Choose Single Agent Mode for**:

- Individual task completion
- Baseline performance measurement
- Simple interaction scenarios
- Resource-constrained environments

**Choose Centralized Mode for**:

- Collaborative task scenarios
- When coordination is critical
- Limited communication bandwidth
- When consistency is paramount

**Plan Decentralized Mode for**:

- Highly scalable scenarios
- Fault-tolerant requirements
- Emergent behavior research
- Distributed decision-making studies

Implementation Guidelines
^^^^^^^^^^^^^^^^^^^^^^^^^

**Configuration Management**:

- Use separate config files for each mode
- Validate configuration compatibility
- Document mode-specific parameters
- Implement configuration validation

**Error Handling**:

- Implement mode-specific error recovery
- Handle coordination failures gracefully
- Provide fallback mechanisms
- Log mode-specific debugging information

**Performance Optimization**:

- Profile mode-specific bottlenecks
- Optimize communication patterns
- Cache frequently accessed state
- Monitor resource usage per mode

**Testing and Validation**:

- Test each mode independently
- Validate coordination mechanisms
- Stress test with multiple agents
- Compare performance across modes

API Reference
-------------

For complete API documentation, see:

- :class:`modes.single_agent.llm_agent.LLMAgent`
- :class:`modes.centralized.centralized_agent.CentralizedAgent`
- :class:`core.base_agent.BaseAgent` 