#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轨迹记录器 - 记录智能体执行过程中的详细轨迹信息
"""

import os
import json
import time
import copy
import csv
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TrajectoryRecorder:
    """
    轨迹记录器 - 记录智能体的执行轨迹
    """
    
    def __init__(self, output_dir: str, run_name: str, scenario_id: str = None):
        """
        初始化轨迹记录器

        Args:
            output_dir: 输出目录
            run_name: 运行名称（用于文件命名）
            scenario_id: 场景ID（用于文件分类）
        """
        self.output_dir = output_dir
        self.run_name = run_name
        self.scenario_id = scenario_id or "unknown"

        # 创建分类的子目录结构
        self._create_directory_structure()

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 轨迹数据 - 统一格式，包含详细轨迹和统计信息
        self.trajectory = {
            'execution_info': {
                'run_name': run_name,
                'start_time': datetime.now().isoformat(),
                'end_time': None,
                'total_duration_seconds': 0,
                'evaluation_mode': None
            },
            'configuration': {},
            'scenario_info': {},
            'agent_info': {},
            'task_info': {},
            'task_executions': [],  # 详细的任务执行轨迹
            'execution_statistics': {
                'total_tasks': 0,
                'completed_tasks': 0,
                'failed_tasks': 0,
                'completion_rate': 0.0,
                'total_actions': 0,
                'average_actions_per_task': 0.0,
                'task_category_stats': {},
                'action_type_stats': {}
            }
        }
        
        # 当前任务信息
        self.current_task_index = 0
        self.current_task = None
        
        # 文件路径 - 按类别分类存储
        self.trajectories_dir = os.path.join(output_dir, "trajectories")
        self.logs_dir = os.path.join(output_dir, "logs")
        self.llm_qa_dir = os.path.join(output_dir, "llm_qa")

        self.trajectory_file = os.path.join(self.trajectories_dir, f"{self.scenario_id}_trajectory.json")
        self.compact_trajectory_file = os.path.join(self.trajectories_dir, f"{self.scenario_id}_compact_trajectory.json")
        self.log_file = os.path.join(self.logs_dir, f"{self.scenario_id}_execution.log")
        self.llm_qa_file = os.path.join(self.llm_qa_dir, f"{self.scenario_id}_llm_qa.json")

        # CSV实时记录文件 - 在运行输出目录
        self.csv_file = os.path.join(output_dir, "subtask_execution_log.csv")

        # 简洁轨迹数据 - 仅包含关键执行信息
        self.compact_trajectory = {
            'execution_info': {
                'run_name': run_name,
                'start_time': datetime.now().isoformat(),
                'end_time': None,
                'evaluation_mode': None
            },
            'task_executions': []
        }

        # 当前简洁任务信息
        self.current_compact_task = None
        self.global_action_index = 0  # 全局动作索引

        # LLM QA记录 - 按子任务分类
        self.llm_qa_records = {}
        self.current_subtask_index = None

        # 设置文件日志记录器
        self._setup_file_logger()

        # 初始化CSV文件
        self._init_csv_file()

        logger.info(f"📝 轨迹记录器初始化完成: {self.trajectory_file}")
        logger.info(f"📊 CSV记录文件: {self.csv_file}")
        logger.info(f"🏠 场景ID: {self.scenario_id}")

    def _create_directory_structure(self):
        """创建分类的目录结构"""
        # 创建子目录
        self.trajectories_dir = os.path.join(self.output_dir, "trajectories")
        self.logs_dir = os.path.join(self.output_dir, "logs")
        self.llm_qa_dir = os.path.join(self.output_dir, "llm_qa")

        # 确保所有目录存在
        for directory in [self.trajectories_dir, self.logs_dir, self.llm_qa_dir]:
            os.makedirs(directory, exist_ok=True)

    def _setup_file_logger(self):
        """设置文件日志记录器"""
        # 检查是否禁用子任务日志记录
        disable_subtask_logging = os.environ.get('DISABLE_SUBTASK_LOGGING') == 'true'
        if disable_subtask_logging:
            logger.debug("🚫 子任务日志记录已禁用，跳过文件日志设置")
            return

        # 创建文件处理器
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)

        # 创建专用的日志记录器，避免重复日志
        self.file_logger = logging.getLogger(f'trajectory_recorder_{self.scenario_id}')
        self.file_logger.setLevel(logging.DEBUG)
        self.file_logger.addHandler(file_handler)
        self.file_logger.propagate = False  # 防止传播到根日志记录器

    def _init_csv_file(self):
        """初始化CSV文件，如果不存在则创建表头"""
        csv_headers = [
            'timestamp',
            'scenario_id',
            'subtask_index',
            'subtask_description',
            'task_category',  # 任务类型（如attribute_reasoning, direct_command等）
            'agent_type',  # 智能体类型（single_agent或multi_agent）
            'status',
            'task_executed',  # 任务是否执行完成（True/False）
            'subtask_completed',  # 模拟器判断的子任务是否完成（True/False）
            'total_steps',
            'successful_steps',
            'failed_steps',
            'command_success_rate',  # 命令成功率（百分比）
            'start_time',
            'end_time',
            'duration_seconds',
            'llm_interactions'
        ]

        # 检查文件是否存在，如果不存在则创建并写入表头
        if not os.path.exists(self.csv_file):
            try:
                with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(csv_headers)
                logger.info(f"📊 创建CSV记录文件: {self.csv_file}")
            except Exception as e:
                logger.error(f"❌ 创建CSV文件失败: {e}")

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
        self.trajectory['execution_info']['evaluation_mode'] = mode
        self.compact_trajectory['execution_info']['evaluation_mode'] = mode
        logger.info(f"📋 评测模式已设置: {mode}")

    def record_llm_qa(self, instruction: str, output: str, system: str = None):
        """
        记录LLM问答信息

        Args:
            instruction: 用户指令（必填）
            output: 模型回答（必填）
            system: 系统提示词（选填）
        """
        qa_record = {
            "instruction": instruction,
            "output": output,
            "timestamp": datetime.now().isoformat()
        }

        if system:
            qa_record["system"] = system

        # 将QA记录添加到当前子任务中
        if self.current_subtask_index is not None:
            if self.current_subtask_index not in self.llm_qa_records:
                self.llm_qa_records[self.current_subtask_index] = {
                    "subtask_index": self.current_subtask_index,
                    "subtask_description": f"Subtask {self.current_subtask_index}",
                    "qa_interactions": []
                }
            self.llm_qa_records[self.current_subtask_index]["qa_interactions"].append(qa_record)
        else:
            # 如果没有当前子任务，创建一个默认分类
            if "general" not in self.llm_qa_records:
                self.llm_qa_records["general"] = {
                    "subtask_index": "general",
                    "subtask_description": "General interactions",
                    "qa_interactions": []
                }
            self.llm_qa_records["general"]["qa_interactions"].append(qa_record)

        # 实时保存LLM QA记录
        self._save_llm_qa()

        logger.debug(f"🤖 记录LLM问答: 指令长度={len(instruction)}, 回答长度={len(output)}")

    def start_task(self, task_index: int, task_description: str, task_type: str = 'subtask'):
        """开始新任务"""
        self.current_task_index = task_index
        self.current_subtask_index = task_index  # 设置当前子任务索引

        logger.info(f"🚀 开始任务 {task_index}: {task_description}")

        # 为当前子任务初始化LLM QA记录
        if task_index not in self.llm_qa_records:
            self.llm_qa_records[task_index] = {
                "subtask_index": task_index,
                "subtask_description": task_description,
                "qa_interactions": []
            }

        # 创建新的任务执行记录
        self.current_task = {
            'task_index': task_index,
            'task_description': task_description,
            'task_type': task_type,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'status': 'running',
            'completed': False,
            'action_sequence': [],  # 该任务的所有动作序列
            'subtask_completions': []  # 混合模式下的子任务完成记录
        }

        # 创建简洁任务记录
        self.current_compact_task = {
            'task_index': task_index,
            'task_description': task_description,
            'action_sequence': [],
            'subtask_completions': []
        }

        # 如果是combined模式，需要特殊处理
        if self.compact_trajectory['execution_info']['evaluation_mode'] == 'combined':
            # Combined模式下，只有一个任务记录，但包含多个子任务的完成信息
            if len(self.compact_trajectory['task_executions']) == 0:
                # 第一次创建任务时，使用组合任务描述
                self.current_compact_task['task_description'] = "Combined task execution"

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
            'action_command': action,
            'execution_status': status_name,
            'success': success,
            'result_message': message,
            'agent_id': agent_id,
            'timestamp': datetime.now().isoformat()
        }

        # 如果有额外的结果数据，也保存下来
        if result is not None:
            action_record['detailed_result'] = result

        self.current_task['action_sequence'].append(action_record)

        # 记录到简洁轨迹（只记录关键动作）
        if self.current_compact_task is not None:
            compact_action = {
                'action_index': len(self.current_compact_task['action_sequence']),
                'action_command': action,
                'execution_status': status_name,
                'result_message': message,
                'agent_id': agent_id
            }
            self.current_compact_task['action_sequence'].append(compact_action)

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
                'completed_at': len(self.current_compact_task['action_sequence']) - 1  # 完成于哪个动作索引
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
            current_action_index = len(self.current_compact_task['action_sequence']) - 1
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
        self.current_task['status'] = 'completed' if self.current_task['completed'] else 'failed'

        # 记录到CSV文件
        self._record_to_csv()

        # 将当前任务添加到轨迹中
        self.trajectory['task_executions'].append(self.current_task)

        # 将简洁任务添加到简洁轨迹中
        if self.current_compact_task is not None:
            if self.compact_trajectory['execution_info']['evaluation_mode'] == 'combined':
                # Combined模式：累积到同一个任务中
                if len(self.compact_trajectory['task_executions']) == 0:
                    # 第一个任务，直接添加
                    self.compact_trajectory['task_executions'].append(self.current_compact_task)
                else:
                    # 后续任务，合并到第一个任务中
                    existing_task = self.compact_trajectory['task_executions'][0]
                    # 合并动作（重新编号）
                    base_index = len(existing_task['action_sequence'])
                    for action in self.current_compact_task['action_sequence']:
                        action['action_index'] = base_index + action['action_index']
                        existing_task['action_sequence'].append(action)
                    # 合并子任务完成记录（调整动作索引）
                    for completion in self.current_compact_task['subtask_completions']:
                        if completion['completed_at'] >= 0:
                            completion['completed_at'] += base_index
                        existing_task['subtask_completions'].append(completion)
            else:
                # Sequential/Independent模式：每个任务单独记录
                self.compact_trajectory['task_executions'].append(self.current_compact_task)

        logger.info(f"🏁 任务 {self.current_task_index} 结束: {'完成' if self.current_task['completed'] else '未完成'}")

        # 清空当前任务
        self.current_task = None
        self.current_compact_task = None
    
    def finalize(self, summary: Dict[str, Any]):
        """完成记录并保存最终结果"""
        self.trajectory['execution_info']['end_time'] = datetime.now().isoformat()

        # 计算总时长
        start_time = datetime.fromisoformat(self.trajectory['execution_info']['start_time'])
        end_time = datetime.fromisoformat(self.trajectory['execution_info']['end_time'])
        self.trajectory['execution_info']['total_duration_seconds'] = (end_time - start_time).total_seconds()

        # 计算执行统计信息
        self._calculate_execution_statistics()

        # 设置简洁轨迹的结束时间
        self.compact_trajectory['execution_info']['end_time'] = self.trajectory['execution_info']['end_time']

        # 保存最终轨迹
        self.save_trajectory()
        self.save_compact_trajectory()

        logger.info(f"✅ 轨迹记录完成: {self.trajectory_file}")
        logger.info(f"📄 简洁轨迹记录完成: {self.compact_trajectory_file}")

        stats = self.trajectory['execution_statistics']
        logger.info(f"📊 执行统计: {stats['total_tasks']} 个任务, {stats['completed_tasks']} 个完成, "
                   f"完成率: {stats['completion_rate']:.1%}, 总时长: {self.trajectory['execution_info']['total_duration_seconds']:.2f}秒")

    def _calculate_execution_statistics(self):
        """计算执行统计信息"""
        stats = self.trajectory['execution_statistics']
        task_executions = self.trajectory['task_executions']

        # 基本统计
        stats['total_tasks'] = len(task_executions)
        stats['completed_tasks'] = sum(1 for task in task_executions if task['completed'])
        stats['failed_tasks'] = stats['total_tasks'] - stats['completed_tasks']
        stats['completion_rate'] = stats['completed_tasks'] / stats['total_tasks'] if stats['total_tasks'] > 0 else 0.0

        # 动作统计
        total_actions = sum(len(task['action_sequence']) for task in task_executions)
        stats['total_actions'] = total_actions
        stats['average_actions_per_task'] = total_actions / stats['total_tasks'] if stats['total_tasks'] > 0 else 0.0

        # 任务类别统计
        task_category_stats = {}
        for task in task_executions:
            task_type = task.get('task_type', 'unknown')
            if task_type not in task_category_stats:
                task_category_stats[task_type] = {'total': 0, 'completed': 0, 'completion_rate': 0.0}

            task_category_stats[task_type]['total'] += 1
            if task['completed']:
                task_category_stats[task_type]['completed'] += 1

        # 计算各类别完成率
        for category, category_stats in task_category_stats.items():
            if category_stats['total'] > 0:
                category_stats['completion_rate'] = category_stats['completed'] / category_stats['total']

        stats['task_category_stats'] = task_category_stats

        # 动作类型统计
        action_type_stats = {}
        for task in task_executions:
            for action in task['action_sequence']:
                action_cmd = action['action_command']
                if action_cmd not in action_type_stats:
                    action_type_stats[action_cmd] = {'total': 0, 'success': 0, 'success_rate': 0.0}

                action_type_stats[action_cmd]['total'] += 1
                if action['success']:
                    action_type_stats[action_cmd]['success'] += 1

        # 计算各动作类型成功率
        for action_type, action_stats in action_type_stats.items():
            if action_stats['total'] > 0:
                action_stats['success_rate'] = action_stats['success'] / action_stats['total']

        stats['action_type_stats'] = action_type_stats

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

            # 如果有未完成的当前任务，临时添加到task_executions中
            if self.current_compact_task is not None and len(self.current_compact_task['action_sequence']) > 0:
                # 检查是否已经在task_executions中（避免重复添加）
                task_already_exists = False
                for existing_task in trajectory_to_save['task_executions']:
                    if (existing_task.get('task_description') == self.current_compact_task.get('task_description') and
                        existing_task.get('task_index') == self.current_compact_task.get('task_index')):
                        task_already_exists = True
                        break

                if not trajectory_to_save['execution_info']['evaluation_mode'] == 'combined':
                    # Sequential/Independent模式：如果任务不存在，添加当前任务
                    if not task_already_exists:
                        trajectory_to_save['task_executions'].append(self.current_compact_task)
                else:
                    # Combined模式：合并到第一个任务中
                    if len(trajectory_to_save['task_executions']) == 0:
                        trajectory_to_save['task_executions'].append(self.current_compact_task)
                    else:
                        # 更新第一个任务的动作
                        existing_task = trajectory_to_save['task_executions'][0]
                        # 合并动作（重新编号）
                        base_index = len([a for a in existing_task['action_sequence'] if a.get('action_index', -1) < len(self.current_compact_task['action_sequence'])])
                        for action in self.current_compact_task['action_sequence']:
                            if action['action_index'] >= base_index:
                                action_copy = copy.deepcopy(action)
                                action_copy['action_index'] = base_index + action['action_index']
                                existing_task['action_sequence'].append(action_copy)

            with open(self.compact_trajectory_file, 'w', encoding='utf-8') as f:
                json.dump(trajectory_to_save, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ 保存简洁轨迹失败: {e}")

    def _save_llm_qa(self):
        """保存LLM QA记录到文件"""
        try:
            # 转换为列表格式，按子任务分类
            qa_data = []
            for subtask_key in sorted(self.llm_qa_records.keys(), key=lambda x: x if isinstance(x, int) else float('inf')):
                qa_data.append(self.llm_qa_records[subtask_key])

            with open(self.llm_qa_file, 'w', encoding='utf-8') as f:
                json.dump(qa_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ 保存LLM QA记录失败: {e}")

    def _record_to_csv(self):
        """将当前任务信息记录到CSV文件"""
        if self.current_task is None:
            return

        try:
            # 计算任务统计信息
            action_sequence = self.current_task.get('action_sequence', [])
            total_steps = len(action_sequence)
            successful_steps = sum(1 for action in action_sequence if action.get('success', False))
            failed_steps = total_steps - successful_steps
            completion_rate = successful_steps / total_steps if total_steps > 0 else 0.0

            # 计算持续时间
            start_time = self.current_task.get('start_time', '')
            end_time = self.current_task.get('end_time', '')
            duration_seconds = 0
            if start_time and end_time:
                try:
                    start_dt = datetime.fromisoformat(start_time)
                    end_dt = datetime.fromisoformat(end_time)
                    duration_seconds = (end_dt - start_dt).total_seconds()
                except:
                    duration_seconds = 0

            # 计算LLM交互次数
            llm_interactions = 0
            if self.current_subtask_index in self.llm_qa_records:
                llm_interactions = len(self.llm_qa_records[self.current_subtask_index]["qa_interactions"])

            # 检查模拟器判断的子任务完成状态
            subtask_completed = self._check_subtask_completion_by_simulator()

            # 获取任务类型信息
            task_category = self._get_task_category()
            agent_type = self._get_agent_type()

            # 准备CSV行数据
            csv_row = [
                datetime.now().isoformat(),  # timestamp
                self.scenario_id,  # scenario_id
                self.current_task.get('task_index', ''),  # subtask_index
                self.current_task.get('task_description', ''),  # subtask_description
                task_category,  # task_category - 任务类型
                agent_type,  # agent_type - 智能体类型
                self.current_task.get('status', ''),  # status
                self.current_task.get('completed', False),  # task_executed - 任务是否执行完成
                subtask_completed,  # subtask_completed - 模拟器判断的子任务是否完成
                total_steps,  # total_steps
                successful_steps,  # successful_steps
                failed_steps,  # failed_steps
                f"{completion_rate:.2%}",  # command_success_rate - 命令成功率
                start_time,  # start_time
                end_time,  # end_time
                f"{duration_seconds:.2f}",  # duration_seconds
                llm_interactions  # llm_interactions
            ]

            # 写入CSV文件
            try:
                with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(csv_row)
                logger.debug(f"📊 已记录任务到CSV: {self.current_task.get('task_description', '未知任务')}")
            except Exception as csv_error:
                logger.error(f"❌ CSV记录失败: {csv_error}")
                # 尝试重新创建CSV文件
                try:
                    self._init_csv_file()
                    with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(csv_row)
                    logger.info("✅ CSV文件重新创建并记录成功")
                except Exception as retry_error:
                    logger.error(f"❌ CSV重试记录也失败: {retry_error}")

        except Exception as e:
            logger.error(f"❌ 记录CSV失败: {e}")

    def _check_subtask_completion_by_simulator(self) -> bool:
        """
        检查当前子任务是否被模拟器判断为完成

        Returns:
            bool: 模拟器判断的子任务完成状态
        """
        if self.current_task is None:
            return False

        # 检查subtask_completions中是否有模拟器反馈的完成记录
        subtask_completions = self.current_task.get('subtask_completions', [])
        for completion in subtask_completions:
            # 查找来源为模拟器的完成记录
            if completion.get('source') == 'simulator':
                return True

        return False

    def _get_task_category(self) -> str:
        """获取当前任务的类型"""
        if self.current_task is None:
            return 'unknown'

        task_index = self.current_task.get('task_index', 0)
        task_description = self.current_task.get('task_description', '')
        task_info = self.trajectory.get('task_info', {})
        tasks = task_info.get('tasks', [])

        # 方法1: 根据任务索引找到对应的任务（任务索引从1开始）
        adjusted_index = task_index - 1
        if 0 <= adjusted_index < len(tasks):
            category = tasks[adjusted_index].get('task_category', 'unknown')
            if category != 'unknown':
                return category

        # 方法2: 如果索引方法失败，尝试通过任务描述匹配
        for task in tasks:
            if task.get('task_description', '') == task_description:
                return task.get('task_category', 'unknown')

        # 方法3: 如果还是找不到，尝试通过任务描述的部分匹配
        for task in tasks:
            task_desc = task.get('task_description', '')
            if task_desc and task_desc in task_description:
                return task.get('task_category', 'unknown')

        return 'unknown'

    def _get_agent_type(self) -> str:
        """获取智能体类型"""
        agent_info = self.trajectory.get('agent_info', {})
        agent_type = agent_info.get('agent_type', 'unknown')

        # 将内部类型映射为用户友好的类型
        if agent_type == 'single':
            return 'single_agent'
        elif agent_type in ['multi_centralized', 'multi_decentralized']:
            return 'multi_agent'
        else:
            return 'unknown'

    def get_trajectory_summary(self) -> Dict[str, Any]:
        """获取轨迹摘要"""
        task_executions = self.trajectory['task_executions']
        stats = self.trajectory['execution_statistics']

        return {
            'run_name': self.run_name,
            'scenario_id': self.scenario_id,
            'execution_statistics': stats,
            'output_files': {
                'trajectory_file': self.trajectory_file,
                'compact_trajectory_file': self.compact_trajectory_file,
                'log_file': self.log_file,
                'llm_qa_file': self.llm_qa_file,
                'csv_file': self.csv_file
            },
            'execution_info': self.trajectory['execution_info']
        }
