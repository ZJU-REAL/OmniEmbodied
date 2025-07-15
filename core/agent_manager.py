from typing import Dict, List, Any, Optional
import logging

from OmniSimulator.core.engine import SimulationEngine
from core.base_agent import BaseAgent
from core.agent_factory import create_agent

logger = logging.getLogger(__name__)

class AgentManager:
    """
    智能体管理器，负责创建、管理和协调多个智能体
    """
    
    def __init__(self, simulator: SimulationEngine):
        """
        初始化智能体管理器
        
        Args:
            simulator: 模拟引擎实例
        """
        self.simulator = simulator
        self.agents: Dict[str, BaseAgent] = {}
    
    def create_agent(self, agent_id: str, agent_type: str, config: Optional[Dict[str, Any]] = None) -> BaseAgent:
        """
        创建并注册新的智能体
        
        Args:
            agent_id: 智能体ID
            agent_type: 智能体类型
            config: 配置字典
            
        Returns:
            BaseAgent: 创建的智能体实例
        """
        if agent_id in self.agents:
            logger.warning(f"智能体ID已存在: {agent_id}，将被覆盖")
        
        agent = create_agent(agent_type, self.simulator, agent_id, config)
        self.agents[agent_id] = agent
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        获取指定ID的智能体
        
        Args:
            agent_id: 智能体ID
            
        Returns:
            Optional[BaseAgent]: 智能体实例，如果不存在则返回None
        """
        return self.agents.get(agent_id)
    
    def remove_agent(self, agent_id: str) -> bool:
        """
        移除指定ID的智能体
        
        Args:
            agent_id: 智能体ID
            
        Returns:
            bool: 是否成功移除
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False
    
    def get_all_agents(self) -> Dict[str, BaseAgent]:
        """
        获取所有智能体
        
        Returns:
            Dict[str, BaseAgent]: 智能体字典，键为ID
        """
        return self.agents.copy()
    
    def step_all(self) -> Dict[str, Any]:
        """
        推进所有智能体执行一步
        
        Returns:
            Dict[str, Any]: 各智能体的执行结果
        """
        results = {}
        for agent_id, agent in self.agents.items():
            try:
                status, message, data = agent.step()
                results[agent_id] = {
                    "status": status.name if hasattr(status, "name") else str(status),
                    "message": message,
                    "data": data
                }
            except Exception as e:
                logger.exception(f"智能体 {agent_id} 执行步骤时出错: {e}")
                results[agent_id] = {
                    "status": "ERROR",
                    "message": f"执行出错: {str(e)}",
                    "data": None
                }
        
        return results 