from typing import Dict, Optional, Tuple, Any, Type, List

from ..core.enums import ActionStatus
from .action_manager import ActionManager
from .actions.base_action import BaseAction

class ActionHandler:
    """
    动作处理器 - 负责处理智能体的动作请求
    
    此类是模拟器的主要对外接口，用于处理智能体的动作请求。
    它封装了ActionManager的内部复杂性，提供简单直观的API。
    
    使用示例:
    ```python
    action_handler = ActionHandler(world_state, env_manager, agent_manager)
    status, message, result = action_handler.process_command('agent_1', 'GRAB cup_1')
    ```
    """
    
    def __init__(self, world_state, env_manager, agent_manager, scene_abilities=None, config=None):
        """
        初始化动作处理器

        Args:
            world_state: 世界状态对象
            env_manager: 环境管理器
            agent_manager: 智能体管理器
            scene_abilities: 场景支持的能力列表，用于注册不需要工具的属性动作
            config: 配置字典，包含验证相关配置
        """
        self.action_manager = ActionManager(
            world_state,
            env_manager,
            agent_manager,
            scene_abilities=scene_abilities
        )
        self.config = config or {}
        self.task_verifier = None  # 将在设置验证数据时初始化
    
    def process_command(self, agent_id: str, command_str: str) -> Tuple[ActionStatus, str, Optional[Dict[str, Any]]]:
        """
        处理智能体的命令

        Args:
            agent_id: 智能体ID
            command_str: 命令字符串

        Returns:
            Tuple[ActionStatus, str, Optional[Dict]]: (执行状态, 反馈消息, 额外结果数据)
        """
        # 检查是否是done命令
        if command_str.strip().lower() == "done":
            return self._handle_done_command()

        # 使用ActionManager处理命令
        status, message, result = self.action_manager.process_command(command_str, agent_id)

        # 如果启用了任务验证，在动作执行后进行验证
        if self._should_verify_tasks():
            verification_result = self._perform_task_verification()
            if result is None:
                result = {}
            result["task_verification"] = verification_result

        return status, message, result
    
    def register_action_class(self, action_name: str, action_class: Type[BaseAction]):
        """
        注册单个动作类
        
        Args:
            action_name: 动作名称
            action_class: 动作类
            
        Returns:
            self: 支持链式调用
        """
        self.action_manager.register_action_class(action_name, action_class)
        return self
        
    def register_action_classes(self, action_classes_dict: Dict[str, Type[BaseAction]]):
        """
        批量注册多个动作类
        
        Args:
            action_classes_dict: 动作名称到动作类的映射字典
            
        Returns:
            self: 支持链式调用
        """
        self.action_manager.register_action_classes(action_classes_dict)
        return self
        
    def register_attribute_actions(self):
        """
        加载属性动作配置（仅为保持向后兼容）
        
        Returns:
            self: 支持链式调用
        """
        from .actions.attribute_actions import AttributeAction
        AttributeAction.load_from_csv()
        return self
    
    def get_pending_corporate_actions(self) -> Dict[str, Any]:
        """
        获取待处理的合作动作

        Returns:
            Dict[str, Any]: 动作ID到动作数据的映射
        """
        # 从world_state获取待处理的合作动作
        return getattr(self.action_manager.world_state, 'pending_corporate_actions', {})

    def set_task_verifier(self, task_data: Dict[str, Any]):
        """
        设置任务验证器

        Args:
            task_data: 任务数据，来自task.json文件
        """
        verification_config = self.config.get("task_verification", {})
        enabled = verification_config.get("enabled", False)
        mode = verification_config.get("mode", "disabled")

        # 只要启用了验证且模式不是disabled，就创建验证器
        if task_data and enabled and mode != "disabled":
            from utils.task_verifier import TaskVerifier
            env_manager = self.action_manager.env_manager
            self.task_verifier = TaskVerifier(task_data, env_manager, verification_config)

    def _should_verify_tasks(self) -> bool:
        """
        检查是否应该进行任务验证

        Returns:
            bool: 是否应该验证
        """
        verification_config = self.config.get("task_verification", {})
        enabled = verification_config.get("enabled", False)
        mode = verification_config.get("mode", "disabled")
        return enabled and mode == "step_by_step"

    def _perform_task_verification(self) -> Optional[Dict[str, Any]]:
        """
        执行任务验证

        Returns:
            Optional[Dict[str, Any]]: 验证结果，如果未启用验证则返回None
        """
        if not self.task_verifier:
            return None

        try:
            verification_config = self.config.get("task_verification", {})
            return_subtask_status = verification_config.get("return_subtask_status", True)

            if return_subtask_status:
                # 获取任务完成情况摘要
                summary = self.task_verifier.get_completion_summary()

                # 获取子任务完成状态列表
                subtask_completion_list = self.task_verifier.get_subtask_completion_list()

                result = {
                    "completion_summary": summary,
                    "subtask_completion_list": subtask_completion_list,
                    "timestamp": self._get_current_timestamp()
                }

                return result

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"任务验证过程中发生错误: {e}")
            return {"error": f"Verification failed: {str(e)}"}

        return None

    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        import datetime
        return datetime.datetime.now().isoformat()

    def _handle_done_command(self) -> Tuple[ActionStatus, str, Optional[Dict[str, Any]]]:
        """
        处理done命令，进行全局任务验证

        Returns:
            Tuple[ActionStatus, str, Optional[Dict]]: (执行状态, 反馈消息, 验证结果)
        """
        verification_config = self.config.get("task_verification", {})
        enabled = verification_config.get("enabled", False)
        mode = verification_config.get("mode", "disabled")

        if not enabled or mode == "disabled":
            return ActionStatus.SUCCESS, "Task verification is disabled", None

        if not self.task_verifier:
            return ActionStatus.INVALID, "Task verifier not initialized", None

        try:
            # 执行全局任务验证
            verification_result = self._perform_task_verification()

            if verification_result:
                completion_summary = verification_result.get("completion_summary", {})
                total_tasks = completion_summary.get("total_tasks", 0)
                completed_tasks = completion_summary.get("completed_tasks", 0)
                completion_rate = completion_summary.get("completion_rate", 0.0)

                message = f"DONE command executed - Global task verification: {completed_tasks}/{total_tasks} tasks completed ({completion_rate:.1%})"

                result_data = {
                    "global_verification": verification_result,
                    "is_all_completed": completion_rate >= 1.0,
                    "completion_status": self.task_verifier.get_current_completion_status()
                }

                return ActionStatus.SUCCESS, message, result_data
            else:
                return ActionStatus.INVALID, "Task verification failed", None

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"处理done命令时发生错误: {e}")
            return ActionStatus.INVALID, f"Verification failed: {str(e)}", None

    def get_task_verification_status(self) -> Optional[Dict[str, Any]]:
        """
        手动获取任务验证状态（用于手动查询）

        Returns:
            Optional[Dict[str, Any]]: 验证状态，如果未启用验证则返回None
        """
        if not self.task_verifier:
            return None

        return self._perform_task_verification()

    def get_agent_supported_actions_description(self, agent_ids: List[str]) -> str:
        """
        获取智能体支持的所有动作的字符串描述

        Args:
            agent_ids: 智能体ID列表，支持单个或多个智能体

        Returns:
            str: 包含所有支持动作的描述字符串（英文）
        """
        return self.action_manager.get_agent_supported_actions_description(agent_ids)