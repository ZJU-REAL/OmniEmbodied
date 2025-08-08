Developer Guide
===============

Welcome to the OmniEmbodied developer documentation. This guide covers everything you need to know for contributing to and extending OmniEmbodied.

.. toctree::
   :maxdepth: 2

   contributing

Getting Started
---------------

**For Contributors**:

- :doc:`contributing` - How to contribute to the project
- :doc:`testing` - Running tests and ensuring code quality
- Development setup and workflow

**For Extenders**:

- :doc:`extending` - Creating custom components and integrations
- :doc:`architecture` - Understanding the system design
- Plugin development and integration points

**For Maintainers**:

- :doc:`debugging` - Debugging techniques and tools
- :doc:`release_process` - Release procedures and guidelines
- Code review and maintenance practices

Development Environment
-----------------------

**Prerequisites**:

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/ZJU-REAL/OmniEmbodied.git
   cd OmniEmbodied

   # Create development environment
   conda create -n omniembodied-dev python=3.8
   conda activate omniembodied-dev

   # Install in development mode
   pip install -e .
   pip install -e OmniSimulator/

   # Install development dependencies
   pip install -r requirements-dev.txt

**Development Dependencies**:

.. code-block:: bash

   # Testing
   pytest>=6.0.0
   pytest-cov>=2.10.0
   pytest-mock>=3.3.0

   # Code Quality
   black>=21.0.0
   flake8>=3.8.0
   isort>=5.9.0
   mypy>=0.910

   # Documentation
   sphinx>=4.0.0
   sphinx-rtd-theme>=1.0.0

Code Organization
-----------------

OmniEmbodied follows a modular architecture:

.. code-block:: text

   OmniEmbodied/
   ├── OmniSimulator/           # Core simulation engine
   │   ├── core/               # Core simulation logic
   │   ├── action/             # Action system
   │   ├── agent/              # Agent interfaces
   │   ├── environment/        # Environment management
   │   └── utils/              # Utilities and helpers
   ├── evaluation/             # Evaluation framework
   ├── modes/                  # Agent implementation modes
   │   ├── single_agent/       # Single agent implementations
   │   └── centralized/        # Multi-agent implementations
   ├── llm/                    # LLM integrations
   ├── config/                 # Configuration management
   ├── data_generation/        # Data generation tools
   └── utils/                  # Global utilities

**Key Design Principles**:

- **Modularity**: Clear separation of concerns
- **Extensibility**: Plugin architecture for custom components
- **Testability**: Comprehensive test coverage
- **Documentation**: Self-documenting code and comprehensive docs

Development Workflow
--------------------

**Standard Workflow**:

1. **Create Feature Branch**:

   .. code-block:: bash

      git checkout -b feature/your-feature-name

2. **Implement Changes**:

   - Write code following project conventions
   - Add comprehensive tests
   - Update documentation as needed

3. **Run Quality Checks**:

   .. code-block:: bash

      # Format code
      black .
      isort .

      # Check style
      flake8 .

      # Type checking
      mypy .

      # Run tests
      pytest tests/

4. **Submit Pull Request**:

   - Create pull request with clear description
   - Link to related issues
   - Ensure CI passes

**Code Standards**:

- **Python Style**: Follow PEP 8 with Black formatting
- **Type Hints**: Use type hints for all public APIs
- **Documentation**: Docstrings for all classes and public methods
- **Testing**: Comprehensive unit tests for new functionality

Testing Strategy
-----------------

OmniEmbodied uses a comprehensive testing approach:

**Unit Tests**:

.. code-block:: python

   import pytest
   from OmniSimulator.core.engine import SimulationEngine

   def test_engine_initialization():
       engine = SimulationEngine()
       assert engine is not None
       assert engine.state is not None

**Integration Tests**:

.. code-block:: python

   def test_full_simulation_workflow():
       engine = SimulationEngine()
       results = engine.run_simulation(scenario_id="test_scenario")
       assert results["status"] == "completed"

**Performance Tests**:

.. code-block:: python

   import time

   def test_simulation_performance():
       start_time = time.time()
       # Run simulation
       duration = time.time() - start_time
       assert duration < 60  # Should complete within 1 minute

