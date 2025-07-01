#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轨迹记录器 - 记录智能体执行过程中的详细轨迹信息
"""

import os
import json
import time
import copy
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TrajectoryRecorder:
    """
    轨迹记录器 - 记录智能体的执行轨迹
    """
    
    def __init__(self, output_dir: str, run_name: str):
        """
        初始化轨迹记录器
        
        Args:
            output_dir: 输出目录
            run_name: 运行名称（用于文件命名）
        """
        self.output_dir = output_dir
        self.run_name = run_name
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 轨迹数据
        self.trajectory = {
            'run_info': {
                'run_name': run_name,
                'start_time': datetime.now().isoformat(),
                'end_time': None,
                'total_duration': 0
            },
            'configuration': {},
            'scenario_info': {},
            'agent_info': {},
            'task_info': {},
            'tasks': [],  # 按任务组织的轨迹
            'summary': {}
        }
        
        # 当前任务信息
        self.current_task_index = 0
        self.current_task = None
        
        # 文件路径
        self.trajectory_file = os.path.join(output_dir, "trajectory.json")
        self.compact_trajectory_file = os.path.join(output_dir, "compact_trajectory.json")
        self.log_file = os.path.join(output_dir, f"{run_name}_execution.log")

        # 简洁轨迹数据
        self.compact_trajectory = {
            'run_info': {
                'run_name': run_name,
                'start_time': datetime.now().isoformat(),
                'end_time': None,
                'evaluation_mode': None  # 'sequential' or 'combined'
            },
            'tasks': []
        }

        # 当前简洁任务信息
        self.current_compact_task = None
        self.global_action_index = 0  # 全局动作索引
        
        # 设置文件日志记录器
        self._setup_file_logger()
        
        logger.info(f"📝 轨迹记录器初始化完成: {self.trajectory_file}")
    
    def _setup_file_logger(self):
        """设置文件日志记录器"""
        # 创建文件处理器
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # 添加到根日志记录器
        logging.getLogger().addHandler(file_handler)
    
    def set_configuration(self, config: Dict[str, Any]):
        """设置配置信息"""
        self.trajectory['configuration'] = config
        logger.info("📋 配置信息已记录")
    
    def set_scenario_info(self, scenario_info: Dict[str, Any]):
        """设置场景信息"""
        self.trajectory['scenario_info'] = scenario_info
        logger.info(f"🏠 场景信息已记录: {scenario_info.get('scenario_id', 'unknown')}")
    
    def set_agent_info(self, agent_info: Dict[str, Any]):
        """设置智能体信息"""
        self.trajectory['agent_info'] = agent_info
        logger.info(f"🤖 智能体信息已记录: {list(agent_info.keys())}")
    
    def set_task_info(self, task_info: Dict[str, Any]):
        """设置任务信息"""
        self.trajectory['task_info'] = task_info
        logger.info(f"🎯 任务信息已记录: {len(task_info.get('tasks', []))} 个子任务")

    def set_evaluation_mode(self, mode: str):
        """设置评测模式"""
        self.compact_trajectory['run_info']['evaluation_mode'] = mode
        logger.info(f"📋 评测模式已设置: {mode}")
    
    def start_task(self, task_index: int, task_description: str, task_type: str = 'subtask'):
        """开始新任务"""
        self.current_task_index = task_index

        # 创建新的任务记录
        self.current_task = {
            'task_index': task_index,
            'task_description': task_description,
            'task_type': task_type,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'completed': False,
            'actions': [],  # 该任务的所有动作
            'subtask_completions': []  # 混合模式下的子任务完成记录
        }

        # 创建简洁任务记录
        self.current_compact_task = {
            'subtask_index': task_index,
            'subtask_description': task_description,
            'actions': [],
            'subtask_completions': []
        }

        # 如果是combined模式，需要特殊处理
        if self.compact_trajectory['run_info']['evaluation_mode'] == 'combined':
            # Combined模式下，只有一个任务记录，但包含多个子任务的完成信息
            if len(self.compact_trajectory['tasks']) == 0:
                # 第一次创建任务时，使用组合任务描述
                self.current_compact_task['subtask_description'] = "Combined task execution"

        logger.info(f"🎯 开始任务 {task_index}: {task_description}")
    
    def record_action(self, action: str, status, message: str = "", agent_id: str = None, result: Any = None):
        """
        记录动作执行

        Args:
            action: 执行的动作命令
            status: 模拟器返回的状态（ActionStatus枚举或字符串）
            message: 结果描述
            agent_id: 智能体ID
            result: 模拟器返回的完整结果数据
        """
        if self.current_task is None:
            logger.warning("尝试记录动作但没有当前任务")
            return

        # 处理状态信息
        if hasattr(status, 'name'):
            status_name = status.name  # ActionStatus枚举
            success = status_name == 'SUCCESS'
        else:
            status_name = str(status)  # 字符串状态
            success = status_name.upper() == 'SUCCESS'

        action_record = {
            'action': action,
            'status': status_name,  # 保存完整的状态信息
            'success': success,     # 保留布尔值便于快速判断
            'message': message,
            'agent_id': agent_id,
            'timestamp': datetime.now().isoformat()
        }

        # 如果有额外的结果数据，也保存下来
        if result is not None:
            action_record['result'] = result

        self.current_task['actions'].append(action_record)

        # 记录到简洁轨迹（只记录成功的动作）
        if self.current_compact_task is not None and success:
            compact_action = {
                'action_index': len(self.current_compact_task['actions']),
                'action': action,
                'status': status_name,
                'message': message,
                'agent_id': agent_id
            }
            self.current_compact_task['actions'].append(compact_action)

        # 记录到日志
        status_emoji = "✅" if success else "❌" if status_name in ['FAILURE', 'INVALID'] else "⚠️"
        log_msg = f"{status_emoji} Action: {action} (Status: {status_name})"
        if agent_id:
            log_msg += f" (Agent: {agent_id})"
        if message:
            log_msg += f" - {message}"

        logger.info(log_msg)

        # 自动保存轨迹（确保中断时不丢失数据）
        self.save_trajectory()
        self.save_compact_trajectory()
    
    def record_subtask_completion(self, subtask_index: int, subtask_description: str):
        """
        记录子任务完成（用于混合评测模式）

        Args:
            subtask_index: 子任务索引
            subtask_description: 子任务描述
        """
        if self.current_task is None:
            logger.warning("尝试记录子任务完成但没有当前任务")
            return

        completion_record = {
            'subtask_index': subtask_index,
            'subtask_description': subtask_description,
            'completed_at': datetime.now().isoformat(),
            'action_count': len(self.current_task['actions'])
        }

        self.current_task['subtask_completions'].append(completion_record)

        # 记录到简洁轨迹
        if self.current_compact_task is not None:
            compact_completion = {
                'subtask_index': subtask_index,
                'completed_at': len(self.current_compact_task['actions']) - 1  # 完成于哪个动作索引
            }
            self.current_compact_task['subtask_completions'].append(compact_completion)

        logger.info(f"✅ 子任务 {subtask_index} 完成: {subtask_description}")

    def record_environment_reset(self, reset_info: Dict[str, Any]):
        """
        记录环境重置信息（独立评测模式专用）

        Args:
            reset_info: 环境重置信息
        """
        if self.current_task is None:
            logger.warning("尝试记录环境重置但没有当前任务")
            return

        reset_record = {
            'type': 'environment_reset',
            'timestamp': datetime.now().isoformat(),
            'reset_info': reset_info
        }

        # 添加到当前任务的特殊记录中
        if 'environment_resets' not in self.current_task:
            self.current_task['environment_resets'] = []
        self.current_task['environment_resets'].append(reset_record)

        logger.info("📝 环境重置信息已记录")

    def record_task_completion(self, completed: bool):
        """记录当前任务完成情况"""
        if self.current_task is None:
            logger.warning("尝试记录任务完成但没有当前任务")
            return

        self.current_task['completed'] = completed
        logger.info(f"任务 {self.current_task_index} {'完成' if completed else '未完成'}")

    def record_simulator_completion(self, completion_record: Dict[str, Any]):
        """
        记录模拟器检测到的任务完成情况

        Args:
            completion_record: 包含完成信息的记录
        """
        if self.current_task is None:
            logger.warning("尝试记录模拟器完成状态但没有当前任务")
            return

        # 添加到subtask_completions中，标记为模拟器反馈
        completion_record['source'] = 'simulator'
        self.current_task['subtask_completions'].append(completion_record)

        # 记录到简洁轨迹（模拟器反馈）
        if self.current_compact_task is not None:
            # 获取当前动作索引，如果没有动作则为-1
            current_action_index = len(self.current_compact_task['actions']) - 1
            if current_action_index < 0:
                current_action_index = -1

            compact_completion = {
                'subtask_index': completion_record.get('subtask_index', self.current_task_index),
                'completed_at': current_action_index
            }
            self.current_compact_task['subtask_completions'].append(compact_completion)

        logger.info(f"📊 记录模拟器反馈: {completion_record.get('task_description', '未知任务')}")

    def end_task(self):
        """结束当前任务"""
        if self.current_task is None:
            logger.warning("尝试结束任务但没有当前任务")
            return

        self.current_task['end_time'] = datetime.now().isoformat()

        # 将当前任务添加到轨迹中
        self.trajectory['tasks'].append(self.current_task)

        # 将简洁任务添加到简洁轨迹中
        if self.current_compact_task is not None:
            if self.compact_trajectory['run_info']['evaluation_mode'] == 'combined':
                # Combined模式：累积到同一个任务中
                if len(self.compact_trajectory['tasks']) == 0:
                    # 第一个任务，直接添加
                    self.compact_trajectory['tasks'].append(self.current_compact_task)
                else:
                    # 后续任务，合并到第一个任务中
                    existing_task = self.compact_trajectory['tasks'][0]
                    # 合并动作（重新编号）
                    base_index = len(existing_task['actions'])
                    for action in self.current_compact_task['actions']:
                        action['action_index'] = base_index + action['action_index']
                        existing_task['actions'].append(action)
                    # 合并子任务完成记录（调整动作索引）
                    for completion in self.current_compact_task['subtask_completions']:
                        if completion['completed_at'] >= 0:
                            completion['completed_at'] += base_index
                        existing_task['subtask_completions'].append(completion)
            else:
                # Sequential/Independent模式：每个任务单独记录
                self.compact_trajectory['tasks'].append(self.current_compact_task)

        logger.info(f"🏁 任务 {self.current_task_index} 结束: {'完成' if self.current_task['completed'] else '未完成'}")

        # 清空当前任务
        self.current_task = None
        self.current_compact_task = None
    
    def finalize(self, summary: Dict[str, Any]):
        """完成记录并保存最终结果"""
        self.trajectory['run_info']['end_time'] = datetime.now().isoformat()
        
        # 计算总时长
        start_time = datetime.fromisoformat(self.trajectory['run_info']['start_time'])
        end_time = datetime.fromisoformat(self.trajectory['run_info']['end_time'])
        self.trajectory['run_info']['total_duration'] = (end_time - start_time).total_seconds()
        
        # 设置摘要
        self.trajectory['summary'] = summary
        
        # 设置简洁轨迹的结束时间
        self.compact_trajectory['run_info']['end_time'] = self.trajectory['run_info']['end_time']

        # 保存最终轨迹
        self.save_trajectory()
        self.save_compact_trajectory()

        logger.info(f"✅ 轨迹记录完成: {self.trajectory_file}")
        logger.info(f"📄 简洁轨迹记录完成: {self.compact_trajectory_file}")
        logger.info(f"📊 总任务数: {len(self.trajectory['tasks'])}, 总时长: {self.trajectory['run_info']['total_duration']:.2f}秒")
    
    def save_trajectory(self):
        """保存轨迹到文件"""
        try:
            with open(self.trajectory_file, 'w', encoding='utf-8') as f:
                json.dump(self.trajectory, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ 保存轨迹失败: {e}")

    def save_compact_trajectory(self):
        """保存简洁轨迹到文件"""
        try:
            # 创建要保存的轨迹副本
            trajectory_to_save = copy.deepcopy(self.compact_trajectory)

            # 如果有未完成的当前任务，临时添加到tasks中
            if self.current_compact_task is not None and len(self.current_compact_task['actions']) > 0:
                # 检查是否已经在tasks中（避免重复添加）
                task_already_exists = False
                for existing_task in trajectory_to_save['tasks']:
                    if (existing_task.get('task_description') == self.current_compact_task.get('task_description') and
                        existing_task.get('start_time') == self.current_compact_task.get('start_time')):
                        task_already_exists = True
                        break

                if not trajectory_to_save['run_info']['evaluation_mode'] == 'combined':
                    # Sequential/Independent模式：如果任务不存在，添加当前任务
                    if not task_already_exists:
                        trajectory_to_save['tasks'].append(self.current_compact_task)
                else:
                    # Combined模式：合并到第一个任务中
                    if len(trajectory_to_save['tasks']) == 0:
                        trajectory_to_save['tasks'].append(self.current_compact_task)
                    else:
                        # 更新第一个任务的动作
                        existing_task = trajectory_to_save['tasks'][0]
                        # 合并动作（重新编号）
                        base_index = len([a for a in existing_task['actions'] if a.get('action_index', -1) < len(self.current_compact_task['actions'])])
                        for action in self.current_compact_task['actions']:
                            if action['action_index'] >= base_index:
                                action_copy = copy.deepcopy(action)
                                action_copy['action_index'] = base_index + action['action_index']
                                existing_task['actions'].append(action_copy)

            with open(self.compact_trajectory_file, 'w', encoding='utf-8') as f:
                json.dump(trajectory_to_save, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ 保存简洁轨迹失败: {e}")
    
    def get_trajectory_summary(self) -> Dict[str, Any]:
        """获取轨迹摘要"""
        total_actions = sum(len(task['actions']) for task in self.trajectory['tasks'])
        completed_tasks = sum(1 for task in self.trajectory['tasks'] if task['completed'])

        return {
            'run_name': self.run_name,
            'total_actions': total_actions,
            'total_tasks': len(self.trajectory['tasks']),
            'completed_tasks': completed_tasks,
            'trajectory_file': self.trajectory_file,
            'log_file': self.log_file
        }
