from typing import Dict, List, Optional, Any, Tuple
import logging

from utils.embodied_simulator import SimulationEngine, ActionStatus

from core.base_agent import BaseAgent
from llm import BaseLLM, create_llm_from_config
from config import ConfigManager
from utils.prompt_manager import PromptManager
from .communication import CommunicationManager, MessageType, MessagePriority

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
            "system_prompt",
            agent_id=agent_id,
            personality=self.personality,
            skills=", ".join(self.skills)
        )
        
        # 对话历史
        self.chat_history = []
        max_chat_history = self.config.get('max_chat_history', 10)
        # -1 表示不限制历史长度
        self.max_chat_history = None if max_chat_history == -1 else max_chat_history
        
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
    
    def send_message(self, receiver_id: str, content: str,
                    message_type: MessageType = MessageType.DIRECT_MESSAGE,
                    priority: MessagePriority = MessagePriority.MEDIUM) -> bool:
        """
        发送消息给其他智能体 - 增强版本

        Args:
            receiver_id: 接收者ID
            content: 消息内容
            message_type: 消息类型
            priority: 消息优先级

        Returns:
            bool: 是否成功发送
        """
        if self.comm_manager:
            return self.comm_manager.send_message(self.agent_id, receiver_id, content,
                                                message_type, priority)
        return False

    def broadcast_message(self, content: str,
                         message_type: MessageType = MessageType.BROADCAST,
                         priority: MessagePriority = MessagePriority.MEDIUM) -> bool:
        """
        广播消息给所有已知智能体 - 增强版本

        Args:
            content: 消息内容
            message_type: 消息类型
            priority: 消息优先级

        Returns:
            bool: 是否成功发送
        """
        if self.comm_manager:
            return self.comm_manager.broadcast_message(self.agent_id, content,
                                                     message_type, priority)
        return False

    def share_information(self, receiver_id: str, info_type: str, info_data: Any) -> bool:
        """
        分享信息给其他智能体 - 参考CoELA的信息共享机制

        Args:
            receiver_id: 接收者ID
            info_type: 信息类型 (location, object, status等)
            info_data: 信息数据

        Returns:
            bool: 是否成功发送
        """
        if self.comm_manager:
            return self.comm_manager.send_info_sharing_message(
                self.agent_id, receiver_id, info_type, info_data)
        return False

    def coordinate_task(self, receiver_id: str, task_type: str, task_details: Dict[str, Any]) -> bool:
        """
        与其他智能体协调任务

        Args:
            receiver_id: 接收者ID
            task_type: 任务类型
            task_details: 任务详情

        Returns:
            bool: 是否成功发送
        """
        if self.comm_manager:
            return self.comm_manager.send_task_coordination_message(
                self.agent_id, receiver_id, task_type, task_details)
        return False
    
    def _parse_prompt(self) -> str:
        """
        解析并构建提示词
        
        Returns:
            str: 格式化后的提示词
        """
        # 获取历史记录设置
        history_config = self.config.get('history', {})
        max_history_in_prompt = history_config.get('max_history_in_prompt', 50)  # 默认显示50条历史记录
        
        # 格式化消息历史
        messages_summary = self.prompt_manager.format_messages(self.mode, self.message_queue)
        
        # 格式化行动历史
        history_summary = ""
        if self.history:
            history_summary = self.prompt_manager.format_history(self.mode, self.history, max_entries=max_history_in_prompt)
        
        # 获取环境描述
        env_description = ""
        env_config = self.config.get('env_description', {})
        if not isinstance(env_config, dict):
            env_config = {}
            
        # 自主智能体通常只能看到自己所在的房间
        if self.bridge:
            try:
                agent_info = self.bridge.get_agent_info(self.agent_id)
                if agent_info and 'location_id' in agent_info:
                    room_id = agent_info.get('location_id')
                    
                    detail_level = env_config.get('detail_level', 'room')
                    
                    # 根据详细程度选择不同的描述
                    if detail_level == 'full':
                        # 完整环境描述
                        env_description = self.bridge.describe_environment_natural_language(
                            sim_config={
                                'nlp_show_object_properties': env_config.get('show_object_properties', True),
                                'nlp_only_show_discovered': env_config.get('only_show_discovered', True)
                            }
                        )
                    elif detail_level == 'room':
                        # 当前房间描述
                        env_description = self.bridge.describe_room_natural_language(room_id)
                    else:
                        # 简要描述
                        env_description = self.bridge.describe_agent_natural_language(self.agent_id)
            except Exception as e:
                logger.warning(f"获取环境描述时出错: {e}")
        
        # 使用提示词管理器格式化完整提示词
        prompt = self.prompt_manager.get_formatted_prompt(
            self.mode,
            "user_prompt",
            task_description=self.task_description,
            messages_summary=messages_summary,
            history_summary=history_summary,
            environment_description=env_description
        )
        
        return prompt
    
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
        if self.max_chat_history is not None and len(self.chat_history) > self.max_chat_history * 2:
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

        # 尝试从响应中提取动作命令
        action = ""

        # 查找包含动作命令的行
        for line in lines:
            line = line.strip()

            # 检查是否是消息 - 支持更丰富的消息格式
            if line.startswith("MSG") and ":" in line:
                parts = line.split(":", 1)
                receiver_id = parts[0][3:].strip()
                content = parts[1].strip()

                # 检查是否包含消息类型标识
                message_type = MessageType.DIRECT_MESSAGE
                priority = MessagePriority.MEDIUM

                if content.startswith("[INFO]"):
                    message_type = MessageType.INFO_SHARING
                    content = content[6:].strip()
                elif content.startswith("[TASK]"):
                    message_type = MessageType.TASK_COORDINATION
                    priority = MessagePriority.HIGH
                    content = content[6:].strip()
                elif content.startswith("[HELP]"):
                    message_type = MessageType.HELP_REQUEST
                    priority = MessagePriority.HIGH
                    content = content[6:].strip()
                elif content.startswith("[STATUS]"):
                    message_type = MessageType.STATUS_UPDATE
                    content = content[8:].strip()

                success = self.send_message(receiver_id, content, message_type, priority)
                if success:
                    return f"SENT_MESSAGE_TO_{receiver_id}"
                else:
                    return "EXPLORE"

            # 检查是否是广播
            elif line.startswith("BROADCAST:"):
                content = line[10:].strip()

                # 检查广播类型
                message_type = MessageType.BROADCAST
                priority = MessagePriority.MEDIUM

                if content.startswith("[URGENT]"):
                    priority = MessagePriority.URGENT
                    content = content[8:].strip()
                elif content.startswith("[INFO]"):
                    message_type = MessageType.INFO_SHARING
                    content = content[6:].strip()

                success = self.broadcast_message(content, message_type, priority)
                if success:
                    return "BROADCAST_MESSAGE"
                else:
                    return "EXPLORE"

            # 检查是否是常见的动作命令
            elif any(line.startswith(cmd) for cmd in ['GOTO', 'GRAB', 'PLACE', 'EXPLORE', 'LOOK', 'DONE', 'OPEN', 'CLOSE', 'TURN_ON', 'TURN_OFF']):
                action = line
                break

            # 检查是否包含"动作命令："前缀
            elif "动作命令：" in line:
                action = line.split("动作命令：", 1)[1].strip()
                break

            # 检查是否是单个大写单词（可能是动作）
            elif line.isupper() and len(line.split()) == 1 and line.isalpha():
                action = line
                break

        # 如果没有找到明确的动作，使用最后一行
        if not action:
            action = lines[-1] if lines else "EXPLORE"

        # 清理动作命令
        action = action.strip()

        # 如果动作为空或包含中文解释，使用默认动作
        if not action or any('\u4e00' <= char <= '\u9fff' for char in action):
            action = "EXPLORE"

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
        status, message, result_data = self.bridge.process_command(self.agent_id, action)

        # 记录历史
        self.record_action(action, {"status": status, "message": message, "result": result_data})

        # 更新连续失败计数
        if status == ActionStatus.FAILURE or status == ActionStatus.INVALID:
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0

        # 清空处理过的消息队列
        self.message_queue = []

        return status, message, result_data