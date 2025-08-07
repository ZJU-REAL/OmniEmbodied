Environment System
==================

The environment system in OmniSimulator provides the foundation for realistic embodied AI simulations. It manages the spatial world, object interactions, and state persistence across agent actions.

.. toctree::
   :maxdepth: 2

Core Components
---------------

Environment Manager
^^^^^^^^^^^^^^^^^^^

The ``EnvironmentManager`` is the central component that orchestrates all environment-related operations:

- **Scene Loading**: Parses JSON scene descriptions and builds the simulation world
- **Object Management**: Handles creation, positioning, and state tracking of all objects
- **Spatial Relationships**: Maintains containment hierarchies and spatial connections
- **State Persistence**: Ensures consistent world state across agent actions

.. code-block:: python

   from OmniSimulator.environment.environment_manager import EnvironmentManager
   from OmniSimulator.core.state import WorldState

   # Initialize environment with world state
   world_state = WorldState()
   env_manager = EnvironmentManager(world_state)

   # Load scene from JSON data
   scene_data = {
       "rooms": [...],
       "objects": [...],
       "connections": [...]
   }
   success = env_manager.load_scene(scene_data)

Room System
^^^^^^^^^^^

Rooms are spatial containers that organize the simulation world:

**Room Properties**:

- **Spatial Boundaries**: Defined areas with specific layouts
- **Object Containment**: Hold furniture, items, and interactive objects  
- **Connectivity**: Links to other rooms through doorways and passages
- **Visibility**: Control what agents can observe in each space

**Room Types**:

- **Basic Rooms**: Simple containers (bedroom, kitchen, office)
- **Connected Spaces**: Rooms with multiple access points
- **Specialized Areas**: Rooms with unique interaction patterns

.. code-block:: python

   from OmniSimulator.environment.room import Room

   # Create room instance
   kitchen = Room(
       room_id="kitchen_001",
       room_type="kitchen",
       description="A modern kitchen with appliances and counter space"
   )

   # Add room to environment
   env_manager.add_room(kitchen)

   # Connect rooms
   env_manager.connect_rooms("kitchen_001", "living_room_001")

Object Hierarchy
^^^^^^^^^^^^^^^^

OmniSimulator uses a rich object hierarchy to model realistic interactions:

**Base Object Types**:

- **StaticObject**: Immovable environmental elements (walls, floors)
- **InteractableObject**: Objects that can be manipulated but not moved
- **GrabbableObject**: Items that can be picked up and carried
- **FurnitureObject**: Large interactive furniture pieces
- **ItemObject**: Small items with specific properties

**Object Properties**:

- **Physical Attributes**: Size, weight, material, temperature
- **State Variables**: Open/closed, on/off, clean/dirty, etc.
- **Containment**: Ability to hold other objects
- **Accessibility**: Whether agents can interact with the object

.. code-block:: python

   from OmniSimulator.environment.object_defs import (
       GrabbableObject, FurnitureObject, ItemObject
   )

   # Create different object types
   apple = GrabbableObject(
       object_id="red_apple_001",
       properties={
           "color": "red",
           "size": "small", 
           "weight": "light",
           "edible": True
       }
   )

   refrigerator = FurnitureObject(
       object_id="kitchen_fridge",
       properties={
           "size": "large",
           "has_door": True,
           "is_open": False,
           "contains": []
       }
   )

Spatial Relationships
^^^^^^^^^^^^^^^^^^^^

The system maintains complex spatial relationships:

**Containment Hierarchy**:

- Objects can contain other objects
- Nested containment (box in cabinet in room)
- Capacity and size constraints

**Position Tracking**:

- Absolute positions within rooms
- Relative positions (on, in, under, beside)
- Accessibility based on spatial constraints

.. code-block:: python

   # Place object in specific location
   env_manager.place_object("red_apple_001", "kitchen_table")

   # Query spatial relationships
   objects_on_table = env_manager.get_objects_at_location("on:kitchen_table")
   objects_in_fridge = env_manager.get_objects_at_location("in:kitchen_fridge")

Environment Configuration
-------------------------

Global Observation Settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Control what agents can observe initially:

.. code-block:: yaml

   simulator:
     global_observation: false    # Agents must explore to discover objects
     explore_mode: thorough      # Detailed vs. basic exploration

   environment:
     physics_enabled: true       # Enable realistic physics constraints
     max_objects_per_room: 50    # Limit objects for performance
     state_persistence: true     # Maintain state between sessions

Scene Loading Process
^^^^^^^^^^^^^^^^^^^^^

The environment manager loads scenes in a structured process:

