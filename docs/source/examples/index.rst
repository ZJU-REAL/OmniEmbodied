Examples
========

This section provides comprehensive examples demonstrating different aspects of OmniEmbodied. From basic usage to advanced customization, these examples will help you understand and utilize the platform effectively.

.. toctree::
   :maxdepth: 2

   basic_simulation

Quick Start Examples
--------------------

**Basic Single Agent Simulation:**

.. code-block:: python

   # examples/basic_simulation.py
   from examples.single_agent_example import main
   
   # Run with default configuration
   results = main()
   print(f"Success rate: {results['success_rate']:.2%}")

**Multi-Agent Collaboration:**

.. code-block:: python

   # examples/multi_agent_demo.py
   from examples.centralized_agent_example import main
   
   # Run centralized multi-agent scenario
   results = main("centralized_config")

**Task Filtering:**

.. code-block:: python

   # examples/task_filtering_demo.py
   from examples.task_filtering_example import main
   
   # Only direct command tasks
   results = main(categories=["direct_command"])

Example Categories
------------------

**Getting Started**:
- :doc:`basic_simulation` - Your first simulation
- Simple configuration modifications
- Understanding output and results

**Configuration**:
- :doc:`configuration_examples` - Advanced configuration patterns
- Environment variable usage
- Profile-based configurations

**Customization**:
- :doc:`custom_agents` - Building custom agent types
- Custom action implementations
- Environment modifications

**Evaluation**:
- :doc:`evaluation_workflows` - Systematic evaluation strategies
- Comparative studies
- Performance analysis

**Data**:
- :doc:`data_generation` - Creating custom datasets
- Scenario generation
- Data preprocessing

**Analysis**:
- :doc:`analysis_notebooks` - Jupyter notebook tutorials
- Result visualization
- Statistical analysis

Available Example Scripts
-------------------------

The ``examples/`` directory contains ready-to-run scripts:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Script
     - Description
   * - ``single_agent_example.py``
     - Basic single-agent task execution
   * - ``centralized_agent_example.py``
     - Multi-agent centralized coordination
   * - ``task_filtering_example.py``
     - Task category filtering demonstration
   * - ``config_usage_example.py``
     - Configuration system usage patterns
   * - ``results_analysis.ipynb``
     - Jupyter notebook for result analysis
   * - ``common_utils.py``
     - Shared utilities for examples

Running Examples
----------------

**Prerequisites:**

.. code-block:: bash

   # Ensure OmniEmbodied is installed
   cd OmniEmbodied
   pip install -e .
   pip install -e OmniSimulator/

**Basic Usage:**

.. code-block:: bash

   # Run single agent example
   python examples/single_agent_example.py

   # Run with custom configuration
   python examples/single_agent_example.py --config my_config.yaml

   # Run specific scenario
   python examples/single_agent_example.py --scenario 00001

**With Parameters:**

.. code-block:: bash

   # Filter by task type
   python examples/task_filtering_example.py --categories direct_command attribute_reasoning

   # Specify scenario range
   python examples/single_agent_example.py --start 00001 --end 00010

   # Enable debug mode
   python examples/single_agent_example.py --debug

Interactive Examples
--------------------

**Jupyter Notebooks:**

Launch Jupyter to explore interactive examples:

.. code-block:: bash

   jupyter notebook examples/results_analysis.ipynb

The notebooks cover:

- Loading and exploring simulation results
- Visualizing agent performance
- Statistical analysis of success rates
- Comparing different configurations
- Error analysis and debugging

**Python REPL Examples:**

.. code-block:: python

   # Interactive exploration
   from OmniSimulator.core.engine import SimulationEngine
   from examples.common_utils import load_config

   # Setup
   config = load_config("single_agent_config")
   engine = SimulationEngine()

   # Load scenario
   scenario = engine.load_scenario("00001")
   print(scenario.keys())

   # Examine environment
   env = scenario['environment']
   print(f"Rooms: {list(env['rooms'].keys())}")

