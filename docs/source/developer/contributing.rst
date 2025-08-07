Contributing to OmniEmbodied
=============================

We welcome contributions from the community! This guide will help you get started with contributing to OmniEmbodied.

Ways to Contribute
------------------

There are many ways to contribute to OmniEmbodied:

🐛 **Report Bugs**
   Help us identify and fix issues by reporting bugs with detailed information.

✨ **Request Features**
   Suggest new features or improvements to existing functionality.

📝 **Improve Documentation**
   Help make our documentation clearer and more comprehensive.

💻 **Contribute Code**
   Fix bugs, implement features, or improve existing code.

🧪 **Add Tests**
   Help improve code quality by writing tests for existing functionality.

📊 **Share Results**
   Share your research results or interesting use cases with the community.

Getting Started
---------------

Development Setup
^^^^^^^^^^^^^^^^^

1. **Fork the Repository**:
   
   Fork the OmniEmbodied repository on GitHub to your account.

2. **Clone Your Fork**:

   .. code-block:: bash

      git clone https://github.com/ZJU-REAL/OmniEmbodied.git
      cd OmniEmbodied

3. **Create Development Environment**:

   .. code-block:: bash

      # Using conda (recommended)
      conda create -n omniembodied-dev python=3.8
      conda activate omniembodied-dev

      # Using virtualenv
      python -m venv omniembodied-dev
      source omniembodied-dev/bin/activate  # On Windows: omniembodied-dev\Scripts\activate

4. **Install in Development Mode**:

   .. code-block:: bash

      # Install main package
      pip install -e .
      
      # Install OmniSimulator
      cd OmniSimulator
      pip install -e .
      cd ..
      
      # Install development dependencies
      pip install -r requirements-dev.txt

5. **Verify Installation**:

   .. code-block:: bash

      python -c "import OmniSimulator; print('✅ OmniSimulator installed')"
      python -c "from evaluation import evaluation_manager; print('✅ Framework installed')"

Development Workflow
^^^^^^^^^^^^^^^^^^^^^

1. **Create Feature Branch**:

   .. code-block:: bash

      git checkout -b feature/your-feature-name

2. **Make Changes**:
   
   - Write code following our style guidelines
   - Add appropriate tests
   - Update documentation as needed

3. **Test Your Changes**:

   .. code-block:: bash

      # Run tests
      pytest tests/

      # Run code quality checks
      black .
      isort .
      flake8 .

4. **Commit Changes**:

   .. code-block:: bash

      git add .
      git commit -m "Add feature: brief description"

5. **Push and Create PR**:

   .. code-block:: bash

      git push origin feature/your-feature-name

   Then create a Pull Request on GitHub.

Code Standards
--------------

Python Code Style
^^^^^^^^^^^^^^^^^^

We follow PEP 8 with some additional conventions:

**Formatting:**
- Use Black for code formatting: ``black .``
- Use isort for import sorting: ``isort .``
- Line length: 88 characters (Black default)

**Naming Conventions:**
- Classes: ``PascalCase``
- Functions and variables: ``snake_case``
- Constants: ``UPPER_SNAKE_CASE``
- Private methods/attributes: ``_leading_underscore``

**Type Hints:**
- Use type hints for all public APIs
- Import types from ``typing`` when needed
- Use ``Optional[Type]`` for nullable parameters

.. code-block:: python

   from typing import Dict, List, Optional

   def process_scenarios(
       scenario_ids: List[str],
       config: Dict[str, Any],
       max_steps: Optional[int] = None
   ) -> List[Dict[str, Any]]:
       """Process scenarios with given configuration.
       
       Args:
           scenario_ids: List of scenario identifiers
           config: Configuration dictionary
           max_steps: Maximum steps per scenario (optional)
           
       Returns:
           List of processing results
       """
       # Implementation here
       pass

Documentation Standards
^^^^^^^^^^^^^^^^^^^^^^^^

**Docstrings:**
- Use Google-style docstrings
- Include Args, Returns, and Raises sections
- Provide usage examples for complex functions

