Data Generation Tools
======================

The OmniEmbodied Framework includes comprehensive data generation tools for creating custom training and evaluation datasets. The system supports automated generation of scenarios, tasks, and evaluation criteria with quality validation.

.. toctree::
   :maxdepth: 2

Overview
--------

The data generation system provides:

- **Automated Pipeline**: End-to-end generation from raw concepts to complete scenarios
- **Multi-Stage Generation**: Clue generation → Scene generation → Task generation → Validation
- **Quality Control**: Automated validation and consistency checking
- **Scalable Processing**: Concurrent generation with progress tracking
- **Customizable Generators**: Extensible architecture for domain-specific needs

The system generates three types of outputs:

- **Scenarios**: Complete environment descriptions with objects and spatial relationships
- **Tasks**: Goal-oriented activities with success criteria and verification rules
- **Evaluation Data**: Structured datasets for benchmarking agent performance

Core Components
---------------

Data Generation Pipeline
^^^^^^^^^^^^^^^^^^^^^^^^

The ``Pipeline`` class orchestrates the complete generation process:

.. code-block:: python

   from data_generation.pipeline import Pipeline

   # Initialize pipeline
   pipeline = Pipeline()

   # Configure generation parameters
   config = {
       "num_items": 100,
       "max_workers": 4,
       "output_format": "json"
   }

   # Run end-to-end generation
   results = pipeline.run(
       input_file="concepts.txt",
       config=config
   )

   print(f"Generated {results['completed']} scenarios")
   print(f"Total token usage: {results['token_usage']}")

Pipeline Architecture
^^^^^^^^^^^^^^^^^^^^^^

The pipeline processes data through multiple stages:

.. code-block:: text

   Raw Concepts → Clue Generation → Scene Generation → Task Generation → Validation
        ↓              ↓                 ↓                ↓               ↓
   Text Input    Object Lists     Environment     Task Definition   Quality Check
                 Properties       Layout          Success Criteria  Consistency

Each stage builds upon the previous output, ensuring consistency and coherence throughout the generation process.

Generation Stages
-----------------

Clue Generation
^^^^^^^^^^^^^^^^

The ``ClueGenerator`` creates object lists and properties from concept descriptions:

**Features**:
- Object identification and categorization
- Property assignment (color, size, material, etc.)
- Relationship inference
- Context-aware object selection

.. code-block:: python

   from data_generation.generators.clue_generator import ClueGenerator

   # Initialize generator
   clue_gen = ClueGenerator(config)

   # Generate object clues
   clues = clue_gen.generate(
       concept="kitchen cooking scenario",
       num_objects=15
   )

   # Example output:
   # {
   #   "objects": [
   #     {"name": "cooking_pot", "color": "silver", "size": "medium"},
   #     {"name": "wooden_spoon", "color": "brown", "size": "small"},
   #     {"name": "ingredients", "type": "vegetables", "count": "multiple"}
   #   ],
   #   "relationships": ["pot_on_stove", "ingredients_in_fridge"]
   # }

Scene Generation
^^^^^^^^^^^^^^^^^

The ``SceneGenerator`` creates complete environment descriptions:

**Features**:
- Room layout generation
- Object placement and spatial relationships
- Realistic environmental constraints
- Multi-room scene support

.. code-block:: python

   from data_generation.generators.scene_generator import SceneGenerator

   # Initialize generator
   scene_gen = SceneGenerator(config)

   # Generate scene from clues
   scene = scene_gen.generate(
       clues=clues,
       scene_type="kitchen"
   )

   # Example output structure:
   # {
   #   "scene_id": "kitchen_001",
   #   "rooms": [
   #     {
   #       "id": "kitchen",
   #       "type": "kitchen",
   #       "objects": [...]
   #     }
   #   ],
   #   "objects": [...],
   #   "spatial_relationships": [...]
   # }

Task Generation
^^^^^^^^^^^^^^^^

The ``TaskGenerator`` creates goal-oriented tasks with verification criteria:

**Features**:
- Task description generation
- Success criteria definition
- Multi-step task planning
- Verification rule creation

.. code-block:: python

   from data_generation.generators.task_generator import TaskGenerator

   # Initialize generator
   task_gen = TaskGenerator(config)

   # Generate task from scene
   task = task_gen.generate(
       scene=scene,
       task_type="cooking_task"
   )

   # Example output:
   # {
   #   "task_id": "cook_001", 
   #   "description": "Prepare a simple meal using the ingredients in the kitchen",
   #   "success_criteria": [
   #     "Ingredients are removed from refrigerator",
   #     "Cooking pot is placed on stove", 
   #     "Ingredients are added to pot"
   #   ],
   #   "verification": {
   #     "type": "state_check",
   #     "conditions": [...]
   #   }
   # }

Configuration and Customization
-------------------------------

Pipeline Configuration
^^^^^^^^^^^^^^^^^^^^^^

Configure the generation pipeline through YAML files:

