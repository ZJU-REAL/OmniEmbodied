Evaluation Workflows
====================

This guide provides practical workflows for evaluating embodied AI agents using the OmniEmbodied Framework. It covers everything from basic evaluations to advanced research protocols.

.. toctree::
   :maxdepth: 2

Getting Started with Evaluation
-------------------------------

Quick Start Evaluation
^^^^^^^^^^^^^^^^^^^^^

Run your first evaluation in just a few steps:

.. code-block:: bash

   # 1. Set up your API key
   export OPENAI_API_KEY="your-api-key-here"

   # 2. Run a basic evaluation
   cd scripts/
   bash qwen7b-wg.sh

   # 3. Check results
   ls ../output/

This runs a single-agent evaluation on a subset of scenarios using Qwen-7B with guidance prompts.

Configuration Overview
^^^^^^^^^^^^^^^^^^^^^

The evaluation system uses hierarchical configuration:

.. code-block:: text

   config/
   ├── baseline/
   │   ├── base_config.yaml          # Base settings
   │   ├── single_agent_config.yaml  # Single-agent configuration
   │   ├── centralized_config.yaml   # Multi-agent configuration
   │   ├── llm_config.yaml           # LLM settings
   │   └── prompts_config.yaml       # Prompt templates
   └── data_generation/              # Data generation configs

Basic Evaluation Workflow
--------------------------

Step 1: Configure Your LLM
^^^^^^^^^^^^^^^^^^^^^^^^^^

Edit the LLM configuration for your model:

.. code-block:: yaml

   # config/baseline/llm_config.yaml
   api:
     provider: "openai"              # openai, anthropic, vllm
     model_name: "gpt-4"
     base_url: "https://api.openai.com/v1"
     api_key_env: "OPENAI_API_KEY"
     
   generation:
     temperature: 0.1
     max_tokens: 512
     timeout: 60

Step 2: Select Evaluation Scenarios
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Configure which scenarios to evaluate:

.. code-block:: yaml

   # In your agent config file
   evaluation:
     dataset_type: "single"          # single, multi, mixed
     scenario_range:
       start: "00001"
       end: "00100"                  # Evaluate first 100 scenarios
     
     # Or use specific scenarios
     scenario_list: ["00001", "00002", "00042", "00078"]
     
     # Or filter by task type
     task_filter:
       categories: ["direct_command", "attribute_reasoning"]
       exclude_categories: []

Step 3: Run the Evaluation
^^^^^^^^^^^^^^^^^^^^^^^^^^

Execute the evaluation using Python:

.. code-block:: python

   from evaluation.evaluation_manager import EvaluationManager

   # Initialize evaluator
   evaluator = EvaluationManager(
       config_file="single_agent_config",
       agent_type="single",
       task_type="independent",
       scenario_selection={
           "dataset_type": "single",
           "scenario_range": {"start": "00001", "end": "00050"}
       }
   )

   # Run evaluation
   print("Starting evaluation...")
   results = evaluator.run_evaluation()

   # Print results
   print(f"Success rate: {results['success_rate']:.2%}")
   print(f"Average steps: {results['average_steps']:.1f}")
   print(f"Total time: {results['total_time']:.1f} seconds")

Step 4: Analyze Results
^^^^^^^^^^^^^^^^^^^^^^

Results are automatically saved and can be analyzed:

.. code-block:: python

   # Load and analyze results
   from evaluation.result_analyzer import ResultAnalyzer

   analyzer = ResultAnalyzer("path/to/results.json")
   
   # Generate summary report
   summary = analyzer.generate_summary()
   print(summary)
   
   # Create visualizations
   analyzer.plot_success_by_task_type("success_analysis.png")
   analyzer.plot_error_distribution("error_analysis.png")
   
   # Export detailed report
   analyzer.export_html_report("evaluation_report.html")

Advanced Evaluation Workflows
-----------------------------

Comparative Evaluation
^^^^^^^^^^^^^^^^^^^^^^

Compare multiple models or configurations:

.. code-block:: python

   from evaluation.batch_evaluator import BatchEvaluator

   # Define evaluation configurations
   configs = [
       {
           "name": "GPT-4",
           "config_file": "gpt4_config.yaml",
           "llm_overrides": {"model_name": "gpt-4"}
       },
       {
           "name": "GPT-3.5-Turbo", 
           "config_file": "gpt35_config.yaml",
           "llm_overrides": {"model_name": "gpt-3.5-turbo"}
       },
       {
           "name": "Qwen-7B",
           "config_file": "qwen_config.yaml",
           "llm_overrides": {"model_name": "Qwen2.5-7B-Instruct"}
       }
   ]

   # Run comparative evaluation
   batch_evaluator = BatchEvaluator()
   comparison_results = batch_evaluator.run_comparison(
       configs=configs,
       scenarios={"start": "00001", "end": "00200"},
       parallel=True
   )

   # Generate comparison report
   batch_evaluator.generate_comparison_report(
       results=comparison_results,
       output_file="model_comparison.html"
   )

Multi-Agent Evaluation
^^^^^^^^^^^^^^^^^^^^^^

Evaluate collaborative agent scenarios:

.. code-block:: python

   # Configure for multi-agent evaluation
   evaluator = EvaluationManager(
       config_file="centralized_config",
       agent_type="multi",
       task_type="collaborative",
       scenario_selection={
           "dataset_type": "multi",
           "scenario_range": {"start": "00001", "end": "00300"}
       }
   )

   # Run multi-agent evaluation
   results = evaluator.run_evaluation()

   # Analyze collaboration patterns
   collaboration_metrics = results['collaboration_analysis']
   print(f"Coordination success rate: {collaboration_metrics['coordination_success']:.2%}")
   print(f"Communication efficiency: {collaboration_metrics['communication_efficiency']:.2f}")

Hyperparameter Optimization
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Systematically optimize agent parameters:

.. code-block:: python

   from evaluation.hyperparameter_optimizer import HyperparameterOptimizer

   # Define parameter search space
   search_space = {
       "temperature": [0.0, 0.1, 0.2, 0.3],
       "max_history": [10, 20, 30],
       "use_chain_of_thought": [True, False]
   }

   # Initialize optimizer
   optimizer = HyperparameterOptimizer(
       base_config="single_agent_config.yaml",
       search_space=search_space
   )

   # Run optimization
   best_params = optimizer.optimize(
       scenarios={"start": "00001", "end": "00100"},
       optimization_metric="success_rate",
       max_trials=20
   )

   print(f"Best parameters: {best_params}")
   print(f"Best score: {best_params['score']:.3f}")

Custom Evaluation Protocols
---------------------------

Domain-Specific Evaluation
^^^^^^^^^^^^^^^^^^^^^^^^^^

Create custom evaluation protocols for specific domains:

.. code-block:: python

   from evaluation.custom_evaluator import CustomEvaluator

   class KitchenTaskEvaluator(CustomEvaluator):
       def __init__(self, config):
           super().__init__(config)
           self.kitchen_specific_metrics = {}
           
       def evaluate_scenario(self, scenario_id):
           # Run standard evaluation
           base_result = super().evaluate_scenario(scenario_id)
           
           # Add domain-specific evaluation
           kitchen_score = self.evaluate_kitchen_skills(
               scenario_id, base_result
           )
           
           # Combine results
           base_result.update({
               'kitchen_proficiency': kitchen_score,
               'safety_compliance': self.check_safety_rules(base_result),
               'efficiency_rating': self.calculate_efficiency(base_result)
           })
           
           return base_result

   # Use custom evaluator
   kitchen_evaluator = KitchenTaskEvaluator(config)
   results = kitchen_evaluator.run_evaluation()

Ablation Studies
^^^^^^^^^^^^^^^

Systematically test component contributions:

.. code-block:: python

   from evaluation.ablation_study import AblationStudy

   # Define components to ablate
   components = {
       "chain_of_thought": {"use_chain_of_thought": False},
       "memory": {"max_history": 0},
       "guidance": {"use_guidance_prompts": False},
       "exploration": {"exploration_strategy": "random"}
   }

   # Run ablation study
   ablation = AblationStudy(
       baseline_config="single_agent_config.yaml",
       components=components
   )

   results = ablation.run_study(
       scenarios={"start": "00001", "end": "00200"}
   )

   # Analyze component importance
   importance = ablation.calculate_component_importance(results)
   for component, impact in importance.items():
       print(f"{component}: {impact:.1%} impact on performance")