**Test Organization**:

.. code-block:: text

   tests/
   ├── unit/                   # Unit tests
   │   ├── test_engine.py
   │   ├── test_actions.py
   │   └── test_agents.py
   ├── integration/            # Integration tests
   │   ├── test_simulation.py
   │   └── test_evaluation.py
   ├── fixtures/               # Test data and fixtures
   └── conftest.py            # Pytest configuration

Documentation Standards
-----------------------

**Code Documentation**:

.. code-block:: python

   class SimulationEngine:
       """Main simulation engine for OmniEmbodied.
       
       The SimulationEngine coordinates between agents, environments,
       and task verification systems to run embodied AI simulations.
       
       Args:
           config: Configuration dictionary or ConfigManager instance
           
       Attributes:
           state: Current simulation state
           agents: Registered agents
           environment: Environment manager
           
       Example:
           >>> engine = SimulationEngine()
           >>> results = engine.run_simulation("00001")
           >>> print(results["success_rate"])
       """

**API Documentation**:

- Use Google-style docstrings
- Include parameter types and return values
- Provide usage examples
- Document exceptions and edge cases

**User Documentation**:

- Write documentation from user perspective
- Include practical examples
- Provide troubleshooting guidance
- Keep documentation up-to-date with code changes

Debugging and Profiling
------------------------

**Logging Configuration**:

.. code-block:: python

   import logging
   
   # Enable debug logging
   logging.basicConfig(level=logging.DEBUG)
   
   # For specific modules
   logger = logging.getLogger("OmniSimulator.core")
   logger.setLevel(logging.DEBUG)

**Performance Profiling**:

.. code-block:: python

   import cProfile
   import pstats
   
   # Profile simulation
   pr = cProfile.Profile()
   pr.enable()
   
   # Run simulation
   engine.run_simulation("00001")
   
   pr.disable()
   stats = pstats.Stats(pr)
   stats.sort_stats('cumulative')
   stats.print_stats()

**Common Debugging Techniques**:

- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- Add timing information for performance analysis
- Use assertions for internal consistency checks
- Implement graceful error handling and recovery

Extension Points
----------------

OmniEmbodied is designed for extensibility:

**Custom Actions**:

.. code-block:: python

   from OmniSimulator.action.actions.base_action import BaseAction

   class CustomAction(BaseAction):
       def execute(self, agent, target, **kwargs):
           # Custom action logic
           return result

**Custom Agents**:

.. code-block:: python

   from core.base_agent import BaseAgent

   class CustomAgent(BaseAgent):
       def decide_action(self, observation):
           # Custom decision logic
           return action

**Custom Evaluators**:

.. code-block:: python

   from evaluation.evaluator import BaseEvaluator

   class CustomEvaluator(BaseEvaluator):
       def evaluate(self, results):
           # Custom evaluation logic
           return metrics

Community Guidelines
--------------------

**Communication**:

- Be respectful and constructive in all interactions
- Use clear, descriptive commit messages
- Provide detailed pull request descriptions
- Respond promptly to code review feedback

**Code Review Process**:

- All changes require at least one approval
- Automated tests must pass
- Documentation must be updated
- Breaking changes require discussion

**Issue Management**:

- Use appropriate labels and milestones
- Provide clear reproduction steps for bugs
- Include system information and error messages
- Link related issues and pull requests

**Community Support**:

- Help answer questions in issues
- Review pull requests from other contributors
- Share knowledge and best practices
- Mentor new contributors

Next Steps
----------

Ready to contribute? Here's what to do next:

1. **Set up Development Environment** - Follow the setup instructions above
2. **Read Contributing Guide** - Review :doc:`contributing` for detailed guidelines
3. **Understand Architecture** - Study :doc:`architecture` to understand the system
4. **Pick an Issue** - Find a good first issue on GitHub to work on
5. **Join the Community** - Participate in issues and code reviews

For specific development tasks:

- **Adding Features**: See :doc:`extending` for extension patterns
- **Fixing Bugs**: Check :doc:`debugging` for troubleshooting techniques
- **Writing Tests**: Review :doc:`testing` for testing best practices
- **Improving Docs**: Documentation contributions are always welcome! 