.. code-block:: yaml

   # pipeline.yaml
   pipeline:
     max_workers: 4              # Concurrent processing threads
     retry_attempts: 3           # Retries for failed generations
     timeout_seconds: 300        # Timeout per generation step
     
   output:
     format: "json"              # Output format (json, yaml)
     compression: true           # Compress output files
     validation: true            # Enable quality validation
     
   generation:
     num_scenarios: 100          # Number of scenarios to generate
     scene_complexity: "medium"  # Scenario complexity level
     task_variety: "high"        # Task type diversity

Generator Configuration
^^^^^^^^^^^^^^^^^^^^^^^^

Configure individual generators:

.. code-block:: yaml

   # clue_gen_config.yaml
   clue_generator:
     max_objects: 20            # Maximum objects per scenario
     object_categories:         # Allowed object types
       - "furniture"
       - "tools"  
       - "consumables"
     property_richness: "high"  # Detail level for object properties
     
   # scene_gen_config.yaml  
   scene_generator:
     room_types:               # Supported room types
       - "kitchen"
       - "living_room" 
       - "bedroom"
     spatial_complexity: "medium"  # Layout complexity
     object_density: 0.7       # Object placement density
     
   # task_gen_config.yaml
   task_generator:
     task_categories:          # Task types to generate
       - "direct_command"
       - "attribute_reasoning"
       - "multi_step"
     difficulty_distribution:  # Difficulty level distribution
       easy: 0.3
       medium: 0.5
       hard: 0.2

Custom Generators
^^^^^^^^^^^^^^^^^

Extend base generators for custom requirements:

.. code-block:: python

   from data_generation.generators.base_generator import BaseGenerator

   class CustomSceneGenerator(BaseGenerator):
       def __init__(self, config):
           super().__init__(config)
           self.domain_knowledge = self._load_domain_data()
           
       def generate(self, clues, **kwargs):
           # Custom generation logic
           base_scene = super().generate(clues, **kwargs)
           
           # Apply domain-specific modifications
           enhanced_scene = self._apply_domain_constraints(base_scene)
           specialized_scene = self._add_domain_objects(enhanced_scene)
           
           return specialized_scene
           
       def _apply_domain_constraints(self, scene):
           # Implement domain-specific spatial constraints
           return scene
           
       def _add_domain_objects(self, scene):
           # Add specialized objects for the domain
           return scene

Quality Control and Validation
------------------------------

Task Validation
^^^^^^^^^^^^^^^

The ``TaskValidator`` ensures generated content meets quality standards:

.. code-block:: python

   from data_generation.utils.task_validator import TaskValidator

   # Initialize validator
   validator = TaskValidator()

   # Validate generated task
   validation_result = validator.validate_task(
       task=generated_task,
       scene=scene_data
   )

   if not validation_result.is_valid:
       print(f"Validation failed: {validation_result.errors}")
       print(f"Suggestions: {validation_result.suggestions}")

**Validation Checks**:

- **Logical Consistency**: Task requirements match scene contents
- **Feasibility**: Tasks can be completed given available objects
- **Completeness**: All necessary information is present
- **Clarity**: Task descriptions are unambiguous
- **Verification**: Success criteria are measurable

Automated Quality Metrics
^^^^^^^^^^^^^^^^^^^^^^^^^

Built-in quality assessment:

.. code-block:: python

   # Quality metrics computed automatically
   quality_metrics = {
       'coherence_score': 0.87,       # Logical consistency
       'complexity_score': 0.65,      # Appropriate difficulty
       'completeness_score': 0.92,    # Information completeness
       'feasibility_score': 0.89,     # Task feasibility
       'diversity_score': 0.78        # Content variety
   }

   # Filter by quality thresholds
   high_quality_tasks = validator.filter_by_quality(
       tasks=all_tasks,
       min_coherence=0.8,
       min_feasibility=0.85
   )

Batch Processing and Workflows
------------------------------

Large-Scale Generation
^^^^^^^^^^^^^^^^^^^^^^

Generate datasets at scale with progress monitoring:

.. code-block:: python

   from data_generation.pipeline import Pipeline

   # Configure large-scale generation
   pipeline = Pipeline()
   
   # Generate 1000 scenarios with progress tracking
   results = pipeline.run_batch(
       concepts_file="domain_concepts.txt",
       num_scenarios=1000,
       batch_size=50,
       progress_callback=lambda p: print(f"Progress: {p:.1%}")
   )

   # Results include detailed statistics
   print(f"Success rate: {results['success_rate']:.2%}")
   print(f"Average quality score: {results['avg_quality']:.2f}")
   print(f"Token usage: {results['total_tokens']:,}")

Resume and Incremental Generation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Resume interrupted generations and add to existing datasets:

.. code-block:: python

   # Resume interrupted generation
   pipeline = Pipeline()
   results = pipeline.resume(
       checkpoint_file="generation_checkpoint.json",
       output_dir="data/scenarios"
   )

   # Incremental generation (add to existing dataset)
   additional_results = pipeline.extend_dataset(
       existing_dir="data/scenarios",
       additional_count=200,
       maintain_distribution=True  # Keep same task type distribution
   )

Distributed Generation
^^^^^^^^^^^^^^^^^^^^^^

Scale across multiple machines:

.. code-block:: python

   # Distributed generation coordinator
   from data_generation.distributed import DistributedPipeline

   coordinator = DistributedPipeline()
   
   # Configure worker nodes
   workers = [
       {"host": "worker1.local", "threads": 8},
       {"host": "worker2.local", "threads": 8}, 
       {"host": "worker3.local", "threads": 8}
   ]

   # Distribute generation across workers
   results = coordinator.run_distributed(
       concepts="large_concept_set.txt",
       workers=workers,
       total_scenarios=5000
   )

Data Management and Export
--------------------------

Dataset Organization
^^^^^^^^^^^^^^^^^^^^^

Generated data is automatically organized:

.. code-block:: text

   data/
   ├── clue/           # Generated object clues
   │   ├── batch_001.json
   │   └── batch_002.json
   ├── scene/          # Generated scenes
   │   ├── scene_001.json
   │   └── scene_002.json
   ├── task/           # Generated tasks
   │   ├── task_001.json
   │   └── task_002.json
   └── metadata/       # Generation metadata
       ├── generation_log.json
       └── quality_metrics.json

Export Formats
^^^^^^^^^^^^^^^

Export to various formats for different use cases:

.. code-block:: python

   from data_generation.exporters import DatasetExporter

   exporter = DatasetExporter()

   # Export for evaluation framework
   exporter.export_evaluation_format(
       input_dir="data/",
       output_file="evaluation_dataset.json",
       split_ratio={"train": 0.7, "test": 0.3}
   )

   # Export for training
   exporter.export_training_format(
       input_dir="data/",
       output_file="training_dataset.jsonl",
       include_trajectories=True
   )

   # Export statistics and analysis
   exporter.export_analysis(
       input_dir="data/",
       output_file="dataset_analysis.html",
       include_visualizations=True
   )

Performance Optimization
------------------------

Generation Efficiency
^^^^^^^^^^^^^^^^^^^^^

Optimize generation speed and resource usage:

.. code-block:: yaml

   performance:
     # Parallel processing
     max_workers: 8              # Concurrent threads
     batch_size: 20              # Items per batch
     
     # Caching
     enable_llm_cache: true      # Cache LLM responses
     cache_expiry_hours: 24      # Cache duration
     
     # Resource management
     memory_limit_mb: 4096       # Memory limit per worker
     timeout_seconds: 120        # Generation timeout
     
     # Quality vs speed trade-offs
     validation_level: "basic"   # basic, standard, comprehensive
     quality_threshold: 0.75     # Minimum quality score

Token Usage Optimization
^^^^^^^^^^^^^^^^^^^^^^^^^

Manage LLM API costs effectively:

.. code-block:: python

   # Monitor token usage
   usage_tracker = pipeline.get_token_usage()
   
   print(f"Clue generation: {usage_tracker['clue_tokens']:,} tokens")
   print(f"Scene generation: {usage_tracker['scene_tokens']:,} tokens") 
   print(f"Task generation: {usage_tracker['task_tokens']:,} tokens")
   print(f"Estimated cost: ${usage_tracker['estimated_cost']:.2f}")

   # Optimize prompts for efficiency
   pipeline.enable_prompt_optimization(
       target_reduction=0.2,  # 20% token reduction target
       preserve_quality=True  # Maintain generation quality
   )

Best Practices
--------------

Generation Strategy
^^^^^^^^^^^^^^^^^^^^

**Planning Generation**:

- Start with small test batches to validate quality
- Use diverse seed concepts for variety
- Balance task difficulty distribution
- Plan for dataset size requirements early

**Quality Management**:

- Set appropriate quality thresholds
- Review samples manually before large-scale generation  
- Use validation metrics to filter results
- Maintain generation logs for reproducibility

**Resource Management**:

- Monitor token usage and costs
- Use appropriate parallelism for available hardware
- Implement checkpointing for long generations
- Plan storage requirements for large datasets

Troubleshooting
^^^^^^^^^^^^^^^

**Common Issues**:

- **Low Quality Outputs**: Adjust prompts or increase model temperature
- **Generation Failures**: Check LLM connectivity and increase timeouts
- **Memory Issues**: Reduce batch size or worker count
- **Slow Processing**: Increase parallelism or optimize prompts

**Debugging Tools**:

.. code-block:: python

   # Enable debug logging
   pipeline.enable_debug_logging()
   
   # Inspect failed generations
   failures = pipeline.get_failed_items()
   for failure in failures:
       print(f"Item: {failure['item']}")
       print(f"Error: {failure['error']}")
       print(f"Stage: {failure['stage']}")

   # Validate configuration
   config_check = pipeline.validate_configuration()
   if not config_check.is_valid:
       print(f"Config errors: {config_check.errors}")

API Reference
-------------

For complete API documentation, see:

- :class:`data_generation.pipeline.Pipeline`
- :class:`data_generation.generators.base_generator.BaseGenerator`
- :class:`data_generation.generators.clue_generator.ClueGenerator`
- :class:`data_generation.generators.scene_generator.SceneGenerator`
- :class:`data_generation.generators.task_generator.TaskGenerator`
- :class:`data_generation.utils.task_validator.TaskValidator` 