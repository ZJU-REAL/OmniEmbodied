User Guide
==========

This comprehensive user guide covers all aspects of using OmniEmbodied for embodied AI research and evaluation.

.. toctree::
   :maxdepth: 2

   task_types
   evaluation_workflows

Overview
--------

The user guide is organized into the following sections:

**Core Concepts**:

- :doc:`task_types` - Understanding different task categories and complexity levels

**Evaluation and Testing**:

- :doc:`evaluation_workflows` - Complete evaluation procedures and best practices

Core Concepts
-------------

Task Types and Categories
^^^^^^^^^^^^^^^^^^^^^^^^^

OmniEmbodied supports diverse task types with varying complexity:

**Single-Agent Tasks**:

- **Direct Command Tasks**: Simple instruction following
- **Attribute Reasoning**: Tasks requiring understanding of object properties
- **Spatial Navigation**: Movement and exploration tasks
- **Object Manipulation**: Interaction with environment objects

**Multi-Agent Tasks**:

- **Collaborative Tasks**: Agents work together toward common goals
- **Communication Tasks**: Information sharing and coordination
- **Competitive Tasks**: Resource competition and strategic planning

**Task Complexity Levels**:

1. **Basic**: Single-step actions with clear objectives
2. **Intermediate**: Multi-step procedures with dependencies
3. **Advanced**: Complex reasoning with multiple constraints

Evaluation Framework
^^^^^^^^^^^^^^^^^^^^

The framework provides comprehensive evaluation capabilities:

**Scenario Management**:

- Automated scenario loading and validation
- Flexible filtering by task type, difficulty, or categories
- Support for custom scenario definitions

**Performance Metrics**:

- Success rate and completion statistics
- Efficiency measurements (steps, time, resources)
- Error analysis and categorization
- Multi-agent coordination metrics

**Result Analysis**:

- Detailed execution traces and trajectories
- Statistical summaries across scenario categories
- Comparative analysis between different agents/models
- Export capabilities for further analysis

Configuration System
^^^^^^^^^^^^^^^^^^^^^

Flexible configuration management for all components:

**Agent Configuration**:

- LLM selection and parameters
- Reasoning strategies and planning approaches
- Memory and context management settings

**Evaluation Configuration**:

- Scenario selection and filtering criteria
- Execution parameters and resource limits
- Output formatting and storage options

**Environment Configuration**:

- Simulation engine parameters
- Environment dynamics and rules
- Action space and capability definitions

Best Practices
--------------

Evaluation Design
^^^^^^^^^^^^^^^^^

**Scenario Selection**:

- Use stratified sampling across task categories
- Include diverse difficulty levels and edge cases
- Validate scenario quality and consistency

**Metric Selection**:

- Choose metrics aligned with research objectives
- Include both primary success metrics and diagnostic measures
- Consider computational cost vs. insight trade-offs

**Statistical Analysis**:

- Use appropriate statistical tests for comparisons
- Account for multiple testing when comparing many systems
- Report confidence intervals and effect sizes

Performance Optimization
^^^^^^^^^^^^^^^^^^^^^^^^

**Resource Management**:

- Configure parallelism based on available resources
- Monitor memory usage during long evaluation runs
- Implement appropriate timeout mechanisms

**Data Management**:

- Organize results with consistent naming conventions
- Implement data versioning for reproducibility
- Regular cleanup of intermediate files

**Debugging and Troubleshooting**:

- Enable detailed logging for development and debugging
- Use smaller scenario sets for rapid iteration
- Validate configurations before full evaluation runs

Getting Started
---------------

To get started with the user guide:

1. **Understanding Tasks**: Start with :doc:`task_types` to understand the evaluation framework
2. **Running Evaluations**: Follow :doc:`evaluation_workflows` for step-by-step evaluation procedures

For detailed API documentation, see :doc:`../api/index`.

Advanced Topics
---------------

For advanced usage and customization, consult the developer documentation:

- Framework extension and customization patterns
- Advanced configuration techniques
- Performance optimization strategies
- Integration with external tools and systems 