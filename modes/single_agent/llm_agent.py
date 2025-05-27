import json
import logging
from typing import Dict, List, Optional, Any, Tuple

from embodied_simulator import SimulationEngine
from embodied_simulator.core import ActionStatus

from ...core.base_agent import BaseAgent
from ...config import ConfigManager
from ...llm import BaseLLM, create_llm_from_config
from ...utils.prompt_manager import PromptManager

# 确保logger使用正确的名称，与文件路径一致
logger = logging.getLogger(__name__)

class LLMAgent(BaseAgent):
    """
    基于大语言模型的智能体，使用LLM决策下一步动作
    """
    
    def __init__(self, simulator: SimulationEngine, agent_id: str, config: Optional[Dict[str, Any]] = None, 
                 llm_config_name: str = 'llm_config'):
        """
        初始化LLM智能体
        
        Args:
            simulator: 模拟引擎实例
            agent_id: 智能体ID
            config: 配置字典，可选
            llm_config_name: LLM配置名称，可选
        """
        super().__init__(simulator, agent_id, config)
        
        # 加载LLM配置
        config_manager = ConfigManager()
        self.llm_config = config_manager.get_config(llm_config_name)
        
        # 创建LLM实例
        self.llm = create_llm_from_config(self.llm_config)
        
        # 创建提示词管理器
        self.prompt_manager = PromptManager("prompts_config")
        
        # 模式名称
        self.mode = "single_agent"
        
        # 从配置中获取系统提示词
        self.system_prompt = self.prompt_manager.get_prompt_template(self.mode, "system", 
            "你是一个在虚拟环境中执行任务的智能体。你可以探索环境、与物体交互，并执行各种动作。注意：你必须先靠近物体才能与之交互。")
        
        # 对话历史
        self.chat_history = []
        self.max_chat_history = self.config.get('max_chat_history', 10)
        
        # 任务描述 - 从bridge获取而不是从配置中获取
        try:
            self.task_description = self.bridge.get_task_description()
            if not self.task_description:
                # 如果bridge没有返回任务描述，则使用配置或默认值
                self.task_description = self.config.get('task_description', "探索环境并与物体交互")
                logger.warning("无法从模拟器获取任务描述，使用默认值: %s", self.task_description)
        except Exception as e:
            self.task_description = self.config.get('task_description', "探索环境并与物体交互")
            logger.warning("获取任务描述时出错: %s，使用默认值: %s", e, self.task_description)
        
        # 记录任务描述
        if logger.level <= logging.DEBUG:
            logger.debug("当前任务: %s", self.task_description)
        
        # 是否使用思考链
        self.use_cot = self.config.get('use_cot', True)
        
        # 最大尝试次数
        self.max_attempts = self.config.get('max_attempts', 3)
        
        # 调试级别日志时记录完整的提示词和回复
        self._log_init_debug_info()
    
    def _log_init_debug_info(self) -> None:
        """记录初始化调试信息"""
        if logger.level <= logging.DEBUG:
            logger.debug("=== LLMAgent初始化信息 ===")
            logger.debug("智能体ID: %s", self.agent_id)
            logger.debug("LLM提供商: %s", self.llm_config.get('provider', '未指定'))
            logger.debug("系统提示词: %s", self.system_prompt)
            logger.debug("使用思考链: %s", self.use_cot)
            logger.debug("最大尝试次数: %d", self.max_attempts)
            logger.debug("========================")
    
    def set_task(self, task_description: str) -> None:
        """
        设置任务描述
        
        Args:
            task_description: 任务描述文本
        """
        self.task_description = task_description
        if logger.level <= logging.DEBUG:
            logger.debug("设置新任务: %s", task_description)
    
    def _format_object_list(self, objects: List[Dict[str, Any]]) -> str:
        """格式化物体列表为可读字符串"""
        if not objects:
            return "无"
        
        return ", ".join([f"{obj.get('name', obj.get('id', '未知'))}({obj.get('id', '未知')})" for obj in objects])
    
    def _get_nearby_objects(self) -> List[Dict[str, Any]]:
        """获取附近物体列表（房间中的所有已发现物体）"""
        agent_info = self.bridge.get_agent_info(self.agent_id)
        if not agent_info:
            return []
        
        location_id = agent_info.get('location_id', '')
        if not location_id:
            return []
        
        # 使用bridge获取房间内物体
        return self.bridge.get_objects_in_room(location_id)
    
    def _parse_prompt(self) -> str:
        """
        解析并构建提示词
        
        Returns:
            str: 格式化后的提示词
        """
        # 初始化历史记录摘要
        history_summary = ""
        
        # 格式化历史记录
        if self.history:
            # 获取历史记录设置
            history_config = self.config.get('history', {})
            max_history_in_prompt = history_config.get('max_history_in_prompt', 50)  # 默认显示50条历史记录
            history_summary = self.prompt_manager.format_history(self.mode, self.history, max_entries=max_history_in_prompt)
        
        # 确定思考提示词
        thinking_prompt = self.prompt_manager.get_prompt_template(
            self.mode, 
            "thinking_prompt" if self.use_cot else "action_prompt"
        )
        
        # 获取环境描述
        env_description = ""
        env_config = self.config.get('env_description', {})
        if not isinstance(env_config, dict):
            env_config = {}
            
        # 默认使用房间级别的描述
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
                                'nlp_show_object_properties': env_config.get('show_object_properties', False),
                                'nlp_only_show_discovered': env_config.get('only_show_discovered', True),
                                'nlp_detail_level': detail_level
                            }
                        )
                    elif detail_level == 'room':
                        # 当前房间描述
                        env_description = self.bridge.describe_room_natural_language(room_id)
                    else:
                        # 简要描述
                        env_description = self.bridge.describe_agent_natural_language(self.agent_id)
                    
                    # 记录调试级别的环境描述
                    if logger.level <= logging.DEBUG:
                        logger.debug("=== 当前环境描述(%s) ===\n%s\n===================", detail_level, env_description)
            except Exception as e:
                logger.warning(f"获取环境描述时出错: {e}")
        
        # 使用提示词管理器格式化提示词
        prompt = self.prompt_manager.get_formatted_prompt(
            self.mode, 
            "task_template",
            task_description=self.task_description,
            history_summary=history_summary,
            thinking_prompt=thinking_prompt,
            environment_description=env_description
        )
        
        return prompt
    
    def decide_action(self) -> str:
        """
        决定下一步动作
        
        Returns:
            str: 动作命令字符串
        """
        # 记录完整的对话历史（在调试模式下）
        if logger.level <= logging.DEBUG:
            self._log_chat_history()
        
        # 构建提示词
        prompt = self._parse_prompt()
        
        # 记录调试级别的提示词
        if logger.level <= logging.DEBUG:
            logger.debug("=== 发送给LLM的提示词 ===\n%s\n===================", prompt)
        
        # 记录到对话历史
        self.chat_history.append({"role": "user", "content": prompt})
        
        # 控制对话历史长度
        if len(self.chat_history) > self.max_chat_history * 2:  # 成对减少
            self.chat_history = self.chat_history[-self.max_chat_history*2:]
        
        try:
            # 调用LLM生成响应
            response = self.llm.generate_chat(self.chat_history, system_message=self.system_prompt)
            
            # 记录调试级别的LLM完整响应
            if logger.level <= logging.DEBUG:
                logger.debug("=== LLM原始响应 ===\n%s\n===================", response)
            
            # 解析响应中的动作命令
            action = self._extract_action(response)
            
            # 记录调试级别的解析后动作
            if logger.level <= logging.DEBUG:
                logger.debug("解析出的动作命令: %s", action)
            
            # 记录LLM响应到对话历史
            self.chat_history.append({"role": "assistant", "content": response})
            
            # 记录更新后的对话历史（在调试模式下）
            if logger.level <= logging.DEBUG:
                self._log_chat_history(is_after_response=True)
            
            return action
            
        except Exception as e:
            logger.exception(f"LLM生成动作时出错: {e}")
            # 如果出错，返回LOOK命令，相对安全
            return "LOOK"
    
    def _extract_action(self, response: str) -> str:
        """
        从LLM响应中提取动作命令
        
        Args:
            response: LLM响应文本
            
        Returns:
            str: 提取的动作命令
        """
        # 尝试找出最后提出的动作
        lines = response.split('\n')
        action = ""
        
        # 从后向前遍历，找到第一个可能的动作命令
        for line in reversed(lines):
            line = line.strip()
            # 跳过空行
            if not line:
                continue
                
            # 检查是否是动作命令（简单规则：包含大写动作词）
            action_words = ['GOTO', 'GRAB', 'PLACE', 'LOOK', 'OPEN', 'CLOSE', 
                           'ON', 'OFF', 'EXPLORE', 'NAVIGATE', 'PICK', 'CORP_GRAB', 
                           'CORP_GOTO', 'CORP_PLACE']
            
            for word in action_words:
                if word in line.upper():
                    # 可能找到了动作，进一步清理
                    parts = line.split(word, 1)
                    if len(parts) > 1:
                        # 提取参数部分并去除标点符号
                        param_part = parts[1].split('。')[0].split('，')[0].strip()
                        # 只有当参数非空时才添加空格，避免尾随空格
                        action = word if not param_part else word + " " + param_part
                        
                        # 调试级别记录动作提取过程
                        if logger.level <= logging.DEBUG:
                            logger.debug("动作提取: 在'%s'中找到动作词'%s'，提取为'%s'", line, word, action)
                        
                        return action
                    else:
                        # 如果只有动作词没有参数，直接返回动作词
                        return word
        
        # 如果没找到明确的动作，返回原始文本的最后一行（非空）
        for line in reversed(lines):
            if line.strip():
                if logger.level <= logging.DEBUG:
                    logger.debug("动作提取: 未找到明确动作词，使用最后一行非空文本'%s'", line.strip())
                return line.strip()
                
        # 保底返回
        if logger.level <= logging.DEBUG:
            logger.debug("动作提取: 使用整个响应的去空白版本")
        return response.strip()
    
    def step(self) -> Tuple[ActionStatus, str, Optional[Dict[str, Any]]]:
        """
        执行一步智能体行为（重写BaseAgent的step方法，增加调试信息）
        
        Returns:
            Tuple: (执行状态, 反馈消息, 结果数据)
        """
        # 决定要执行的动作
        action = self.decide_action()
        
        # 确保动作命令两端没有多余空格
        action = action.strip()
        
        # 记录执行命令日志 - 使用根日志器确保显示
        root_logger = logging.getLogger("single_agent_example")
        root_logger.info("执行命令: %s", action)
        
        # 调试日志使用本模块的日志器
        if logger.level <= logging.DEBUG:
            logger.debug("准备执行动作: %s", action)
        
        # 执行动作
        status, message, result = self.bridge.process_command(self.agent_id, action)
        
        # 记录调试级别的执行结果
        if logger.level <= logging.DEBUG:
            logger.debug("动作执行结果: 状态=%s, 消息=%s", status, message)
            if result:
                logger.debug("详细结果数据: %s", json.dumps(result, ensure_ascii=False, indent=2))
            
            # 执行后获取更新的环境描述
            try:
                agent_info = self.bridge.get_agent_info(self.agent_id)
                if agent_info and 'location_id' in agent_info:
                    room_id = agent_info.get('location_id')
                    room_desc = self.bridge.describe_room_natural_language(room_id)
                    logger.debug("=== 执行后房间状态 ===\n%s\n===================", room_desc)
            except Exception as e:
                logger.debug("获取执行后环境描述出错: %s", e)
        
        # 记录历史
        self.record_action(action, {"status": status, "message": message, "result": result})
        
        # 更新连续失败计数
        if status == ActionStatus.FAILURE or status == ActionStatus.INVALID:
            self.consecutive_failures += 1
            if logger.level <= logging.DEBUG:
                logger.debug("连续失败次数增加到: %d", self.consecutive_failures)
        else:
            self.consecutive_failures = 0
        
        return status, message, result 

    def _log_chat_history(self, is_after_response: bool = False) -> None:
        """
        记录完整的聊天历史（仅在DEBUG模式下）
        
        Args:
            is_after_response: 是否在获取响应后记录
        """
        if logger.level <= logging.DEBUG:
            logger.debug("=== 当前聊天历史 %s ===", "（响应后）" if is_after_response else "（请求前）")
            for i, message in enumerate(self.chat_history):
                role = message.get("role", "unknown")
                content = message.get("content", "")
                # 为不同角色使用不同前缀，便于区分
                prefix = "系统" if role == "system" else "用户" if role == "user" else "AI"
                logger.debug(f"[{i}] {prefix}: {content[:150]}..." if len(content) > 150 else f"[{i}] {prefix}: {content}")
            logger.debug("===================") 