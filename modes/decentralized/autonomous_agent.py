from typing import Dict, List, Optional, Any, Tuple
import logging

from embodied_simulator import SimulationEngine
from embodied_simulator.core import ActionStatus

from ...core.base_agent import BaseAgent
from ...llm import BaseLLM, create_llm_from_config
from ...config import ConfigManager
from ...utils.prompt_manager import PromptManager
from .communication import CommunicationManager

logger = logging.getLogger(__name__)

class AutonomousAgent(BaseAgent):
    """
    自主智能体，拥有自己的LLM进行决策，能够与其他智能体通信
    """
    
    def __init__(self, simulator: SimulationEngine, agent_id: str, config: Optional[Dict[str, Any]] = None, 
                 llm_config_name: str = 'llm_config', comm_manager: Optional[CommunicationManager] = None):
        """
        初始化自主智能体
        
        Args:
            simulator: 模拟引擎实例
            agent_id: 智能体ID
            config: 配置字典，可选
            llm_config_name: LLM配置名称，可选
            comm_manager: 通信管理器，可选
        """
        super().__init__(simulator, agent_id, config)
        
        # 加载LLM配置
        config_manager = ConfigManager()
        self.llm_config = config_manager.get_config(llm_config_name)
        
        # 创建LLM实例
        self.llm = create_llm_from_config(self.llm_config)
        
        # 通信管理器
        self.comm_manager = comm_manager
        
        # 创建提示词管理器
        self.prompt_manager = PromptManager("prompts_config")
        
        # 模式名称
        self.mode = "decentralized"
        
        # 个性设置，影响智能体行为风格
        self.personality = self.config.get('personality', '合作、高效、谨慎')
        
        # 特长和技能，影响智能体的专长领域
        self.skills = self.config.get('skills', ['探索', '交互'])
        
        # 系统提示词
        self.system_prompt = self.prompt_manager.get_formatted_prompt(
            self.mode,
            "autonomous_system",
            f"""
            你是一个自主智能体，ID为{agent_id}，拥有以下特点：
            - 个性：{self.personality}
            - 特长技能：{', '.join(self.skills)}
            
            你可以独立决策，也可以与其他智能体协作完成任务。
            在做决定时，考虑环境状态、自身能力和其他智能体的情况。
            如果需要协作，可以主动与其他智能体通信协商。
            """,
            agent_id=agent_id,
            personality=self.personality,
            skills=", ".join(self.skills)
        )
        
        # 对话历史
        self.chat_history = []
        self.max_chat_history = self.config.get('max_chat_history', 10)
        
        # 任务描述
        self.task_description = self.config.get('task_description', "完成目标")
        
        # 信息接收队列
        self.message_queue = []
        
        # 其他智能体信息
        self.known_agents = {}
    
    def set_task(self, task_description: str) -> None:
        """
        设置任务描述
        
        Args:
            task_description: 任务描述文本
        """
        self.task_description = task_description
    
    def receive_message(self, sender_id: str, content: str) -> None:
        """
        接收来自其他智能体的消息
        
        Args:
            sender_id: 发送者ID
            content: 消息内容
        """
        self.message_queue.append({
            "sender_id": sender_id,
            "content": content,
            "time": self.simulator.get_current_time() if hasattr(self.simulator, 'get_current_time') else 0
        })
    
    def send_message(self, receiver_id: str, content: str) -> bool:
        """
        发送消息给其他智能体
        
        Args:
            receiver_id: 接收者ID
            content: 消息内容
            
        Returns:
            bool: 是否成功发送
        """
        if self.comm_manager:
            return self.comm_manager.send_message(self.agent_id, receiver_id, content)
        return False
    
    def broadcast_message(self, content: str) -> bool:
        """
        广播消息给所有已知智能体
        
        Args:
            content: 消息内容
            
        Returns:
            bool: 是否成功发送
        """
        if self.comm_manager:
            return self.comm_manager.broadcast_message(self.agent_id, content)
        return False
    
    def _parse_prompt(self) -> str:
        """
        解析并构建提示词
        
        Returns:
            str: 格式化后的提示词
        """
        state = self.get_state()
        
        # 格式化库存
        inventory = ", ".join([item.get('name', item.get('id', 'unknown')) 
                             for item in state.get('inventory', [])]) or "空"
        
        # 格式化消息历史
        messages = self.prompt_manager.format_messages(self.mode, self.message_queue)
        
        # 格式化行动历史
        history = ""
        if self.history:
            history = self.prompt_manager.format_history(self.mode, self.history)
        
        # 使用提示词管理器格式化完整提示词
        return self.prompt_manager.get_formatted_prompt(
            self.mode,
            "autonomous_template",
            default_value="任务: {task_description}\n\n请决定下一步行动。",
            task_description=self.task_description,
            location=state.get('location', {}).get('name', 'unknown'),
            inventory=inventory,
            messages=messages,
            history=history
        )
    
    def decide_action(self) -> str:
        """
        决定下一步动作
        
        Returns:
            str: 动作命令字符串
        """
        # 构建提示词
        prompt = self._parse_prompt()
        
        # 记录到对话历史
        self.chat_history.append({"role": "user", "content": prompt})
        
        # 控制对话历史长度
        if len(self.chat_history) > self.max_chat_history * 2:
            self.chat_history = self.chat_history[-self.max_chat_history*2:]
        
        try:
            # 调用LLM生成响应
            response = self.llm.generate_chat(self.chat_history, system_message=self.system_prompt)
            
            # 记录LLM响应到对话历史
            self.chat_history.append({"role": "assistant", "content": response})
            
            # 处理响应
            return self._process_response(response)
            
        except Exception as e:
            logger.exception(f"自主智能体决策时出错: {e}")
            return "LOOK"
    
    def _process_response(self, response: str) -> str:
        """
        处理LLM响应，提取动作或发送消息
        
        Args:
            response: LLM响应文本
            
        Returns:
            str: 处理后的动作命令
        """
        lines = response.strip().split('\n')
        action = lines[-1] if lines else ""
        
        # 检查是否是消息
        if action.startswith("MSG") and ":" in action:
            parts = action.split(":", 1)
            receiver_id = parts[0][3:].strip()
            content = parts[1].strip()
            
            success = self.send_message(receiver_id, content)
            if success:
                # 如果发送成功，返回一个虚拟动作表示已发送消息
                return f"SENT_MESSAGE_TO_{receiver_id}"
            else:
                # 如果发送失败，执行查看环境的动作
                return "LOOK"
                
        # 检查是否是广播
        elif action.startswith("BROADCAST:"):
            content = action[10:].strip()
            success = self.broadcast_message(content)
            if success:
                # 如果广播成功，返回一个虚拟动作表示已广播消息
                return "BROADCAST_MESSAGE"
            else:
                # 如果广播失败，执行查看环境的动作
                return "LOOK"
        
        # 否则返回常规动作
        return action
    
    def step(self) -> Tuple[ActionStatus, str, Optional[Dict[str, Any]]]:
        """
        执行一步，包括处理消息和决策行动
        
        Returns:
            Tuple[ActionStatus, str, Optional[Dict[str, Any]]]: (执行状态, 反馈消息, 额外结果数据)
        """
        # 先决策
        action = self.decide_action()
        
        # 检查是否是虚拟消息动作
        if action.startswith("SENT_MESSAGE_TO_") or action == "BROADCAST_MESSAGE":
            # 创建一个模拟的成功状态
            from enum import Enum
            class VirtualStatus(Enum):
                MESSAGE_SENT = 1
            
            # 记录到历史
            self.history.append({
                "action": action,
                "result": {
                    "status": "MESSAGE_SENT",
                    "message": "消息已发送",
                }
            })
            
            return VirtualStatus.MESSAGE_SENT, "消息已发送", None
        
        # 执行实际动作
        result = self.execute_action(action)
        
        # 清空处理过的消息队列
        self.message_queue = []
        
        return result 