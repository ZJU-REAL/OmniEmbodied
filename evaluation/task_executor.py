"""
任务执行器 - 执行单个任务的详细步骤
"""

import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
from enum import Enum

from .trajectory_recorder import TrajectoryRecorder

logger = logging.getLogger(__name__)


class ActionStatus(Enum):
    """动作执行状态"""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    INVALID = "INVALID"


class TaskExecutor:
    """任务执行器 - 执行单个任务的详细步骤"""
    
    def __init__(self, simulator, agent_adapter, trajectory_recorder: TrajectoryRecorder):
        """
        初始化任务执行器
        
        Args:
            simulator: 模拟器实例
            agent_adapter: 智能体适配器
            trajectory_recorder: 轨迹记录器
        """
        self.simulator = simulator
        self.agent_adapter = agent_adapter
        self.trajectory_recorder = trajectory_recorder
        
        logger.debug("🔧 任务执行器初始化完成")
    
    def execute_task(self, task: Dict[str, Any], task_index: int, 
                    max_steps: int = 50) -> Dict[str, Any]:
        """
        执行单个任务
        
        Args:
            task: 任务信息
            task_index: 任务索引（从1开始）
            max_steps: 最大步数
            
        Returns:
            Dict: 任务执行结果
        """
        logger.info(f"🎯 开始执行任务 {task_index}: {task.get('task_description', 'Unknown')}")
        
        start_time = datetime.now()
        
        # 设置任务描述给智能体
        task_description = task.get('task_description', '')
        self.agent_adapter.set_task(task_description)
        
        # 执行步骤循环
        execution_result = self._execute_step_loop(task, task_index, max_steps)
        
        # 计算执行时间
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 生成任务结果
        task_result = self._generate_task_result(
            task, task_index, execution_result, start_time, end_time, duration
        )
        
        logger.info(f"✅ 任务 {task_index} 执行完成，状态: {task_result['status']}")
        return task_result
    
    def _execute_step_loop(self, task: Dict[str, Any], task_index: int, 
                          max_steps: int) -> Dict[str, Any]:
        """执行步骤循环 - 核心执行逻辑"""
        successful_steps = 0
        failed_steps = 0
        llm_interactions = 0
        done_command_step = -1
        actual_completion_step = -1
        step_start_time = datetime.now()  # 记录步骤开始时间
        
        for step in range(max_steps):
            logger.debug(f"🔄 执行步骤 {step + 1}/{max_steps}")
            
            try:
                # 1. 执行智能体步骤（包含决策和执行）
                status, message, result = self.agent_adapter.step()

                # 2. 获取执行的动作 - 从智能体的最后一次动作获取
                action = self._get_last_action_from_agent()

                # 3. 记录LLM交互（如果有）
                llm_info = self._record_llm_interaction(task_index, llm_interactions)
                if llm_info:
                    llm_interactions += 1
                
                # 4. 记录动作执行
                agent_id = self._get_agent_id()
                self._record_action_execution(task_index, step, action, status, message, result, agent_id)
                
                # 5. 更新统计
                if status == ActionStatus.SUCCESS:
                    successful_steps += 1
                else:
                    failed_steps += 1
                
                # 6. 检查DONE命令
                if "DONE" in action.upper() and done_command_step == -1:
                    done_command_step = step
                
                # 7. 检查任务完成状态
                completion_status = self._check_task_completion(task, step)
                if completion_status and actual_completion_step == -1:
                    actual_completion_step = step
                    self._record_task_completion(task_index, step)
                
                # 8. 检查结束条件
                if self._should_terminate(action, completion_status):
                    logger.debug(f"🏁 任务在步骤 {step + 1} 结束")
                    break
                    
            except Exception as e:
                logger.error(f"❌ 步骤 {step + 1} 执行失败: {e}")
                failed_steps += 1
                
                # 记录失败的动作
                agent_id = self._get_agent_id()
                self._record_action_execution(
                    task_index, step, "ERROR", ActionStatus.FAILED, str(e), {}, agent_id
                )
        
        # 生成执行日志数据
        execution_log = {
            'task_index': task_index,
            'task_description': task.get('task_description', ''),
            'task_category': task.get('task_category', ''),
            'agent_type': 'single',
            'start_time': step_start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'total_steps': step + 1,
            'successful_steps': successful_steps,
            'failed_steps': failed_steps,
            'llm_interactions': llm_interactions,
            'done_command_step': done_command_step,
            'actual_completion_step': actual_completion_step,
            'command_success_rate': successful_steps / (step + 1) if step >= 0 else 0.0
        }

        return {
            'total_steps': step + 1,
            'successful_steps': successful_steps,
            'failed_steps': failed_steps,
            'llm_interactions': llm_interactions,
            'done_command_step': done_command_step,
            'actual_completion_step': actual_completion_step,
            'execution_log': execution_log
        }
    
    def _record_llm_interaction(self, task_index: int, interaction_index: int) -> Dict[str, Any]:
        """记录LLM交互 - 按照文档格式要求"""
        try:
            # 尝试从智能体获取LLM交互信息
            if hasattr(self.agent_adapter, 'get_llm_interaction_info'):
                llm_info = self.agent_adapter.get_llm_interaction_info()
                if llm_info:
                    # 按照文档要求的格式记录
                    self.trajectory_recorder.record_llm_interaction(
                        task_index, interaction_index,
                        llm_info.get('prompt', ''),
                        llm_info.get('response', ''),
                        llm_info.get('tokens_used', {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}),
                        llm_info.get('response_time_ms', 0.0),
                        llm_info.get('extracted_action', 'UNKNOWN')
                    )
                    return llm_info
        except Exception as e:
            logger.warning(f"记录LLM交互失败: {e}")

        return None

    def _get_agent_id(self) -> str:
        """获取智能体ID"""
        try:
            # 对于单智能体模式
            if hasattr(self.agent_adapter, 'agent') and hasattr(self.agent_adapter.agent, 'agent_id'):
                return self.agent_adapter.agent.agent_id
            # 对于多智能体模式
            elif hasattr(self.agent_adapter, 'primary_agent') and hasattr(self.agent_adapter.primary_agent, 'agent_id'):
                return self.agent_adapter.primary_agent.agent_id
            else:
                return 'unknown'
        except Exception:
            return 'unknown'

    def _get_last_action_from_agent(self) -> str:
        """从智能体获取最后执行的动作"""
        try:
            # 尝试从智能体的历史记录中获取最后一次动作
            if hasattr(self.agent_adapter, 'agent'):
                agent = self.agent_adapter.agent
                if hasattr(agent, 'history') and agent.history:
                    last_entry = agent.history[-1]
                    if isinstance(last_entry, dict) and 'action' in last_entry:
                        return last_entry['action']
                # 如果没有历史记录，尝试获取当前动作
                if hasattr(agent, 'current_action'):
                    return agent.current_action
            return "UNKNOWN"
        except Exception as e:
            logger.warning(f"获取最后动作失败: {e}")
            return "UNKNOWN"
    
    def _record_action_execution(self, task_index: int, step: int,
                                action: str, status: ActionStatus,
                                message: str, result: Dict[str, Any],
                                agent_id: str = None):
        """记录动作执行"""
        try:
            self.trajectory_recorder.record_action_execution(
                task_index, step, action, status.value, message, result, agent_id
            )
        except Exception as e:
            logger.error(f"记录动作执行失败: {e}")
    
    def _record_task_completion(self, task_index: int, step: int):
        """记录任务完成状态"""
        try:
            self.trajectory_recorder.record_task_completion(task_index, step)
        except Exception as e:
            logger.error(f"记录任务完成失败: {e}")
    
    def _check_task_completion(self, task: Dict[str, Any], step: int) -> Dict[str, Any]:
        """检查任务完成状态"""
        try:
            # 方法1：从模拟器的task_verifier检查任务完成状态
            if hasattr(self.simulator, 'task_verifier') and self.simulator.task_verifier:
                completion_status = self.simulator.task_verifier.get_current_completion_status()
                if completion_status and completion_status.get('completed_tasks', 0) > 0:
                    return {
                        'completed': True,
                        'step': step,
                        'validation_result': completion_status,
                        'timestamp': datetime.now().isoformat()
                    }

            # 方法2：从action_handler检查任务验证状态
            elif hasattr(self.simulator, 'action_handler') and self.simulator.action_handler:
                verification_status = self.simulator.action_handler.get_task_verification_status()
                if verification_status and verification_status.get('completion_summary', {}).get('completed_tasks', 0) > 0:
                    return {
                        'completed': True,
                        'step': step,
                        'validation_result': verification_status,
                        'timestamp': datetime.now().isoformat()
                    }

            # 方法3：直接调用模拟器的任务验证方法
            elif hasattr(self.simulator, 'get_task_verification_status'):
                verification_status = self.simulator.get_task_verification_status()
                if verification_status and verification_status.get('summary', {}).get('completed_tasks', 0) > 0:
                    return {
                        'completed': True,
                        'step': step,
                        'validation_result': verification_status,
                        'timestamp': datetime.now().isoformat()
                    }

        except Exception as e:
            logger.warning(f"检查任务完成状态失败: {e}")

        return None
    
    def _should_terminate(self, action: str, completion_status: Dict[str, Any]) -> bool:
        """判断是否应该终止执行"""
        # 只有智能体输出DONE命令才终止
        if "DONE" in action.upper():
            return True

        # 不再因为任务完成就自动终止，必须等待DONE命令
        # completion_status参数保留用于兼容性，但不再用于终止判断
        return False

    def _calculate_evaluation_metrics(self, actually_completed: bool, model_claimed_done: bool) -> Dict[str, bool]:
        """
        计算四种评估情况

        Args:
            actually_completed: 模拟器验证的实际完成状态
            model_claimed_done: 模型声称的完成状态（是否输出DONE）

        Returns:
            Dict: 包含四种评估情况的字典
        """
        return {
            # 真正例：模型说完成且模拟器验证完成
            'true_positive': model_claimed_done and actually_completed,

            # 假正例：模型说完成但模拟器验证未完成
            'false_positive': model_claimed_done and not actually_completed,

            # 真负例：模型说未完成且模拟器验证未完成
            'true_negative': not model_claimed_done and not actually_completed,

            # 假负例：模型说未完成但模拟器验证完成
            'false_negative': not model_claimed_done and actually_completed
        }

    def _generate_task_result(self, task: Dict[str, Any], task_index: int,
                             execution_result: Dict[str, Any], 
                             start_time: datetime, end_time: datetime,
                             duration: float) -> Dict[str, Any]:
        """生成任务结果"""
        total_steps = execution_result['total_steps']
        successful_steps = execution_result['successful_steps']
        failed_steps = execution_result['failed_steps']
        
        # 计算成功率
        command_success_rate = successful_steps / total_steps if total_steps > 0 else 0.0
        
        # 判断任务状态
        actual_completion_step = execution_result['actual_completion_step']
        done_command_step = execution_result['done_command_step']
        
        # 任务是否实际完成（以模拟器判断为准）
        actually_completed = actual_completion_step != -1

        # 模型是否声称完成（输出了DONE命令）
        model_claimed_done = done_command_step != -1

        # 计算四种评估情况
        evaluation_result = self._calculate_evaluation_metrics(actually_completed, model_claimed_done)

        # 确定最终状态
        if actually_completed:
            status = 'completed'
        elif total_steps >= 50:  # 达到最大步数
            status = 'timeout'
        else:
            status = 'failed'
        
        return {
            'task_index': task_index,
            'task_description': task.get('task_description', ''),
            'task_category': task.get('task_category', 'unknown'),
            'status': status,
            'task_executed': True,
            'subtask_completed': actually_completed,
            'model_claimed_done': model_claimed_done,
            'actual_completion_step': actual_completion_step,
            'done_command_step': done_command_step,
            'total_steps': total_steps,
            'successful_steps': successful_steps,
            'failed_steps': failed_steps,
            'command_success_rate': command_success_rate,
            'evaluation_result': evaluation_result,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'llm_interactions': execution_result['llm_interactions']
        }