.. code-block:: python

   def evaluate_agent(agent_id: str, scenarios: List[str]) -> Dict[str, float]:
       """Evaluate agent performance on given scenarios.
       
       Args:
           agent_id: Unique identifier for the agent
           scenarios: List of scenario IDs to evaluate
           
       Returns:
           Dictionary containing evaluation metrics:
           - 'success_rate': Proportion of successful completions
           - 'average_steps': Mean steps per scenario
           - 'error_rate': Proportion of failed scenarios
           
       Raises:
           ValueError: If agent_id is not found
           FileNotFoundError: If scenario files are missing
           
       Example:
           >>> results = evaluate_agent("llm_agent_1", ["00001", "00002"])
           >>> print(f"Success rate: {results['success_rate']:.2%}")
       """

**Comments:**
- Use comments sparingly for complex logic
- Prefer self-documenting code over extensive comments
- Explain "why" rather than "what" when commenting

Testing Guidelines
^^^^^^^^^^^^^^^^^^

**Test Organization:**
- Unit tests in ``tests/unit/``
- Integration tests in ``tests/integration/``
- Test data in ``tests/fixtures/``

**Test Writing:**
- Use pytest framework
- One test file per module: ``test_module_name.py``
- Descriptive test names: ``test_should_raise_error_when_invalid_config``

.. code-block:: python

   import pytest
   from evaluation.evaluator import Evaluator

   class TestEvaluator:
       def test_should_initialize_with_valid_config(self):
           config = {"model_name": "test", "max_steps": 10}
           evaluator = Evaluator(config)
           assert evaluator.config["model_name"] == "test"

       def test_should_raise_error_with_invalid_config(self):
           invalid_config = {}
           with pytest.raises(ValueError, match="model_name is required"):
               Evaluator(invalid_config)

Contribution Guidelines
-----------------------

Bug Reports
^^^^^^^^^^^

When reporting bugs, please include:

**Environment Information:**
- Python version
- OmniEmbodied version
- Operating system
- Hardware specifications (if relevant)

**Bug Description:**
- Clear, concise description of the issue
- Expected behavior vs. actual behavior
- Steps to reproduce the bug
- Error messages and stack traces

**Minimal Example:**
- Provide the smallest code example that reproduces the bug
- Include necessary configuration files
- Remove any sensitive information

.. code-block:: text

   **Bug Report Template:**
   
   ## Environment
   - Python: 3.8.10
   - OmniEmbodied: v1.0.0
   - OS: Ubuntu 20.04
   
   ## Description
   Simulation hangs when agent attempts to take an object that doesn't exist.
   
   ## Expected Behavior
   Should return error message and continue simulation.
   
   ## Actual Behavior
   Process hangs indefinitely without error message.
   
   ## Steps to Reproduce
   1. Load scenario "kitchen_basic.json"
   2. Execute action: `take nonexistent_object`
   3. Simulation hangs
   
   ## Code Example
   ```python
   engine = SimulationEngine()
   engine.load_scenario("kitchen_basic.json")
   result = engine.execute_action("agent_1", "take", {"target": "nonexistent_object"})
   # Hangs here
   ```

Feature Requests
^^^^^^^^^^^^^^^^^

When requesting features:

**Use Case Description:**
- Explain the problem you're trying to solve
- Describe your specific use case
- Explain why existing functionality isn't sufficient

**Proposed Solution:**
- Suggest how the feature might work
- Consider API design and user experience
- Think about backward compatibility

**Examples and Mockups:**
- Provide code examples of how you'd like to use the feature
- Include configuration examples if applicable

Pull Request Guidelines
^^^^^^^^^^^^^^^^^^^^^^^

**Before Submitting:**
- Ensure all tests pass
- Add tests for new functionality
- Update documentation as needed
- Follow code style guidelines
- Write clear, descriptive commit messages

**PR Description:**
- Reference any related issues
- Describe what the PR does and why
- List any breaking changes
- Include testing instructions

**PR Template:**

.. code-block:: text

   ## Description
   Brief description of changes and motivation.
   
   ## Related Issues
   Fixes #123
   
   ## Changes
   - [ ] New feature: X
   - [ ] Bug fix: Y
   - [ ] Documentation update
   - [ ] Breaking change
   
   ## Testing
   - [ ] Added new tests
   - [ ] All existing tests pass
   - [ ] Manual testing completed
   
   ## Documentation
   - [ ] Updated API documentation
   - [ ] Updated user guide
   - [ ] Updated examples

