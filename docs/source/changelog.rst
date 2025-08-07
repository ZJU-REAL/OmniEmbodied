Changelog
=========

This document tracks all notable changes to OmniEmbodied.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_, and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

[1.0.0] - 2025-08-07
--------------------

**Initial Release**

This is the first public release of OmniEmbodied: A Comprehensive Benchmark for Embodied Multi-Agent Systems.

**Added**
- Core OmniSimulator simulation engine with text-based environment representation
- Comprehensive EAR-Bench evaluation suite with 1,500 scenarios
- Multi-agent evaluation framework supporting single-agent and multi-agent tasks
- LLM integration supporting multiple providers (OpenAI, DeepSeek, Qwen, etc.)
- Task categories: tool reasoning, implicit collaboration, compound reasoning
- Automated data generation pipeline for scenario creation
- Configuration management system with YAML-based configuration
- Documentation with Sphinx and Read the Docs integration
- Evaluation metrics for success rates, step efficiency, and performance analysis
- Examples and tutorials for quick start

**Core Features**
- **OmniSimulator Engine**: Text-based simulation with physical constraints and dynamic capabilities
- **EAR-Bench Dataset**: 1,500 diverse scenarios across household and industrial domains  
- **Multi-Agent Support**: Single-agent and multi-agent coordination scenarios
- **LLM Integration**: Support for various language model providers with standardized interfaces
- **Evaluation Framework**: Comprehensive benchmarking with detailed performance metrics
- **Data Generation Tools**: Automated scenario generation and task creation pipeline

**Task Categories**
- Tool reasoning: Dynamic capability acquisition and tool usage
- Implicit collaboration: Autonomous coordination without explicit directives  
- Compound reasoning: Complex multi-step problem solving
- Physical reasoning: Understanding constraints and spatial relationships

**Technical Highlights**
- Text-based environment representation for LLM compatibility
- Dynamic capability system allowing agents to acquire tools as needed
- Comprehensive action validation and execution system
- Detailed logging and trajectory recording for analysis
- Parallel evaluation support for efficient benchmarking

Version History
---------------

**v1.0.0** (2025-08-07)
  Initial public release of OmniEmbodied

Contributing to Changelog
--------------------------

When contributing to OmniEmbodied, please update this changelog:

1. **Add entries to [Unreleased] section** for future releases
2. **Use appropriate categories:** Added, Changed, Deprecated, Removed, Fixed, Security
3. **Write clear, concise descriptions**
4. **Include issue/PR numbers where relevant**
5. **Follow the existing format**

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

Support
-------

For support questions, see :doc:`faq` or open an issue on GitHub. 