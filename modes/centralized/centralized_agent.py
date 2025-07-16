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

        # 加载LLM配置
        config_manager = ConfigManager()
        self.llm_config = config_manager.get_config('llm_config')

        # 创建LLM实例
        self.llm = create_llm_from_config(self.llm_config)

        # 创建提示词管理器
        self.prompt_manager = PromptManager("prompts_config")

        # 模式名称
        self.mode = "centralized"

        # 基础系统提示词模板
        self.base_system_prompt = self.prompt_manager.get_prompt_template(
            self.mode,
            "system_prompt",
            "你是一个协调两个智能体完成任务的中央控制系统。"
        )

        # 轨迹记录器引用（用于记录LLM QA）
        self.trajectory_recorder = None

        # 对话历史
        self.chat_history = []

        # 获取历史长度配置
        history_config = self.config.get('history', {})
        max_history_length = history_config.get('max_history_length', 10)
        # -1 表示不限制历史长度
        self.max_chat_history = None if max_history_length == -1 else max_history_length

        # 同时更新动作历史的长度限制
        if max_history_length == -1:
            self.max_history = float('inf')  # 不限制动作历史长度
        else:
            self.max_history = max_history_length

        # 任务描述
        self.task_description = ""

        # 保存最后一次LLM回复，用于历史记录
        self.last_llm_response = ""

        # 环境描述缓存和更新计数
        self.env_description_cache = ""
        self.step_count = 0

        # 管理的智能体ID列表
        self.managed_agent_ids = ["agent_1", "agent_2"]
        
        # 循环检测
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
        self.last_assignments = None

    def set_trajectory_recorder(self, trajectory_recorder):
        """设置轨迹记录器引用"""
        self.trajectory_recorder = trajectory_recorder
        logger.debug(f"🔗 中心化控制器 {self.agent_id} 已连接轨迹记录器")

    def set_task(self, task_description: str) -> None:
        """设置任务描述"""
        self.task_description = task_description

    def _get_system_prompt(self) -> str:
        """获取包含动态动作描述的系统提示词"""
        # 获取动态动作描述（传入两个智能体ID列表）
        actions_description = ""
        if self.bridge:
            actions_description = self.bridge.get_agent_supported_actions_description(self.managed_agent_ids)

        # 如果获取到动作描述，则插入到系统提示词中
        if actions_description:
            return f"{self.base_system_prompt}\n\n{actions_description}"
        else:
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

    def _parse_prompt(self) -> str:
        """构建提示词"""
        # 历史记录摘要
        history_summary = ""
        if self.history:
            # 使用配置的历史长度，如果是无限制(-1)则使用所有历史
            max_display_entries = len(self.history) if self.max_chat_history is None else self.max_chat_history
            history_summary = self.prompt_manager.format_history(self.mode, self.history, max_entries=max_display_entries)

        # 获取环境描述（根据配置）
        env_description = self._get_environment_description()
        
        # 获取智能体状态
        agents_status = self._get_agents_status()

        # 格式化提示词
        prompt = self.prompt_manager.get_formatted_prompt(
            self.mode,
            "user_prompt",
            task_description=self.task_description,
            history_summary=history_summary,
            environment_description=env_description,
            agents_status=agents_status
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

            # 格式1: agent_1_action: EXPLORE
            if line.startswith('agent_1_action:') or line.startswith('agent_1_动作：') or line.startswith('agent_1_动作:'):
                if line.startswith('agent_1_action:'):
                    action = line[15:].strip()  # 去掉"agent_1_action:"前缀
                elif line.startswith('agent_1_动作：'):
                    action = line[8:].strip()   # 去掉"agent_1_动作："前缀
                else:
                    action = line[8:].strip()   # 去掉"agent_1_动作:"前缀

                action = action.rstrip('。，！？.!?')
                if action:
                    actions['agent_1'] = action
                    logger.debug(f"解析到agent_1动作: {action}")

            # 格式2: agent_2_action: GOTO kitchen_1
            elif line.startswith('agent_2_action:') or line.startswith('agent_2_动作：') or line.startswith('agent_2_动作:'):
                if line.startswith('agent_2_action:'):
                    action = line[15:].strip()  # 去掉"agent_2_action:"前缀
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
            self.consecutive_failures += 1
            logger.warning(f"动作解析失败或不完整 (连续失败次数: {self.consecutive_failures})")
            logger.warning(f"解析结果: {actions}")

            if self.consecutive_failures >= self.max_consecutive_failures:
                logger.error("连续解析失败次数过多，使用默认策略")
                # 使用默认策略：让两个智能体都探索
                actions = {"agent_1": "EXPLORE", "agent_2": "EXPLORE"}
                self.consecutive_failures = 0  # 重置计数器
            else:
                # 为缺失的智能体分配默认动作
                if 'agent_1' not in actions:
                    actions['agent_1'] = "EXPLORE"
                if 'agent_2' not in actions:
                    actions['agent_2'] = "EXPLORE"
        else:
            self.consecutive_failures = 0  # 重置失败计数器

        # 检查是否与上次分配相同（避免无限循环）
        if actions == self.last_assignments:
            logger.warning("检测到重复的任务分配，添加随机性")
            # 为其中一个智能体分配不同的动作
            import random
            agent_ids = list(actions.keys())
            if agent_ids:
                random_agent = random.choice(agent_ids)
                alternative_actions = ["EXPLORE", "LOOK", "DONE"]
                current_action = actions[random_agent]
                alternative_actions = [a for a in alternative_actions if a != current_action]
                if alternative_actions:
                    actions[random_agent] = random.choice(alternative_actions)
                    logger.debug(f"为 {random_agent} 分配替代动作: {actions[random_agent]}")

        self.last_assignments = actions.copy()
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

        history_entry = {
            'action': 'COORDINATE',
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
                logger.error(f"执行 {agent_id} 动作时出错: {e}")
                results[agent_id] = {
                    "status": "FAILURE",
                    "message": f"执行出错: {str(e)}",
                    "result": None
                }
                messages.append(f"{agent_id}: 执行出错")
                overall_status = ActionStatus.FAILURE

        # 特殊处理协作动作的结果聚合
        overall_status, combined_message = self._process_cooperation_results(actions, results, messages)

        # 记录历史
        self.record_action(actions, results)

        # 更新连续失败计数
        if overall_status == ActionStatus.FAILURE or overall_status == ActionStatus.INVALID:
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0

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
