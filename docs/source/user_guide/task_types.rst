Task Types and Categories
==========================

OmniEmbodied includes a comprehensive taxonomy of tasks designed to evaluate different aspects of embodied AI capabilities. This guide explains the different task categories, their characteristics, and evaluation criteria.

Task Taxonomy Overview
-----------------------

Tasks are organized into two main groups:

**Single-Agent Tasks:**
Tasks that can be completed by a single agent working independently.

**Multi-Agent Tasks:**
Tasks that require coordination between multiple agents.

.. code-block:: text

   Task Categories
   ├── Single-Agent Tasks
   │   ├── Direct Command Following
   │   ├── Attribute-Based Reasoning
   │   ├── Tool Use and Manipulation
   │   ├── Spatial Reasoning
   │   └── Compound Multi-Step Reasoning
   └── Multi-Agent Tasks
       ├── Explicit Collaboration
       ├── Implicit Collaboration
       └── Compound Collaboration

Single-Agent Task Categories
----------------------------

Direct Command Following
^^^^^^^^^^^^^^^^^^^^^^^^^

**Description:**
Basic command execution tasks that require agents to follow explicit instructions without complex reasoning.

**Characteristics:**
- Clear, unambiguous instructions
- Single-step or simple multi-step actions
- Minimal environmental reasoning required
- Direct mapping from instruction to action

**Example Tasks:**
- "Go to the kitchen"
- "Take the red apple from the table"
- "Open the refrigerator door"
- "Turn on the living room lights"

**Evaluation Criteria:**
- Task completion accuracy
- Instruction following precision
- Error handling for impossible actions

**Sample Scenario:**

.. code-block:: json

   {
     "task_id": "direct_001",
     "category": "direct_command",
     "description": "Take the blue book from the shelf",
     "initial_state": {
       "agent_location": "study_room",
       "target_object": "blue_book",
       "object_location": "bookshelf"
     },
     "success_criteria": {
       "agent_has_object": "blue_book"
     }
   }

**Difficulty Levels:**
- **Basic**: Single action commands ("take apple")
- **Intermediate**: Multi-step commands ("go to kitchen, take apple")
- **Advanced**: Commands with implicit steps ("prepare the apple" → wash, cut, etc.)

Attribute-Based Reasoning
^^^^^^^^^^^^^^^^^^^^^^^^^^

**Description:**
Tasks requiring agents to reason about object properties and select items based on specific attributes.

**Characteristics:**
- Object selection based on properties
- Comparison and filtering operations
- Understanding of attribute relationships
- Context-aware decision making

**Example Tasks:**
- "Find the heaviest object in the room"
- "Take the red item that can hold liquids"
- "Get the smallest electronic device"
- "Bring me something soft and warm"

**Evaluation Criteria:**
- Correct attribute identification
- Accurate object selection
- Reasoning about attribute relationships

**Sample Scenario:**

.. code-block:: json

   {
     "task_id": "attr_001",
     "category": "attribute_reasoning",
     "description": "Find the largest container that is currently empty",
     "initial_state": {
       "objects": [
         {"id": "bowl_small", "size": "small", "type": "container", "contents": []},
         {"id": "pot_large", "size": "large", "type": "container", "contents": ["soup"]},
         {"id": "bucket_medium", "size": "medium", "type": "container", "contents": []}
       ]
     },
     "success_criteria": {
       "selected_object": "bucket_medium"
     }
   }

**Key Attributes:**
- **Physical**: size, weight, color, material, temperature
- **Functional**: can_open, can_contain, is_electronic, is_fragile
- **State-based**: is_clean, is_on, is_open, contents

Tool Use and Manipulation
^^^^^^^^^^^^^^^^^^^^^^^^^^

**Description:**
Tasks involving the use of tools and objects to accomplish goals, requiring understanding of object affordances and tool functionality.

**Characteristics:**
- Tool selection and usage
- Understanding object affordances
- Sequential manipulation actions
- Cause-and-effect reasoning

