import json
import logging
from typing import Dict, List, Optional, Any, Tuple

from OmniSimulator.core.enums import ActionStatus
from OmniSimulator.core.engine import SimulationEngine

from core.base_agent import BaseAgent
from config.config_manager import ConfigManager
from llm.base_llm import BaseLLM
from llm.llm_factory import create_llm_from_config
from utils.prompt_manager import PromptManager

# 确保logger使用正确的名称，与文件路径一致
logger = logging.getLogger(__name__)

class LLMAgent(BaseAgent):
    """
    基于大语言模型的智能体，使用LLM决策下一步动作
    """
    
    def __init__(self, simulator: SimulationEngine, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """初始化LLM智能体"""
        super().__init__(simulator, agent_id, config)

        # 优先使用传递的配置，避免子进程中重新加载配置文件
        if config and '_llm_config' in config:
            # 使用传递的完整LLM配置（包含运行时覆盖）
            self.llm_config = config['_llm_config']
            logger.debug("使用传递的LLM配置（包含运行时覆盖）")
        else:
            # 回退到重新加载配置（主要用于单独测试）- 使用全局单例
            from config.config_manager import get_config_manager
            config_manager = get_config_manager()
            self.llm_config = config_manager.get_config('llm_config')
            logger.debug("从配置文件重新加载LLM配置（使用全局单例）")

        # 创建LLM实例
        self.llm = create_llm_from_config(self.llm_config)

        # 自动选择提示词模板
        self.prompt_template = self._select_prompt_template()

        # 创建提示词管理器，优先使用传递的配置
        if config and '_prompts_config' in config:
            self.prompt_manager = PromptManager(config_dict=config['_prompts_config'])
            logger.debug("使用传递的提示词配置（包含运行时覆盖）")
        else:
            self.prompt_manager = PromptManager("prompts_config")
            logger.debug("从配置文件重新加载提示词配置（使用全局单例）")

        # 模式名称
        self.mode = "single_agent"

        # 基础系统提示词模板
        self.base_system_prompt = self.prompt_manager.get_prompt_template(
            self.prompt_template,
            "system_prompt",
            "你是一个在虚拟环境中执行任务的智能体。"
        )

        # 轨迹记录器引用（用于记录LLM QA）
        self.trajectory_recorder = None

        # 对话历史
        self.chat_history = []

        # 获取历史长度配置
        agent_config = self.config.get('agent_config', {})
        max_history_length = agent_config.get('max_history', 10)

        # 处理 max_history = -1 的特殊情况
        if max_history_length == -1:
            # 当 max_history = -1 时，使用 max_steps_per_task 的值
            execution_config = self.config.get('execution', {})
            max_steps_per_task = execution_config.get('max_steps_per_task', 50)
            self.max_history = max_steps_per_task
            self.max_chat_history = max_steps_per_task
            logger.info(f"max_history设置为-1，使用max_steps_per_task值: {max_steps_per_task}")
        else:
            # 使用指定的历史长度
            self.max_history = max_history_length
            self.max_chat_history = max_history_length

        # 任务描述
        self.task_description = ""

        # 保存最后一次LLM回复，用于历史记录
        self.last_llm_response = ""

        # 环境描述缓存和更新计数
        self.env_description_cache = ""
        self.step_count = 0

    def set_trajectory_recorder(self, trajectory_recorder):
        """设置轨迹记录器引用"""
        self.trajectory_recorder = trajectory_recorder
        logger.debug(f"🔗 智能体 {self.agent_id} 已连接轨迹记录器")

    def set_task(self, task_description: str) -> None:
        """设置任务描述"""
        self.task_description = task_description

    def _get_available_actions_list(self) -> str:
        """获取可用动作列表"""
        try:
            if not self.bridge:
                return "Available actions information unavailable"

            # 获取单智能体的动作描述
            actions_description = self.bridge.get_agent_supported_actions_description(self.agent_id)
            if actions_description:
                return actions_description
            else:
                return "Actions information unavailable"
        except Exception as e:
            logger.warning(f"Error getting available actions list: {e}")
            return "Available actions information unavailable"
    

    
    def _get_environment_description(self) -> str:
        """获取环境描述，根据配置决定详细程度和更新频率"""
        if not self.bridge:
            return ""

        # 获取环境描述配置（从agent_config下读取）
        agent_config = self.config.get('agent_config', {})
        env_config = agent_config.get('environment_description', {})
        detail_level = env_config.get('detail_level', 'full')
        show_properties = env_config.get('show_object_properties', True)
        only_discovered = env_config.get('only_show_discovered', False)
        include_other_agents = env_config.get('include_other_agents', True)
        update_frequency = env_config.get('update_frequency', 0)

        # 检查是否需要更新环境描述缓存
        should_update = (
            update_frequency == 0 or  # 每步都更新
            self.step_count % update_frequency == 0 or  # 按频率更新
            not self.env_description_cache  # 首次获取
        )

        if not should_update:
            return self.env_description_cache

        # 构建模拟器配置
        sim_config = {
            'nlp_show_object_properties': show_properties,
            'nlp_only_show_discovered': only_discovered,
            'nlp_detail_level': detail_level
        }

        # 获取智能体信息
        agents = None
        if include_other_agents:
            agents = self.bridge.get_all_agents()
        else:
            # 只包含当前智能体
            agent_info = self.bridge.get_agent_info(self.agent_id)
            if agent_info:
                agents = {self.agent_id: agent_info}

        # 根据详细程度获取环境描述
        if detail_level == 'room':
            # 只描述当前房间
            agent_info = self.bridge.get_agent_info(self.agent_id)
            if agent_info and 'location_id' in agent_info:
                room_id = agent_info.get('location_id')
                env_description = self.bridge.describe_room_natural_language(room_id, agents, sim_config)
            else:
                env_description = "Unable to determine current location"
        elif detail_level == 'brief':
            # 只描述智能体状态
            env_description = self.bridge.describe_environment_natural_language(agents, sim_config)
        else:  # detail_level == 'full'
            # 描述完整环境
            env_description = self.bridge.describe_environment_natural_language(agents, sim_config)

        # 更新缓存
        self.env_description_cache = env_description
        return env_description

    def _parse_prompt(self) -> str:
        """构建提示词"""
        # 历史记录摘要
        history_summary = ""
        if self.history:
            # 使用配置的历史长度，如果是无限制(-1)则使用所有历史
            max_display_entries = len(self.history) if self.max_chat_history is None else self.max_chat_history

            # 获取历史记录格式配置
            history_format_config = self.config.get('history', {}).get('format', {})

            history_summary = self.prompt_manager.format_history(
                self.mode,
                self.history,
                max_entries=max_display_entries,
                config=history_format_config
            )

        # 获取环境描述（根据配置）
        env_description = self._get_environment_description()

        # 获取可用动作列表
        available_actions_list = self._get_available_actions_list()

        # 格式化提示词，使用选择的模板
        prompt = self.prompt_manager.get_formatted_prompt(
            self.prompt_template,
            "user_prompt",
            task_description=self.task_description,
            history_summary=history_summary,
            environment_description=env_description,
            available_actions_list=available_actions_list
        )

        return prompt
    
    def decide_action(self) -> str:
        """决定下一步动作"""
        # 构建提示词
        prompt = self._parse_prompt()

        # 记录到对话历史
        self.chat_history.append({"role": "user", "content": prompt})

        # 控制对话历史长度
        if self.max_chat_history is not None and len(self.chat_history) > self.max_chat_history:
            self.chat_history = self.chat_history[-self.max_chat_history:]

        # 调用LLM生成响应，使用基础系统提示词
        response = self.llm.generate_chat(self.chat_history, system_message=self.base_system_prompt)

        # 解析响应中的动作命令
        action = self._extract_action(response)

        # 记录LLM交互到轨迹记录器（使用新接口）
        if self.trajectory_recorder:
            # 获取token使用情况
            tokens_used = getattr(self.llm, 'last_token_usage', {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
            response_time_ms = getattr(self.llm, 'last_response_time_ms', 0.0)

            # 获取当前任务索引，如果没有设置则使用默认值1
            current_task_index = getattr(self, 'current_task_index', 1)

            # 单智能体使用步数作为交互索引
            self.trajectory_recorder.record_llm_interaction(
                task_index=current_task_index,  # 使用当前任务索引
                interaction_index=self.step_count,  # 使用步数作为交互索引
                prompt=prompt,
                response=response,
                tokens_used=tokens_used,
                response_time_ms=response_time_ms,
                extracted_action=action
            )

        # 记录LLM响应到对话历史
        self.chat_history.append({"role": "assistant", "content": response})

        # 保存完整的LLM回复，用于历史记录
        self.last_llm_response = response

        # 保存最后一次LLM交互信息（用于新评测器）
        self.last_llm_interaction = {
            'prompt': prompt,
            'response': response,
            'tokens_used': getattr(self.llm, 'last_token_usage', {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}),
            'response_time_ms': getattr(self.llm, 'last_response_time_ms', 0.0),
            'extracted_action': action
        }

        return action

    def get_llm_interaction_info(self) -> Dict[str, Any]:
        """获取最后一次LLM交互的详细信息（用于新评测器）"""
        return getattr(self, 'last_llm_interaction', None)

    def _extract_action(self, response: str) -> str:
        """从LLM响应中提取动作命令"""
        lines = response.split('\n')

        # 直接匹配"Agnet_1_Action:"格式，提取后面的命令
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 匹配"Agent_1_Action:"格式（支持中英文）
            if line.startswith('Agent_1_Action:') or line.startswith('Agnet_1_Action:') or line.startswith('Action:') or line.startswith('动作：') or line.startswith('动作:'):
                # 提取冒号后的内容作为动作命令
                if line.startswith('Agent_1_Action:'):
                    action = line[15:].strip()  # 去掉"Agent_1_Action:"前缀
                elif line.startswith('Agnet_1_Action:'):
                    action = line[15:].strip()  # 去掉"Agnet_1_Action:"前缀（向后兼容拼写错误）
                elif line.startswith('Action:'):
                    action = line[7:].strip()  # 去掉"Action:"前缀（向后兼容）
                elif line.startswith('动作：'):
                    action = line[3:].strip()  # 去掉"动作："前缀
                else:
                    action = line[3:].strip()  # 去掉"动作:"前缀

                # 去除可能的标点符号
                action = action.rstrip('。，！？.!?')

                if action:
                    return action

        # 如果没找到格式，返回最后一行非空文本作为回退
        for line in reversed(lines):
            if line.strip():
                return line.strip()

        return response.strip()

    def record_action(self, action: str, result: Dict[str, Any]) -> None:
        """
        记录动作到历史，包含完整的LLM回复（思考+动作）

        Args:
            action: 动作命令
            result: 执行结果
        """
        # 创建包含完整LLM回复的历史记录
        history_entry = {
            'action': action,
            'result': result,
            'llm_response': getattr(self, 'last_llm_response', ''),  # 包含思考内容的完整回复
        }

        self.history.append(history_entry)

        # 保持历史长度在限制范围内
        if self.max_history != float('inf') and len(self.history) > self.max_history:
            self.history = self.history[-int(self.max_history):]

    def step(self) -> Tuple[ActionStatus, str, Optional[Dict[str, Any]]]:
        """执行一步智能体行为"""
        # 增加步数计数器
        self.step_count += 1

        # 决定要执行的动作
        action = self.decide_action()
        action = action.strip()

        # 记录执行命令
        logger.info("Executing command: %s", action)

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

    def _select_prompt_template(self) -> str:
        """
        根据配置自动选择合适的提示词模板

        Returns:
            str: 提示词模板名称
        """
        # 获取环境描述配置
        agent_config = self.config.get('agent_config', {})
        env_config = agent_config.get('environment_description', {})

        # 检查是否启用全局观察模式
        only_show_discovered = env_config.get('only_show_discovered', True)
        detail_level = env_config.get('detail_level', 'room')

        # 全局观察模式的判断条件：
        # 1. only_show_discovered = False (显示所有物体)
        # 2. detail_level = 'full' (显示所有房间)
        is_global_mode = (not only_show_discovered) and (detail_level == 'full')

        if is_global_mode:
            template_name = 'single_agent_global'
            logger.info(f"🌍 检测到全局观察模式，使用模板: {template_name}")
        else:
            template_name = 'single_agent'
            logger.info(f"🔍 使用探索模式，使用模板: {template_name}")

        logger.info("🤖 智能体配置分析:")
        logger.info(f"  - detail_level: {detail_level}")
        logger.info(f"  - only_show_discovered: {only_show_discovered}")
        logger.info(f"  - 选择的模板: {template_name}")
        logger.info(f"  - 模式: {'🌍 全局观察' if is_global_mode else '🔍 探索模式'}")

        return template_name