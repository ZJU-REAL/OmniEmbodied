Evaluation System
=================

The evaluation system in OmniEmbodied Framework provides comprehensive benchmarking capabilities for embodied AI agents. It handles scenario management, parallel execution, performance measurement, and detailed result analysis.

.. toctree::
   :maxdepth: 2

Overview
--------

The evaluation system is designed for rigorous, reproducible research:

- **Standardized Benchmarks**: 1400+ curated scenarios across multiple task types
- **Parallel Execution**: Efficient evaluation with configurable parallelism
- **Comprehensive Metrics**: Success rates, efficiency measures, and error analysis
- **Flexible Configuration**: Support for custom evaluation protocols
- **Result Management**: Organized storage and analysis of experimental data

Core Components
---------------

Evaluation Manager
^^^^^^^^^^^^^^^^^^

The ``EvaluationManager`` serves as the central coordinator for all evaluation activities:

**Key Features**:

- Scenario selection and filtering
- Parallel execution management
- Result collection and aggregation
- Performance monitoring and optimization
- Experimental configuration management

.. code-block:: python

   from evaluation.evaluation_interface import EvaluationInterface

   # Run evaluation using the interface
   result = EvaluationInterface.run_evaluation(
       config_file="single_agent_config",  # Will resolve to config/baseline/
       agent_type="single",
       task_type="independent",
       scenario_selection={
           "dataset_type": "single",
           "scenario_range": {"start": "00001", "end": "00100"}
       }
   )
   
   print(f"Success rate: {result.get('success_rate', 0):.2%}")

Scenario Management
^^^^^^^^^^^^^^^^^^^

**Scenario Selector**:

The scenario selection system provides flexible filtering and sampling:

.. code-block:: python

   from evaluation.scenario_selector import ScenarioSelector

   # Define selection criteria
   selection_config = {
       "dataset_type": "single",
       "task_categories": ["direct_command", "attribute_reasoning"],
       "difficulty_levels": ["basic", "intermediate"],
       "scenario_count": 50
   }

   # Get scenario list
   scenarios = ScenarioSelector.get_scenario_list(config, selection_config)

**Scenario Types**:

- **Single-Agent Scenarios**: Independent task completion
- **Multi-Agent Scenarios**: Collaborative task scenarios
- **Progressive Difficulty**: From basic commands to complex reasoning
- **Specialized Tasks**: Domain-specific evaluation scenarios

Task Execution
^^^^^^^^^^^^^^

**Scenario Executor**:

Handles individual scenario execution with proper state management:

.. code-block:: python

   from evaluation.scenario_executor import ScenarioExecutor

   # Execute single scenario
   executor = ScenarioExecutor(config)
   result = executor.execute_scenario(
       scenario_id="00001",
       max_steps=50,
       timeout=300
   )

   # Result contains detailed execution information
   print(f"Scenario: {result['scenario_id']}")
   print(f"Success: {result['success']}")
   print(f"Steps taken: {result['steps_taken']}")
   print(f"Execution time: {result['execution_time']:.2f}s")

**Task Executor**:

Manages the execution lifecycle for individual tasks:

.. code-block:: python

   from evaluation.task_executor import TaskExecutor

   # Initialize task executor
   task_executor = TaskExecutor(agent_config, llm_config)

   # Execute task with detailed tracking
   result = task_executor.execute_task(
       scenario_data=scenario,
       task_config=task_config
   )

Evaluation Workflows
--------------------

Basic Evaluation Workflow
^^^^^^^^^^^^^^^^^^^^^^^^^

Standard evaluation process for single agents:

.. code-block:: python

   # 1. Configure evaluation parameters
   scenario_selection = {
       "dataset_type": "single",
       "scenario_range": {"start": "00001", "end": "00050"},
   }

   # 2. Run evaluation using interface
   result = EvaluationInterface.run_evaluation(
       config_file="single_agent_config", 
       agent_type="single",
       task_type="independent",
       scenario_selection=scenario_selection
   )

   # 3. Analyze results
   print(f"Overall success rate: {result.get('success_rate', 0):.2%}")
   print(f"Total scenarios: {result.get('total_scenarios', 0)}")

Multi-Agent Evaluation
^^^^^^^^^^^^^^^^^^^^^^

Evaluation workflow for multi-agent scenarios:

.. code-block:: python

   # Configure for multi-agent evaluation
   result = EvaluationInterface.run_evaluation(
       config_file="centralized_config",  # Will resolve to config/baseline/centralized_config.yaml
       agent_type="multi",
       task_type="collaborative",
       scenario_selection={
           "dataset_type": "multi",
           "scenario_range": {"start": "00001", "end": "00050"}
       }
   )

   print(f"Multi-agent success rate: {result.get('success_rate', 0):.2%}")

Parallel Evaluation
^^^^^^^^^^^^^^^^^^^

Configure parallel execution for efficient evaluation:

