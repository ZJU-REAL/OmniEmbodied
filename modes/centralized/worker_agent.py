from typing import Dict, List, Optional, Any, Tuple

from embodied_simulator import SimulationEngine
from embodied_simulator.core import ActionStatus
from ...core.base_agent import BaseAgent

class WorkerAgent(BaseAgent):
    """
    工作智能体，执行协调器分配的任务
    """
    
    def __init__(self, simulator: SimulationEngine, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化工作智能体
        
        Args:
            simulator: 模拟引擎实例
            agent_id: 智能体ID
            config: 配置字典，可选
        """
        super().__init__(simulator, agent_id, config)
        self.next_action = None
        self.waiting_for_instruction = True
    
    def set_next_action(self, action: str) -> None:
        """
        设置下一步要执行的动作
        
        Args:
            action: 动作命令
        """
        self.next_action = action
        self.waiting_for_instruction = False
    
    def decide_action(self) -> str:
        """
        决定下一步动作，使用预设的动作或默认行为
        
        Returns:
            str: 动作命令字符串
        """
        if self.next_action is not None:
            action = self.next_action
            self.next_action = None
            self.waiting_for_instruction = True
            return action
        
        # 如果没有预设动作，执行默认行为
        if self.waiting_for_instruction:
            return "EXPLORE"  # 默认使用EXPLORE代替WAIT
        
        # 兜底行为：探索当前环境
        return "EXPLORE" 