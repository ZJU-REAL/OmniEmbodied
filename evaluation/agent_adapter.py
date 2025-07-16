"""
智能体适配器 - 统一不同模式智能体的接口
"""

import logging
from typing import Dict, Any, Tuple, List, Union
from importlib import import_module

from .task_executor import ActionStatus

logger = logging.getLogger(__name__)


class AgentAdapter:
    """智能体适配器 - 统一不同模式智能体的接口"""
    
    def __init__(self, agent_type: str, config: Dict[str, Any], 
                 simulator, trajectory_recorder):
        """
        初始化智能体适配器
        
        Args:
            agent_type: 智能体类型 ('single', 'centralized', 'decentralized')
            config: 配置字典
            simulator: 模拟器实例
            trajectory_recorder: 轨迹记录器
        """
        self.agent_type = agent_type
        self.config = config
        self.simulator = simulator
        self.trajectory_recorder = trajectory_recorder
        
        # 创建对应的智能体实例
        self.agent = self._create_agent()
        
        # 设置轨迹记录器
        if hasattr(self.agent, 'set_trajectory_recorder'):
            self.agent.set_trajectory_recorder(trajectory_recorder)
        
        logger.info(f"🤖 智能体适配器初始化完成: {agent_type}")
    
    def _create_agent(self):
        """根据agent_type创建对应的智能体实例"""
        if self.agent_type == 'single':
            return self._create_single_agent()
        elif self.agent_type == 'centralized':
            return self._create_centralized_agents()
        elif self.agent_type == 'decentralized':
            return self._create_decentralized_agents()
        else:
            raise ValueError(f"不支持的智能体类型: {self.agent_type}")
    
    def _create_single_agent(self):
        """创建单智能体"""
        try:
            # 从配置获取智能体类
            agent_config = self.config.get('agent_config', {})
            agent_class_path = agent_config.get('agent_class', 'modes.single_agent.llm_agent.LLMAgent')
            
            # 动态导入智能体类
            module_path, class_name = agent_class_path.rsplit('.', 1)
            module = import_module(module_path)
            agent_class = getattr(module, class_name)
            
            # 创建智能体实例（单智能体模式使用agent_1）
            agent = agent_class(self.simulator, "agent_1", self.config)
            
            logger.info(f"✅ 单智能体创建成功: {agent_class_path}")
            return agent
            
        except Exception as e:
            logger.error(f"❌ 创建单智能体失败: {e}")
            raise
    
    def _create_centralized_agents(self):
        """创建中心化智能体系统"""
        try:
            # 从配置获取智能体类
            agent_config = self.config.get('agent_config', {})
            agent_class_path = agent_config.get('agent_class', 'modes.centralized.centralized_agent.CentralizedAgent')

            # 动态导入智能体类
            module_path, class_name = agent_class_path.rsplit('.', 1)
            module = import_module(module_path)
            agent_class = getattr(module, class_name)

            # 创建中心化智能体实例（使用centralized_controller作为ID）
            agent = agent_class(self.simulator, "centralized_controller", self.config)

            logger.info(f"✅ 中心化智能体创建成功: {agent_class_path}")
            return agent

        except Exception as e:
            logger.error(f"❌ 创建中心化智能体失败: {e}")
            raise
            return coordinator
            
        except Exception as e:
            logger.error(f"❌ 创建中心化智能体系统失败: {e}")
            raise
    
    def _create_decentralized_agents(self):
        """创建去中心化智能体系统"""
        try:
            # 从配置获取智能体类
            agent_config = self.config.get('agent_config', {})
            agent_class_path = agent_config.get(
                'agent_class', 'modes.decentralized.autonomous_agent.AutonomousAgent'
            )
            
            # 动态导入智能体类
            module_path, class_name = agent_class_path.rsplit('.', 1)
            module = import_module(module_path)
            agent_class = getattr(module, class_name)
            
            # 创建多个自主智能体
            num_agents = agent_config.get('num_agents', 3)
            agents = []
            
            for i in range(num_agents):
                agent_id = f"agent_{i+1}"
                agent = agent_class(self.simulator, agent_id, self.config)
                agents.append(agent)
            
            # 设置对等智能体关系
            for agent in agents:
                peers = [a for a in agents if a != agent]
                if hasattr(agent, 'set_peer_agents'):
                    agent.set_peer_agents(peers)
            
            logger.info(f"✅ 去中心化智能体系统创建成功: {num_agents}个自主智能体")
            
            # 返回智能体列表，但主要使用第一个作为主要接口
            return DecentralizedAgentWrapper(agents)
            
        except Exception as e:
            logger.error(f"❌ 创建去中心化智能体系统失败: {e}")
            raise
    
    def decide_action(self) -> str:
        """统一的动作决策接口"""
        try:
            if hasattr(self.agent, 'decide_action'):
                action = self.agent.decide_action()
                logger.debug(f"🎯 智能体决策: {action}")
                return action
            else:
                raise AttributeError(f"智能体没有实现decide_action方法")
        except Exception as e:
            logger.error(f"❌ 智能体决策失败: {e}")
            return "ERROR"
    
    def step(self) -> Tuple[ActionStatus, str, Dict[str, Any]]:
        """统一的步骤执行接口"""
        try:
            if hasattr(self.agent, 'step'):
                # 调用智能体的step方法
                status, message, result = self.agent.step()

                # 转换状态格式 - 处理多种可能的状态格式
                if isinstance(status, str):
                    if status.upper() == 'SUCCESS':
                        action_status = ActionStatus.SUCCESS
                    elif status.upper() == 'FAILED':
                        action_status = ActionStatus.FAILED
                    else:
                        action_status = ActionStatus.INVALID
                else:
                    # 处理来自OmniSimulator的ActionStatus枚举
                    # 导入OmniSimulator的ActionStatus以进行比较
                    try:
                        from OmniSimulator.core.enums import ActionStatus as SimActionStatus
                        if status == SimActionStatus.SUCCESS:
                            action_status = ActionStatus.SUCCESS
                        elif status == SimActionStatus.FAILURE:
                            action_status = ActionStatus.FAILED
                        elif status == SimActionStatus.INVALID:
                            action_status = ActionStatus.INVALID
                        elif status == SimActionStatus.PARTIAL:
                            action_status = ActionStatus.SUCCESS  # 部分成功视为成功
                        elif status == SimActionStatus.WAITING:
                            action_status = ActionStatus.SUCCESS  # 等待状态视为成功
                        else:
                            action_status = ActionStatus.INVALID
                    except ImportError:
                        # 如果无法导入，尝试通过名称判断
                        if hasattr(status, 'name'):
                            if status.name == 'SUCCESS':
                                action_status = ActionStatus.SUCCESS
                            elif status.name == 'FAILURE':
                                action_status = ActionStatus.FAILED
                            elif status.name == 'INVALID':
                                action_status = ActionStatus.INVALID
                            elif status.name == 'PARTIAL':
                                action_status = ActionStatus.SUCCESS
                            elif status.name == 'WAITING':
                                action_status = ActionStatus.SUCCESS
                            else:
                                action_status = ActionStatus.INVALID
                        else:
                            # 最后的兜底处理
                            action_status = status if isinstance(status, ActionStatus) else ActionStatus.INVALID

                return action_status, message, result
            else:
                raise AttributeError(f"智能体没有实现step方法")
        except Exception as e:
            logger.error(f"❌ 智能体步骤执行失败: {e}")
            return ActionStatus.FAILED, str(e), {}
    
    def set_task(self, task_description: str) -> None:
        """统一的任务设置接口"""
        try:
            if hasattr(self.agent, 'set_task'):
                self.agent.set_task(task_description)
                logger.debug(f"📋 任务已设置: {task_description}")
            else:
                logger.warning("智能体没有实现set_task方法")
        except Exception as e:
            logger.error(f"❌ 设置任务失败: {e}")
    
    def reset(self) -> None:
        """统一的重置接口"""
        try:
            if hasattr(self.agent, 'reset'):
                self.agent.reset()
                logger.debug("🔄 智能体已重置")
            else:
                logger.warning("智能体没有实现reset方法")
        except Exception as e:
            logger.error(f"❌ 重置智能体失败: {e}")
    
    def get_llm_interaction_info(self) -> Dict[str, Any]:
        """获取LLM交互信息"""
        try:
            if hasattr(self.agent, 'get_llm_interaction_info'):
                return self.agent.get_llm_interaction_info()
        except Exception as e:
            logger.warning(f"获取LLM交互信息失败: {e}")
        
        return None
    
    def get_mode_name(self) -> str:
        """获取模式名称"""
        try:
            if hasattr(self.agent, 'get_mode_name'):
                return self.agent.get_mode_name()
            else:
                return self.agent_type
        except Exception as e:
            logger.warning(f"获取模式名称失败: {e}")
            return self.agent_type