.. code-block:: yaml

   # Configuration for parallel evaluation
   parallel_evaluation:
     scenario_parallelism:
       max_parallel_scenarios: 5    # Number of scenarios to run simultaneously
       timeout_per_scenario: 300    # Timeout for individual scenarios
       
     resource_management:
       memory_limit_mb: 8192        # Memory limit per process
       cpu_cores: 4                 # CPU cores to use
       
     error_handling:
       max_retries: 3               # Retry failed scenarios
       continue_on_error: true      # Continue evaluation after failures

Performance Metrics
-------------------

Success Metrics
^^^^^^^^^^^^^^^

The evaluation system tracks multiple success criteria:

**Primary Metrics**:

- **Success Rate**: Percentage of completed tasks
- **Efficiency**: Steps taken relative to optimal solution
- **Completion Time**: Total execution time per scenario
- **Resource Usage**: Memory and computational requirements

**Secondary Metrics**:

- **Error Categories**: Classification of failure modes
- **Action Distribution**: Frequency of different action types
- **Exploration Efficiency**: Coverage of search space
- **Communication Patterns**: Inter-agent message analysis (multi-agent)

.. code-block:: python

   # Access detailed metrics
   metrics = results['detailed_metrics']
   
   print(f"Success rate by task type:")
   for task_type, rate in metrics['success_by_task_type'].items():
       print(f"  {task_type}: {rate:.2%}")
       
   print(f"Average steps by difficulty:")
   for difficulty, steps in metrics['steps_by_difficulty'].items():
       print(f"  {difficulty}: {steps:.1f}")

Error Analysis
^^^^^^^^^^^^^^

Comprehensive error categorization and analysis:

.. code-block:: python

   # Analyze failure modes
   error_analysis = results['error_analysis']
   
   print("Common failure modes:")
   for error_type, count in error_analysis['error_types'].items():
       percentage = (count / results['total_scenarios']) * 100
       print(f"  {error_type}: {count} ({percentage:.1f}%)")
   
   # Get detailed error information
   failed_scenarios = error_analysis['failed_scenarios']
   for failure in failed_scenarios[:5]:  # Show first 5 failures
       print(f"Scenario {failure['scenario_id']}: {failure['error_message']}")

Comparative Analysis
^^^^^^^^^^^^^^^^^^^^

Compare different models or configurations:

.. code-block:: python

   # Compare multiple evaluation runs
   from evaluation.analysis import ResultsAnalyzer

   analyzer = ResultsAnalyzer()
   
   # Load multiple result sets
   gpt4_results = analyzer.load_results("gpt-4_evaluation_results.json")
   claude_results = analyzer.load_results("claude_evaluation_results.json")
   
   # Generate comparison report
   comparison = analyzer.compare_results([
       ("GPT-4", gpt4_results),
       ("Claude-3", claude_results)
   ])
   
   print(comparison['summary'])

Configuration and Customization
-------------------------------

Evaluation Configuration
^^^^^^^^^^^^^^^^^^^^^^^

Comprehensive configuration options:

.. code-block:: yaml

   # evaluation_config.yaml
   evaluation:
     # Dataset selection
     dataset_type: "single"           # single, multi, mixed
     scenario_range:
       start: "00001"
       end: "00800" 
       
     # Task filtering
     task_filter:
       categories: ["direct_command", "attribute_reasoning"]
       difficulty_levels: ["basic", "intermediate", "advanced"]
       exclude_scenarios: []          # Specific scenarios to exclude
       
     # Execution parameters
     max_steps: 50                    # Maximum steps per scenario
     timeout: 300                     # Timeout in seconds
     max_retries: 3                   # Retries for failed scenarios
     
     # Output configuration
     save_trajectories: true          # Save detailed execution traces
     save_intermediate_states: false # Save state at each step
     output_format: "json"           # json, csv, both

Agent Configuration
^^^^^^^^^^^^^^^^^^^

Configure agent behavior for evaluation:

.. code-block:: yaml

   # agent_evaluation_config.yaml
   agent_config:
     # Core agent settings
     agent_class: "modes.single_agent.llm_agent.LLMAgent"
     max_history: 20                  # Maximum conversation history
     
     # Reasoning configuration
     use_chain_of_thought: true       # Enable CoT reasoning
     reflection_enabled: false        # Enable self-reflection
     
     # Performance settings
     action_timeout: 30               # Timeout per action
     retry_failed_actions: true       # Retry on action failure
     
     # Evaluation-specific settings
     detailed_logging: true           # Enable detailed logging
     save_reasoning_traces: true      # Save reasoning steps

Custom Evaluation Protocols
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Define custom evaluation procedures:

.. code-block:: python

   from evaluation.custom_evaluator import CustomEvaluator

   class DomainSpecificEvaluator(CustomEvaluator):
       def __init__(self, config):
           super().__init__(config)
           self.domain_metrics = {}
           
       def evaluate_scenario(self, scenario):
           # Standard evaluation
           result = super().evaluate_scenario(scenario)
           
           # Add domain-specific metrics
           domain_result = self.evaluate_domain_specific(scenario, result)
           result.update(domain_result)
           
           return result
           
       def evaluate_domain_specific(self, scenario, base_result):
           # Implement domain-specific evaluation logic
           return {
               'domain_score': self.calculate_domain_score(scenario),
               'custom_metrics': self.extract_custom_metrics(base_result)
           }

