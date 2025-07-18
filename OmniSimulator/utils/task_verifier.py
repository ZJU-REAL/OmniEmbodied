"""
任务验证器 - 负责验证子任务的完成情况

该模块提供了TaskVerifier类，用于根据verify.json文件中的验证条件
检查子任务是否已完成，并返回详细的验证结果。
"""

from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class TaskVerificationResult:
    """任务验证结果类"""
    
    def __init__(self, task_id: str, task_description: str):
        self.task_id = task_id
        self.task_description = task_description
        self.is_completed = False
        self.completion_details = {}
        self.error_message = None
        
    def mark_completed(self, details: Dict[str, Any] = None):
        """标记任务为已完成"""
        self.is_completed = True
        self.completion_details = details or {}
        
    def mark_failed(self, error_message: str):
        """标记任务验证失败"""
        self.is_completed = False
        self.error_message = error_message
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "task_description": self.task_description,
            "is_completed": self.is_completed,
            "completion_details": self.completion_details,
            "error_message": self.error_message
        }


class TaskVerifier:
    """任务验证器 - 验证子任务完成情况"""

    def __init__(self, task_data: Dict[str, Any], env_manager, config: Dict[str, Any] = None):
        """
        初始化任务验证器

        Args:
            task_data: 任务数据，来自task.json文件
            env_manager: 环境管理器，用于获取物体状态
            config: 验证配置
        """
        self.task_data = task_data
        self.env_manager = env_manager
        self.config = config or {}

        # 解析任务数据中的验证信息
        self.tasks = task_data.get("tasks", [])

        # 验证结果缓存
        self.verification_cache = {}

        # 任务完成状态持久化存储（维护递增性）
        self.completed_tasks = set()  # 存储已完成的任务ID
        
    def verify_all_tasks(self) -> List[TaskVerificationResult]:
        """
        验证所有任务

        Returns:
            List[TaskVerificationResult]: 验证结果列表
        """
        results = []

        # 验证所有任务
        for task in self.tasks:
            result = self._verify_single_task(task)
            results.append(result)

        return results
        
    def verify_task_category(self, category: str) -> List[TaskVerificationResult]:
        """
        验证特定类别的任务

        Args:
            category: 任务类别，如 "direct_command", "tool_use"等

        Returns:
            List[TaskVerificationResult]: 验证结果列表
        """
        results = []

        # 筛选指定类别的任务
        filtered_tasks = [task for task in self.tasks if task.get('task_category') == category]

        for task in filtered_tasks:
            result = self._verify_single_task(task)
            results.append(result)

        return results
        

        
    def _verify_single_task(self, task: Dict[str, Any]) -> TaskVerificationResult:
        """
        验证单个任务

        Args:
            task: 任务定义，包含验证条件

        Returns:
            TaskVerificationResult: 验证结果
        """
        # 使用任务描述作为ID（因为新格式没有单独的ID字段）
        task_description = task.get("task_description", "")
        task_id = f"task_{hash(task_description) % 10000}"  # 生成简短的任务ID

        result = TaskVerificationResult(task_id, task_description)

        # 如果任务已经完成过，直接返回完成状态（维护递增性）
        if task_id in self.completed_tasks:
            result.mark_completed({"previously_completed": True})
            logger.debug(f"任务已完成（缓存）: {task_id}")
            return result

        try:
            # 获取验证检查列表
            validation_checks = task.get("validation_checks", [])
            if not validation_checks:
                result.mark_failed("任务没有验证条件")
                return result

            # 检查所有验证条件
            verification_passed = True
            completion_details = {}

            for check in validation_checks:
                check_id = check.get("id")
                if not check_id:
                    verification_passed = False
                    logger.debug("验证检查缺少id字段")
                    continue

                # 获取目标物体
                obj = self.env_manager.get_object_by_id(check_id)
                if not obj:
                    verification_passed = False
                    logger.debug(f"目标物体不存在: {check_id}")
                    continue

                # 检查各种验证条件
                for state_key, expected_value in check.items():
                    if state_key == "id":
                        continue

                    if state_key == "location_id":
                        # 检查位置
                        current_location = obj.get("location_id")
                        location_match = self._check_location_match(current_location, expected_value)
                        if not location_match:
                            verification_passed = False
                            logger.debug(f"位置验证失败 - 物体: {check_id}, 期望: {expected_value}, 实际: {current_location}")
                        else:
                            completion_details[f"{check_id}_location_verified"] = True

                    elif state_key.startswith("is_"):
                        # 检查状态属性
                        current_value = obj.get("states", {}).get(state_key)
                        if current_value != expected_value:
                            verification_passed = False
                            logger.debug(f"状态验证失败 - 物体: {check_id}, {state_key}: 期望 {expected_value}, 实际 {current_value}")
                        else:
                            # 检查是否为合作任务，如果是则需要验证合作标记
                            if self._is_cooperative_task(task):
                                coop_attrs = obj.get("states", {}).get("cooperative_modified_attributes", [])
                                if state_key in coop_attrs:
                                    completion_details[f"{check_id}_{state_key}_verified"] = True
                                else:
                                    verification_passed = False
                                    logger.debug(f"合作任务验证失败 - 物体: {check_id}, 属性 {state_key} 未通过合作方式修改")
                            else:
                                completion_details[f"{check_id}_{state_key}_verified"] = True

            if verification_passed:
                result.mark_completed(completion_details)
                # 记录已完成的任务（维护递增性）
                self.completed_tasks.add(task_id)
                logger.debug(f"任务验证成功: {task_id}")
            else:
                result.mark_failed("验证条件不满足")
                logger.debug(f"任务验证失败: {task_id}")

        except Exception as e:
            result.mark_failed(f"验证过程中发生错误: {str(e)}")
            logger.error(f"验证任务 {task_id} 时发生错误: {e}")

        return result

    def _is_cooperative_task(self, task: Dict[str, Any]) -> bool:
        """
        判断任务是否为合作任务

        Args:
            task: 任务定义

        Returns:
            bool: 如果是合作任务返回True，否则返回False
        """
        # 通过task_category判断
        task_category = task.get("task_category", "")
        cooperative_categories = {
            "explicit_collaboration",
            "implicit_collaboration",
            "compound_collaboration"
        }

        if task_category in cooperative_categories:
            return True

        # 通过任务描述中的关键词判断
        task_description = task.get("task_description", "").lower()
        cooperative_keywords = [
            "cooperate", "cooperation", "cooperatively",
            "work together", "collaborate", "collaboration",
            "together", "jointly", "team up"
        ]

        for keyword in cooperative_keywords:
            if keyword in task_description:
                return True

        return False

    def get_completion_summary(self) -> Dict[str, Any]:
        """
        获取任务完成情况摘要

        Returns:
            Dict[str, Any]: 完成情况摘要
        """
        all_results = self.verify_all_tasks()

        summary = {
            "total_tasks": len(all_results),
            "completed_tasks": sum(1 for r in all_results if r.is_completed),
            "completion_rate": 0.0,
            "categories": {}
        }

        # 按类别统计
        category_stats = {}
        for result in all_results:
            # 从任务数据中获取类别信息
            task_category = None
            for task in self.tasks:
                if task.get("task_description") == result.task_description:
                    task_category = task.get("task_category", "unknown")
                    break

            if task_category not in category_stats:
                category_stats[task_category] = {"total": 0, "completed": 0}

            category_stats[task_category]["total"] += 1
            if result.is_completed:
                category_stats[task_category]["completed"] += 1

        # 计算各类别完成率
        for category, stats in category_stats.items():
            summary["categories"][category] = {
                "total": stats["total"],
                "completed": stats["completed"],
                "completion_rate": stats["completed"] / stats["total"] if stats["total"] > 0 else 0.0
            }

        if summary["total_tasks"] > 0:
            summary["completion_rate"] = summary["completed_tasks"] / summary["total_tasks"]

        return summary
        
    def get_subtask_completion_list(self) -> List[bool]:
        """
        获取所有子任务的完成状态列表

        Returns:
            List[bool]: 按顺序返回每个子任务的完成状态 [True, False, True, ...]
        """
        all_results = self.verify_all_tasks()
        completion_list = []

        # 按任务顺序收集完成状态
        for result in all_results:
            completion_list.append(result.is_completed)

        return completion_list

    def verify_single_subtask(self, subtask: Dict[str, Any]) -> TaskVerificationResult:
        """
        验证单个子任务

        Args:
            subtask: 子任务定义，包含验证条件

        Returns:
            TaskVerificationResult: 验证结果
        """
        return self._verify_single_task(subtask)

    def get_current_completion_status(self) -> Dict[str, Any]:
        """
        获取当前所有任务的完成状态

        Returns:
            Dict[str, Any]: 包含完成状态的详细信息
        """
        all_results = self.verify_all_tasks()
        completed_tasks = []

        for result in all_results:
            if result.is_completed:
                completed_tasks.append({
                    'task_id': result.task_id,
                    'task_description': result.task_description,
                    'completion_details': result.completion_details
                })

        return {
            'total_tasks': len(all_results),
            'completed_tasks': len(completed_tasks),
            'completion_rate': len(completed_tasks) / len(all_results) if all_results else 0.0,
            'completed_task_details': completed_tasks
        }

    def _check_location_match(self, current_location: str, expected_location: str) -> bool:
        """
        检查位置是否匹配，支持灵活的in/on判定

        支持的格式：
        - "in:location" - 精确匹配in前缀
        - "on:location" - 精确匹配on前缀
        - ":location" - 空前缀，匹配任何前缀的location
        - "location" - 无前缀，匹配任何前缀的location

        Args:
            current_location: 当前位置，如 "in:restoration_lab"
            expected_location: 期望位置，如 ":restoration_lab" 或 "in:restoration_lab"

        Returns:
            bool: 位置是否匹配
        """
        if not current_location or not expected_location:
            return current_location == expected_location

        # 解析期望位置
        if expected_location.startswith(("in:", "on:")):
            # 有明确前缀（in: 或 on:），进行精确匹配
            return current_location == expected_location
        elif expected_location.startswith(":"):
            # 空前缀格式 ":location"，提取基础位置名
            expected_base = expected_location[1:]  # 去掉":"前缀
        else:
            # 没有前缀，直接使用原值作为基础位置名
            expected_base = expected_location

        # 解析当前位置，提取基础位置名
        if current_location.startswith("in:"):
            current_base = current_location[3:]  # 去掉"in:"前缀
        elif current_location.startswith("on:"):
            current_base = current_location[3:]  # 去掉"on:"前缀
        elif current_location.startswith(":"):
            current_base = current_location[1:]  # 去掉":"前缀
        else:
            current_base = current_location

        # 比较基础位置名
        return current_base == expected_base
