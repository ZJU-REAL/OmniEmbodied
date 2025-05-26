import json
import logging
from typing import Dict, List, Optional, Any, Tuple

from embodied_simulator import SimulationEngine
from embodied_simulator.core import ActionStatus

from ...core.base_agent import BaseAgent
from ...config import ConfigManager
from ...llm import BaseLLM, create_llm_from_config
from ...utils.prompt_manager import PromptManager

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
        
        # 任务描述
        self.task_description = self.config.get('task_description', "探索环境并与物体交互")
        
        # 是否使用思考链
        self.use_cot = self.config.get('use_cot', True)
        
        # 最大尝试次数
        self.max_attempts = self.config.get('max_attempts', 3)
    
    def set_task(self, task_description: str) -> None:
        """
        设置任务描述
        
        Args:
            task_description: 任务描述文本
        """
        self.task_description = task_description
    
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
        state = self.get_state()
        nearby_objects = self._get_nearby_objects()
        
        # 格式化历史记录
        history_summary = ""
        if self.history:
            history_summary = self.prompt_manager.format_history(self.mode, self.history)
        
        # 确定思考提示词
        thinking_prompt = self.prompt_manager.get_prompt_template(
            self.mode, 
            "thinking_prompt" if self.use_cot else "action_prompt"
        )
        
        # 使用提示词管理器格式化提示词
        return self.prompt_manager.get_formatted_prompt(
            self.mode, 
            "task_template",
            default_value="当前任务：{task_description}\n请告诉我接下来应该执行什么动作？",
            task_description=self.task_description,
            current_location=state.get('location', {}).get('name', 'unknown'),
            nearby_objects=self._format_object_list(nearby_objects),
            near_objects=self._format_object_list(state.get('near_objects', [])),
            inventory=self._format_object_list(state.get('inventory', [])),
            history_summary=history_summary,
            thinking_prompt=thinking_prompt
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
        if len(self.chat_history) > self.max_chat_history * 2:  # 成对减少
            self.chat_history = self.chat_history[-self.max_chat_history*2:]
        
        try:
            # 调用LLM生成响应
            response = self.llm.generate_chat(self.chat_history, system_message=self.system_prompt)
            
            # 解析响应中的动作命令
            action = self._extract_action(response)
            
            # 记录LLM响应到对话历史
            self.chat_history.append({"role": "assistant", "content": response})
            
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
                        # 提取出动作部分
                        action = word + " " +parts[1].split('。')[0].split('，')[0].strip()
                        return action
        
        # 如果没找到明确的动作，返回原始文本的最后一行（非空）
        for line in reversed(lines):
            if line.strip():
                return line.strip()
                
        # 保底返回
        return response.strip() 