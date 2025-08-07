OmniSimulator
=============

OmniSimulator is the core simulation engine that powers embodied AI research. It provides realistic environments, flexible action systems, and clean APIs for agent integration.

.. toctree::
   :maxdepth: 2

   overview
   environments
   actions
   agents

What is OmniSimulator?
----------------------

OmniSimulator is a text-based embodied AI simulation engine designed for:

- **Research**: Reproducible experimentation with embodied AI agents
- **Development**: Rapid prototyping and testing of agent behaviors  
- **Evaluation**: Comprehensive benchmarking across diverse scenarios
- **Education**: Learning platform for embodied AI concepts

Key Features
------------

**Text-Based Simulation**:

- Rich natural language descriptions of environments and states
- Intuitive command-based interaction model
- Support for complex multi-step reasoning tasks
- Realistic object interactions and physics

**Flexible Agent Interface**:

- Clean API for integrating various AI models
- Support for single and multi-agent scenarios
- Customizable action spaces and capabilities
- Built-in state management and history tracking

**Comprehensive Evaluation**:

- Standardized task definitions and metrics
- Automated scenario generation and validation
- Performance tracking and analysis tools
- Integration with evaluation frameworks

Core Components
---------------

**Simulation Engine**:

- Central coordinator for all simulation activities
- Handles environment state, agent actions, and task progression
- Provides consistent interfaces for all simulation operations
- Supports parallel execution and batch processing

**Environment System**:

- Dynamic room-based spatial representation
- Object management with realistic properties and states
- Spatial reasoning and pathfinding capabilities
- Support for complex object relationships and containment

**Action Framework**:

- Extensible action system with built-in action types
- Validation and execution pipelines with proper error handling
- Support for collaborative multi-agent actions
- Real-time action description generation

**Agent Interface**:

- Clean abstraction layer between AI models and simulation
- State management and observation interfaces
- Action execution with detailed feedback
- History tracking and replay capabilities

Supported Task Types
---------------------

**Navigation Tasks**:

- Room-to-room movement and pathfinding
- Object localization and approach behaviors
- Spatial reasoning and exploration strategies

**Manipulation Tasks**:

- Object grasping, moving, and placement
- Container interactions (opening, closing)
- Multi-object coordination and assembly tasks

**Reasoning Tasks**:

- Attribute-based object identification and filtering
- Complex goal decomposition and planning
- Multi-step task execution with dependencies

**Collaboration Tasks**:

- Multi-agent coordination and communication
- Resource sharing and task delegation
- Emergent collective behaviors

Architecture Overview
----------------------

OmniSimulator follows a modular architecture:

.. code-block:: text

   ┌─────────────────────────────────────────────────────────┐
   │                  Agent Interface                        │
   │  ┌─────────────────────────────────────────────────┐    │
   │  │              AI Models                          │    │
   │  │  ┌─────────────┐  ┌─────────────┐               │    │
   │  │  │     LLM     │  │  Baseline   │    ...        │    │
   │  │  │   Agents    │  │   Agents    │               │    │
   │  │  └─────────────┘  └─────────────┘               │    │
   │  └─────────────────────────────────────────────────┘    │
   └─────────────────────────────────────────────────────────┘
   ┌─────────────────────────────────────────────────────────┐
   │                Simulation Engine                        │
   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
   │  │   Action    │  │Environment  │  │    Task     │     │
   │  │  Manager    │  │  Manager    │  │  Manager    │     │
   │  └─────────────┘  └─────────────┘  └─────────────┘     │
   └─────────────────────────────────────────────────────────┘
   ┌─────────────────────────────────────────────────────────┐
   │                   Data Layer                            │
   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
   │  │  Scenarios  │  │    Tasks    │  │   Objects   │     │
   │  │             │  │             │  │ Properties  │     │
   │  └─────────────┘  └─────────────┘  └─────────────┘     │
   └─────────────────────────────────────────────────────────┘

Getting Started with OmniSimulator
-----------------------------------

**Quick Start**:

1. **Initialize Engine**: Create a simulation engine instance
2. **Load Scenario**: Load environment and task definitions
3. **Create Agents**: Instantiate agents with desired capabilities
4. **Execute Actions**: Run agent actions and observe results
5. **Evaluate Performance**: Analyze task completion and efficiency

**Basic Example**:

.. code-block:: python

   from OmniSimulator.core.engine import SimulationEngine
   
   # Create simulation
   engine = SimulationEngine()
   
   # Load scenario
   success = engine.initialize_with_task("example_scenario.json")
   
   if success:
       # Process agent commands
       result = engine.process_command("explore living room")
       print(f"Result: {result}")

**Next Steps**:

- :doc:`../examples/basic_simulation` - Hands-on examples

For detailed information on each component:

**Core Documentation**:

- :doc:`overview` - Detailed system overview and concepts
- :doc:`environments` - Environment system and spatial modeling
- :doc:`actions` - Action framework and built-in action types  
- :doc:`agents` - Agent interface and integration patterns

**Practical Guides**:

- :doc:`../examples/basic_simulation` - Basic simulation examples

Integration Examples
--------------------

**Single Agent Setup**:

.. code-block:: python

   from OmniSimulator.core.engine import SimulationEngine
   from OmniSimulator.agent.agent import Agent
   
   # Initialize simulation
   engine = SimulationEngine()
   
   # Create agent
   agent = Agent(
       agent_id="helper",
       name="Assistant", 
       location_id="living_room"
   )
   
   # Agent interaction
   print(f"Agent inventory: {agent.inventory}")
   can_grab_cup = agent.can_grab("cup")

**Action Execution**:

.. code-block:: python

   from OmniSimulator.action.action_manager import ActionManager
   
   # Initialize action system
   action_manager = ActionManager()
   
   # Execute action with validation
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

**Environment Queries**:

.. code-block:: python

   from OmniSimulator.environment.environment_manager import EnvironmentManager
   
   env = EnvironmentManager()
   
   # Get room and object information
   living_room = env.get_room("living_room")
   objects_in_room = env.get_objects_in_room("living_room")
   
   print(f"Room: {living_room.name}")
   print(f"Objects: {len(objects_in_room)}")

Performance and Scalability
----------------------------

**Optimization Features**:

- Efficient state management with minimal memory footprint
- Optimized pathfinding and spatial reasoning algorithms
- Batch processing capabilities for multiple scenarios
- Configurable simulation parameters for performance tuning

**Scalability**:

- Support for large environment spaces (100+ rooms)
- Handle complex object hierarchies (1000+ objects)  
- Multi-agent scenarios with coordination overhead
- Parallel execution for batch evaluation

**Resource Usage**:

- Memory: ~50-200MB per simulation instance
- CPU: Scales with environment complexity and agent count
- Storage: Minimal for state persistence, configurable logging

Extensibility
-------------

**Custom Actions**:

.. code-block:: python

   from OmniSimulator.action.actions.base_action import BaseAction
   
   class CustomAction(BaseAction):
       def validate(self):
           # Custom validation logic
           return True
           
       def execute(self):
           # Custom execution logic  
           return {"success": True}

**Environment Extensions**:

- Custom object types with specialized properties
- Domain-specific room configurations
- Extended spatial relationships and containment rules

**Agent Integration**:

- Support for various AI architectures and models
- Flexible observation and action space definitions
- Custom reasoning and planning integration points

Advanced Topics
---------------

For advanced usage and customization, consult the developer documentation:

- Framework extension and customization patterns
- Advanced configuration techniques
- Performance optimization strategies
- Integration with external tools and systems 