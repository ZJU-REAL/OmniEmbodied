"""
合作动作模块
定义智能体之间的合作动作，如合作抓取、合作移动、合作放置等
"""

from typing import Dict, List, Optional, Any, Tuple
from ...core import ActionType, ActionStatus
from .base_action import BaseAction


class CorpGrabAction(BaseAction):
    """合作抓取动作"""
    
    def __init__(self, agent_id: str, agents: List[str], target_object: str):
        """
        初始化合作抓取动作
        
        Args:
            agent_id: 主要智能体ID
            agents: 参与合作的所有智能体ID列表
            target_object: 目标物体ID
        """
        super().__init__(agent_id, ActionType.CORP_GRAB)
        self.agents = agents
        self.target_object = target_object
    
    @classmethod
    def from_command(cls, command_str: str, agent_id: str) -> Optional['CorpGrabAction']:
        """
        从命令字符串创建合作抓取动作
        
        Args:
            command_str: 命令字符串，格式: "corp_grab agent1,agent2 object_id"
            agent_id: 执行命令的智能体ID
            
        Returns:
            CorpGrabAction: 合作抓取动作对象，解析失败返回None
        """
        try:
            parts = command_str.strip().split()
            if len(parts) < 3:
                return None
            
            # 解析智能体列表
            agents_str = parts[1]
            agents = [a.strip() for a in agents_str.split(',')]
            
            # 目标物体
            target_object = parts[2]
            
            return cls(agent_id, agents, target_object)
        except:
            return None
    
    def validate(self, world_state, env_manager, agent_manager) -> Tuple[bool, str]:
        """验证合作抓取动作是否可执行"""
        # 检查所有智能体是否存在
        for agent_id in self.agents:
            if not agent_manager.get_agent(agent_id):
                return False, f"Agent {agent_id} does not exist"

        # 检查目标物体是否存在
        target_obj = env_manager.get_object_by_id(self.target_object)
        if not target_obj:
            return False, f"Object {self.target_object} does not exist"

        # 检查物体是否需要合作抓取
        # 获取物体重量
        object_weight = target_obj.get('properties', {}).get('weight', 0)

        # 获取所有参与智能体的最大承重能力
        max_individual_capacity = 0
        for agent_id in self.agents:
            agent = agent_manager.get_agent(agent_id)
            if agent:
                agent_max_weight = agent.properties.get('max_weight', 10.0)  # 默认10kg
                max_individual_capacity = max(max_individual_capacity, agent_max_weight)

        # 如果存在智能体能够单独承载该物体，则不需要合作
        if object_weight <= max_individual_capacity:
            return False, f"Object {self.target_object} (weight: {object_weight}kg) does not require cooperative grab - can be carried by single agent (max capacity: {max_individual_capacity}kg)"

        # 检查所有智能体是否都靠近目标物体
        for agent_id in self.agents:
            is_near, reason = env_manager.is_agent_near_object(agent_id, self.target_object)
            if not is_near:
                return False, f"Agent {agent_id} must be near {self.target_object} before cooperative grab: {reason}"

        return True, "Cooperative grab action is valid"
    
    def execute(self, world_state, env_manager, agent_manager) -> Tuple[ActionStatus, str, Optional[Dict[str, Any]]]:
        """执行合作抓取动作"""
        try:
            # 简化实现：标记所有参与的智能体进入合作模式
            for agent_id in self.agents:
                agent = agent_manager.get_agent(agent_id)
                if agent:
                    agent.corporate_mode_object_id = self.target_object
            
            return ActionStatus.SUCCESS, f"Agents {', '.join(self.agents)} started cooperative grab of {self.target_object}", None
        except Exception as e:
            return ActionStatus.FAILURE, f"Cooperative grab failed: {str(e)}", None


