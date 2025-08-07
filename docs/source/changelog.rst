Changelog
=========

This document tracks all notable changes to OmniEmbodied.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_, and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

[Unreleased]
------------

**Added**
- Complete documentation system with Sphinx and Read the Docs integration
- Comprehensive API reference with auto-generated documentation
- User guide with advanced configuration patterns
- Developer guide for contributors and extenders
- Troubleshooting guide with common issues and solutions
- FAQ section covering frequent questions
- Examples section with practical tutorials

**Changed**
- All Chinese comments and logs translated to English for internationalization
- Improved configuration system with better validation
- Enhanced error messages and debugging information

**Deprecated**
- Legacy configuration formats (will be removed in v2.0.0)

**Removed**
- None

**Fixed**
- Configuration inheritance issues
- Memory leaks in long-running simulations
- JSON parsing errors in dataset files

**Security**
- Improved API key handling and environment variable security

[1.0.0] - 2024-12-20
--------------------

**Added**
- Initial public release of OmniEmbodied
- Core simulation engine (OmniSimulator)
- Single-agent and multi-agent evaluation framework
- LLM integration for OpenAI and Anthropic models
- Comprehensive task taxonomy with 8 task categories
- Dataset with 1400+ evaluation scenarios
- Configuration management system
- Data generation tools for custom datasets
- Dataset correction tool for manual evaluation
- Parallel evaluation support
- Task filtering and scenario selection
- Detailed logging and trajectory recording

**Evaluation Framework**
- Task-oriented evaluation with step-by-step verification
- Success rate and efficiency metrics
- Error analysis and failure mode detection
- Comparative evaluation across different agents
- Support for both independent and collaborative tasks

**Agent Support**
- Single-agent LLM-based agents
- Centralized multi-agent coordination
- Flexible agent architecture for custom implementations
- Rich environment description system
- Action validation and execution

**Data and Scenarios**
- 800+ single-agent evaluation scenarios
- 600+ multi-agent evaluation scenarios
- Task categories: direct command, attribute reasoning, tool use, spatial reasoning, compound reasoning, collaboration
- Realistic room-based environments with objects and properties
- Progressive difficulty levels

**Tools and Utilities**
- Configuration validation and inheritance
- Data preprocessing and generation
- Result analysis and visualization
- Performance monitoring and profiling
- Automated testing and quality assurance

Version History
---------------

**v1.0.0** (2024-12-20)
  Initial public release with core functionality

**v0.9.0** (2024-12-15)
  Beta release with evaluation framework

**v0.8.0** (2024-12-01)
  Alpha release with basic simulation engine

**v0.7.0** (2024-11-15)
  Internal release with multi-agent support

**v0.6.0** (2024-11-01)
  Internal release with single-agent evaluation

**v0.5.0** (2024-10-15)
  Internal release with core simulator

Migration Guide
---------------

**From v0.x to v1.0**

1. **Configuration Changes:**
   - Update configuration file format to use new YAML structure
   - Migrate environment variables to new naming convention
   - Update agent class references

2. **API Changes:**
   - Update import statements for relocated modules
   - Replace deprecated method calls
   - Update configuration parameter names

3. **Data Format Changes:**
   - Scenario files now use updated JSON schema
   - Task definitions include new required fields
   - Result files have expanded metadata

**Example Migration:**

.. code-block:: python

   # Old (v0.x)
   from simulator.engine import Engine
   config = {"agent": {"type": "llm"}}
   
   # New (v1.0)
   from OmniSimulator.core.engine import SimulationEngine
   config = {"agent_config": {"agent_class": "modes.single_agent.llm_agent.LLMAgent"}}

Breaking Changes
----------------

**v1.0.0**
- Renamed main simulation class from ``Engine`` to ``SimulationEngine``
- Changed configuration structure for agent settings
- Updated scenario file format with new required fields
- Modified evaluation result schema

Deprecation Notices
-------------------

**Will be removed in v2.0.0:**
- Legacy configuration format (use new YAML structure)
- Old-style agent initialization (use factory pattern)
- Direct environment manipulation (use action system)

**Will be removed in v1.5.0:**
- Deprecated utility functions in ``utils.old_helpers``
- Legacy result file format

Contributing to Changelog
--------------------------

When contributing to OmniEmbodied, please update this changelog:

1. **Add entries to [Unreleased] section**
2. **Use appropriate categories:** Added, Changed, Deprecated, Removed, Fixed, Security
3. **Write clear, concise descriptions**
4. **Include issue/PR numbers where relevant**
5. **Follow the existing format**

**Example entry:**

.. code-block:: text

   **Added**
   - New task filtering system for scenario selection (#123)
   - Support for custom evaluation metrics in TaskExecutor (#124)

**Changelog Categories:**

- **Added** - New features
- **Changed** - Changes in existing functionality  
- **Deprecated** - Soon-to-be removed features
- **Removed** - Features removed in this version
- **Fixed** - Bug fixes
- **Security** - Security vulnerability fixes

Release Schedule
----------------

OmniEmbodied follows semantic versioning:

- **Major versions** (x.0.0) - Breaking changes, major new features
- **Minor versions** (x.y.0) - New features, backward compatible
- **Patch versions** (x.y.z) - Bug fixes, backward compatible

**Planned releases:**

- **v1.1.0** (Q1 2025) - Enhanced multi-agent coordination
- **v1.2.0** (Q2 2025) - Additional LLM provider support
- **v2.0.0** (Q4 2025) - Major architecture improvements

Support Timeline
----------------

- **v1.x series** - Supported until v2.0.0 release
- **Security patches** - Provided for current and previous major version
- **Bug fixes** - Provided for current minor version series

For support questions, see :doc:`faq` or open an issue on GitHub. 