**Example Tasks:**
- "Use the can opener to open the can"
- "Cut the vegetables with the knife"
- "Clean the table with the cloth"
- "Measure the liquid with the measuring cup"

**Evaluation Criteria:**
- Appropriate tool selection
- Correct tool usage sequence
- Goal achievement through tool use

**Sample Scenario:**

.. code-block:: json

   {
     "task_id": "tool_001",
     "category": "tool_use",
     "description": "Open the can of soup using available tools",
     "initial_state": {
       "target_object": "soup_can",
       "available_tools": ["can_opener", "knife", "spoon"],
       "object_states": {
         "soup_can": {"is_open": false}
       }
     },
     "success_criteria": {
       "object_states": {
         "soup_can": {"is_open": true}
       }
     }
   }

**Tool Categories:**
- **Kitchen Tools**: knives, can openers, measuring cups, mixers
- **Cleaning Tools**: cloths, brushes, vacuum cleaners, mops
- **Maintenance Tools**: screwdrivers, hammers, wrenches
- **Electronic Tools**: remote controls, computers, phones

Spatial Reasoning
^^^^^^^^^^^^^^^^^

**Description:**
Tasks requiring understanding of spatial relationships, navigation, and positional reasoning.

**Characteristics:**
- Understanding spatial relationships
- Navigation planning
- Positional reasoning
- 3D spatial understanding

**Example Tasks:**
- "Put the book between the lamp and the clock"
- "Find the object that is behind the chair"
- "Move the table to create more space"
- "Arrange objects in order of height"

**Evaluation Criteria:**
- Accurate spatial understanding
- Correct positional placement
- Efficient navigation paths

**Sample Scenario:**

.. code-block:: json

   {
     "task_id": "spatial_001",
     "category": "spatial_reasoning",
     "description": "Place the vase in the center of the dining table",
     "initial_state": {
       "agent_location": "dining_room",
       "target_object": "vase",
       "target_location": "dining_table_center"
     },
     "success_criteria": {
       "object_location": {
         "vase": "dining_table_center"
       }
     }
   }

**Spatial Concepts:**
- **Relationships**: on, in, under, behind, between, next to
- **Directions**: north, south, left, right, forward, back
- **Distances**: near, far, close, adjacent, opposite
- **Arrangements**: center, corner, edge, middle, side

Compound Multi-Step Reasoning
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Description:**
Complex tasks requiring multiple reasoning steps, planning, and integration of various cognitive abilities.

**Characteristics:**
- Multi-step planning required
- Integration of multiple task types
- Complex goal decomposition
- Long-horizon reasoning

**Example Tasks:**
- "Prepare a simple sandwich for lunch"
- "Clean and organize the living room"
- "Set up the dining table for two people"
- "Find and repair the broken lamp"

**Evaluation Criteria:**
- Correct task decomposition
- Logical step sequencing
- Successful completion of all sub-goals

**Sample Scenario:**

.. code-block:: json

   {
     "task_id": "compound_001",
     "category": "compound_reasoning",
     "description": "Prepare the kitchen for cooking dinner",
     "subtasks": [
       {
         "id": "clean_counter",
         "description": "Clean the kitchen counter",
         "type": "tool_use"
       },
       {
         "id": "gather_utensils",
         "description": "Get cooking utensils from drawer",
         "type": "direct_command"
       },
       {
         "id": "preheat_oven",
         "description": "Set oven to 350°F",
         "type": "tool_use"
       }
     ]
   }

Multi-Agent Task Categories
---------------------------

Explicit Collaboration
^^^^^^^^^^^^^^^^^^^^^^^

**Description:**
Tasks requiring direct communication and coordination between agents with clearly defined roles.

**Characteristics:**
- Direct inter-agent communication
- Clearly defined roles and responsibilities
- Coordinated action sequences
- Shared goal achievement

