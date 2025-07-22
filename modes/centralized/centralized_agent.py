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

class CentralizedAgent(BaseAgent):
    """
    中心化多智能体控制器，基于LLMAgent修改
    使用单个LLM同时控制两个智能体，保持与单智能体相同的接口和功能
    """
    
    def __init__(self, simulator: SimulationEngine, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """初始化中心化多智能体控制器"""
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
        self.mode = "centralized"

        # 基础系统提示词模板
        self.base_system_prompt = self.prompt_manager.get_prompt_template(
            self.prompt_template,
            "system_prompt",
            "你是一个协调两个智能体完成任务的中央控制系统。"
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

        # 管理的智能体ID列表
        self.managed_agent_ids = ["agent_1", "agent_2"]

    def set_trajectory_recorder(self, trajectory_recorder):
        """设置轨迹记录器引用"""
        self.trajectory_recorder = trajectory_recorder
        logger.debug(f"🔗 中心化控制器 {self.agent_id} 已连接轨迹记录器")

    def set_task(self, task_description: str) -> None:
        """设置任务描述"""
        self.task_description = task_description

    def _get_system_prompt(self) -> str:
        """获取系统提示词（不包含动态动作描述）"""
        # 直接返回基础系统提示词，动作信息将在user prompt中提供
        return self.base_system_prompt

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

        # 获取智能体信息（包含两个智能体）
        agents = None
        if include_other_agents:
            agents = self.bridge.get_all_agents()
        else:
            # 包含管理的两个智能体
            agents = {}
            for agent_id in self.managed_agent_ids:
                agent_info = self.bridge.get_agent_info(agent_id)
                if agent_info:
                    agents[agent_id] = agent_info

        # 根据详细程度获取环境描述
        if detail_level == 'room':
            # 描述两个智能体所在的房间
            env_description = ""
            for agent_id in self.managed_agent_ids:
                agent_info = self.bridge.get_agent_info(agent_id)
                if agent_info and 'location_id' in agent_info:
                    room_id = agent_info.get('location_id')
                    room_desc = self.bridge.describe_room_natural_language(room_id, agents, sim_config)
                    env_description += f"\n{agent_id} location: {room_desc}"
        elif detail_level == 'brief':
            # 只描述智能体状态
            env_description = self.bridge.describe_environment_natural_language(agents, sim_config)
        else:  # detail_level == 'full'
            # 描述完整环境
            env_description = self.bridge.describe_environment_natural_language(agents, sim_config)

        # 更新缓存
        self.env_description_cache = env_description
        return env_description

    def _get_agents_status(self) -> str:
        """获取两个智能体的状态信息"""
        if not self.bridge:
            return ""
        
        status_info = []
        for agent_id in self.managed_agent_ids:
            agent_info = self.bridge.get_agent_info(agent_id)
            if agent_info:
                location = agent_info.get('location_id', 'unknown')
                status_info.append(f"{agent_id}: located at {location}")
            else:
                status_info.append(f"{agent_id}: status unknown")
        
        return "\n".join(status_info)

    def _get_available_actions_list(self) -> str:
        """获取可用动作列表"""
        try:
            if not self.bridge:
                return "Available actions information unavailable"

            # 直接使用现有的API调用，它会返回两个智能体的完整动作描述
            # 包括基础动作、智能体特定动作和协作动作
            actions_description = self.bridge.get_agent_supported_actions_description(self.managed_agent_ids)
            if actions_description:
                return actions_description
            else:
                return "Actions information unavailable"
        except Exception as e:
            logger.warning(f"获取可用动作列表时出错: {e}")
            return "Available actions information unavailable"

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

    def decide_action(self) -> Dict[str, str]:
        """决定两个智能体的下一步动作"""
        # 构建提示词
        prompt = self._parse_prompt()

        # 记录到对话历史
        self.chat_history.append({"role": "user", "content": prompt})

        # 控制对话历史长度
        if self.max_chat_history is not None and len(self.chat_history) > self.max_chat_history:
            self.chat_history = self.chat_history[-self.max_chat_history:]

        # 调用LLM生成响应，使用动态系统提示词
        system_prompt = self._get_system_prompt()
        response = self.llm.generate_chat(self.chat_history, system_message=system_prompt)

        # 解析响应中的动作命令
        actions = self._extract_dual_actions(response)

        # 记录LLM交互到轨迹记录器（使用新接口）
        if self.trajectory_recorder:
            # 获取token使用情况
            tokens_used = getattr(self.llm, 'last_token_usage', {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
            response_time_ms = getattr(self.llm, 'last_response_time_ms', 0.0)

            # 使用新的record_llm_interaction接口
            self.trajectory_recorder.record_llm_interaction(
                task_index=1,  # 默认任务索引
                interaction_index=0,  # 将由轨迹记录器内部管理
                prompt=prompt,
                response=response,
                tokens_used=tokens_used,
                response_time_ms=response_time_ms,
                extracted_action=f"agent_1={actions.get('agent_1', 'UNKNOWN')}, agent_2={actions.get('agent_2', 'UNKNOWN')}"
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
            'extracted_action': f"agent_1={actions.get('agent_1', 'UNKNOWN')}, agent_2={actions.get('agent_2', 'UNKNOWN')}"
        }

        return actions

    def _extract_dual_actions(self, response: str) -> Dict[str, str]:
        """从LLM响应中提取两个智能体的动作命令"""
        actions = {}
        lines = response.split('\n')

        logger.debug(f"解析LLM响应: {response}")

        # 尝试多种格式解析
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 格式1: Agent_1_Action: EXPLORE (新格式)
            if line.startswith('Agent_1_Action:') or line.startswith('Agnet_1_Action:') or line.startswith('agent_1_action:') or line.startswith('agent_1_动作：') or line.startswith('agent_1_动作:'):
                if line.startswith('Agent_1_Action:'):
                    action = line[15:].strip()  # 去掉"Agent_1_Action:"前缀
                elif line.startswith('Agnet_1_Action:'):
                    action = line[15:].strip()  # 去掉"Agnet_1_Action:"前缀（向后兼容拼写错误）
                elif line.startswith('agent_1_action:'):
                    action = line[15:].strip()  # 去掉"agent_1_action:"前缀（向后兼容）
                elif line.startswith('agent_1_动作：'):
                    action = line[8:].strip()   # 去掉"agent_1_动作："前缀
                else:
                    action = line[8:].strip()   # 去掉"agent_1_动作:"前缀

                action = action.rstrip('。，！？.!?')
                if action:
                    actions['agent_1'] = action
                    logger.debug(f"解析到agent_1动作: {action}")

            # 格式2: Agent_2_Action: GOTO kitchen_1 (新格式)
            elif line.startswith('Agent_2_Action:') or line.startswith('agent_2_action:') or line.startswith('agent_2_动作：') or line.startswith('agent_2_动作:'):
                if line.startswith('Agent_2_Action:'):
                    action = line[15:].strip()  # 去掉"Agent_2_Action:"前缀
                elif line.startswith('agent_2_action:'):
                    action = line[15:].strip()  # 去掉"agent_2_action:"前缀（向后兼容）
                elif line.startswith('agent_2_动作：'):
                    action = line[8:].strip()   # 去掉"agent_2_动作："前缀
                else:
                    action = line[8:].strip()   # 去掉"agent_2_动作:"前缀

                action = action.rstrip('。，！？.!?')
                if action:
                    actions['agent_2'] = action
                    logger.debug(f"解析到agent_2动作: {action}")

        # 检查是否解析成功
        if not actions or len(actions) < 2:
            logger.error(f"Action parsing failed or incomplete")
            logger.error(f"Parsing result: {actions}")
            logger.error(f"Original LLM response: {response}")

            # 不分配默认动作，直接返回解析失败的结果
            return {"agent_1": "PARSE_FAILED", "agent_2": "PARSE_FAILED"}

        logger.debug(f"最终动作分配: {actions}")
        return actions

    def get_llm_interaction_info(self) -> Dict[str, Any]:
        """获取最后一次LLM交互的详细信息（用于新评测器）"""
        return getattr(self, 'last_llm_interaction', None)

    def record_action(self, actions: Dict[str, str], results: Dict[str, Any]) -> None:
        """
        记录两个智能体的动作到历史，包含完整的LLM回复

        Args:
            actions: 两个智能体的动作字典
            results: 两个智能体的执行结果字典
        """
        # 聚合执行状态
        agent_1_status = results.get('agent_1', {}).get('status', ActionStatus.FAILURE)
        agent_2_status = results.get('agent_2', {}).get('status', ActionStatus.FAILURE)

        # 确定总体状态
        if agent_1_status == ActionStatus.SUCCESS and agent_2_status == ActionStatus.SUCCESS:
            overall_status = ActionStatus.SUCCESS
        elif agent_1_status == ActionStatus.SUCCESS or agent_2_status == ActionStatus.SUCCESS:
            overall_status = ActionStatus.SUCCESS  # 部分成功也算成功
        else:
            overall_status = ActionStatus.FAILURE

        # 合并结果消息
        agent_1_msg = results.get('agent_1', {}).get('message', '')
        agent_2_msg = results.get('agent_2', {}).get('message', '')
        combined_message = f"agent_1: {agent_1_msg}; agent_2: {agent_2_msg}"

        # 创建包含完整LLM回复的历史记录（扩展格式，向后兼容）
        # 确保ActionStatus枚举被转换为字符串以支持JSON序列化
        def serialize_status(status):
            if hasattr(status, 'name'):
                return status.name
            return str(status)

        # 序列化结果，确保ActionStatus被转换为字符串
        serialized_results = {}
        for agent_id, result in results.items():
            serialized_result = result.copy()
            if 'status' in serialized_result:
                serialized_result['status'] = serialize_status(serialized_result['status'])
            serialized_results[agent_id] = serialized_result

        # 构建动作字符串，显示两个智能体的具体动作
        action_str = f"agent_1={actions.get('agent_1', 'UNKNOWN')}, agent_2={actions.get('agent_2', 'UNKNOWN')}"

        history_entry = {
            'action': action_str,  # 显示具体的智能体动作而不是'COORDINATE'
            'result': {
                'status': serialize_status(overall_status),
                'message': combined_message,
                'result': serialized_results
            },
            'llm_response': getattr(self, 'last_llm_response', ''),  # 包含思考内容的完整回复

            # 中心化模式特有字段（扩展格式）
            'coordination_details': {
                'agent_1': {
                    'action': actions.get('agent_1', 'UNKNOWN'),
                    'result': serialized_results.get('agent_1', {})
                },
                'agent_2': {
                    'action': actions.get('agent_2', 'UNKNOWN'),
                    'result': serialized_results.get('agent_2', {})
                }
            }
        }

        self.history.append(history_entry)

        # 保持历史长度在限制范围内
        if self.max_history != float('inf') and len(self.history) > self.max_history:
            self.history = self.history[-int(self.max_history):]

    def step(self) -> Tuple[ActionStatus, str, Optional[Dict[str, Any]]]:
        """执行一步中心化多智能体行为"""
        # 增加步数计数器
        self.step_count += 1

        # 决定两个智能体要执行的动作
        actions = self.decide_action()

        logger.info(f"协调器分配动作: agent_1={actions.get('agent_1', 'UNKNOWN')}, agent_2={actions.get('agent_2', 'UNKNOWN')}")

        # 检查是否解析失败
        agent_1_failed = actions.get('agent_1', '').strip() == 'PARSE_FAILED'
        agent_2_failed = actions.get('agent_2', '').strip() == 'PARSE_FAILED'

        if agent_1_failed or agent_2_failed:
            logger.error("🚫 LLM response parsing failed, unable to extract valid actions")
            # 记录解析失败的历史
            results = {
                "agent_1": {"status": "FAILURE", "message": "LLM response parsing failed: Agent_1_Action not found", "result": None},
                "agent_2": {"status": "FAILURE", "message": "LLM response parsing failed: Agent_2_Action not found", "result": None}
            }
            self.record_action(actions, results)

            combined_message = "LLM response parsing failed: unable to extract Agent_1_Action and Agent_2_Action"
            return ActionStatus.FAILURE, combined_message, {
                "coordination_details": results,
                "actions": actions,
                "parse_failed": True
            }

        # 检查是否两个智能体都输出DONE
        agent_1_done = actions.get('agent_1', '').strip().upper() == 'DONE'
        agent_2_done = actions.get('agent_2', '').strip().upper() == 'DONE'

        if agent_1_done and agent_2_done:
            logger.info("🏁 两个智能体都输出DONE，任务结束")
            # 两个智能体都完成，返回DONE状态
            combined_message = "Both agents completed: agent_1=DONE, agent_2=DONE"

            # 记录历史
            results = {
                "agent_1": {"status": "SUCCESS", "message": "DONE", "result": None},
                "agent_2": {"status": "SUCCESS", "message": "DONE", "result": None}
            }
            self.record_action(actions, results)

            return ActionStatus.SUCCESS, combined_message, {
                "coordination_details": results,
                "actions": actions,
                "both_agents_done": True
            }

        # 同时执行两个智能体的动作
        results = {}
        overall_status = ActionStatus.SUCCESS
        messages = []

        for agent_id in self.managed_agent_ids:
            action = actions.get(agent_id, "EXPLORE")
            action = action.strip()

            # 如果是DONE命令，不需要执行，直接记录
            if action.upper() == 'DONE':
                results[agent_id] = {
                    "status": "SUCCESS",
                    "message": "DONE",
                    "result": None
                }
                messages.append(f"{agent_id}: DONE")
                logger.info(f"{agent_id} 输出DONE")
                continue

            # 记录执行命令
            logger.info(f"执行命令 {agent_id}: {action}")

            # 执行动作
            try:
                status, message, result = self.bridge.process_command(agent_id, action)
                results[agent_id] = {
                    "status": status.name if hasattr(status, 'name') else str(status),
                    "message": message,
                    "result": result
                }
                messages.append(f"{agent_id}: {message}")

                # 更新总体状态
                if status == ActionStatus.FAILURE or status == ActionStatus.INVALID:
                    if overall_status == ActionStatus.SUCCESS:
                        overall_status = status  # 如果之前是成功，现在变为失败

            except Exception as e:
                logger.error(f"Error executing {agent_id} action: {e}")
                results[agent_id] = {
                    "status": "FAILURE",
                    "message": f"Execution error: {str(e)}",
                    "result": None
                }
                messages.append(f"{agent_id}: Execution error")
                overall_status = ActionStatus.FAILURE

        # 特殊处理协作动作的结果聚合
        overall_status, combined_message = self._process_cooperation_results(actions, results, messages)

        # 记录历史
        self.record_action(actions, results)

        # 返回聚合结果（保持与单智能体相同的接口）
        return overall_status, combined_message, {
            "coordination_details": results,
            "actions": actions
        }

    def _process_cooperation_results(self, actions: Dict[str, str], results: Dict[str, Dict],
                                   messages: List[str]) -> Tuple[ActionStatus, str]:
        """
        处理协作动作的结果聚合逻辑

        当存在协作动作时，如果有任何一个智能体成功执行了协作动作，
        则认为整个协作是成功的，即使另一个智能体返回INVALID
        """
        # 检查是否存在协作动作
        has_cooperation = False
        cooperation_success = False
        cooperation_messages = []

        for agent_id, action in actions.items():
            if action.startswith('CORP_'):
                has_cooperation = True
                break

        if not has_cooperation:
            # 非协作动作，使用原有逻辑
            overall_status = ActionStatus.SUCCESS
            for agent_id, result in results.items():
                status_str = result.get("status", "FAILURE")
                if status_str in ["FAILURE", "INVALID"]:
                    if status_str == "FAILURE":
                        overall_status = ActionStatus.FAILURE
                    elif status_str == "INVALID" and overall_status == ActionStatus.SUCCESS:
                        overall_status = ActionStatus.INVALID
            return overall_status, "; ".join(messages)

        # 协作动作的特殊处理
        success_messages = []
        invalid_messages = []
        failure_messages = []

        for agent_id, result in results.items():
            status_str = result.get("status", "FAILURE")
            message = result.get("message", "")

            if status_str == "SUCCESS":
                success_messages.append(f"{agent_id}: {message}")
                # 检查是否是协作成功的消息
                if "successfully cooperated" in message:
                    cooperation_success = True
                    cooperation_messages.append(message)
            elif status_str == "INVALID":
                invalid_messages.append(f"{agent_id}: {message}")
            else:  # FAILURE
                failure_messages.append(f"{agent_id}: {message}")

        # 协作结果判断逻辑
        if cooperation_success:
            # 如果有协作成功，则整体视为成功
            # 使用协作成功的消息作为主要消息，其他消息作为补充
            if cooperation_messages:
                primary_message = cooperation_messages[0]  # 使用第一个协作成功消息
                combined_message = primary_message

                # 如果有其他成功消息，也包含进来
                other_success = [msg for msg in success_messages if "successfully cooperated" not in msg]
                if other_success:
                    combined_message += "; " + "; ".join(other_success)
            else:
                combined_message = "; ".join(success_messages)

            return ActionStatus.SUCCESS, combined_message

        elif success_messages and not failure_messages:
            # 有成功但没有协作成功，且没有失败
            return ActionStatus.SUCCESS, "; ".join(success_messages + invalid_messages)

        elif failure_messages:
            # 有失败消息
            return ActionStatus.FAILURE, "; ".join(failure_messages + success_messages + invalid_messages)

        else:
            # 全部是INVALID
            return ActionStatus.INVALID, "; ".join(invalid_messages)

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
        detail_level = env_config.get('detail_level', 'full')  # 中心化默认就是full

        # 全局观察模式判断
        is_global_mode = not only_show_discovered

        if is_global_mode:
            template_name = 'centralized_global'
            logger.info(f"🌍 检测到中心化全局观察模式，使用模板: {template_name}")
        else:
            template_name = 'centralized'
            logger.info(f"🔍 使用中心化探索模式，使用模板: {template_name}")

        logger.info("🤖 中心化智能体配置分析:")
        logger.info(f"  - detail_level: {detail_level}")
        logger.info(f"  - only_show_discovered: {only_show_discovered}")
        logger.info(f"  - 选择的模板: {template_name}")
        logger.info(f"  - 模式: {'🌍 全局观察' if is_global_mode else '🔍 探索模式'}")

        return template_name
