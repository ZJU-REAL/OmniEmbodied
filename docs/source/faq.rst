Frequently Asked Questions
==========================

This page answers common questions about OmniEmbodied. If you can't find the answer to your question here, check the :doc:`troubleshooting` guide or open an issue on `GitHub <https://github.com/ZJU-REAL/OmniEmbodied/issues>`_.

General Questions
-----------------

**What is OmniEmbodied?**

OmniEmbodied is a comprehensive simulation and evaluation platform for embodied AI agents. It provides realistic environments where intelligent agents can perform complex tasks requiring perception, reasoning, and action.

**Who is OmniEmbodied for?**

- **Researchers** studying embodied AI, multi-agent systems, and task-oriented dialog
- **Developers** building intelligent agents and testing their capabilities
- **Educators** teaching AI concepts with hands-on simulations
- **Students** learning about embodied AI through practical examples

**How is OmniEmbodied different from other simulation platforms?**

OmniEmbodied focuses specifically on embodied AI with:

- Rich task taxonomies covering reasoning, collaboration, and tool use
- Built-in LLM integration for natural language agents
- Comprehensive evaluation framework with detailed metrics
- Real-world inspired scenarios and object interactions
- Support for both single-agent and multi-agent scenarios

Installation and Setup
-----------------------

**What are the system requirements?**

- Python 3.8 or higher
- 8GB RAM (recommended)
- 5GB free disk space
- Linux, macOS, or Windows

**Do I need GPU support?**

No, OmniEmbodied runs entirely on CPU. However, if you're using local LLMs that require GPU acceleration, you'll need appropriate GPU setup for those models.

**Can I use OmniEmbodied without API keys?**

Yes, you can:

- Use the dataset correction tool without LLMs
- Analyze existing simulation results
- Explore the codebase and documentation
- Run tests and development tools

However, running actual simulations with intelligent agents requires LLM access.

**Which LLM providers are supported?**

Currently supported:

- OpenAI (GPT-3.5, GPT-4, GPT-4-turbo)
- Anthropic (Claude-3 family)
- Local models via vLLM
- Custom API endpoints

Configuration and Usage
-----------------------

**How do I configure OmniEmbodied for my use case?**

1. Start with a base configuration file
2. Copy and modify for your specific needs
3. Use configuration inheritance to avoid duplication
4. Set environment variables for sensitive information

See :doc:`configuration` for detailed guidance.

**What task types are available?**

Single-agent tasks:
- Direct command following
- Attribute reasoning
- Tool usage
- Spatial reasoning
- Compound reasoning

Multi-agent tasks:
- Explicit collaboration
- Implicit collaboration
- Compound collaboration

See :doc:`user_guide/task_types` for details.

**How many scenarios are included?**

The platform includes:
- 800+ single-agent evaluation scenarios
- 600+ multi-agent evaluation scenarios
- 1500+ source scenarios for data generation
- Thousands of generated training scenarios

**Can I create custom scenarios?**

Yes! You can:
- Create new task definitions using JSON format
- Design custom scene layouts and object configurations
- Generate scenarios automatically using data generation tools
- Import scenarios from external sources

Evaluation and Results
----------------------

**How is task success measured?**

Task success is evaluated through:

- **Subtask completion**: Step-by-step progress tracking
- **Final verification**: End-state validation against goal conditions
- **Efficiency metrics**: Steps taken, time elapsed
- **Quality measures**: Accuracy of actions and decisions

**What metrics are provided?**

- Success rates by task category
- Average steps per task
- Error analysis and failure modes
- Agent action patterns
- Comparative performance across configurations

**How do I compare different agents?**

1. Use consistent evaluation scenarios
2. Apply identical configuration parameters
3. Run multiple trials for statistical significance
4. Analyze results using built-in analytics tools

**Can I reproduce published results?**

Yes, OmniEmbodied is designed for reproducibility:

- Fixed random seeds for deterministic results
- Version-controlled scenarios and configurations
- Detailed logging of all simulation steps
- Standardized evaluation protocols