Result Management
-----------------

Result Storage
^^^^^^^^^^^^^^

Organized storage of evaluation results:

.. code-block:: python

   # Results are automatically saved with structured naming
   # Format: {model}_{dataset}_{timestamp}_{suffix}.json
   
   # Example result structure:
   results = {
       'metadata': {
           'model_name': 'gpt-4',
           'dataset_type': 'single',
           'evaluation_time': '2024-01-15T10:30:00',
           'total_scenarios': 100,
           'config_hash': 'abc123...'
       },
       'summary': {
           'success_rate': 0.85,
           'average_steps': 12.3,
           'total_time': 1800.5
       },
       'detailed_results': [
           {
               'scenario_id': '00001',
               'success': True,
               'steps_taken': 8,
               'execution_time': 15.2,
               'trajectory': [...]
           }
       ]
   }

Result Analysis
^^^^^^^^^^^^^^

Built-in analysis tools for result interpretation:

.. code-block:: python

   from evaluation.result_analyzer import ResultAnalyzer

   # Load and analyze results
   analyzer = ResultAnalyzer("evaluation_results.json")
   
   # Generate summary statistics
   summary = analyzer.generate_summary()
   print(summary)
   
   # Create visualizations
   analyzer.plot_success_by_task_type("success_by_task.png")
   analyzer.plot_steps_distribution("steps_distribution.png")
   analyzer.plot_error_analysis("error_analysis.png")
   
   # Export detailed report
   analyzer.export_detailed_report("evaluation_report.html")

Batch Processing
^^^^^^^^^^^^^^^^

Process multiple evaluation runs efficiently:

.. code-block:: python

   from evaluation.batch_processor import BatchProcessor

   # Define multiple evaluation configurations
   eval_configs = [
       {"model": "gpt-3.5-turbo", "scenarios": "00001-00100"},
       {"model": "gpt-4", "scenarios": "00001-00100"},
       {"model": "claude-3", "scenarios": "00001-00100"}
   ]

   # Process all configurations
   processor = BatchProcessor()
   all_results = processor.process_batch(eval_configs)
   
   # Generate comparative analysis
   comparison_report = processor.generate_comparison(all_results)

Best Practices
--------------

Evaluation Design
^^^^^^^^^^^^^^^^

**Scenario Selection**:

- Use stratified sampling for representative evaluation sets
- Include diverse task types and difficulty levels
- Validate scenario quality and consistency
- Consider domain-specific requirements

**Metric Selection**:

- Choose metrics aligned with research objectives
- Include both primary and secondary metrics
- Consider efficiency metrics alongside accuracy
- Use standardized metrics for comparability

Performance Optimization
^^^^^^^^^^^^^^^^^^^^^^^^

**Parallel Execution**:

- Configure parallelism based on available resources
- Monitor memory usage during parallel evaluation
- Implement proper error handling for parallel processes
- Use timeout mechanisms to prevent hanging evaluations

**Resource Management**:

- Set appropriate memory and CPU limits
- Monitor resource usage during evaluation
- Implement cleanup procedures for failed evaluations
- Consider cost implications of API usage

Reproducibility
^^^^^^^^^^^^^^^

**Configuration Management**:

- Use version control for evaluation configurations
- Document all experimental parameters
- Save configuration hashes with results
- Implement deterministic random seeding where possible

**Result Documentation**:

- Include comprehensive metadata with results
- Document evaluation environment and dependencies
- Save detailed execution traces for debugging
- Implement result validation and consistency checks

Troubleshooting
---------------

Common Issues
^^^^^^^^^^^^^

**Performance Problems**:

- High memory usage during parallel evaluation
- Slow execution due to API rate limits
- Timeout issues with complex scenarios
- Resource contention in multi-process execution

**Configuration Errors**:

- Missing or incorrect configuration parameters
- Incompatible agent and evaluation configurations
- Path and file access issues
- Version compatibility problems

**Result Inconsistencies**:

- Non-deterministic behavior in evaluations
- Inconsistent scenario interpretations
- Missing or corrupted result files
- Statistical significance issues

Debugging Tools
^^^^^^^^^^^^^^^

.. code-block:: python

   # Enable detailed debugging
   evaluator.enable_debug_mode()
   
   # Get execution traces
   trace = evaluator.get_last_execution_trace()
   
   # Validate evaluation configuration
   validation_result = evaluator.validate_configuration()
   
   # Monitor resource usage
   resource_stats = evaluator.get_resource_statistics()

API Reference
-------------

For complete API documentation, see:

- :class:`evaluation.evaluation_manager.EvaluationManager`
- :class:`evaluation.scenario_executor.ScenarioExecutor`
- :class:`evaluation.task_executor.TaskExecutor`
- :class:`evaluation.scenario_selector.ScenarioSelector` 