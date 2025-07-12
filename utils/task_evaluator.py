#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务评测器 - 支持四种评测模式的独立评测器
- 单智能体逐个评测
- 单智能体混合评测
- 多智能体逐个评测
- 多智能体混合评测
"""

import os
import json
import time
import logging
import signal
import sys
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from utils.embodied_simulator import ActionStatus
from config import ConfigManager
from utils.simulator_bridge import SimulatorBridge
from utils.trajectory_recorder import TrajectoryRecorder
from utils.run_naming import RunNamingManager
from modes.single_agent.llm_agent import LLMAgent
from modes.centralized.coordinator import Coordinator
from modes.centralized.worker_agent import WorkerAgent
from modes.decentralized.autonomous_agent import AutonomousAgent
from modes.decentralized.communication import CommunicationManager

logger = logging.getLogger(__name__)


class TaskEvaluator:
    """
    任务评测器 - 支持四种评测模式
    """

    def __init__(self, config_file: str, agent_type: str, task_type: str,
                 scenario_id: str = None, custom_suffix: str = None):
        """
        初始化评测器

        Args:
            config_file: 配置文件名 (如 'single_agent_config', 'centralized_config')
            agent_type: 智能体类型 ('single' 或 'multi')
            task_type: 任务类型 ('sequential', 'combined', 'independent')
            scenario_id: 场景ID（如果为None，将从配置文件读取默认值）
            custom_suffix: 自定义后缀（如果为None，将从配置文件读取默认值）
        """
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config(config_file)

        # 从配置文件读取默认值
        eval_config = self.config.get('evaluation', {})
        run_settings = eval_config.get('run_settings', {})

        # 评测模式配置
        self.agent_type = agent_type
        self.task_type = task_type
        # 如果没有提供scenario_id，从配置文件读取默认值
        self.scenario_id = scenario_id or eval_config.get('default_scenario', '00001')
        self.config_file = config_file

        # 如果没有提供custom_suffix，从配置文件读取默认值
        if custom_suffix is None:
            custom_suffix = run_settings.get('default_suffix', 'demo')

        # 保存custom_suffix为实例属性
        self.custom_suffix = custom_suffix

        # 生成运行名称
        self.run_name = RunNamingManager.generate_run_name(
            agent_type=agent_type,
            task_type=task_type,
            scenario_id=scenario_id or 'default',
            config_name=config_file,
            custom_suffix=custom_suffix
        )

        # 设置输出目录
        eval_config = self.config.get('evaluation', {})
        output_config = eval_config.get('output', {})
        base_output_dir = output_config.get('output_directory', 'output')

        # 检查是否有环境变量指定的输出目录（用于并行评测）
        scenario_output_dir = os.environ.get('SCENARIO_OUTPUT_DIR')
        disable_auto_output = os.environ.get('DISABLE_AUTO_OUTPUT_DIR') == 'true'

        if scenario_output_dir and disable_auto_output:
            # 并行评测模式：使用指定的输出目录，不创建新目录
            self.output_dir = scenario_output_dir
        elif scenario_output_dir:
            # 兼容模式：使用指定的输出目录
            self.output_dir = scenario_output_dir
        else:
            # 正常模式：自动生成输出目录
            self.output_dir = RunNamingManager.generate_output_directory(base_output_dir, self.run_name)

        # 初始化轨迹记录器
        self.trajectory_recorder = TrajectoryRecorder(self.output_dir, self.run_name, scenario_id)

        # 初始化组件
        self.bridge = None
        self.agents = {}
        self.coordinator = None
        self.comm_manager = None

        # 结果收集
        self.results = {
            'run_name': self.run_name,
            'evaluation_mode': f"{self.agent_type}_{self.task_type}",
            'config_file': config_file,
            'start_time': None,
            'end_time': None,
            'total_duration': 0,
            'scenario_id': scenario_id,
            'task_results': [],
            'summary': {
                'total_tasks': 0,
                'completed_tasks': 0,
                'failed_tasks': 0,
                'completion_rate': 0.0,
                'total_steps': 0,
                'average_steps_per_task': 0.0
            },
            'output_files': {
                'trajectory_file': None,
                'log_file': None
            }
        }

        # 设置日志
        self._setup_logging()

        # 设置信号处理，确保中断时保存轨迹
        self._setup_signal_handlers()

    def _setup_logging(self):
        """设置日志配置"""
        eval_config = self.config.get('evaluation', {})
        debug_config = eval_config.get('debug', {})
        run_settings = eval_config.get('run_settings', {})

        # 优先使用debug配置中的log_level，如果没有则使用run_settings中的log_level
        log_level_str = debug_config.get('log_level') or run_settings.get('log_level', 'INFO')
        log_level = getattr(logging, log_level_str, logging.INFO)
        logging.getLogger().setLevel(log_level)

        if debug_config.get('verbose_logging', True):
            # 添加详细日志格式
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

            # 轨迹记录器已经设置了文件日志处理器
            logger.info(f"📝 日志级别设置为: {log_level_str}")
            logger.info(f"📁 输出目录: {self.output_dir}")
            logger.info(f"🏃 运行名称: {self.run_name}")

    def _setup_signal_handlers(self):
        """设置信号处理器，确保中断时保存轨迹"""
        try:
            def signal_handler(signum, frame):
                logger.warning(f"⚠️ 接收到中断信号 {signum}，正在保存轨迹...")
                try:
                    # 如果有独立执行器，先执行聚合逻辑
                    if hasattr(self, 'independent_executor') and self.independent_executor:
                        if hasattr(self, 'trajectory_recorder') and self.trajectory_recorder:
                            logger.info("📋 执行compact_trajectory聚合...")
                            self.independent_executor.aggregate_compact_trajectories(self.trajectory_recorder)
                            logger.info("✅ compact_trajectory聚合完成")

                    # 先结束当前任务，再保存轨迹
                    if hasattr(self, 'trajectory_recorder') and self.trajectory_recorder:
                        # 如果有正在进行的任务，先结束它
                        if self.trajectory_recorder.current_task is not None:
                            logger.info("📝 结束当前任务...")
                            self.trajectory_recorder.end_task()

                        # 保存轨迹
                        self.trajectory_recorder.save_trajectory()
                        self.trajectory_recorder.save_compact_trajectory()
                        logger.info("✅ 轨迹已保存")
                except Exception as e:
                    logger.error(f"❌ 保存轨迹时出错: {e}")
                finally:
                    logger.info("🔚 程序退出")
                    sys.exit(0)

            # 注册信号处理器（只在主线程中有效）
            signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
            signal.signal(signal.SIGTERM, signal_handler)  # 终止信号
        except ValueError as e:
            # 在非主线程中会抛出 "signal only works in main thread" 错误
            # 这是正常的，我们忽略这个错误
            logger.debug(f"信号处理器设置跳过（非主线程）: {e}")
        except Exception as e:
            logger.warning(f"⚠️ 设置信号处理器失败: {e}")

    def initialize_scenario(self, scenario_id: Optional[str] = None) -> bool:
        """
        初始化场景

        Args:
            scenario_id: 场景ID，如果为None则使用配置的场景

        Returns:
            bool: 是否成功初始化
        """
        if scenario_id is None:
            # 使用实例的scenario_id，它已经从配置文件读取了默认值
            scenario_id = self.scenario_id

        self.results['scenario_id'] = scenario_id

        # 创建模拟器桥接
        self.bridge = SimulatorBridge()

        # 初始化场景
        if not self.bridge.initialize_with_scenario(scenario_id):
            logger.error(f"❌ 场景初始化失败: {scenario_id}")
            return False

        # 记录场景信息到轨迹
        scenario_info = {
            'scenario_id': scenario_id,
            'initialization_time': datetime.now().isoformat()
        }

        # 尝试获取更多场景信息
        try:
            if hasattr(self.bridge, 'get_scenario_info'):
                scenario_info.update(self.bridge.get_scenario_info())
        except Exception as e:
            logger.warning(f"⚠️ 无法获取详细场景信息: {e}")

        self.trajectory_recorder.set_scenario_info(scenario_info)

        logger.info(f"✅ 场景初始化成功: {scenario_id}")
        return True

    def initialize_agents(self) -> bool:
        """
        根据配置初始化智能体

        Returns:
            bool: 是否成功初始化
        """
        try:
            if self.agent_type == 'single':
                return self._initialize_single_agent()
            else:
                return self._initialize_multi_agents()
        except Exception as e:
            logger.exception(f"❌ 智能体初始化失败: {e}")
            return False

    def _initialize_single_agent(self) -> bool:
        """初始化单智能体"""
        # 获取可用智能体
        available_agents = self.bridge.simulator.agent_manager.get_all_agents()
        if not available_agents:
            logger.error("❌ 没有找到任何智能体")
            return False

        # 选择第一个可用智能体
        agent_id = list(available_agents.keys())[0]

        logger.info(f"🤖 使用单智能体: {agent_id}")

        # 创建LLM智能体（使用当前配置）
        agent = LLMAgent(self.bridge.simulator, agent_id, self.config)

        # 设置轨迹记录器引用，用于记录LLM QA
        agent.set_trajectory_recorder(self.trajectory_recorder)

        self.agents[agent_id] = agent

        # 记录智能体信息
        agent_info = {
            'agent_type': 'single',
            'agents': {
                agent_id: {
                    'type': 'LLMAgent',
                    'config': self.config_file
                }
            }
        }
        self.trajectory_recorder.set_agent_info(agent_info)

        return True

    def _initialize_multi_agents(self) -> bool:
        """初始化多智能体"""
        # 获取可用智能体
        available_agents = self.bridge.simulator.agent_manager.get_all_agents()
        if not available_agents:
            logger.error("❌ 没有找到任何智能体")
            return False

        # 根据配置文件类型确定模式
        if 'coordinator' in self.config:
            return self._initialize_centralized_agents(available_agents)
        else:
            return self._initialize_decentralized_agents(available_agents)

    def _initialize_centralized_agents(self, available_agents: Dict) -> bool:
        """初始化中心化多智能体"""
        # 使用所有可用智能体
        agent_ids = list(available_agents.keys())

        if not agent_ids:
            logger.error("❌ 没有可用的智能体")
            return False

        logger.info(f"🤖 使用中心化多智能体: {agent_ids}")

        # 创建协调器（使用第一个智能体作为协调器）
        coordinator_id = agent_ids[0]
        coordinator_config = self.config.get('coordinator', {})
        self.coordinator = Coordinator(self.bridge.simulator, coordinator_id, coordinator_config)

        # 创建工作智能体
        worker_config = self.config.get('worker_agents', {})
        for agent_id in agent_ids[1:]:  # 除了协调器之外的智能体作为工作者
            worker = WorkerAgent(self.bridge.simulator, agent_id, worker_config)
            self.coordinator.add_worker(worker)
            self.agents[agent_id] = worker

        self.agents[coordinator_id] = self.coordinator

        # 记录智能体信息
        agent_info = {
            'agent_type': 'multi_centralized',
            'coordinator': coordinator_id,
            'workers': list(agent_ids[1:]),
            'agents': {}
        }

        for agent_id in agent_ids:
            if agent_id == coordinator_id:
                agent_info['agents'][agent_id] = {
                    'type': 'Coordinator',
                    'config': self.config_file
                }
            else:
                agent_info['agents'][agent_id] = {
                    'type': 'WorkerAgent',
                    'config': self.config_file
                }

        self.trajectory_recorder.set_agent_info(agent_info)

        return True

    def _initialize_decentralized_agents(self, available_agents: Dict) -> bool:
        """初始化去中心化多智能体"""
        # 使用所有可用智能体
        agent_ids = list(available_agents.keys())

        if not agent_ids:
            logger.error("❌ 没有可用的智能体")
            return False

        logger.info(f"🤖 使用去中心化多智能体: {agent_ids}")

        # 创建通信管理器
        self.comm_manager = CommunicationManager()

        # 创建自主智能体
        agent_config = self.config.get('autonomous_agent', {})
        for agent_id in agent_ids:
            agent = AutonomousAgent(self.bridge.simulator, agent_id, agent_config)
            self.agents[agent_id] = agent
            self.comm_manager.register_agent(agent_id, agent, agent.receive_message)

        # 创建智能体组
        self.comm_manager.create_group("task_group", list(agent_ids))

        # 记录智能体信息
        agent_info = {
            'agent_type': 'multi_decentralized',
            'agents': {}
        }

        for agent_id in agent_ids:
            agent_info['agents'][agent_id] = {
                'type': 'AutonomousAgent',
                'config': self.config_file
            }

        self.trajectory_recorder.set_agent_info(agent_info)

        return True

    def _filter_tasks_by_agent_type(self, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据智能体类型过滤任务

        Args:
            task_info: 原始任务信息

        Returns:
            Dict: 过滤后的任务信息
        """
        if not task_info or 'tasks' not in task_info:
            return task_info

        original_tasks = task_info['tasks']
        original_count = len(original_tasks)

        if self.agent_type == 'single':
            # 单智能体模式：过滤掉协作任务
            collaboration_categories = {
                'explicit_collaboration',
                'implicit_collaboration',
                'compound_collaboration'
            }

            filtered_tasks = [
                task for task in original_tasks
                if task.get('task_category') not in collaboration_categories
            ]

            filtered_count = len(filtered_tasks)
            excluded_count = original_count - filtered_count

            logger.info(f"🔍 单智能体模式任务过滤:")
            logger.info(f"  - 原始任务数: {original_count}")
            logger.info(f"  - 过滤后任务数: {filtered_count}")
            logger.info(f"  - 排除协作任务数: {excluded_count}")

            if excluded_count > 0:
                excluded_categories = set()
                for task in original_tasks:
                    if task.get('task_category') in collaboration_categories:
                        excluded_categories.add(task.get('task_category'))
                logger.info(f"  - 排除的任务类别: {', '.join(sorted(excluded_categories))}")

        else:
            # 多智能体模式：保留所有任务
            filtered_tasks = original_tasks
            logger.info(f"🔍 多智能体模式保留所有任务: {original_count} 个")

        # 创建过滤后的任务信息副本
        filtered_task_info = task_info.copy()
        filtered_task_info['tasks'] = filtered_tasks

        return filtered_task_info

    def _update_task_verifier(self, filtered_task_info: Dict[str, Any]):
        """
        使用过滤后的任务信息更新任务验证器

        Args:
            filtered_task_info: 过滤后的任务信息
        """
        try:
            # 更新模拟器的任务配置
            if hasattr(self.bridge.simulator, 'task_config'):
                self.bridge.simulator.task_config = filtered_task_info

            # 重新创建任务验证器
            if hasattr(self.bridge.simulator, '_create_task_verifier'):
                self.bridge.simulator.task_verifier = self.bridge.simulator._create_task_verifier(filtered_task_info)

                # 确保action_handler也使用新的任务验证器
                if hasattr(self.bridge.simulator, 'action_handler') and self.bridge.simulator.action_handler:
                    self.bridge.simulator.action_handler.task_verifier = self.bridge.simulator.task_verifier
                    logger.debug("已更新action_handler的任务验证器")

                logger.info(f"✅ 已使用过滤后的任务信息重新创建任务验证器")
            else:
                logger.warning("⚠️ 无法重新创建任务验证器，模拟器不支持此功能")

        except Exception as e:
            logger.error(f"❌ 更新任务验证器失败: {e}")

    def run_evaluation(self, scenario_id: Optional[str] = None) -> Dict[str, Any]:
        """
        运行评测

        Args:
            scenario_id: 场景ID

        Returns:
            Dict: 评测结果
        """
        logger.info(f"🚀 开始评测 - 模式: {self.agent_type}_{self.task_type}")
        logger.info(f"🏃 运行名称: {self.run_name}")

        self.results['start_time'] = datetime.now().isoformat()
        start_time = time.time()

        # 记录配置信息
        self.trajectory_recorder.set_configuration({
            'agent_type': self.agent_type,
            'task_type': self.task_type,
            'config_file': self.config_file,
            'scenario_id': scenario_id,
            'config_data': self.config
        })

        try:
            # 初始化场景
            if not self.initialize_scenario(scenario_id):
                raise Exception("场景初始化失败")

            # 初始化智能体
            if not self.initialize_agents():
                raise Exception("智能体初始化失败")

            # 获取任务信息
            task_info = self.bridge.get_task_info()
            if not task_info:
                raise Exception("无法获取任务信息")

            # 根据智能体类型过滤任务
            filtered_task_info = self._filter_tasks_by_agent_type(task_info)

            # 记录过滤后的任务信息
            self.trajectory_recorder.set_task_info(filtered_task_info)

            # 设置评测模式
            self.trajectory_recorder.set_evaluation_mode(self.task_type)

            # 重新创建任务验证器以使用过滤后的任务
            self._update_task_verifier(filtered_task_info)

            # 执行任务（使用过滤后的任务信息）
            if self.task_type == 'sequential':
                self._run_sequential_evaluation(filtered_task_info)
            elif self.task_type == 'combined':
                self._run_combined_evaluation(filtered_task_info)
            elif self.task_type == 'independent':
                self._run_independent_evaluation(filtered_task_info)
            else:
                raise ValueError(f"不支持的任务类型: {self.task_type}")

        except Exception as e:
            logger.exception(f"❌ 评测执行失败: {e}")
            self.results['error'] = str(e)

            # 记录错误到日志
            logger.error(f"评测执行失败: {e}")

        finally:
            # 计算总时间
            end_time = time.time()
            self.results['end_time'] = datetime.now().isoformat()
            self.results['total_duration'] = end_time - start_time

            # 生成摘要
            self._generate_summary()

            # 完成轨迹记录
            self.trajectory_recorder.finalize(self.results['summary'])

            # 更新输出文件信息
            trajectory_summary = self.trajectory_recorder.get_trajectory_summary()
            self.results['output_files'] = trajectory_summary.get('output_files', {})

            # 保存结果报告
            eval_config = self.config.get('evaluation', {})
            output_config = eval_config.get('output', {})
            if output_config.get('generate_report', True):
                self._save_results()

        return self.results

    def _run_sequential_evaluation(self, task_info: Dict[str, Any]):
        """运行逐个评测"""
        logger.info("📋 开始逐个评测模式")

        subtasks = task_info.get("tasks", [])
        task_background = task_info.get('task_background', '探索环境并完成任务')

        self.results['summary']['total_tasks'] = len(subtasks)

        # 获取配置
        eval_config = self.config.get('evaluation', {})
        exec_config = eval_config.get('execution', {})
        seq_config = exec_config.get('sequential', {})

        max_steps_per_task = self.config.get('task_evaluator', {}).get('max_steps_per_task', 30)
        max_total_steps = self.config.get('execution', {}).get('max_total_steps', 300)
        clear_history = True  # 逐个评测默认清空历史
        continue_on_failure = seq_config.get('continue_on_failure', True)

        total_step_count = 0

        for task_index, subtask in enumerate(subtasks):
            if total_step_count >= max_total_steps:
                logger.warning(f"⏰ 达到总最大步数 {max_total_steps}，停止执行")
                break

            task_desc = subtask.get("task_description", f"子任务{task_index + 1}")
            logger.info(f"\n🎯 开始执行子任务 {task_index + 1}/{len(subtasks)}: {task_desc}")
            logger.info(f"📊 当前进度: 已完成 {self.results['summary']['completed_tasks']}/{len(subtasks)} 个子任务")

            # 开始任务记录
            self.trajectory_recorder.start_task(task_index + 1, task_desc, 'subtask')

            # 清空历史记录（如果配置要求）
            if clear_history and task_index > 0:
                logger.info("🧹 清空智能体历史记录")
                self._clear_agent_history()

            # 设置任务
            full_task = f"{task_background}\n\n当前子任务: {task_desc}"
            self._set_agent_task(full_task)

            # 执行子任务
            task_result = self._execute_single_task(
                subtask, task_index + 1, max_steps_per_task,
                max_total_steps - total_step_count
            )

            total_step_count += task_result['steps_taken']
            self.results['task_results'].append(task_result)

            # 记录任务完成情况
            self.trajectory_recorder.record_task_completion(task_result['completed'])

            # 结束任务记录
            self.trajectory_recorder.end_task()

            if task_result['completed']:
                self.results['summary']['completed_tasks'] += 1
                logger.info(f"✅ 子任务 {task_index + 1} 完成！用时 {task_result['steps_taken']} 步")
                logger.info(f"🎉 总体进度: {self.results['summary']['completed_tasks']}/{len(subtasks)} 个子任务已完成")
            else:
                self.results['summary']['failed_tasks'] += 1
                logger.warning(f"❌ 子任务 {task_index + 1} 失败，用时 {task_result['steps_taken']} 步")

                if not continue_on_failure:
                    logger.warning("🛑 配置要求失败时停止，终止评测")
                    break

            # 如果还有下一个子任务，打印即将开始的信息
            if task_index + 1 < len(subtasks):
                next_task_desc = subtasks[task_index + 1].get("task_description", f"子任务{task_index + 2}")
                logger.info(f"⏭️ 准备进入下一个子任务: {next_task_desc}")
            else:
                logger.info("🏁 所有子任务已处理完毕")

        self.results['summary']['total_steps'] = total_step_count

    def _run_combined_evaluation(self, task_info: Dict[str, Any]):
        """运行混合评测"""
        logger.info("📋 开始混合评测模式")

        subtasks = task_info.get("tasks", [])
        task_background = task_info.get('task_background', '探索环境并完成任务')

        self.results['summary']['total_tasks'] = 1  # 混合模式视为一个大任务

        # 构建组合任务描述
        combined_config = self.config.get('evaluation', {}).get('execution', {}).get('combined', {})
        separator = combined_config['task_separator']
        add_numbers = combined_config['add_task_numbers']

        task_descriptions = []
        for i, subtask in enumerate(subtasks):
            desc = subtask.get("task_description", f"子任务{i + 1}")
            if add_numbers:
                desc = f"{i + 1}. {desc}"
            task_descriptions.append(desc)

        combined_task = task_background + separator + separator.join(task_descriptions)

        logger.info(f"🎯 执行组合任务，包含 {len(subtasks)} 个子任务")

        # 开始任务记录
        self.trajectory_recorder.start_task(1, '组合任务', 'combined')

        # 设置任务
        self._set_agent_task(combined_task)

        # 执行组合任务
        max_total_steps = self.config.get('execution', {}).get('max_total_steps', 300)

        task_result = {
            'task_index': 1,
            'task_description': '组合任务',
            'subtasks': subtasks,
            'start_time': datetime.now().isoformat(),
            'completed': False,
            'steps_taken': 0,
            'completion_details': []
        }

        step_count = 0
        completed_subtasks = 0

        while step_count < max_total_steps:
            step_count += 1

            # 执行一步
            step_results = self._execute_agent_step()

            # Combined模式：完全以大模型的DONE命令为准
            if self._check_done_command_completion(step_results):
                logger.info("🎯 Combined模式检测到DONE命令，任务结束（大模型判断）")
                task_result['completed'] = True
                break

            # 记录模拟器的客观反馈（不影响任务完成判断）
            for subtask_index, subtask in enumerate(subtasks):
                if self._is_subtask_completed(subtask):
                    # 检查是否已经记录过这个子任务的完成
                    already_recorded = any(
                        detail['subtask_index'] == subtask_index
                        for detail in task_result['completion_details']
                    )

                    if not already_recorded:
                        subtask_desc = subtask.get("task_description", f"子任务{subtask_index + 1}")
                        task_result['completion_details'].append({
                            'subtask_index': subtask_index,
                            'subtask_description': subtask_desc,
                            'completed_at_step': step_count,
                            'completed_time': datetime.now().isoformat()
                        })

                        # 记录模拟器反馈的子任务完成
                        self._record_simulator_completion(subtask, step_count, subtask_index)

                        logger.info(f"📊 模拟器检测到子任务 {subtask_index + 1} 状态满足条件（第 {step_count} 步）")

            # 调试暂停
            if self.config.get('evaluation', {}).get('debug', {}).get('pause_between_steps', False):
                time.sleep(self.config['debug']['pause_duration'])

        task_result['end_time'] = datetime.now().isoformat()
        task_result['steps_taken'] = step_count
        task_result['completed_subtasks'] = completed_subtasks
        task_result['completion_rate'] = completed_subtasks / len(subtasks) if subtasks else 0.0

        # 记录任务完成情况
        self.trajectory_recorder.record_task_completion(task_result['completed'])

        # 结束任务记录
        self.trajectory_recorder.end_task()

        self.results['task_results'].append(task_result)
        self.results['summary']['total_steps'] = step_count

        if task_result['completed']:
            self.results['summary']['completed_tasks'] = 1
        else:
            self.results['summary']['failed_tasks'] = 1

    def _execute_single_task(self, subtask: Dict[str, Any], task_index: int,
                           max_steps: int, remaining_total_steps: int) -> Dict[str, Any]:
        """
        执行单个子任务

        Args:
            subtask: 子任务配置
            task_index: 任务索引
            max_steps: 最大步数
            remaining_total_steps: 剩余总步数

        Returns:
            Dict: 任务执行结果
        """
        task_result = {
            'task_index': task_index,
            'task_description': subtask.get("task_description", f"子任务{task_index}"),
            'start_time': datetime.now().isoformat(),
            'completed': False,
            'steps_taken': 0
        }

        # 设置智能体任务描述（特别是为independent模式）
        task_desc = subtask.get("task_description", f"子任务{task_index}")

        # 如果有任务背景信息，组合完整的任务描述
        if hasattr(self, 'trajectory_recorder') and self.trajectory_recorder:
            task_info = getattr(self.trajectory_recorder, 'task_info', {})
            task_background = task_info.get('task_background', '')
            if task_background:
                full_task = f"{task_background}\n\n当前子任务: {task_desc}"
            else:
                full_task = task_desc
        else:
            full_task = task_desc

        # 设置智能体任务
        self._set_agent_task(full_task)
        logger.info(f"🎯 已设置子任务描述: {task_desc}")

        max_steps = min(max_steps, remaining_total_steps)
        step_count = 0

        while step_count < max_steps:
            step_count += 1

            # 执行一步
            step_results = self._execute_agent_step()

            # Sequential模式：完全以大模型的DONE命令为准
            if self._check_done_command_completion(step_results):
                task_result['completed'] = True
                logger.info(f"✅ 子任务通过DONE命令在第 {step_count} 步完成（大模型判断）")
                break

            # 记录模拟器的客观反馈（不影响任务完成判断）
            if self._is_subtask_completed(subtask):
                # 记录模拟器认为任务已完成，但不结束任务
                self._record_simulator_completion(subtask, step_count, task_index)
                logger.info(f"📊 模拟器检测到子任务状态满足条件（第 {step_count} 步），但等待大模型DONE命令")

            # 调试暂停
            eval_config = self.config.get('evaluation', {})
            debug_config = eval_config.get('debug', {})
            if debug_config.get('pause_between_steps', False):
                time.sleep(debug_config.get('pause_duration', 1.0))

        task_result['end_time'] = datetime.now().isoformat()
        task_result['steps_taken'] = step_count

        return task_result

    def _execute_agent_step(self) -> Dict[str, Any]:
        """执行智能体一步"""
        step_start_time = time.time()

        if self.agent_type == 'single':
            # 单智能体模式
            agent = list(self.agents.values())[0]

            # 执行步骤
            status, message, result = agent.step()

            # 从智能体历史记录中获取最后执行的动作
            action_command = 'unknown'
            if hasattr(agent, 'history') and agent.history:
                last_action = agent.history[-1]
                if isinstance(last_action, dict) and 'action' in last_action:
                    action_command = last_action['action']
                elif isinstance(last_action, str):
                    action_command = last_action

            self.trajectory_recorder.record_action(
                action=action_command,
                status=status,
                message=message,
                agent_id=agent.agent_id,
                result=result
            )

            step_result = {
                'agent_id': agent.agent_id,
                'status': status.name if hasattr(status, 'name') else str(status),
                'message': message,
                'result': result,
                'command': action_command,  # 添加command字段用于DONE检测
                'execution_time': time.time() - step_start_time
            }

            return step_result

        else:
            # 多智能体模式
            if self.coordinator:
                # 中心化模式
                status, message, result = self.coordinator.step()

                step_result = {
                    'mode': 'centralized',
                    'coordinator_id': self.coordinator.agent_id,
                    'status': status.name if hasattr(status, 'name') else str(status),
                    'message': message,
                    'result': result,
                    'execution_time': time.time() - step_start_time
                }

                return step_result
            else:
                # 去中心化模式
                results = {}
                for agent_id, agent in self.agents.items():
                    agent_start_time = time.time()
                    status, message, result = agent.step()

                    # 从智能体历史记录中获取最后执行的动作
                    action_command = 'unknown'
                    if hasattr(agent, 'history') and agent.history:
                        last_action = agent.history[-1]
                        if isinstance(last_action, dict) and 'action' in last_action:
                            action_command = last_action['action']
                        elif isinstance(last_action, str):
                            action_command = last_action

                    self.trajectory_recorder.record_action(
                        action=action_command,
                        status=status,
                        message=message,
                        agent_id=agent_id,
                        result=result
                    )

                    results[agent_id] = {
                        'status': status.name if hasattr(status, 'name') else str(status),
                        'message': message,
                        'result': result,
                        'execution_time': time.time() - agent_start_time
                    }

                return {
                    'mode': 'decentralized',
                    'agent_results': results,
                    'total_execution_time': time.time() - step_start_time
                }

    def _extract_action_info(self, result: Any) -> Dict[str, Any]:
        """从结果中提取动作信息"""
        if isinstance(result, dict):
            return {
                'action': result.get('action', 'unknown'),
                'parameters': result.get('parameters', {}),
                'success': result.get('success', False)
            }
        elif hasattr(result, 'action'):
            return {
                'action': getattr(result, 'action', 'unknown'),
                'parameters': getattr(result, 'parameters', {}),
                'success': getattr(result, 'success', False)
            }
        else:
            return {
                'action': 'unknown',
                'parameters': {},
                'success': False
            }

    def _set_agent_task(self, task_description: str):
        """设置智能体任务"""
        if self.agent_type == 'single':
            # 单智能体模式
            agent = list(self.agents.values())[0]
            if hasattr(agent, 'set_task'):
                agent.set_task(task_description)
        else:
            # 多智能体模式
            if self.coordinator:
                # 中心化模式
                if hasattr(self.coordinator, 'set_task'):
                    self.coordinator.set_task(task_description)
            else:
                # 去中心化模式
                for agent in self.agents.values():
                    if hasattr(agent, 'set_task'):
                        agent.set_task(task_description)

    def _clear_agent_history(self):
        """清空智能体历史记录"""
        if self.agent_type == 'single':
            # 单智能体模式
            agent = list(self.agents.values())[0]
            if hasattr(agent, 'clear_history'):
                agent.clear_history()
            elif hasattr(agent, 'history'):
                agent.history = []
        else:
            # 多智能体模式
            if self.coordinator:
                # 中心化模式
                if hasattr(self.coordinator, 'clear_history'):
                    self.coordinator.clear_history()
                elif hasattr(self.coordinator, 'history'):
                    self.coordinator.history = []

                # 清空工作智能体历史
                for worker in self.coordinator.workers.values():
                    if hasattr(worker, 'clear_history'):
                        worker.clear_history()
                    elif hasattr(worker, 'history'):
                        worker.history = []
            else:
                # 去中心化模式
                for agent in self.agents.values():
                    if hasattr(agent, 'clear_history'):
                        agent.clear_history()
                    elif hasattr(agent, 'history'):
                        agent.history = []

    def _is_subtask_completed(self, subtask: Dict[str, Any]) -> bool:
        """检查子任务是否完成"""
        try:
            validation_checks = subtask.get("validation_checks", [])
            if not validation_checks:
                return False

            for check in validation_checks:
                check_id = check.get("id")
                if not check_id:
                    continue

                # 获取目标物体
                obj = None
                if hasattr(self.bridge, 'get_object_by_id'):
                    obj = self.bridge.get_object_by_id(check_id)
                elif hasattr(self.bridge, 'simulator') and hasattr(self.bridge.simulator, 'env_manager'):
                    obj = self.bridge.simulator.env_manager.get_object_by_id(check_id)

                if not obj:
                    return False

                # 检查验证条件
                for state_key, expected_value in check.items():
                    if state_key == "id":
                        continue

                    if state_key == "location_id":
                        current_location = obj.get("location_id")
                        if not self._check_location_match(current_location, expected_value):
                            return False

                    elif state_key.startswith("is_"):
                        current_value = obj.get("states", {}).get(state_key)
                        if current_value != expected_value:
                            return False

            return True

        except Exception as e:
            logger.error(f"验证子任务时发生错误: {e}")
            return False

    def _check_location_match(self, current_location: str, expected_location: str) -> bool:
        """检查位置是否匹配"""
        if not current_location or not expected_location:
            return False

        # 直接匹配
        if current_location == expected_location:
            return True

        # 处理容器位置匹配（如 "in:container_id"）
        if ":" in expected_location:
            expected_prefix, expected_container = expected_location.split(":", 1)
            if ":" in current_location:
                current_prefix, current_container = current_location.split(":", 1)
                return expected_prefix == current_prefix and expected_container == current_container

        return False

    def _check_done_command_completion(self, step_results: Dict[str, Any]) -> bool:
        """
        检查是否执行了DONE命令

        Args:
            step_results: 步骤执行结果

        Returns:
            bool: 是否执行了DONE命令
        """
        try:
            # 检查命令是否是DONE
            command = step_results.get('command', '').strip().upper()
            if command == 'DONE':
                logger.info(f"🎯 检测到大模型执行DONE命令")
                return True

            return False

        except Exception as e:
            logger.error(f"检查DONE命令时发生错误: {e}")
            return False

    def _record_simulator_completion(self, subtask: Dict[str, Any], step_count: int, subtask_index: int = None):
        """
        记录模拟器检测到的任务完成情况

        Args:
            subtask: 子任务信息
            step_count: 当前步数
            subtask_index: 子任务索引（Combined模式使用）
        """
        try:
            completion_record = {
                'step': step_count,
                'timestamp': datetime.now().isoformat(),
                'task_description': subtask.get('task_description', ''),
                'simulator_status': 'completed'
            }

            if subtask_index is not None:
                completion_record['subtask_index'] = subtask_index

            # 记录到trajectory中
            self.trajectory_recorder.record_simulator_completion(completion_record)

        except Exception as e:
            logger.error(f"记录模拟器完成状态时发生错误: {e}")

    def _generate_summary(self):
        """生成评测摘要"""
        summary = self.results['summary']

        if summary['total_tasks'] > 0:
            summary['completion_rate'] = summary['completed_tasks'] / summary['total_tasks']

        if summary['total_tasks'] > 0 and summary['total_steps'] > 0:
            summary['average_steps_per_task'] = summary['total_steps'] / summary['total_tasks']

        logger.info(f"\n📊 评测摘要:")
        logger.info(f"   模式: {self.results['evaluation_mode']}")
        logger.info(f"   场景: {self.results['scenario_id']}")
        logger.info(f"   总任务数: {summary['total_tasks']}")
        logger.info(f"   完成任务数: {summary['completed_tasks']}")
        logger.info(f"   失败任务数: {summary['failed_tasks']}")
        logger.info(f"   完成率: {summary['completion_rate']:.1%}")
        logger.info(f"   总步数: {summary['total_steps']}")
        logger.info(f"   平均步数/任务: {summary['average_steps_per_task']:.1f}")
        logger.info(f"   总耗时: {self.results['total_duration']:.2f}秒")

    def _save_results(self):
        """保存评测结果（合并report和summary为一个meta文件）"""
        try:
            # 只保存一个包含关键meta信息的文件
            meta_path = os.path.join(self.output_dir, f"{self.run_name}_meta.json")

            # 提取关键meta信息
            meta_data = {
                'scenario_id': self.results['scenario_id'],
                'evaluation_mode': self.results['evaluation_mode'],
                'execution_info': {
                    'start_time': self.results['start_time'],
                    'end_time': self.results['end_time'],
                    'total_duration': self.results['total_duration']
                },
                'task_completion': {
                    'total_tasks': self.results['summary']['total_tasks'],
                    'completed_tasks': self.results['summary']['completed_tasks'],
                    'failed_tasks': self.results['summary']['failed_tasks'],
                    'completion_rate': self.results['summary']['completion_rate']
                },
                'execution_stats': {
                    'total_steps': self.results['summary']['total_steps'],
                    'average_steps_per_task': self.results['summary']['average_steps_per_task']
                },
                'output_files': self.results['output_files']
            }

            # 对于independent模式，添加子任务详细信息
            if self.task_type == 'independent':
                subtask_stats = []
                for task_result in self.results.get('task_results', []):
                    if 'subtask_results' in task_result:
                        for subtask in task_result['subtask_results']:
                            subtask_stats.append({
                                'subtask_index': subtask.get('subtask_index', 0),
                                'task_description': subtask.get('task_description', ''),
                                'task_category': subtask.get('task_category', ''),
                                'completed': subtask.get('completed', False),
                                'steps_taken': subtask.get('steps_taken', 0),
                                'duration': subtask.get('duration', 0)
                            })
                meta_data['subtask_details'] = subtask_stats

            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, ensure_ascii=False, indent=2)

            logger.info(f"📊 场景meta信息已保存: {meta_path}")

        except Exception as e:
            logger.exception(f"❌ 保存评测报告失败: {e}")





    def _run_independent_evaluation(self, task_info: Dict[str, Any]):
        """
        运行独立评测模式（基于独立实例）

        每个子任务都在完全独立的TaskEvaluator实例中执行，确保完全隔离。
        """
        logger.info("📋 开始独立评测模式 - 使用独立实例策略")
        self._run_isolated_instances_evaluation(task_info)

    def _run_isolated_instances_evaluation(self, task_info: Dict[str, Any]):
        """
        运行基于独立实例的独立评测模式

        这个方法使用IndependentTaskExecutor来执行评测，
        每个子任务都在完全独立的TaskEvaluator实例中执行。
        """
        logger.info("🔧 使用独立实例策略执行独立评测")

        try:
            # 导入IndependentTaskExecutor
            from utils.independent_task_executor import IndependentTaskExecutor

            # 创建独立任务执行器
            executor = IndependentTaskExecutor(
                config_file=self.config_file,
                agent_type=self.agent_type,
                scenario_id=self.scenario_id,
                custom_suffix=self.custom_suffix,
                output_dir=self.output_dir
            )

            # 保存executor引用，以便在信号处理器中使用
            self.independent_executor = executor

            # 执行独立评测
            aggregated_results = executor.execute_independent_evaluation(task_info)

            # 将聚合结果转换为TaskEvaluator的结果格式
            self._convert_aggregated_results_to_task_evaluator_format(aggregated_results)

            # 聚合子任务的compact_trajectory数据
            if hasattr(self, 'trajectory_recorder') and self.trajectory_recorder:
                executor.aggregate_compact_trajectories(self.trajectory_recorder)
                logger.info("📋 已聚合子任务的compact_trajectory数据")

            # 保存聚合结果
            executor.save_aggregated_results()

            logger.info("✅ 独立实例策略执行完成")

        except Exception as e:
            logger.exception(f"❌ 独立实例策略执行失败: {e}")
            self.results['error'] = str(e)



    def _convert_aggregated_results_to_task_evaluator_format(self, aggregated_results: Dict[str, Any]):
        """
        将IndependentTaskExecutor的聚合结果转换为TaskEvaluator的结果格式

        Args:
            aggregated_results: IndependentTaskExecutor的聚合结果
        """
        try:
            summary = aggregated_results['aggregated_summary']

            # 更新基本统计
            self.results['summary']['total_tasks'] = summary['total_subtasks']
            self.results['summary']['completed_tasks'] = summary['completed_subtasks']
            self.results['summary']['failed_tasks'] = summary['failed_subtasks']
            self.results['summary']['completion_rate'] = summary['completion_rate']
            self.results['summary']['total_steps'] = summary['total_steps']
            self.results['summary']['total_duration'] = summary['total_execution_time']
            self.results['summary']['average_steps_per_task'] = (
                summary['total_steps'] / summary['total_subtasks']
                if summary['total_subtasks'] > 0 else 0
            )

            # 转换子任务结果
            self.results['task_results'] = []
            for subtask_result in aggregated_results['subtask_results']:
                task_result = {
                    'task_index': subtask_result['subtask_index'] + 1,
                    'task_description': subtask_result['subtask_description'],
                    'task_category': subtask_result['task_category'],
                    'completed': subtask_result['result']['status'] == 'success',
                    'steps_taken': subtask_result['result']['steps_taken'],
                    'completion_rate': subtask_result['result']['completion_rate'],
                    'duration': subtask_result['execution_info']['duration'],
                    'validation_results': subtask_result['result'].get('validation_results', []),
                    'execution_mode': 'independent_isolated_instance'
                }

                if 'error' in subtask_result['result']:
                    task_result['error'] = subtask_result['result']['error']

                self.results['task_results'].append(task_result)

            # 添加执行模式信息
            self.results['execution_info'] = {
                'mode': 'independent',
                'strategy': 'isolated_instances',
                'total_subtasks': summary['total_subtasks'],
                'execution_time': summary['total_execution_time'],
                'average_subtask_duration': summary['average_subtask_duration']
            }

            logger.info("✅ 结果格式转换完成")

        except Exception as e:
            logger.exception(f"❌ 结果格式转换失败: {e}")