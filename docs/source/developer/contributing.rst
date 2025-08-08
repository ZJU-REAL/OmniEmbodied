Contributing to OmniEmbodied
=============================

We welcome contributions from the community! This guide will help you get started with contributing to OmniEmbodied.

Ways to Contribute
------------------

🐛 **Report Bugs**
   Help us identify and fix issues by reporting bugs.

✨ **Request Features**
   Suggest new features or improvements.

📝 **Improve Documentation**
   Help make our documentation clearer.

💻 **Contribute Code**
   Fix bugs or implement features.

Getting Started
---------------

Development Setup
^^^^^^^^^^^^^^^^^

1. **Fork and Clone**:

   .. code-block:: bash

      git clone https://github.com/ZJU-REAL/OmniEmbodied.git
      cd OmniEmbodied

2. **Install Development Environment**:

   .. code-block:: bash

      # Install main package
      pip install -e .
      
      # Install OmniSimulator
      cd OmniSimulator
      pip install -e .
      cd ..

3. **Make Changes and Test**:

   .. code-block:: bash

      # Create feature branch
      git checkout -b feature/your-feature-name
      
      # Make your changes
      # ...
      
      # Test your changes
      pytest tests/ (if available)

4. **Submit Pull Request**:

   .. code-block:: bash

      git add .
      git commit -m "Brief description of changes"
      git push origin feature/your-feature-name

   Then create a Pull Request on GitHub.

Bug Reports
-----------

When reporting bugs, please include:
- Python version and operating system
- Steps to reproduce the issue
- Error messages if any
- Minimal code example

Feature Requests
----------------

When requesting features:
- Describe the problem you're trying to solve
- Explain your use case
- Suggest how the feature might work

Community Guidelines
--------------------

- Be respectful and professional
- Be collaborative and welcoming to newcomers
- Focus on constructive feedback

Getting Help
------------

- Check existing issues for similar problems
- Open a new issue for bugs or feature requests
- Use GitHub Issues for questions
- Contact maintainers: wang.zixuan@zju.edu.cn

Thank You
---------

Thank you for contributing to OmniEmbodied! Your contributions help make embodied AI research more accessible for the community. 🚀 