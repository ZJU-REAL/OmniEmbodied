OmniEmbodied Documentation
==========================

**OmniEmbodied** is a comprehensive platform for embodied AI research, consisting of two main components:

1. **OmniSimulator**: A powerful simulation engine for embodied AI agents
2. **OmniEmbodied Framework**: An evaluation and training framework built on top of the simulator

.. image:: https://img.shields.io/badge/python-3.8%2B-blue
   :target: https://www.python.org/downloads/
   :alt: Python Version

.. image:: https://img.shields.io/badge/license-MIT-green
   :target: https://github.com/ZJU-REAL/OmniEmbodied/blob/main/LICENSE
   :alt: License

.. note::
   This documentation covers both OmniSimulator and the OmniEmbodied Framework. 
   For the latest version, see our `GitHub repository <https://github.com/ZJU-REAL/OmniEmbodied>`_.

Quick Links
-----------

* **Installation**: :doc:`installation`
* **Quick Start**: :doc:`quickstart`
* **OmniSimulator API**: :doc:`omnisimulator/index`
* **Framework Guide**: :doc:`framework/index`

Platform Overview
-----------------

🎮 **OmniSimulator**
   Core simulation engine providing realistic environments, action systems, and agent interfaces for embodied AI research.

📊 **OmniEmbodied Framework**
   Evaluation and training framework with LLM integration, multi-agent coordination, and comprehensive benchmarking tools.

Key Features
------------

**OmniSimulator Engine**:

🌍 **Rich Environments**
   Room-based worlds with realistic object interactions and spatial relationships.

🎯 **Flexible Action System** 
   Movement, manipulation, observation, and communication actions with validation.

🤖 **Agent Interfaces**
   Clean APIs for integrating various AI architectures and decision-making systems.

**OmniEmbodied Framework**:

📈 **Comprehensive Evaluation**
   Built-in benchmarks with detailed analytics and performance metrics.

🔧 **LLM Integration**
   Seamless integration with OpenAI, Anthropic, and local language models.

⚖️ **Multi-Agent Support**
   Single-agent and multi-agent scenarios with collaboration patterns.

Getting Started
---------------

If you're new to OmniEmbodied, start with our :doc:`installation` guide, then follow the :doc:`quickstart` tutorial to run your first evaluation.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started
   :hidden:

   installation
   quickstart
   configuration

.. toctree::
   :maxdepth: 2
   :caption: OmniSimulator
   :hidden:

   omnisimulator/index
   omnisimulator/overview
   omnisimulator/environments
   omnisimulator/actions
   omnisimulator/agents

.. toctree::
   :maxdepth: 2
   :caption: OmniEmbodied Framework
   :hidden:

   framework/index
   framework/evaluation
   framework/agents
   framework/data_generation

.. toctree::
   :maxdepth: 2
   :caption: User Guide
   :hidden:

   user_guide/index
   user_guide/task_types
   user_guide/evaluation_workflows

.. toctree::
   :maxdepth: 2
   :caption: Developer Guide
   :hidden:

   developer/index
   developer/contributing

.. toctree::
   :maxdepth: 2
   :caption: API Reference
   :hidden:

   api/index
   api/omnisimulator
   api/framework

.. toctree::
   :maxdepth: 1
   :caption: Additional Resources
   :hidden:

   examples/index
   faq
   troubleshooting
   changelog
   license

Architecture Overview
---------------------

The platform has a layered architecture:

.. code-block:: text

   ┌─────────────────────────────────────────────┐
   │           OmniEmbodied Framework            │
   │  ┌─────────────────┐ ┌─────────────────────┐ │
   │  │   Evaluation    │ │   Agent Modes       │ │
   │  │   Framework     │ │   - Single Agent    │ │
   │  │                 │ │   - Multi-Agent     │ │
   │  └─────────────────┘ └─────────────────────┘ │
   │  ┌─────────────────────────────────────────┐ │
   │  │         LLM Integration Layer           │ │
   │  └─────────────────────────────────────────┘ │
   └─────────────────────────────────────────────┘
   ┌─────────────────────────────────────────────┐
   │              OmniSimulator                  │
   │  ┌─────────────┐ ┌─────────────┐ ┌────────┐ │
   │  │ Environment │ │   Actions   │ │ Agents │ │
   │  │  Management │ │   System    │ │   API  │ │
   │  └─────────────┘ └─────────────┘ └────────┘ │
   │  ┌─────────────────────────────────────────┐ │
   │  │           Simulation Core               │ │
   │  └─────────────────────────────────────────┘ │
   └─────────────────────────────────────────────┘

Use Cases
---------

**For Researchers**:

- **Embodied AI Research**: Study agent perception, reasoning, and action in realistic environments
- **Multi-Agent Systems**: Investigate collaboration, communication, and coordination strategies
- **Benchmarking**: Evaluate and compare different AI architectures on standardized tasks

**For Developers**:

- **Agent Development**: Build and test intelligent agents with comprehensive simulation
- **Algorithm Testing**: Validate planning, learning, and decision-making algorithms
- **Integration**: Incorporate embodied AI capabilities into larger systems

**For Educators**:

- **Teaching Tool**: Demonstrate AI concepts with interactive simulations
- **Research Platform**: Support student research projects with ready-to-use infrastructure
- **Curriculum Development**: Create coursework around embodied AI and multi-agent systems

Community and Support
---------------------

- **Issues**: Report bugs and request features on our `GitHub Issues <https://github.com/ZJU-REAL/OmniEmbodied/issues>`_
- **Discussions**: Join the conversation in `GitHub Discussions <https://github.com/ZJU-REAL/OmniEmbodied/discussions>`_
- **Contributing**: See our :doc:`developer/contributing` guide

Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search` 