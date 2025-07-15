# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Embodied Simulator is a text-based multi-agent simulation environment designed for complex task execution and verification. It features dynamic action registration, real-time tool-based capabilities, and web visualization.

## Common Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install package in editable mode for development
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

### Running the Simulator
```bash
# Interactive task executor (recommended for development)
python tests/task_001_interactive_executor.py

# Run specific scenario tests
python tests/test_scenario_001_tasks.py

# Test proximity and cooperation features
python tests/test_proximity_and_cooperation.py
```

### Testing
```bash
# Run all tests with pytest
pytest

# Run specific test file
pytest tests/test_scenario_001_tasks.py

# Run with verbose output
pytest -v

# Run single test function
pytest tests/test_scenario_001_tasks.py::test_task_01_move_mug -v
```

### Code Quality
```bash
# Format code with black
black embodied_simulator/

# Lint code with flake8
flake8 embodied_simulator/
```

## High-Level Architecture

The simulator follows a layered architecture with clear separation of concerns:

1. **Core Engine** (`core/engine.py`): The `SimulationEngine` class is the main entry point that orchestrates all subsystems. It manages initialization, configuration, and component lifecycle.

2. **Action System** (`action/`): Implements a plugin-based action system with:
   - Base action class for extensibility
   - Dynamic action registration based on scene requirements
   - Real-time capability binding when agents pick up/drop tools
   - Three action categories: basic (GOTO, GRAB), attribute (OPEN, CLEAN), and cooperation (CORP_GRAB)

3. **State Management** (`core/state.py`): The `WorldState` class maintains the global simulation state, tracking agents, objects, and their relationships.

4. **Manager Pattern**: The system uses specialized managers for different concerns:
   - `AgentManager`: Multi-agent lifecycle and coordination
   - `ActionManager`: Action registration and execution
   - `EnvironmentManager`: Scene parsing and spatial management
   - `VisualizationManager`: Web-based real-time visualization

5. **Task Verification** (`utils/task_verifier.py`): Supports multiple verification modes (step_by_step, global, disabled) for task completion detection.

6. **Data Flow**: Scene/task/verification data (JSON) → DataLoader → SimulationEngine → Managers → Actions → State Updates → Visualization

## Key Development Patterns

1. **Scene-Driven Registration**: Actions are only registered if required by the current scene, improving performance.

2. **Tool-Based Capabilities**: Agents gain/lose actions dynamically based on tools they carry.

3. **Command Processing**: Commands flow through ActionHandler → ActionManager → specific Action class → State updates.

4. **Spatial Relationships**: ProximityManager maintains and validates spatial relationships between entities.

5. **Event-Driven Updates**: State changes trigger cascading updates across managers and visualization.

## Important Files and Locations

- **Main Entry Point**: `core/engine.py:SimulationEngine`
- **Command Processing**: `action/action_handler.py:ActionHandler.process_command()`
- **Action Implementation**: `action/actions/` directory
- **Configuration**: `data/simulator_config.yaml`
- **Scene Data**: `data/scene/*_scene.json`
- **Task Data**: `data/task/*_task.json`
- **Interactive Testing**: `tests/task_001_interactive_executor.py`

## Configuration

Global configuration is in `data/simulator_config.yaml`:
- Task verification modes: step_by_step, global, disabled
- Visualization settings: web server on localhost:8080
- Explore modes: normal, thorough

## Adding New Features

1. **New Actions**: Inherit from `BaseAction` in `action/actions/`, implement required methods, register in appropriate manager.

2. **New Scenes**: Create JSON files in `data/scene/` and `data/task/`, add corresponding tests.

3. **Attribute Actions**: Configure in `action/actions/attribute_actions.csv` for data-driven actions.

## Debugging Tips

- Enable visualization for real-time state monitoring: `config = {'visualization': {'enabled': True}}`
- Use the interactive executor for step-by-step debugging
- Check the web interface at http://localhost:8080 when visualization is enabled
- All output is currently in English after recent localization efforts