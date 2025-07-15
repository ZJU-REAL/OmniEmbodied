# OmniEmbodied Installation Guide

This guide provides step-by-step instructions for installing and setting up the OmniEmbodied framework.

## Prerequisites

- **Python**: 3.7 or higher (tested on 3.8, 3.9, 3.10, 3.11)
- **Operating System**: Windows, macOS, or Linux
- **Memory**: At least 512MB RAM recommended
- **Storage**: Approximately 100MB for the framework and dependencies

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd OmniEmbodied
```

### 2. Create Virtual Environment (Recommended)

```bash
# Using conda
conda create -n omniembodied python=3.9
conda activate omniembodied

# Or using venv
python -m venv omniembodied
source omniembodied/bin/activate  # On Windows: omniembodied\Scripts\activate
```

### 3. Install OmniSimulator (Third-party Library)

First, install the OmniSimulator package as a third-party library:

```bash
cd OmniSimulator
pip install -e .
cd ..
```

### 4. Install Framework Dependencies

Install all required dependencies for the OmniEmbodied framework:

```bash
pip install -r requirements.txt
```

### 5. Install Development Dependencies (Optional)

For development and testing:

```bash
pip install -r requirements-dev.txt
```

## Verification

Test that everything is installed correctly:

```bash
python -c "
import yaml, pandas, openai, json_repair, pytest
from OmniSimulator import SimulationEngine, ActionStatus
print('✅ All dependencies installed successfully!')
"
```

## Configuration

### 1. API Keys

If you plan to use LLM features, set up your OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or create a `.env` file in the project root:

```
OPENAI_API_KEY=your-api-key-here
```

### 2. Configuration Files

The framework uses YAML configuration files located in the `config/` directory. Default configurations will be created automatically when needed.

## Running Examples

Test the installation by running example scripts:

```bash
# Test configuration-based evaluation
python examples/config_based_evaluation.py --help

# Test single agent example
python examples/single_agent_example.py --help

# Test centralized example
python examples/centralized_example.py --help
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you've installed OmniSimulator first, then the framework dependencies.

2. **Configuration File Not Found**: This is normal for first-time setup. Default configurations will be created automatically.

3. **API Key Errors**: Set your OpenAI API key as described in the Configuration section.

4. **Path Issues**: Make sure you're running scripts from the project root directory.

### Getting Help

If you encounter issues:

1. Check that all dependencies are installed: `pip list`
2. Verify Python version: `python --version`
3. Check the project structure matches the expected layout
4. Review error messages for specific missing dependencies

## Project Structure

After installation, your project should look like this:

```
OmniEmbodied/
├── OmniSimulator/           # Third-party simulation library
├── config/                  # Configuration files
├── utils/                   # Framework utilities
├── examples/                # Example scripts
├── data/                    # Data files
├── requirements.txt         # Core dependencies
├── requirements-dev.txt     # Development dependencies
└── INSTALL.md              # This file
```

## Next Steps

1. Review the example scripts in the `examples/` directory
2. Check the configuration files in the `config/` directory
3. Read the documentation for detailed usage instructions
4. Start experimenting with your own tasks and scenarios

## Development Setup

For contributors and developers:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks (if available)
pre-commit install

# Run tests
pytest

# Format code
black .
```

---

For more information, please refer to the project documentation or contact the development team.