**Example Tasks:**
- "Agent A: Get ingredients. Agent B: Prepare cooking area"
- "One agent holds the ladder while the other climbs"
- "Coordinate to move the heavy table together"
- "Take turns using the shared tool"

**Evaluation Criteria:**
- Successful role coordination
- Effective communication
- Synchronized actions
- Shared goal achievement

**Sample Scenario:**

.. code-block:: json

   {
     "task_id": "collab_001",
     "category": "explicit_collaboration",
     "description": "Move the heavy sofa from living room to bedroom",
     "agents": {
       "agent_1": {"role": "lifter_front", "initial_location": "living_room"},
       "agent_2": {"role": "lifter_back", "initial_location": "living_room"}
     },
     "coordination_required": {
       "synchronized_lifting": true,
       "coordinated_movement": true
     }
   }

Implicit Collaboration
^^^^^^^^^^^^^^^^^^^^^^^

**Description:**
Tasks where agents must infer collaboration needs and coordinate without explicit communication.

**Characteristics:**
- Implicit coordination cues
- Shared situational awareness
- Emergent cooperation patterns
- Inference-based collaboration

**Example Tasks:**
- "Both agents clean different rooms simultaneously"
- "Prepare different parts of the same meal"
- "Search different areas for the same lost item"
- "Organize items while avoiding interference"

**Evaluation Criteria:**
- Effective implicit coordination
- Minimal interference between agents
- Complementary actions
- Efficient task distribution

**Sample Scenario:**

.. code-block:: json

   {
     "task_id": "implicit_001",
     "category": "implicit_collaboration",
     "description": "Clean the entire house efficiently",
     "global_goal": "all_rooms_clean",
     "coordination_style": "implicit",
     "success_criteria": {
       "all_rooms_clean": true,
       "minimal_redundancy": true,
       "efficient_coverage": true
     }
   }

Compound Collaboration
^^^^^^^^^^^^^^^^^^^^^^

**Description:**
Complex multi-agent tasks combining explicit and implicit coordination with sophisticated planning.

**Characteristics:**
- Mixed coordination modes
- Complex multi-step planning
- Dynamic role assignment
- Adaptive collaboration strategies

**Example Tasks:**
- "Plan and execute a dinner party for guests"
- "Reorganize the entire living space"
- "Collaborate to complete a complex assembly task"
- "Coordinate emergency response procedures"

**Sample Scenario:**

.. code-block:: json

   {
     "task_id": "compound_collab_001",
     "category": "compound_collaboration",
     "description": "Prepare and serve a three-course meal",
     "phases": [
       {"phase": "planning", "type": "explicit_coordination"},
       {"phase": "preparation", "type": "implicit_collaboration"},
       {"phase": "execution", "type": "explicit_coordination"}
     ]
   }

Task Configuration and Filtering
---------------------------------

Task Selection
^^^^^^^^^^^^^^

You can filter tasks by category in your configuration:

.. code-block:: yaml

   scenario_selection:
     task_filter:
       categories:
         - "direct_command"
         - "attribute_reasoning"
         - "tool_use"
       
       # Additional filters
       agent_count: "single"  # single, multi, all
       difficulty: "medium"   # basic, medium, advanced
       max_steps: 20         # Maximum steps allowed

Task Difficulty Levels
^^^^^^^^^^^^^^^^^^^^^^

Each task category has multiple difficulty levels:

**Basic Level:**
- Simple, single-step tasks
- Clear success criteria
- Minimal environmental complexity

**Intermediate Level:**
- Multi-step tasks
- Some environmental reasoning required
- Multiple possible solution paths

**Advanced Level:**
- Complex, long-horizon tasks
- Significant planning required
- Multiple interconnected sub-goals

Evaluation Metrics
------------------

Success Metrics
^^^^^^^^^^^^^^^^

**Binary Success:** Task completed successfully (True/False)

**Partial Success:** Progress towards completion (0.0 - 1.0)

**Efficiency Metrics:**
- Steps taken vs. optimal path
- Time to completion
- Resource utilization

