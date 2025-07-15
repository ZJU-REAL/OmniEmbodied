"""
OmniEmbodied评测器包
"""

from .evaluation_interface import EvaluationInterface
from .evaluation_manager import EvaluationManager
from .scenario_selector import ScenarioSelector
from .scenario_executor import ScenarioExecutor
from .trajectory_recorder import TrajectoryRecorder, CSVRecorder
from .task_executor import TaskExecutor
from .agent_adapter import AgentAdapter

# 便利函数
from .evaluation_interface import (
    run_single_agent_evaluation,
    run_multi_agent_evaluation,
    run_comparison_evaluation
)

__version__ = "1.0.0"
__author__ = "OmniEmbodied Team"

__all__ = [
    'EvaluationInterface',
    'EvaluationManager',
    'ScenarioSelector',
    'ScenarioExecutor',
    'TrajectoryRecorder',
    'CSVRecorder',
    'TaskExecutor',
    'AgentAdapter',
    'run_single_agent_evaluation',
    'run_multi_agent_evaluation',
    'run_comparison_evaluation'
]