Production Evaluation Workflows
-------------------------------

Continuous Integration
^^^^^^^^^^^^^^^^^^^^^

Set up automated evaluation for model updates:

.. code-block:: yaml

   # .github/workflows/evaluation.yml
   name: Agent Evaluation
   
   on:
     push:
       branches: [main]
     pull_request:
       branches: [main]
   
   jobs:
     evaluate:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         
         - name: Setup Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.8'
             
         - name: Install dependencies
           run: |
             pip install -e .
             pip install -e OmniSimulator/
             
         - name: Run evaluation
           env:
             OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
           run: |
             python -m evaluation.ci_runner \
               --config single_agent_config \
               --scenarios 00001:00050 \
               --output-format json
             
         - name: Upload results
           uses: actions/upload-artifact@v3
           with:
             name: evaluation-results
             path: output/

Performance Monitoring
^^^^^^^^^^^^^^^^^^^^^^

Monitor agent performance over time:

.. code-block:: python

   from evaluation.performance_monitor import PerformanceMonitor

   # Set up monitoring
   monitor = PerformanceMonitor(
       baseline_results="baseline_results.json",
       alert_threshold=0.05  # 5% performance drop triggers alert
   )

   # Run regular evaluation
   current_results = evaluator.run_evaluation()
   
   # Check for performance regression
   regression_check = monitor.check_regression(current_results)
   
   if regression_check.has_regression:
       print(f"Performance regression detected!")
       print(f"Decline: {regression_check.decline:.1%}")
       print(f"Affected tasks: {regression_check.affected_tasks}")
       
       # Send alert (implement your alerting system)
       send_alert(regression_check)

Large-Scale Evaluation
^^^^^^^^^^^^^^^^^^^^^^

Handle evaluation at scale:

.. code-block:: python

   # Configure for large-scale evaluation
   large_scale_config = {
       "parallel_evaluation": {
           "scenario_parallelism": {
               "max_parallel_scenarios": 10,
               "timeout_per_scenario": 600
           },
           "resource_management": {
               "memory_limit_mb": 8192,
               "cpu_cores": 8
           }
       }
   }

   # Run large-scale evaluation
   evaluator = EvaluationManager(
       config_file="large_scale_config.yaml",
       scenario_selection={
           "dataset_type": "single",
           "scenario_range": {"start": "00001", "end": "00800"}
       },
       custom_config=large_scale_config
   )

   results = evaluator.run_evaluation()

Best Practices
--------------

Evaluation Design
^^^^^^^^^^^^^^^^

**Scenario Selection Strategy**:

- Start with a representative sample (50-100 scenarios)
- Include diverse task types and difficulty levels
- Use stratified sampling for balanced evaluation
- Reserve held-out test sets for final evaluation

**Baseline Establishment**:

.. code-block:: python

   # Establish baseline performance
   baseline_evaluator = EvaluationManager(
       config_file="baseline_config.yaml",
       scenario_selection={"dataset_type": "single", "scenario_range": {"start": "00001", "end": "00200"}}
   )
   
   baseline_results = baseline_evaluator.run_evaluation()
   
   # Save as reference
   with open("baseline_performance.json", "w") as f:
       json.dump(baseline_results, f)

**Statistical Significance**:

.. code-block:: python

   from evaluation.statistical_analysis import StatisticalAnalyzer

   analyzer = StatisticalAnalyzer()
   
   # Test statistical significance
   significance_test = analyzer.compare_performance(
       results_a=model_a_results,
       results_b=model_b_results,
       alpha=0.05
   )
   
   if significance_test.is_significant:
       print(f"Significant improvement: p={significance_test.p_value:.4f}")
   else:
       print("No statistically significant difference")

Resource Management
^^^^^^^^^^^^^^^^^^

**Cost Optimization**:

.. code-block:: python

   # Monitor and optimize API costs
   from evaluation.cost_monitor import CostMonitor

   cost_monitor = CostMonitor(
       max_daily_cost=100.0,  # $100 daily limit
       cost_per_token={"gpt-4": 0.00003, "gpt-3.5-turbo": 0.000002}
   )

   # Check cost before large evaluation
   estimated_cost = cost_monitor.estimate_evaluation_cost(
       scenarios=800,
       avg_tokens_per_scenario=1500,
       model="gpt-4"
   )

   if estimated_cost > cost_monitor.max_daily_cost:
       print(f"Evaluation cost (${estimated_cost:.2f}) exceeds daily limit")
       # Consider using smaller model or fewer scenarios