**Quality Metrics:**
- Action appropriateness
- Error recovery capability
- Solution elegance

Error Analysis
^^^^^^^^^^^^^^

**Error Categories:**
- **Planning Errors**: Incorrect task decomposition
- **Execution Errors**: Failed action attempts
- **Reasoning Errors**: Incorrect object/attribute identification
- **Coordination Errors**: Failed multi-agent communication

**Error Recovery:**
- Agent's ability to recognize failures
- Adaptive replanning capabilities
- Learning from mistakes

Benchmarking and Comparison
---------------------------

Standard Evaluation Protocol
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. **Scenario Selection**: Representative sample from each category
2. **Multiple Runs**: Average over multiple trials for statistical significance
3. **Consistent Configuration**: Same parameters across different agents
4. **Detailed Logging**: Complete action traces for analysis

**Reporting Format:**

.. code-block:: text

   Task Category Performance Report
   ================================
   Direct Command:           92.3% (185/200)
   Attribute Reasoning:      78.5% (157/200)
   Tool Use:                 71.2% (142/200)
   Spatial Reasoning:        83.7% (167/200)
   Compound Reasoning:       62.1% (124/200)
   
   Overall Single-Agent:     77.6% (775/1000)
   
   Multi-Agent Performance:
   Explicit Collaboration:  65.3% (131/200)
   Implicit Collaboration:  58.7% (117/200)
   Compound Collaboration:   42.1% (84/200)
   
   Overall Multi-Agent:      55.4% (332/600)

Creating Custom Task Types
---------------------------

Task Definition Format
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

   {
     "task_id": "custom_001",
     "category": "custom_category",
     "description": "Human-readable task description",
     "initial_state": {
       "agent_locations": {},
       "object_states": {},
       "environment_conditions": {}
     },
     "success_criteria": {
       "primary_goals": [],
       "secondary_goals": [],
       "failure_conditions": []
     },
     "metadata": {
       "difficulty": "medium",
       "estimated_steps": 15,
       "required_skills": ["reasoning", "manipulation"]
     }
   }

Custom Evaluation Criteria
^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can define custom success criteria:

.. code-block:: python

   def custom_task_verifier(task_definition, final_state):
       """Custom verification logic for specific task types."""
       success_conditions = task_definition['success_criteria']
       
       # Implement custom logic here
       primary_complete = check_primary_goals(success_conditions, final_state)
       secondary_complete = check_secondary_goals(success_conditions, final_state)
       
       return {
           'success': primary_complete,
           'partial_success': calculate_partial_completion(final_state),
           'quality_score': evaluate_solution_quality(final_state)
       }

Best Practices
--------------

For Researchers
^^^^^^^^^^^^^^^^

**Task Selection:**
- Choose diverse tasks that cover your research interests
- Include both basic and advanced difficulty levels
- Ensure statistical significance with adequate sample sizes

**Evaluation Protocol:**
- Use consistent evaluation procedures
- Report both aggregate and per-category results
- Include error analysis and failure modes

**Reproducibility:**
- Document exact configurations used
- Share custom task definitions
- Provide complete experimental details

For Developers
^^^^^^^^^^^^^^^

**Agent Design:**
- Test on diverse task categories to identify limitations
- Implement robust error handling for action failures
- Consider task-specific optimization strategies

**Performance Optimization:**
- Profile performance on computationally intensive tasks
- Optimize for common task patterns
- Balance speed vs. accuracy trade-offs

Next Steps
----------

To learn more about using tasks in OmniEmbodied:

- :doc:`../examples/task_filtering_examples` - Filtering and selecting tasks
- :doc:`evaluation_framework` - Setting up evaluations
- :doc:`../api/framework` - API reference for task handling
- :doc:`../developer/extending` - Creating custom task types

For practical examples:
- :doc:`../examples/evaluation_workflows` - Complete evaluation examples
- Browse the ``data/`` directory for example task definitions
- See ``config/`` directory for task filtering configurations 