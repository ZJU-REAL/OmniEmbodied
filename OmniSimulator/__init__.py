"""
Embodied Simulator - 文本具身任务模拟器

这个包提供了用于模拟智能体在虚拟环境中执行文本具身任务的工具。

使用方式：
    from simulator import SimulationEngine, ActionHandler, SimulationLogger
    from simulator import ActionType, ActionStatus, ObjectType
"""

# 核心组件
from .core.engine import SimulationEngine
from .core.state import WorldState
from .core.enums import ActionType, ActionStatus, ObjectType

# 动作系统
from .action.action_handler import ActionHandler
from .action.action_manager import ActionManager
from .action.actions.base_action import BaseAction
from .action.actions.basic_actions import GotoAction, GrabAction, PlaceAction, LookAction, ExploreAction
from .action.actions.attribute_actions import AttributeAction

# 智能体系统
from .agent.agent import Agent
from .agent.agent_manager import AgentManager

# 环境系统
from .environment.environment_manager import EnvironmentManager
from .environment.room import Room
from .environment.object_defs import BaseObject, StaticObject, InteractableObject, GrabbableObject
from .environment.scene_parser import SceneParser
from .environment.scene_validator import SceneValidator

# 工具模块
from .utils.logger import SimulationLogger
from .utils.data_loader import default_data_loader
from .utils.feedback import FeedbackGenerator
from .utils.task_verifier import TaskVerifier

# 可视化模块
from .visualization.visualization_manager import VisualizationManager
from .visualization.web_server import VisualizationWebServer

__version__ = "0.1.0"
__author__ = "Embodied AI Team"

__all__ = [
    # 核心组件
    'SimulationEngine',
    'WorldState',
    'ActionType',
    'ActionStatus',
    'ObjectType',

    # 动作系统
    'ActionHandler',
    'ActionManager',
    'BaseAction',
    'GotoAction',
    'GrabAction',
    'PlaceAction',
    'LookAction',
    'ExploreAction',
    'AttributeAction',

    # 智能体系统
    'Agent',
    'AgentManager',

    # 环境系统
    'EnvironmentManager',
    'Room',
    'BaseObject',
    'StaticObject',
    'InteractableObject',
    'GrabbableObject',
    'SceneParser',
    'SceneValidator',

    # 工具模块
    'SimulationLogger',
    'default_data_loader',
    'FeedbackGenerator',
    'TaskVerifier',

    # 可视化模块
    'VisualizationManager',
    'VisualizationWebServer'
]