**Resource Monitoring**:

.. code-block:: python

   # Monitor resource usage during evaluation
   import psutil
   import time

   def monitor_resources():
       while evaluation_running:
           cpu_percent = psutil.cpu_percent(interval=1)
           memory_percent = psutil.virtual_memory().percent
           
           if cpu_percent > 90 or memory_percent > 85:
               logger.warning(f"High resource usage: CPU {cpu_percent}%, Memory {memory_percent}%")
           
           time.sleep(10)

Troubleshooting
--------------

Common Issues
^^^^^^^^^^^^

**Low Success Rates**:

1. Check prompt templates and system messages
2. Verify scenario compatibility with agent capabilities
3. Review action validation and error messages
4. Increase max_steps or timeout values

.. code-block:: python

   # Debug low performance
   debug_evaluator = EvaluationManager(
       config_file="debug_config.yaml",
       debug_mode=True
   )
   
   # Run on small subset with detailed logging
   debug_results = debug_evaluator.run_evaluation()
   
   # Analyze failure patterns
   failures = debug_results['failed_scenarios']
   for failure in failures[:5]:
       print(f"Scenario: {failure['scenario_id']}")
       print(f"Error: {failure['error_message']}")
       print(f"Last action: {failure['last_action']}")

**Memory Issues**:

.. code-block:: python

   # Reduce memory usage
   memory_optimized_config = {
       "parallel_evaluation": {
           "scenario_parallelism": {
               "max_parallel_scenarios": 2,  # Reduce parallelism
           }
       },
       "agent_config": {
           "max_history": 10  # Limit conversation history
       }
   }

**Timeout Problems**:

.. code-block:: python

   # Adjust timeouts for complex scenarios
   timeout_config = {
       "execution": {
           "max_steps_per_task": 100,  # Increase step limit
           "timeout_per_step": 60,     # Increase per-step timeout
           "total_timeout": 1800       # 30-minute total timeout
       }
   }

Error Analysis
^^^^^^^^^^^^^

Systematic error analysis:

.. code-block:: python

   from evaluation.error_analyzer import ErrorAnalyzer

   analyzer = ErrorAnalyzer()
   
   # Analyze error patterns
   error_analysis = analyzer.analyze_errors(results)
   
   print("Most common errors:")
   for error_type, count in error_analysis['error_frequency'].items():
       print(f"  {error_type}: {count} occurrences")
   
   # Get error-specific insights
   spatial_errors = analyzer.get_spatial_errors(results)
   action_errors = analyzer.get_action_errors(results)
   
   # Generate improvement suggestions
   suggestions = analyzer.generate_improvement_suggestions(error_analysis)
   for suggestion in suggestions:
       print(f"💡 {suggestion}")

Performance Optimization
^^^^^^^^^^^^^^^^^^^^^^^

Optimize evaluation performance:

.. code-block:: python

   # Profile evaluation bottlenecks
   from evaluation.profiler import EvaluationProfiler

   profiler = EvaluationProfiler()
   
   with profiler:
       results = evaluator.run_evaluation()
   
   # Analyze performance bottlenecks
   profile_report = profiler.get_report()
   print("Time breakdown:")
   for component, time_spent in profile_report.items():
       print(f"  {component}: {time_spent:.1f}s")

   # Optimization recommendations
   optimizations = profiler.get_optimization_recommendations()
   for opt in optimizations:
       print(f"⚡ {opt}")

Next Steps
----------

After completing your evaluation:

1. **Analyze Results**: Use the analysis tools to understand agent performance
2. **Compare Baselines**: Establish performance benchmarks for your domain
3. **Iterate and Improve**: Use insights to improve agent design
4. **Share Findings**: Document results and contribute to the research community

For more advanced topics, see:

- :doc:`../examples/custom_evaluation_protocols` - Creating custom evaluation procedures
- :doc:`../developer/extending_evaluation` - Extending the evaluation framework
- :doc:`../framework/configuration` - Advanced configuration options 