Example Code Patterns
----------------------

**Configuration Loading:**

.. code-block:: python

   import yaml
   from pathlib import Path

   def load_config(config_path):
       """Load configuration with environment variable substitution."""
       with open(config_path, 'r') as f:
           config = yaml.safe_load(f)
       
       # Handle inheritance
       if 'extends' in config:
           base_path = Path(config_path).parent / f"{config['extends']}.yaml"
           base_config = load_config(base_path)
           base_config.update(config)
           config = base_config
       
       return config

**Error Handling:**

.. code-block:: python

   def safe_simulation_run(engine, scenario_id):
       """Run simulation with comprehensive error handling."""
       try:
           results = engine.run_simulation(scenario_id)
           return results
       except KeyboardInterrupt:
           print("Simulation interrupted by user")
           return {"status": "interrupted"}
       except Exception as e:
           print(f"Simulation failed: {str(e)}")
           return {"status": "failed", "error": str(e)}

**Result Processing:**

.. code-block:: python

   def analyze_results(results):
       """Extract key metrics from simulation results."""
       if results["status"] != "completed":
           return None
       
       metrics = {
           'success_rate': results.get('success_rate', 0.0),
           'average_steps': results.get('average_steps', 0),
           'total_scenarios': len(results.get('scenarios', [])),
           'task_breakdown': results.get('task_breakdown', {})
       }
       
       return metrics

Custom Example Template
-----------------------

Use this template to create your own examples:

.. code-block:: python

   #!/usr/bin/env python3
   """
   Custom OmniEmbodied Example
   
   Description: [What this example demonstrates]
   Usage: python my_example.py [options]
   """

   import argparse
   import logging
   from pathlib import Path

   # Import OmniEmbodied components
   from examples.common_utils import load_config, setup_logging
   from evaluation.evaluation_manager import EvaluationManager

   def main():
       """Main example function."""
       parser = argparse.ArgumentParser(description="Custom Example")
       parser.add_argument("--config", default="base_config")
       parser.add_argument("--debug", action="store_true")
       args = parser.parse_args()

       # Setup
       if args.debug:
           setup_logging(logging.DEBUG)
       
       config = load_config(args.config)
       
       # Your example logic here
       print("Running custom example...")
       
       # Example: Run evaluation
       evaluator = EvaluationManager(config)
       results = evaluator.evaluate_scenarios(["00001", "00002"])
       
       # Process and display results
       print(f"Completed {len(results)} scenarios")
       success_rate = sum(r.get('success', False) for r in results) / len(results)
       print(f"Success rate: {success_rate:.2%}")

   if __name__ == "__main__":
       main()

Community Examples
-------------------

**Contributing Examples:**

We welcome community contributions of examples! To contribute:

1. Create a clear, well-documented example
2. Include appropriate error handling
3. Add command-line options for flexibility
4. Test with different configurations
5. Submit a pull request

**Example Ideas:**

- Custom evaluation metrics
- Domain-specific scenarios
- Performance benchmarking
- Integration with other tools
- Educational tutorials

**Sharing Examples:**

- Post in GitHub Discussions
- Include in pull requests
- Share in research papers
- Use in educational materials

Getting Help with Examples
---------------------------

**If examples don't work:**

1. Check your installation: ``python -c "import OmniSimulator"``
2. Verify configuration files exist and are valid
3. Check API keys and environment variables
4. Enable debug logging: ``--debug`` flag

**For understanding examples:**

1. Read the code comments carefully
2. Try modifying parameters to see effects
3. Use interactive debugging (``import pdb; pdb.set_trace()``)
4. Ask questions in GitHub Discussions

**Requesting new examples:**

- Open an issue with "Example Request" label
- Describe the use case or concept to demonstrate
- Provide any relevant context or requirements

The examples are designed to be educational and practical. They demonstrate real-world usage patterns and best practices for OmniEmbodied development. 