class DecentralizedAgentWrapper:
    """去中心化智能体包装器 - 将多个智能体包装成统一接口"""
    
    def __init__(self, agents: List):
        """
        初始化包装器
        
        Args:
            agents: 智能体列表
        """
        self.agents = agents
        self.primary_agent = agents[0] if agents else None
        self.current_agent_index = 0
    
    def decide_action(self) -> str:
        """轮询所有智能体进行决策"""
        if not self.agents:
            return "ERROR"
        
        # 简单的轮询策略，实际可以更复杂
        agent = self.agents[self.current_agent_index]
        action = agent.decide_action()
        
        # 切换到下一个智能体
        self.current_agent_index = (self.current_agent_index + 1) % len(self.agents)
        
        return action
    
    def step(self):
        """执行当前智能体的步骤"""
        if not self.primary_agent:
            return ActionStatus.FAILED, "No agents available", {}
        
        return self.primary_agent.step()
    
    def set_task(self, task_description: str):
        """为所有智能体设置任务"""
        for agent in self.agents:
            if hasattr(agent, 'set_task'):
                agent.set_task(task_description)
    
    def reset(self):
        """重置所有智能体"""
        for agent in self.agents:
            if hasattr(agent, 'reset'):
                agent.reset()
    
    def set_trajectory_recorder(self, recorder):
        """为所有智能体设置轨迹记录器"""
        for agent in self.agents:
            if hasattr(agent, 'set_trajectory_recorder'):
                agent.set_trajectory_recorder(recorder)
    
    def get_llm_interaction_info(self):
        """获取主要智能体的LLM交互信息"""
        if self.primary_agent and hasattr(self.primary_agent, 'get_llm_interaction_info'):
            return self.primary_agent.get_llm_interaction_info()
        return None
    
    def get_mode_name(self) -> str:
        """返回模式名称"""
        return "decentralized"
