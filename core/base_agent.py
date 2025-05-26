import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple

from embodied_simulator import SimulationEngine, ActionStatus
from ..utils.simulator_bridge import SimulatorBridge

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    基础智能体类 - 所有智能体类型的基类
    """
    
    def __init__(self, simulator: SimulationEngine, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化基础智能体
        
        Args:
            simulator: 模拟引擎实例或SimulatorBridge实例
            agent_id: 智能体ID
            config: 配置字典，可选
        """
        # 创建模拟器桥接，如果传入的是模拟引擎实例则包装它
        if isinstance(simulator, SimulatorBridge):
            self.bridge = simulator
            self.simulator = simulator.simulator
        else:
            self.simulator = simulator
            self.bridge = SimulatorBridge(simulator)
            
        self.agent_id = agent_id
        self.config = config or {}
        
        # 默认配置
        self.max_failures = self.config.get('max_failures', 3)
        self.max_history = self.config.get('max_history', 50)
        
        # 执行历史记录
        self.history = []
        self.consecutive_failures = 0
    
    def step(self) -> Tuple[ActionStatus, str, Optional[Dict[str, Any]]]:
        """
        执行一步智能体行为
        
        Returns:
            Tuple: (执行状态, 反馈消息, 结果数据)
        """
        # 决定要执行的动作
        action = self.decide_action()
        
        # 执行动作
        status, message, result = self.bridge.process_command(self.agent_id, action)
        
        # 记录历史
        self.record_action(action, {"status": status, "message": message, "result": result})
        
        # 更新连续失败计数
        if status == ActionStatus.FAILURE or status == ActionStatus.INVALID:
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0
        
        return status, message, result
    
    def decide_action(self) -> str:
        """
        决定下一步动作（需要子类实现）
        
        Returns:
            str: 动作命令字符串
        """
        raise NotImplementedError("BaseAgent的子类必须实现decide_action方法")
    
    def record_action(self, action: str, result: Dict[str, Any]) -> None:
        """
        记录动作到历史
        
        Args:
            action: 动作命令
            result: 执行结果
        """
        self.history.append({
            'action': action,
            'result': result
        })
        
        # 保持历史长度在限制范围内
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_history(self) -> List[Dict[str, Any]]:
        """
        获取执行历史
        
        Returns:
            List: 历史记录列表
        """
        return self.history.copy()
    
    def get_state(self) -> Dict[str, Any]:
        """
        获取智能体当前状态
        
        Returns:
            Dict: 状态信息字典
        """
        # 从模拟器获取最新状态
        agent_info = self.bridge.get_agent_info(self.agent_id)
        if not agent_info:
            return {}
        
        # 将库存项目转换为完整物体信息
        inventory = []
        for item_id in agent_info.get('inventory', []):
            item_info = self.bridge.get_object_info(item_id)
            if item_info:
                inventory.append(item_info)
        
        # 获取当前房间信息
        location_id = agent_info.get('location_id', '')
        location_info = self.bridge.get_room_info(location_id)
        
        return {
            'agent_id': self.agent_id,
            'name': agent_info.get('name', ''),
            'location_id': location_id,
            'location': location_info,
            'inventory': inventory,
            'history': self.get_history(),
            'consecutive_failures': self.consecutive_failures
        } 