1. **Room Creation**: Parse room definitions and create room objects
2. **Room Connections**: Establish spatial links between rooms
3. **Independent Objects**: Load objects placed directly in rooms
4. **Dependent Objects**: Load objects contained within other objects  
5. **Relationship Resolution**: Resolve all spatial relationships and dependencies

.. code-block:: json

   {
     "scene_id": "demo_kitchen",
     "rooms": [
       {
         "id": "kitchen_001",
         "type": "kitchen", 
         "description": "A well-equipped kitchen",
         "connected_to_room_ids": ["living_room_001"]
       }
     ],
     "objects": [
       {
         "id": "kitchen_table",
         "type": "FURNITURE",
         "location_id": "kitchen_001",
         "properties": {
           "size": "medium",
           "material": "wood"
         }
       }
     ]
   }

Advanced Features
-----------------

Dynamic Object Creation
^^^^^^^^^^^^^^^^^^^^^^

Create objects programmatically during simulation:

.. code-block:: python

   # Create object from dictionary
   object_data = {
       "id": "dynamic_item",
       "type": "GRABBABLE",
       "properties": {"color": "blue", "size": "small"}
   }
   new_object = env_manager.create_object_from_dict(object_data)

State Queries and Updates
^^^^^^^^^^^^^^^^^^^^^^^^^

Efficiently query and update world state:

.. code-block:: python

   # Query object states
   object_state = env_manager.get_object_state("red_apple_001")
   
   # Update object properties
   env_manager.update_object_property("kitchen_fridge", "is_open", True)
   
   # Get all objects in a room
   room_objects = env_manager.get_objects_in_room("kitchen_001")

Collision Detection
^^^^^^^^^^^^^^^^^^^

Prevent impossible spatial configurations:

- **Size Constraints**: Large objects cannot fit in small containers
- **Capacity Limits**: Containers have maximum object limits
- **Physical Conflicts**: Objects cannot occupy the same space

Performance Optimization
------------------------

The environment system is optimized for large-scale simulations:

**Efficient Lookups**:

- Spatial indexing for fast object queries
- Cached relationship calculations
- Lazy evaluation of complex computations

**Memory Management**:

- Object pooling for frequently created/destroyed items
- Configurable state history retention
- Efficient serialization for state saving

**Scalability Features**:

- Support for hundreds of objects per room
- Efficient handling of deep containment hierarchies
- Parallel processing of independent operations

Integration with Actions
------------------------

The environment system tightly integrates with the action system:

**Action Validation**: 
- Check spatial constraints before action execution
- Validate object accessibility and interaction rules
- Ensure physical plausibility of requested actions

**State Updates**:
- Modify object positions and properties based on actions
- Update spatial relationships after movements
- Maintain consistency across all environment components

**Feedback Generation**:
- Provide detailed observation results
- Generate appropriate error messages for invalid actions
- Support rich sensory feedback for agent perception

.. code-block:: python

   # Environment automatically validates and executes spatial changes
   action_result = action_manager.execute_action(
       agent_id="agent_001",
       action_type="PLACE",
       parameters={"object": "red_apple_001", "location": "kitchen_table"}
   )

   if action_result.success:
       # Environment state has been updated
       apple_location = env_manager.get_object_location("red_apple_001")
       print(f"Apple is now located: {apple_location}")

Debugging and Visualization
---------------------------

Environment debugging tools:

**State Inspection**:

.. code-block:: python

   # Get complete environment state
   full_state = env_manager.get_complete_state()
   
   # Print spatial hierarchy
   env_manager.print_spatial_hierarchy("kitchen_001")
   
   # Validate environment consistency
   validation_result = env_manager.validate_environment()

**Visualization Support**:

The environment system supports visualization through the web interface:

- Interactive room layouts
- Object placement visualization  
- Spatial relationship diagrams
- Real-time state updates

Best Practices
--------------

**Scene Design**:

- Keep object hierarchies reasonably shallow (< 5 levels deep)
- Use consistent naming conventions for objects and rooms
- Include appropriate physical constraints in object properties
- Test scenes with multiple agents to ensure proper scaling

**Performance Considerations**:

- Limit the number of objects per room for optimal performance
- Use object pooling for frequently created temporary objects
- Consider enabling/disabling physics constraints based on needs
- Monitor memory usage in long-running simulations

**Error Handling**:

- Always check return values from environment operations
- Handle missing objects gracefully in scene loading
- Implement proper cleanup for dynamic object creation
- Use validation methods to ensure environment consistency

API Reference
-------------

For complete API documentation, see:

- :class:`OmniSimulator.environment.environment_manager.EnvironmentManager`
- :class:`OmniSimulator.environment.room.Room`
- :module:`OmniSimulator.environment.object_defs` 