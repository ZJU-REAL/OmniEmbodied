#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立任务执行器 - 基于独立实例的Independent评测实现

这个模块实现了新的Independent评测方式，每个子任务都在完全独立的TaskEvaluator实例中执行，
避免了环境重置的复杂性和开销，确保了完全的任务隔离。

主要特点：
1. 每个子任务创建独立的TaskEvaluator实例
2. 每个子任务有独立的模拟器实例
3. 完全的资源隔离，无状态污染
4. 串行执行，结果可重现
5. 独立的输出目录和日志文件
"""

import os
import sys
import time
import copy
import json
import logging
import threading
import gc
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from utils.task_evaluator import TaskEvaluator
from config import ConfigManager

logger = logging.getLogger(__name__)


class IndependentTaskExecutor:
    """
    独立任务执行器
    
    实现基于独立实例的Independent评测方式，每个子任务都在完全独立的环境中执行。
    这种方式避免了环境重置的复杂性，确保了完全的任务隔离。
    """
    
    def __init__(self, config_file: str, agent_type: str, scenario_id: str, 
                 custom_suffix: str, output_dir: str):
        """
        初始化独立任务执行器
        
        Args:
            config_file: 配置文件名
            agent_type: 智能体类型 ('single' 或 'multi')
            scenario_id: 场景ID
            custom_suffix: 自定义后缀
            output_dir: 输出目录
        """
        self.config_file = config_file
        self.agent_type = agent_type
        self.scenario_id = scenario_id
        self.custom_suffix = custom_suffix
        self.output_dir = output_dir
        
        # 加载配置
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config(config_file)
        
        # 获取independent配置
        eval_config = self.config.get('evaluation', {})
        exec_config = eval_config.get('execution', {})
        self.independent_config = exec_config.get('independent', {})
        
        # 执行配置
        self.continue_on_failure = self.independent_config.get('continue_on_failure', True)
        self.delay_between_subtasks = self.independent_config.get('delay_between_subtasks', 1.0)
        self.show_subtask_progress = self.independent_config.get('show_subtask_progress', True)
        
        # 资源管理配置（硬编码合理默认值）
        self.force_garbage_collection = True  # 强制垃圾回收，确保内存清理
        self.cleanup_timeout = 10  # 实例清理超时时间（秒）
        self.monitor_memory_usage = False  # 不监控内存使用（避免性能开销）
        
        # 输出管理配置
        output_config = self.independent_config.get('output_management', {})
        self.subtask_dir_pattern = output_config.get('subtask_dir_pattern', 'subtask_{index:03d}_{hash}')
        self.create_subtask_directories = output_config.get('create_subtask_directories', False)
        self.save_individual_logs = output_config.get('save_individual_logs', True)
        self.generate_subtask_trajectories = output_config.get('generate_subtask_trajectories', True)
        
        # 结果聚合
        self.subtask_results = []
        self.aggregated_results = {
            'evaluation_info': {
                'mode': 'independent',
                'scenario_id': scenario_id,
                'agent_type': agent_type,
                'start_time': None,
                'end_time': None
            },
            'subtask_results': [],
            'aggregated_summary': {
                'total_subtasks': 0,
                'completed_subtasks': 0,
                'failed_subtasks': 0,
                'completion_rate': 0.0,
                'total_steps': 0,
                'total_execution_time': 0.0,
                'average_subtask_duration': 0.0,
                'category_performance': {}
            }
        }
        
        # 线程安全锁
        self.results_lock = threading.Lock()
        
        logger.info(f"🚀 独立任务执行器初始化完成")
        logger.info(f"📁 输出目录: {self.output_dir}")
        logger.info(f"⚙️ 执行策略: isolated_instances")
    
    def execute_independent_evaluation(self, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行独立评测
        
        Args:
            task_info: 任务信息，包含所有子任务
            
        Returns:
            Dict: 聚合的评测结果
        """
        logger.info("📋 开始独立评测模式（基于独立实例）")
        
        subtasks = task_info.get("tasks", [])
        if not subtasks:
            logger.error("❌ 没有找到子任务")
            return self.aggregated_results
        
        # 记录开始时间
        start_time = time.time()
        self.aggregated_results['evaluation_info']['start_time'] = datetime.now().isoformat()
        self.aggregated_results['aggregated_summary']['total_subtasks'] = len(subtasks)
        
        logger.info(f"📊 准备执行 {len(subtasks)} 个子任务")
        
        # 串行执行每个子任务
        for subtask_index, subtask in enumerate(subtasks):
            if self.show_subtask_progress:
                logger.info(f"\n🎯 开始执行子任务 {subtask_index + 1}/{len(subtasks)}")
                logger.info(f"📝 任务描述: {subtask.get('task_description', '未知任务')}")
            
            # 执行单个子任务
            subtask_result = self._execute_single_subtask(
                subtask, subtask_index, task_info
            )
            
            # 记录结果
            with self.results_lock:
                self.subtask_results.append(subtask_result)
                self.aggregated_results['subtask_results'].append(subtask_result)
                
                # 更新统计
                if subtask_result['result']['status'] == 'success':
                    self.aggregated_results['aggregated_summary']['completed_subtasks'] += 1
                else:
                    self.aggregated_results['aggregated_summary']['failed_subtasks'] += 1
                
                self.aggregated_results['aggregated_summary']['total_steps'] += subtask_result['result']['steps_taken']
            
            # 显示进度
            if self.show_subtask_progress:
                status_icon = "✅" if subtask_result['result']['status'] == 'success' else "❌"
                logger.info(f"📊 子任务 {subtask_index + 1} 完成: {status_icon}")
            
            # 检查是否继续执行
            if subtask_result['result']['status'] != 'success' and not self.continue_on_failure:
                logger.info("⏹️ 子任务失败且配置为不继续，停止执行")
                break
            
            # 子任务间延迟
            if self.delay_between_subtasks > 0 and subtask_index < len(subtasks) - 1:
                time.sleep(self.delay_between_subtasks)
        
        # 记录结束时间和生成最终结果
        end_time = time.time()
        self.aggregated_results['evaluation_info']['end_time'] = datetime.now().isoformat()
        self.aggregated_results['aggregated_summary']['total_execution_time'] = end_time - start_time
        
        # 计算最终统计
        self._calculate_final_statistics()
        
        logger.info("🎉 独立评测完成！")
        self._log_final_summary()
        
        return self.aggregated_results

    def _execute_single_subtask(self, subtask: Dict[str, Any], subtask_index: int,
                               task_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单个子任务（在独立的TaskEvaluator实例中）

        Args:
            subtask: 子任务数据
            subtask_index: 子任务索引
            task_info: 完整的任务信息

        Returns:
            Dict: 子任务执行结果
        """
        # 根据配置决定是否创建子任务独立目录
        if self.create_subtask_directories:
            # 创建子任务输出目录
            subtask_hash = hash(subtask.get('task_description', '')) % 10000
            subtask_dir_name = self.subtask_dir_pattern.format(
                index=subtask_index,
                hash=f"{subtask_hash:04d}"
            )
            subtask_output_dir = os.path.join(self.output_dir, subtask_dir_name)
            os.makedirs(subtask_output_dir, exist_ok=True)
        else:
            # 使用主输出目录，不创建子任务独立目录
            subtask_output_dir = self.output_dir
            subtask_dir_name = f"subtask_{subtask_index:03d}"

        # 初始化结果结构
        subtask_result = {
            'subtask_index': subtask_index,
            'subtask_id': f"subtask_{subtask_index:03d}",
            'subtask_description': subtask.get('task_description', ''),
            'task_category': subtask.get('task_category', 'unknown'),
            'execution_info': {
                'start_time': datetime.now().isoformat(),
                'end_time': None,
                'duration': 0.0,
                'instance_creation_time': 0.0,
                'cleanup_time': 0.0
            },
            'result': {
                'status': 'failed',
                'steps_taken': 0,
                'completion_rate': 0.0,
                'validation_results': []
            },
            'resource_usage': {
                'peak_memory_mb': 0,
                'cpu_time_seconds': 0.0
            },
            'output_files': {
                'trajectory_file': None,
                'log_file': None
            }
        }

        start_time = time.time()
        task_evaluator = None

        try:
            logger.info(f"🔧 为子任务 {subtask_index + 1} 创建独立执行环境")

            # 记录实例创建开始时间
            instance_start_time = time.time()

            # 设置环境变量，防止TaskEvaluator创建自己的输出目录和重复日志
            os.environ['SCENARIO_OUTPUT_DIR'] = subtask_output_dir
            os.environ['DISABLE_AUTO_OUTPUT_DIR'] = 'true'
            os.environ['DISABLE_SUBTASK_LOGGING'] = 'true'  # 禁用子任务独立日志

            # 创建独立的TaskEvaluator实例
            subtask_suffix = f"subtask_{subtask_index:03d}"
            task_evaluator = TaskEvaluator(
                config_file=self.config_file,
                agent_type=self.agent_type,
                task_type='independent',  # 使用independent模式，但实际上会被单独处理
                scenario_id=f"{self.scenario_id}_{subtask_suffix}",  # 为每个子任务提供唯一的scenario_id
                custom_suffix=None  # 不使用后缀，避免自动生成独立目录
            )

            # 清理环境变量
            if 'SCENARIO_OUTPUT_DIR' in os.environ:
                del os.environ['SCENARIO_OUTPUT_DIR']
            if 'DISABLE_AUTO_OUTPUT_DIR' in os.environ:
                del os.environ['DISABLE_AUTO_OUTPUT_DIR']
            if 'DISABLE_SUBTASK_LOGGING' in os.environ:
                del os.environ['DISABLE_SUBTASK_LOGGING']

            # 强制设置子任务专用的输出目录
            task_evaluator.output_dir = subtask_output_dir
            task_evaluator.run_name = subtask_dir_name

            # 记录实例创建时间
            instance_creation_time = time.time() - instance_start_time
            subtask_result['execution_info']['instance_creation_time'] = instance_creation_time

            logger.info(f"✅ 独立执行环境创建完成 ({instance_creation_time:.2f}秒)")

            # 初始化独立环境
            if not self._initialize_isolated_environment(task_evaluator, task_info, subtask):
                raise RuntimeError("独立环境初始化失败")

            # 执行子任务
            execution_result = self._run_subtask_in_isolated_environment(
                task_evaluator, subtask, subtask_index
            )

            # 更新结果
            subtask_result['result'].update(execution_result)

            # 记录输出文件
            if hasattr(task_evaluator, 'trajectory_recorder'):
                subtask_result['output_files']['trajectory_file'] = \
                    os.path.relpath(task_evaluator.trajectory_recorder.trajectory_file, self.output_dir)
                subtask_result['output_files']['log_file'] = \
                    os.path.relpath(task_evaluator.trajectory_recorder.log_file, self.output_dir)

            logger.info(f"✅ 子任务 {subtask_index + 1} 执行完成")

        except Exception as e:
            logger.exception(f"❌ 子任务 {subtask_index + 1} 执行失败: {e}")
            subtask_result['result']['error'] = str(e)

        finally:
            # 清理资源
            cleanup_start_time = time.time()
            self._cleanup_subtask_resources(task_evaluator)
            cleanup_time = time.time() - cleanup_start_time
            subtask_result['execution_info']['cleanup_time'] = cleanup_time

            # 记录总执行时间
            total_duration = time.time() - start_time
            subtask_result['execution_info']['duration'] = total_duration
            subtask_result['execution_info']['end_time'] = datetime.now().isoformat()

            # 记录输出目录（用于聚合）
            subtask_result['execution_info']['output_dir'] = subtask_output_dir

            logger.info(f"🧹 子任务 {subtask_index + 1} 资源清理完成 ({cleanup_time:.2f}秒)")

        return subtask_result

    def _initialize_isolated_environment(self, task_evaluator: TaskEvaluator,
                                       task_info: Dict[str, Any], subtask: Dict[str, Any]) -> bool:
        """
        初始化独立的执行环境

        Args:
            task_evaluator: TaskEvaluator实例
            task_info: 完整的任务信息
            subtask: 当前子任务数据

        Returns:
            bool: 是否成功初始化
        """
        try:
            # 初始化场景
            if not task_evaluator.initialize_scenario(self.scenario_id):
                logger.error("❌ 场景初始化失败")
                return False

            # 初始化智能体
            if not task_evaluator.initialize_agents():
                logger.error("❌ 智能体初始化失败")
                return False

            # 创建只包含当前子任务的任务信息
            single_task_info = {
                'task_background': task_info.get('task_background', ''),
                'tasks': [subtask],  # 只包含当前子任务
                'scene_id': self.scenario_id,
                'agents_config': task_info.get('agents_config', [])
            }

            # 设置任务信息到轨迹记录器
            if hasattr(task_evaluator, 'trajectory_recorder'):
                task_evaluator.trajectory_recorder.set_task_info(single_task_info)
                task_evaluator.trajectory_recorder.set_evaluation_mode('independent')

            # 更新任务验证器
            task_evaluator._update_task_verifier(single_task_info)

            logger.info("✅ 独立环境初始化完成")
            return True

        except Exception as e:
            logger.exception(f"❌ 独立环境初始化失败: {e}")
            return False

    def _run_subtask_in_isolated_environment(self, task_evaluator: TaskEvaluator,
                                           subtask: Dict[str, Any], subtask_index: int) -> Dict[str, Any]:
        """
        在独立环境中运行子任务

        Args:
            task_evaluator: TaskEvaluator实例
            subtask: 子任务数据
            subtask_index: 子任务索引

        Returns:
            Dict: 执行结果
        """
        try:
            # 开始任务记录
            if hasattr(task_evaluator, 'trajectory_recorder'):
                task_evaluator.trajectory_recorder.start_task(
                    subtask_index + 1,
                    subtask.get('task_description', ''),
                    'independent_subtask'
                )

            # 获取配置参数
            max_steps_per_task = self.config.get('task_evaluator', {}).get('max_steps_per_task', 30)
            max_total_steps = self.config.get('execution', {}).get('max_total_steps', 300)

            # 执行子任务（使用TaskEvaluator的单任务执行方法）
            task_result = task_evaluator._execute_single_task(
                subtask, subtask_index + 1, max_steps_per_task, max_total_steps
            )

            # 记录任务完成情况
            if hasattr(task_evaluator, 'trajectory_recorder'):
                task_evaluator.trajectory_recorder.record_task_completion(task_result['completed'])
                task_evaluator.trajectory_recorder.end_task()

            # 返回标准化的结果
            return {
                'status': 'success' if task_result['completed'] else 'failed',
                'steps_taken': task_result['steps_taken'],
                'completion_rate': 1.0 if task_result['completed'] else 0.0,
                'validation_results': task_result.get('validation_results', [])
            }

        except Exception as e:
            logger.exception(f"❌ 子任务执行失败: {e}")
            return {
                'status': 'failed',
                'steps_taken': 0,
                'completion_rate': 0.0,
                'validation_results': [],
                'error': str(e)
            }

    def _cleanup_subtask_resources(self, task_evaluator: Optional[TaskEvaluator]):
        """
        清理子任务资源

        Args:
            task_evaluator: TaskEvaluator实例（可能为None）
        """
        try:
            if task_evaluator is not None:
                # 清理模拟器连接
                if hasattr(task_evaluator, 'bridge') and task_evaluator.bridge:
                    try:
                        if hasattr(task_evaluator.bridge, 'disconnect'):
                            task_evaluator.bridge.disconnect()
                        elif hasattr(task_evaluator.bridge, 'close'):
                            task_evaluator.bridge.close()
                    except Exception as e:
                        logger.warning(f"⚠️ 清理模拟器连接时出错: {e}")

                # 清理其他资源
                if hasattr(task_evaluator, 'agents'):
                    task_evaluator.agents.clear()

                # 删除引用
                del task_evaluator

            # 强制垃圾回收（如果启用）
            if self.force_garbage_collection:
                gc.collect()

        except Exception as e:
            logger.warning(f"⚠️ 资源清理时出错: {e}")

    def _calculate_final_statistics(self):
        """计算最终统计数据"""
        summary = self.aggregated_results['aggregated_summary']

        # 计算完成率
        if summary['total_subtasks'] > 0:
            summary['completion_rate'] = summary['completed_subtasks'] / summary['total_subtasks']

        # 计算平均执行时间
        if summary['total_subtasks'] > 0:
            total_duration = sum(
                result['execution_info']['duration']
                for result in self.aggregated_results['subtask_results']
            )
            summary['average_subtask_duration'] = total_duration / summary['total_subtasks']

        # 按类别统计性能
        category_stats = {}
        for result in self.aggregated_results['subtask_results']:
            category = result['task_category']
            if category not in category_stats:
                category_stats[category] = {'total': 0, 'completed': 0, 'rate': 0.0}

            category_stats[category]['total'] += 1
            if result['result']['status'] == 'success':
                category_stats[category]['completed'] += 1

        # 计算各类别完成率
        for category, stats in category_stats.items():
            if stats['total'] > 0:
                stats['rate'] = stats['completed'] / stats['total']

        summary['category_performance'] = category_stats

    def _log_final_summary(self):
        """记录最终摘要"""
        summary = self.aggregated_results['aggregated_summary']

        logger.info("📊 独立评测结果摘要:")
        logger.info(f"  - 总子任务数: {summary['total_subtasks']}")
        logger.info(f"  - 完成子任务数: {summary['completed_subtasks']}")
        logger.info(f"  - 失败子任务数: {summary['failed_subtasks']}")
        logger.info(f"  - 完成率: {summary['completion_rate']:.1%}")
        logger.info(f"  - 总步数: {summary['total_steps']}")
        logger.info(f"  - 总执行时间: {summary['total_execution_time']:.2f}秒")
        logger.info(f"  - 平均子任务时间: {summary['average_subtask_duration']:.2f}秒")

        # 按类别显示统计
        if summary['category_performance']:
            logger.info("📈 按类别统计:")
            for category, stats in summary['category_performance'].items():
                logger.info(f"  - {category}: {stats['completed']}/{stats['total']} ({stats['rate']:.1%})")

    def save_aggregated_results(self, output_file: str = None) -> str:
        """
        保存聚合结果到文件

        Args:
            output_file: 输出文件路径，如果为None则使用默认路径

        Returns:
            str: 保存的文件路径
        """
        if output_file is None:
            output_file = os.path.join(self.output_dir, 'independent_evaluation_results.json')

        try:
            import json
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.aggregated_results, f, ensure_ascii=False, indent=2)

            logger.info(f"📄 聚合结果已保存: {output_file}")
            return output_file

        except Exception as e:
            logger.exception(f"❌ 保存聚合结果失败: {e}")
            return ""

    def aggregate_compact_trajectories(self, main_trajectory_recorder) -> None:
        """
        聚合所有子任务的compact_trajectory到主轨迹文件中

        Args:
            main_trajectory_recorder: 主TaskEvaluator的轨迹记录器
        """
        try:
            logger.info("📋 开始聚合子任务的compact_trajectory数据")

            aggregated_tasks = []

            # 遍历所有子任务结果，收集compact_trajectory数据
            logger.debug(f"🔍 开始遍历 {len(self.subtask_results)} 个子任务结果")
            for i, subtask_result in enumerate(self.subtask_results):
                subtask_output_dir = subtask_result.get('execution_info', {}).get('output_dir')
                logger.debug(f"🔍 子任务 {i+1} 输出目录: {subtask_output_dir}")

                if not subtask_output_dir or not os.path.exists(subtask_output_dir):
                    logger.debug(f"⚠️ 子任务 {i+1} 输出目录不存在或为空")
                    continue

                # 子任务的compact_trajectory文件路径
                # 每个子任务都有唯一的scenario_id，格式为：原scenario_id_subtask_xxx
                subtask_index = subtask_result.get('subtask_index', i+1)
                subtask_scenario_id = f"{self.scenario_id}_subtask_{subtask_index:03d}"
                compact_trajectory_file = os.path.join(subtask_output_dir, 'trajectories', f'{subtask_scenario_id}_compact_trajectory.json')
                logger.debug(f"🔍 查找轨迹文件: {compact_trajectory_file}")

                if os.path.exists(compact_trajectory_file):
                    logger.debug(f"✅ 找到轨迹文件: {compact_trajectory_file}")
                    try:
                        with open(compact_trajectory_file, 'r', encoding='utf-8') as f:
                            subtask_compact_trajectory = json.load(f)

                        # 提取子任务的轨迹数据
                        subtask_executions = subtask_compact_trajectory.get('task_executions', [])
                        logger.debug(f"📊 子任务 {i+1} 包含 {len(subtask_executions)} 个任务执行记录")

                        for task in subtask_executions:
                            # 为每个任务添加子任务索引信息
                            task['subtask_index'] = subtask_result.get('subtask_index', i+1)
                            task['subtask_output_dir'] = os.path.basename(subtask_output_dir)
                            aggregated_tasks.append(task)

                    except Exception as e:
                        logger.warning(f"⚠️ 读取子任务compact_trajectory失败: {compact_trajectory_file}, 错误: {e}")
                else:
                    logger.debug(f"❌ 轨迹文件不存在: {compact_trajectory_file}")

            # 更新主轨迹记录器的compact_trajectory
            if aggregated_tasks:
                main_trajectory_recorder.compact_trajectory['task_executions'] = aggregated_tasks
                logger.info(f"✅ 成功聚合了 {len(aggregated_tasks)} 个子任务的轨迹数据")
            else:
                logger.warning("⚠️ 没有找到可聚合的子任务轨迹数据")

        except Exception as e:
            logger.exception(f"❌ 聚合compact_trajectory失败: {e}")