Performance and Optimization
-----------------------------

**How fast are the simulations?**

Performance varies by configuration:

- Simple tasks: 10-30 seconds per scenario
- Complex tasks: 1-5 minutes per scenario  
- Multi-agent tasks: 2-10 minutes per scenario

Performance depends on LLM response time, task complexity, and system resources.

**How can I speed up evaluations?**

- Enable parallel scenario execution
- Use faster LLM models for initial testing
- Filter tasks to focus on relevant categories
- Reduce maximum steps per task for quicker iterations

**Why are simulations slow?**

Common causes:
- LLM API rate limits and response times
- Complex scenarios requiring many steps
- Inefficient agent decision-making
- Network latency for API calls

See :doc:`user_guide/performance_tuning` for optimization strategies.

Debugging and Troubleshooting
------------------------------

**Simulation gets stuck or hangs**

- Check LLM API connectivity and rate limits
- Verify agent is making valid action decisions
- Enable debug logging to trace execution
- Set reasonable timeout values

**Agent makes invalid actions**

- Check action validation logic
- Review environment state and object availability
- Ensure proper action syntax and parameters
- Enable detailed action logging

**Configuration errors**

- Validate YAML syntax using online tools
- Check for proper indentation (spaces, not tabs)
- Verify file paths are correct
- Use configuration validation tools

**Memory issues**

- Reduce agent history length
- Limit parallel scenario execution
- Clear logs and temporary files regularly
- Monitor system resources

Development and Customization
------------------------------

**Can I add new action types?**

Yes! Create a new action class inheriting from ``BaseAction`` and implement the required methods. See :doc:`developer/extending` for details.

**How do I integrate a new LLM?**

Implement the ``BaseLLM`` interface with your model's specific API calls. Existing integrations provide good examples.

**Can I modify the environment?**

The environment system is fully extensible. You can:
- Add new object types and properties
- Create custom room layouts
- Implement new interaction rules
- Design domain-specific environments

**How do I contribute back to the project?**

1. Fork the repository on GitHub
2. Create a feature branch for your changes
3. Follow the coding standards and add tests
4. Submit a pull request with clear description
5. Participate in the code review process

See :doc:`developer/contributing` for detailed guidelines.

Licensing and Usage
-------------------

**What license is OmniEmbodied released under?**

OmniEmbodied is released under the MIT License, which allows for both academic and commercial use with proper attribution.

**Can I use OmniEmbodied in commercial applications?**

Yes, the MIT License permits commercial use. However, be aware that:
- LLM API usage may have separate terms and costs
- Some components may have different license requirements
- Always review and comply with all applicable licenses

**How do I cite OmniEmbodied in my research?**

Please cite our paper (when available) and include a link to the GitHub repository. A BibTeX entry will be provided with the official release.

**Can I redistribute modified versions?**

Yes, under the MIT License you can redistribute modified versions as long as you:
- Include the original license notice
- Clearly indicate what changes were made
- Provide appropriate attribution

Data and Privacy
----------------

**What data does OmniEmbodied collect?**

OmniEmbodied does not collect or transmit any personal data. However:
- Simulation results are stored locally
- LLM API calls are subject to provider terms
- Log files may contain detailed execution traces

**Is it safe to use with sensitive information?**

While OmniEmbodied itself doesn't transmit data, be cautious about:
- LLM API providers may log requests
- Configuration files might contain API keys
- Results may include information from your scenarios

**Can I use OmniEmbodied offline?**

Partially:
- Core simulation engine works offline
- Local LLM models can be used instead of APIs
- Dataset analysis and visualization work offline
- Documentation is available locally after build

Still Have Questions?
--------------------

If your question isn't answered here:

1. Check the :doc:`troubleshooting` guide for detailed solutions
2. Search existing issues on `GitHub <https://github.com/ZJU-REAL/OmniEmbodied/issues>`_
3. Ask in `GitHub Issues <https://github.com/ZJU-REAL/OmniEmbodied/issues>`_
4. Create a new issue with a clear description of your problem

We welcome all questions and feedback from the community! 