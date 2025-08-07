Installation
============

This guide will help you install OmniEmbodied on your system.

Requirements
------------

System Requirements
^^^^^^^^^^^^^^^^^^^

- **Operating System**: Linux (Ubuntu 18.04+), macOS (10.14+), or Windows 10+
- **Python**: 3.8 or higher
- **Memory**: At least 8GB RAM recommended
- **Storage**: At least 5GB free disk space

Python Dependencies
^^^^^^^^^^^^^^^^^^^

The main dependencies are automatically installed with OmniEmbodied:

- ``numpy >= 1.19.0``
- ``pandas >= 1.3.0``
- ``pyyaml >= 5.4.0``
- ``tqdm >= 4.62.0``
- ``pathlib >= 1.0.1``

Optional Dependencies
^^^^^^^^^^^^^^^^^^^^^

For enhanced functionality, you may want to install:

- ``openai >= 0.27.0`` - For OpenAI API integration
- ``anthropic >= 0.3.0`` - For Anthropic Claude integration
- ``torch >= 1.9.0`` - For neural network components
- ``matplotlib >= 3.3.0`` - For visualization
- ``jupyter >= 1.0.0`` - For notebook examples

Installation Methods
--------------------

Install from Source (Recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. **Clone the repository and install**:

   .. code-block:: bash

      git clone https://github.com/ZJU-REAL/OmniEmbodied.git
      cd OmniEmbodied/OmniSimulator
      pip install -e .
      cd ..
      pip install -r requirements.txt

2. **Create a virtual environment** (optional but recommended):

   .. code-block:: bash

      # Using conda
      conda create -n omniembodied python=3.8
      conda activate omniembodied

      # Or using virtualenv
      python -m venv omniembodied-env
      source omniembodied-env/bin/activate  # On Windows: omniembodied-env\Scripts\activate

Configuration
-------------

After installation, configure your LLM API key in ``config/baseline/llm_config.yaml``:

.. code-block:: yaml

   api:
     provider: "deepseekv3"  # Choose your provider: deepseekv3, gpt-4, etc.
     providers:
       deepseekv3:
         api_key: "your-api-key-here"  # Replace with your actual API key
         model: "deepseek-chat"
         temperature: 0.3
         max_tokens: 2048

For Global Observation Mode
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you plan to run scripts ending with ``-wg.sh`` (with global observation), you need to configure:

1. **Set runtime parameter**: Use ``--observation-mode global`` when running
2. **Configure simulator**: Set ``global_observation: true`` in ``config/simulator/simulator_config.yaml``

   .. code-block:: yaml

      # config/simulator/simulator_config.yaml
      global_observation: true  # Enable global observation mode

Verification
------------

To verify your installation, run the following command:

.. code-block:: bash

   python -c "import OmniSimulator; print('OmniEmbodied installed successfully!')"

You can also run the test suite:

.. code-block:: bash

   python -m pytest tests/

Running Your First Evaluation
------------------------------

Run a basic evaluation with:

.. code-block:: bash

   bash scripts/deepseekv3-wo.sh

Troubleshooting
---------------

Common Issues
^^^^^^^^^^^^^

**Import Error: No module named 'OmniSimulator'**

This usually means the OmniSimulator subpackage wasn't installed correctly. Try:

.. code-block:: bash

   cd OmniSimulator
   pip install -e .

**Permission denied errors on Windows**

Run your terminal as administrator, or use:

.. code-block:: bash

   pip install --user -e .

**YAML parsing errors**

Make sure you have the correct version of PyYAML:

.. code-block:: bash

   pip install --upgrade PyYAML>=5.4.0

**Memory issues during installation**

If you encounter memory issues, try installing with fewer parallel jobs:

.. code-block:: bash

   pip install -e . --no-cache-dir

Platform-Specific Notes
^^^^^^^^^^^^^^^^^^^^^^^^

**Linux**

On Ubuntu/Debian, you might need to install additional system packages:

.. code-block:: bash

   sudo apt-get update
   sudo apt-get install python3-dev build-essential

**macOS**

Make sure you have Xcode command line tools installed:

.. code-block:: bash

   xcode-select --install

**Windows**

We recommend using Anaconda or Miniconda on Windows for easier dependency management.

Getting Help
------------

If you encounter issues during installation:

1. Check our :doc:`troubleshooting` guide
2. Search existing `GitHub Issues <https://github.com/ZJU-REAL/OmniEmbodied/issues>`_
3. Create a new issue with your system information and error messages

Next Steps
----------

Once you have OmniEmbodied installed, check out the :doc:`quickstart` guide to run your first simulation! 