class CorpGotoAction(BaseAction):
    """合作移动动作"""
    
    def __init__(self, agent_id: str, agents: List[str], target_location: str):
        """
        初始化合作移动动作
        
        Args:
            agent_id: 主要智能体ID
            agents: 参与合作的所有智能体ID列表
            target_location: 目标位置ID
        """
        super().__init__(agent_id, ActionType.CORP_GOTO)
        self.agents = agents
        self.target_location = target_location
    
    @classmethod
    def from_command(cls, command_str: str, agent_id: str) -> Optional['CorpGotoAction']:
        """
        从命令字符串创建合作移动动作
        
        Args:
            command_str: 命令字符串，格式: "corp_goto agent1,agent2 location_id"
            agent_id: 执行命令的智能体ID
            
        Returns:
            CorpGotoAction: 合作移动动作对象，解析失败返回None
        """
        try:
            parts = command_str.strip().split()
            if len(parts) < 3:
                return None
            
            # 解析智能体列表
            agents_str = parts[1]
            agents = [a.strip() for a in agents_str.split(',')]
            
            # 目标位置
            target_location = parts[2]
            
            return cls(agent_id, agents, target_location)
        except:
            return None
    
    def validate(self, world_state, env_manager, agent_manager) -> Tuple[bool, str]:
        """验证合作移动动作是否可执行"""
        # 检查所有智能体是否存在
        for agent_id in self.agents:
            if not agent_manager.get_agent(agent_id):
                return False, f"智能体 {agent_id} 不存在"
        
        # 检查目标位置是否存在
        if not world_state.graph.get_node(self.target_location):
            return False, f"Location {self.target_location} does not exist"

        return True, "Cooperative move action is valid"
    
    def execute(self, world_state, env_manager, agent_manager) -> Tuple[ActionStatus, str, Optional[Dict[str, Any]]]:
        """执行合作移动动作"""
        try:
            # 移动所有参与的智能体到目标位置
            for agent_id in self.agents:
                agent = agent_manager.get_agent(agent_id)
                if agent:
                    agent.location_id = self.target_location
                    world_state.update_agent(agent_id, {'location_id': self.target_location})
            
            return ActionStatus.SUCCESS, f"Agents {', '.join(self.agents)} cooperatively moved to {self.target_location}", None
        except Exception as e:
            return ActionStatus.FAILURE, f"Cooperative move failed: {str(e)}", None


class CorpPlaceAction(BaseAction):
    """合作放置动作"""
    
    def __init__(self, agent_id: str, agents: List[str], target_object: str, location: str):
        """
        初始化合作放置动作
        
        Args:
            agent_id: 主要智能体ID
            agents: 参与合作的所有智能体ID列表
            target_object: 目标物体ID
            location: 放置位置
        """
        super().__init__(agent_id, ActionType.CORP_PLACE)
        self.agents = agents
        self.target_object = target_object
        self.location = location
    
    @classmethod
    def from_command(cls, command_str: str, agent_id: str) -> Optional['CorpPlaceAction']:
        """
        从命令字符串创建合作放置动作
        
        Args:
            command_str: 命令字符串，格式: "corp_place agent1,agent2 object_id location"
            agent_id: 执行命令的智能体ID
            
        Returns:
            CorpPlaceAction: 合作放置动作对象，解析失败返回None
        """
        try:
            parts = command_str.strip().split()
            if len(parts) < 4:
                return None
            
            # 解析智能体列表
            agents_str = parts[1]
            agents = [a.strip() for a in agents_str.split(',')]
            
            # 目标物体和位置
            target_object = parts[2]
            location = parts[3]
            
            return cls(agent_id, agents, target_object, location)
        except:
            return None
    
    def validate(self, world_state, env_manager, agent_manager) -> Tuple[bool, str]:
        """验证合作放置动作是否可执行"""
        # 检查所有智能体是否存在
        for agent_id in self.agents:
            agent = agent_manager.get_agent(agent_id)
            if not agent:
                return False, f"智能体 {agent_id} 不存在"
            
            # 检查智能体是否在合作模式
            if not hasattr(agent, 'corporate_mode_object_id') or agent.corporate_mode_object_id != self.target_object:
                return False, f"智能体 {agent_id} 未在合作抓取 {self.target_object}"
        
        # 检查目标物体是否存在
        if not env_manager.get_object_by_id(self.target_object):
            return False, f"Object {self.target_object} does not exist"

        # 检查放置位置是否存在
        if not world_state.graph.get_node(self.location):
            return False, f"Location {self.location} does not exist"

        return True, "Cooperative place action is valid"
    
    def execute(self, world_state, env_manager, agent_manager) -> Tuple[ActionStatus, str, Optional[Dict[str, Any]]]:
        """执行合作放置动作"""
        try:
            # 检查目标物体是否存在
            target_obj = env_manager.get_object_by_id(self.target_object)
            if not target_obj:
                return ActionStatus.FAILURE, f"Target object does not exist: {self.target_object}", None

            # 使用环境管理器的move_object方法更新物体位置
            new_location_id = f'in:{self.location}'
            success = env_manager.move_object(self.target_object, new_location_id)
            if not success:
                return ActionStatus.FAILURE, f"Cannot move object to specified location: {self.location}", None

            # 解除所有智能体的合作模式
            for agent_id in self.agents:
                agent = agent_manager.get_agent(agent_id)
                if agent:
                    agent.corporate_mode_object_id = None

            return ActionStatus.SUCCESS, f"Agents {', '.join(self.agents)} cooperatively placed {self.target_object} at {self.location}", None
        except Exception as e:
            return ActionStatus.FAILURE, f"Cooperative place failed: {str(e)}", None