Review Process
^^^^^^^^^^^^^^

**Code Review:**
- All PRs require at least one approval
- Maintainers will review for code quality, design, and correctness
- Be responsive to feedback and questions
- Address all reviewer comments

**Automated Checks:**
- All tests must pass
- Code style checks must pass
- Documentation must build successfully

**Merge Process:**
- PRs are typically merged by maintainers
- We use "squash and merge" for clean history
- Large features may be merged in multiple PRs

Community Guidelines
--------------------

Code of Conduct
^^^^^^^^^^^^^^^^

We are committed to providing a welcoming and inclusive environment:

- **Be respectful**: Treat all community members with respect
- **Be collaborative**: Work together constructively
- **Be inclusive**: Welcome newcomers and different perspectives
- **Be professional**: Maintain professional communication

**Unacceptable Behavior:**
- Harassment or discrimination of any kind
- Offensive or inappropriate language
- Personal attacks or inflammatory comments
- Spam or off-topic discussions

Communication Channels
^^^^^^^^^^^^^^^^^^^^^^^

**GitHub Issues:**
- Bug reports
- Feature requests
- Technical discussions

**GitHub Discussions:**
- General questions
- Usage help
- Research discussions
- Community announcements

**Pull Request Comments:**
- Code review discussions
- Implementation feedback
- Design decisions

Getting Help
^^^^^^^^^^^^

**For Contributors:**
- Read this contributing guide thoroughly
- Check existing issues and PRs for similar work
- Ask questions in GitHub Discussions
- Reach out to maintainers for guidance

**For New Contributors:**
- Look for "good first issue" labels
- Start with documentation or test improvements
- Join community discussions to learn
- Don't hesitate to ask for help

Recognition
-----------

Contributors are recognized in several ways:

**Contributors File:**
All contributors are listed in the project's contributors file.

**Release Notes:**
Significant contributions are mentioned in release notes.

**GitHub Recognition:**
Contributors appear in the GitHub contributors graph.

**Research Citations:**
For significant algorithmic contributions, we may include co-authorship opportunities on related publications (with agreement from all parties).

Development Resources
---------------------

Useful Commands
^^^^^^^^^^^^^^^

.. code-block:: bash

   # Development setup
   pip install -e .[dev]
   
   # Run tests
   pytest tests/
   pytest tests/unit/  # Unit tests only
   pytest tests/integration/  # Integration tests only
   
   # Code quality
   black .  # Format code
   isort .  # Sort imports
   flake8 . # Check style
   mypy .   # Type checking
   
   # Documentation
   cd docs/
   make html  # Build docs
   make serve # Serve locally

Project Structure
^^^^^^^^^^^^^^^^^

Understanding the codebase structure:

.. code-block:: text

   OmniEmbodied/
   ├── OmniSimulator/           # Core simulation engine
   │   ├── core/               # Core simulation logic
   │   ├── action/             # Action system
   │   ├── agent/              # Agent interfaces
   │   ├── environment/        # Environment management
   │   └── utils/              # Simulation utilities
   ├── evaluation/             # Evaluation framework
   ├── modes/                  # Agent implementations
   ├── llm/                    # LLM integrations
   ├── config/                 # Configuration system
   ├── data_generation/        # Data generation tools
   ├── utils/                  # Global utilities
   ├── tests/                  # Test suite
   └── docs/                   # Documentation

Development Tips
^^^^^^^^^^^^^^^^

**Local Testing:**
- Test with different Python versions if possible
- Test on different operating systems when making system-level changes
- Use virtual environments to avoid dependency conflicts

**Performance Considerations:**
- Profile code for performance-critical changes
- Consider memory usage for large-scale simulations
- Test with realistic data sizes

**Debugging:**
- Use appropriate logging levels
- Add debug information for complex algorithms
- Include error context in exception messages

Thank You
---------

Thank you for contributing to OmniEmbodied! Your contributions help make embodied AI research more accessible and reproducible for the entire community.

For questions about contributing, please:
1. Check this guide first
2. Search existing issues and discussions
3. Open a new discussion if needed
4. Contact maintainers directly for urgent matters

We appreciate your time and effort in making OmniEmbodied better for everyone! 🚀 