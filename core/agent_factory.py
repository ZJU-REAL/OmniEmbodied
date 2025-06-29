from typing import Dict, Any, Optional

from core.base_agent import BaseAgent
from modes.single_agent.llm_agent import LLMAgent
from modes.centralized.coordinator import Coordinator
from modes.decentralized.autonomous_agent import AutonomousAgent

def create_agent(agent_type: str, simulator, agent_id: str, config: Optional[Dict[str, Any]] = None) -> BaseAgent:
    """
    根据类型创建智能体实例
    
    Args:
        agent_type: 智能体类型，可选值: 'llm', 'coordinator', 'autonomous'
        simulator: 模拟器实例
        agent_id: 智能体ID
        config: 配置字典
        
    Returns:
        BaseAgent: 智能体实例
        
    Raises:
        ValueError: 如果agent_type不受支持
    """
    if agent_type == 'llm':
        return LLMAgent(simulator, agent_id, config)
    elif agent_type == 'coordinator':
        return Coordinator(simulator, agent_id, config)
    elif agent_type == 'autonomous':
        return AutonomousAgent(simulator, agent_id, config)
    else:
        raise ValueError(f"不支持的智能体类型: {agent_type}") 