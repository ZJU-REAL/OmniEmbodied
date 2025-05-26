from typing import Dict, List, Optional, Any, Tuple
import random

from embodied_simulator import SimulationEngine
from embodied_simulator.core import ActionStatus
from ...core.base_agent import BaseAgent

class BasicAgent(BaseAgent):
    """
    基本智能体实现，使用简单规则或随机选择决策
    """
    
    def __init__(self, simulator: SimulationEngine, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化基本智能体
        
        Args:
            simulator: 模拟引擎实例
            agent_id: 智能体ID
            config: 配置字典，可选
        """
        super().__init__(simulator, agent_id, config)
        self.available_actions = [
            "LOOK", "EXPLORE",
            "GOTO kitchen", "GOTO bedroom", "GOTO livingroom", "GOTO bathroom",
            "OPEN fridge", "CLOSE fridge",
            "GRAB apple", "PLACE apple"
        ]
    
    def decide_action(self) -> str:
        """
        决定下一步动作，使用简单策略或随机选择
        
        Returns:
            str: 动作命令字符串
        """
        # 获取当前状态
        state = self.get_state()
        location = state.get('location_name', '')
        
        # 简单规则决策
        if location == '':
            # 如果位置不确定，先查看
            return "LOOK"
        
        if location != 'kitchen' and random.random() < 0.6:
            # 有较大概率前往厨房
            return "GOTO kitchen"
        
        # 否则随机选择一个动作
        return random.choice(self.available_actions) 