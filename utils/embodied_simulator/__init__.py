"""
Embodied Simulator - 文本具身任务模拟器

这个包提供了用于模拟智能体在虚拟环境中执行文本具身任务的工具。
"""

from .core.engine import SimulationEngine
from .core.enums import ObjectType, ActionType, ActionStatus
from .action.action_handler import ActionHandler

__version__ = "0.1.0"
__author__ = "Embodied AI Team"

# 导出主要API
__all__ = [
    # 核心类
    'SimulationEngine', 
    # 枚举类
    'ActionStatus', 'ActionType', 'ObjectType',
    # 接口类
    'ActionHandler'
] 