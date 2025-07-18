from typing import Dict, Optional, Tuple, Any, ClassVar
import re

from ...core.enums import ActionType, ActionStatus
from ...core.state import WorldState

class BaseAction:
    """
    动作基类 - 所有具体动作类的父类
    
    实现动作的核心功能：
    1. 从命令字符串解析生成对应动作
    2. 验证动作是否可执行
    3. 执行动作并返回结果
    """
    
    # 动作类型，子类必须覆盖
    action_type: ClassVar[ActionType] = None
    
    # 命令模式，用于解析命令
    command_pattern: ClassVar[str] = None
    
    def __init__(self, agent_id: str, action_type: Optional[ActionType] = None,
                 target_id: Optional[str] = None, params: Optional[Dict[str, Any]] = None):
        """
        初始化动作

        Args:
            agent_id: 执行动作的智能体ID
            action_type: 动作类型，可选（如果不提供则使用类级别的action_type）
            target_id: 动作的目标对象ID，可选
            params: 动作的附加参数，可选
        """
        self.agent_id = agent_id
        self.action_type = action_type or self.__class__.action_type
        self.target_id = target_id
        self.params = params or {}
    
    @classmethod
    def from_command(cls, command_str: str, agent_id: str) -> Optional['BaseAction']:
        """
        从命令字符串创建动作实例
        
        Args:
            command_str: 命令字符串，如"GRAB cup_1"
            agent_id: 执行动作的智能体ID
            
        Returns:
            BaseAction: 成功则返回动作实例，失败则返回None
        """
        if not cls.command_pattern:
            return None
            
        match = re.match(cls.command_pattern, command_str, re.IGNORECASE)
        if not match:
            return None
            
        # 具体解析逻辑由子类实现
        return cls._parse_command(match, agent_id)
    
    @classmethod
    def _parse_command(cls, match, agent_id: str) -> Optional['BaseAction']:
        """
        解析命令匹配结果，创建动作实例，由子类实现
        
        Args:
            match: 正则表达式匹配结果
            agent_id: 执行动作的智能体ID
            
        Returns:
            BaseAction: 成功则返回动作实例，失败则返回None
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def validate(self, world_state, env_manager, agent_manager) -> Tuple[bool, str]:
        """
        验证动作是否可执行
        
        Args:
            world_state: 世界状态
            env_manager: 环境管理器
            agent_manager: 智能体管理器
            
        Returns:
            Tuple[bool, str]: (是否有效, 原因消息)
        """
        # 检查智能体是否存在
        agent = agent_manager.get_agent(self.agent_id)
        if not agent:
            return False, f"Agent does not exist: {self.agent_id}"
            
        # 具体验证逻辑由子类实现
        return self._validate(agent, world_state, env_manager, agent_manager)
    
    def _validate(self, agent, world_state, env_manager, agent_manager) -> Tuple[bool, str]:
        """
        验证动作的具体逻辑，由子类实现

        Args:
            agent: 执行动作的智能体
            world_state: 世界状态
            env_manager: 环境管理器
            agent_manager: 智能体管理器

        Returns:
            Tuple[bool, str]: (是否有效, 原因消息)
        """
        raise NotImplementedError("Subclass must implement this method")
    
    def execute(self, world_state, env_manager, agent_manager) -> Tuple[ActionStatus, str, Optional[Dict[str, Any]]]:
        """
        执行动作
        
        Args:
            world_state: 世界状态
            env_manager: 环境管理器
            agent_manager: 智能体管理器
            
        Returns:
            Tuple[ActionStatus, str, Optional[Dict]]: (执行状态, 反馈消息, 额外结果数据)
        """
        # 获取智能体
        agent = agent_manager.get_agent(self.agent_id)
        if not agent:
            return ActionStatus.FAILURE, f"智能体不存在: {self.agent_id}", None
            
        # 具体执行逻辑由子类实现
        return self._execute(agent, world_state, env_manager, agent_manager)
    
    def _execute(self, agent, world_state, env_manager, agent_manager) -> Tuple[ActionStatus, str, Optional[Dict[str, Any]]]:
        """
        执行动作的具体逻辑，由子类实现
        
        Args:
            agent: 执行动作的智能体
            world_state: 世界状态
            env_manager: 环境管理器
            agent_manager: 智能体管理器
            
        Returns:
            Tuple[ActionStatus, str, Optional[Dict]]: (执行状态, 反馈消息, 额外结果数据)
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def to_dict(self) -> Dict[str, Any]:
        """将动作转换为字典表示"""
        return {
            "type": self.action_type.name if self.action_type else None,
            "agent_id": self.agent_id,
            "target_id": self.target_id,
            "params": self.params
        } 