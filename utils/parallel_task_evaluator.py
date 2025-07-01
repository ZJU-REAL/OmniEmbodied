#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并行任务评测器
支持多个任务的并行评测，每个任务使用完全独立的模拟器实例
"""

import os
import sys
import time
import copy
import json
import logging
import threading
import multiprocessing
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Tuple

from config import ConfigManager
from utils.task_evaluator import TaskEvaluator
from utils.run_naming import RunNamingManager
from utils.data_loader import DataLoader

logger = logging.getLogger(__name__)


class ParallelTaskEvaluator:
    """
    并行任务评测器 - 支持多个任务的并行评测
    每个任务使用完全独立的模拟器实例，确保完全隔离
    """

    def __init__(self, config_file: str, agent_type: str, task_type: str,
                 scenario_id: str = None, custom_suffix: str = None):
        """
        初始化并行评测器

        Args:
            config_file: 配置文件名
            agent_type: 智能体类型 ('single' 或 'multi')
            task_type: 任务类型 ('sequential', 'combined', 'independent')
            scenario_id: 场景ID
            custom_suffix: 自定义后缀
        """
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config(config_file)
        self.config_file = config_file
        self.agent_type = agent_type
        self.task_type = task_type
        
        # 从配置文件读取默认值
        eval_config = self.config.get('evaluation', {})
        run_settings = eval_config.get('run_settings', {})
        
        self.scenario_id = scenario_id or eval_config.get('default_scenario', '00001')
        self.custom_suffix = custom_suffix or run_settings.get('default_suffix', 'parallel')
        
        # 并行评测配置
        self.parallel_config = self.config.get('parallel_evaluation', {})
        if not self.parallel_config.get('enabled', False):
            raise ValueError("并行评测未启用，请在配置文件中设置 parallel_evaluation.enabled = true")
        
        # 并行执行参数
        self.execution_mode = self.parallel_config.get('execution_mode', 'thread')
        self.max_parallel_tasks = self.parallel_config.get('max_parallel_tasks', 4)
        if self.max_parallel_tasks == 0:
            self.max_parallel_tasks = multiprocessing.cpu_count()
        
        self.startup_delay = self.parallel_config.get('startup_delay', 2.0)
        self.task_timeout = self.parallel_config.get('task_timeout', 1800)
        
        # 故障处理配置
        failure_config = self.parallel_config.get('failure_handling', {})
        self.continue_on_failure = failure_config.get('continue_on_task_failure', True)
        self.max_retries = failure_config.get('max_retries', 1)
        self.retry_delay = failure_config.get('retry_delay', 5.0)
        
        # 生成运行名称和输出目录
        self.run_name = RunNamingManager.generate_run_name(
            agent_type=self.agent_type,
            task_type=f"parallel_{self.task_type}",
            scenario_id=self.scenario_id,
            config_name=self.config_file,
            custom_suffix=self.custom_suffix
        )
        
        # 创建主输出目录
        base_output_dir = self.config.get('output_dir', 'output')
        self.output_dir = RunNamingManager.generate_output_directory(base_output_dir, self.run_name)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 设置主日志文件
        self.main_log_file = os.path.join(self.output_dir, "parallel_execution.log")
        self._setup_main_logger()
        
        # 数据加载器
        self.data_loader = DataLoader()
        
        # 结果收集
        self.results = {
            'run_info': {
                'run_name': self.run_name,
                'start_time': None,
                'end_time': None,
                'total_duration': 0,
                'parallel_config': self.parallel_config
            },
            'task_results': [],
            'summary': {
                'total_tasks': 0,
                'completed_tasks': 0,
                'failed_tasks': 0,
                'average_duration': 0,
                'parallel_efficiency': 0
            }
        }
        
        # 线程安全锁
        self.results_lock = threading.Lock()
        
        logger.info(f"🚀 并行任务评测器初始化完成")
        logger.info(f"📁 输出目录: {self.output_dir}")
        logger.info(f"⚙️ 并行模式: {self.execution_mode}, 最大并行数: {self.max_parallel_tasks}")

    def _setup_main_logger(self):
        """设置主日志记录器"""
        # 创建文件处理器
        file_handler = logging.FileHandler(self.main_log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # 添加到根日志记录器
        logging.getLogger().addHandler(file_handler)

    def _select_tasks(self, all_tasks: List[Dict]) -> List[Dict]:
        """
        根据配置选择要评测的任务

        Args:
            all_tasks: 所有任务列表

        Returns:
            List[Dict]: 选择的任务列表
        """
        selection_config = self.parallel_config.get('task_selection', {})
        mode = selection_config.get('mode', 'all')
        
        if mode == 'all':
            selected_tasks = all_tasks
        elif mode == 'range':
            range_config = selection_config.get('range', {})
            start = range_config.get('start_index', 0)
            end = range_config.get('end_index', -1)
            if end == -1:
                selected_tasks = all_tasks[start:]
            else:
                selected_tasks = all_tasks[start:end]
        elif mode == 'list':
            indices = selection_config.get('task_indices', [])
            selected_tasks = [all_tasks[i] for i in indices if 0 <= i < len(all_tasks)]
        elif mode == 'category':
            categories = selection_config.get('categories', [])
            selected_tasks = [task for task in all_tasks 
                            if task.get('task_category') in categories]
        else:
            raise ValueError(f"不支持的任务选择模式: {mode}")
        
        logger.info(f"📋 任务选择模式: {mode}, 选中 {len(selected_tasks)}/{len(all_tasks)} 个任务")
        return selected_tasks

    def _filter_tasks_by_agent_type(self, tasks: List[Dict]) -> List[Dict]:
        """
        根据智能体类型过滤任务

        Args:
            tasks: 任务列表

        Returns:
            List[Dict]: 过滤后的任务列表
        """
        if self.agent_type == 'single':
            # 单智能体模式：排除协作任务
            collaboration_categories = [
                'explicit_collaboration', 
                'implicit_collaboration', 
                'compound_collaboration'
            ]
            filtered_tasks = [task for task in tasks 
                            if task.get('task_category') not in collaboration_categories]
            
            logger.info(f"🤖 单智能体模式：过滤掉 {len(tasks) - len(filtered_tasks)} 个协作任务")
            return filtered_tasks
        else:
            # 多智能体模式：保留所有任务
            logger.info(f"🤖 多智能体模式：保留所有 {len(tasks)} 个任务")
            return tasks

    def _execute_single_task(self, task_info: Tuple[int, Dict, str]) -> Dict[str, Any]:
        """
        执行单个任务（在独立线程/进程中运行）

        Args:
            task_info: (任务索引, 任务数据, 任务输出目录) 的元组

        Returns:
            Dict: 任务执行结果
        """
        task_index, task_data, task_output_dir = task_info
        task_id = f"task_{task_index:05d}"

        # 创建任务专用的日志记录器
        task_logger = logging.getLogger(f"parallel_task_{task_id}")
        task_log_file = os.path.join(task_output_dir, f"{task_id}_execution.log")

        # 设置任务日志处理器
        task_handler = logging.FileHandler(task_log_file, encoding='utf-8')
        task_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        task_handler.setFormatter(formatter)
        task_logger.addHandler(task_handler)
        task_logger.setLevel(logging.DEBUG)

        start_time = time.time()
        result = {
            'task_id': task_id,
            'task_index': task_index,
            'task_description': task_data.get('task_description', ''),
            'task_category': task_data.get('task_category', ''),
            'status': 'running',
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'duration': 0,
            'success_rate': 0.0,
            'error': None,
            'output_dir': task_output_dir,
            'retry_count': 0
        }

        try:
            task_logger.info(f"🚀 开始执行任务 {task_id}: {task_data.get('task_description', '')}")

            # 添加启动延迟，避免同时初始化造成资源竞争
            if task_index > 0:
                delay = self.startup_delay * (task_index % 3)  # 错开启动时间
                task_logger.info(f"⏱️ 启动延迟 {delay:.1f} 秒")
                time.sleep(delay)

            # 执行任务（带重试机制）
            for retry in range(self.max_retries + 1):
                try:
                    result['retry_count'] = retry
                    if retry > 0:
                        task_logger.info(f"🔄 第 {retry} 次重试")
                        time.sleep(self.retry_delay)

                    # 创建完全独立的任务评测器实例
                    task_result = self._run_isolated_task(task_data, task_output_dir, task_logger)

                    # 更新结果
                    result.update(task_result)
                    result['status'] = 'completed' if task_result.get('success', False) else 'failed'
                    break

                except Exception as e:
                    task_logger.exception(f"❌ 任务执行失败 (尝试 {retry + 1}/{self.max_retries + 1}): {e}")
                    if retry == self.max_retries:
                        result['status'] = 'failed'
                        result['error'] = str(e)

        except Exception as e:
            task_logger.exception(f"❌ 任务执行出现严重错误: {e}")
            result['status'] = 'failed'
            result['error'] = str(e)

        finally:
            # 计算执行时间
            result['end_time'] = datetime.now().isoformat()
            result['duration'] = time.time() - start_time

            task_logger.info(f"✅ 任务 {task_id} 执行完成，状态: {result['status']}, 耗时: {result['duration']:.2f}秒")

            # 清理任务日志处理器
            task_logger.removeHandler(task_handler)
            task_handler.close()

        return result

    def _run_isolated_task(self, task_data: Dict, task_output_dir: str, task_logger) -> Dict[str, Any]:
        """
        在完全隔离的环境中运行单个任务

        Args:
            task_data: 任务数据
            task_output_dir: 任务输出目录
            task_logger: 任务专用日志记录器

        Returns:
            Dict: 任务执行结果
        """
        # 创建任务专用的配置副本（深拷贝确保完全隔离）
        task_config = copy.deepcopy(self.config)

        # 为任务创建独立的TaskEvaluator实例
        # 每个TaskEvaluator会创建自己的模拟器实例，确保完全隔离
        task_evaluator = TaskEvaluator(
            config_file=self.config_file,
            agent_type=self.agent_type,
            task_type='independent',  # 使用独立模式执行单个任务
            scenario_id=self.scenario_id,
            custom_suffix=f"task_{hash(task_data.get('task_description', '')) % 10000}"
        )

        # 设置任务专用的输出目录
        task_evaluator.output_dir = task_output_dir
        task_evaluator.run_name = os.path.basename(task_output_dir)

        try:
            # 初始化场景（每个任务都有独立的模拟器实例）
            if not task_evaluator.initialize_scenario(self.scenario_id):
                raise RuntimeError("场景初始化失败")

            # 初始化智能体
            if not task_evaluator.initialize_agents():
                raise RuntimeError("智能体初始化失败")

            # 获取完整的任务信息
            task_info = task_evaluator.bridge.get_task_info()
            if not task_info:
                raise RuntimeError("无法获取任务信息")

            # 创建只包含当前任务的任务信息
            single_task_info = {
                'task_background': task_info.get('task_background', ''),
                'tasks': [task_data],  # 只包含当前任务
                'scene_id': self.scenario_id,
                'agents_config': task_info.get('agents_config', [])
            }

            # 手动设置任务信息到轨迹记录器
            task_evaluator.trajectory_recorder.set_task_info(single_task_info)
            task_evaluator.trajectory_recorder.set_evaluation_mode('independent')

            # 更新任务验证器
            task_evaluator._update_task_verifier(single_task_info)

            # 直接运行新的独立评测模式
            task_evaluator._run_independent_evaluation(single_task_info)

            # 提取结果
            results = task_evaluator.results
            success = results.get('summary', {}).get('completed_tasks', 0) > 0
            success_rate = results.get('summary', {}).get('completion_rate', 0.0)

            return {
                'success': success,
                'success_rate': success_rate,
                'evaluation_result': results,
                'steps_taken': results.get('summary', {}).get('total_steps', 0)
            }

        except Exception as e:
            task_logger.exception(f"❌ 隔离任务执行失败: {e}")
            raise

        finally:
            # 确保清理资源
            try:
                if hasattr(task_evaluator, 'bridge') and task_evaluator.bridge:
                    # 尝试清理模拟器连接
                    if hasattr(task_evaluator.bridge, 'disconnect'):
                        task_evaluator.bridge.disconnect()
                    elif hasattr(task_evaluator.bridge, 'close'):
                        task_evaluator.bridge.close()
            except Exception as e:
                task_logger.warning(f"⚠️ 清理任务资源时出错: {e}")

    def run_parallel_evaluation(self) -> Dict[str, Any]:
        """
        运行并行评测

        Returns:
            Dict: 并行评测结果
        """
        logger.info(f"🚀 开始并行任务评测 - 模式: {self.agent_type}_{self.task_type}")
        logger.info(f"🏃 运行名称: {self.run_name}")

        self.results['run_info']['start_time'] = datetime.now().isoformat()
        start_time = time.time()

        try:
            # 加载任务数据
            task_data = self.data_loader.load_task(f"{self.scenario_id}_task")
            if not task_data:
                raise RuntimeError(f"无法加载任务数据: {self.scenario_id}_task")

            all_tasks = task_data.get('tasks', [])
            if not all_tasks:
                raise RuntimeError("任务数据中没有找到任务列表")

            # 根据智能体类型过滤任务
            filtered_tasks = self._filter_tasks_by_agent_type(all_tasks)

            # 根据配置选择任务
            selected_tasks = self._select_tasks(filtered_tasks)

            if not selected_tasks:
                raise RuntimeError("没有选择到任何任务进行评测")

            self.results['summary']['total_tasks'] = len(selected_tasks)

            # 准备任务信息列表
            task_infos = []
            for i, task in enumerate(selected_tasks):
                task_output_dir = os.path.join(self.output_dir, f"task_{i:05d}")
                os.makedirs(task_output_dir, exist_ok=True)
                task_infos.append((i, task, task_output_dir))

            logger.info(f"📋 准备并行执行 {len(task_infos)} 个任务")

            # 执行并行评测
            if self.execution_mode == 'process':
                executor_class = ProcessPoolExecutor
            else:
                executor_class = ThreadPoolExecutor

            with executor_class(max_workers=self.max_parallel_tasks) as executor:
                # 提交所有任务
                future_to_task = {
                    executor.submit(self._execute_single_task, task_info): task_info[0]
                    for task_info in task_infos
                }

                # 收集结果
                completed_count = 0
                failed_count = 0

                for future in as_completed(future_to_task, timeout=self.task_timeout):
                    task_index = future_to_task[future]

                    try:
                        task_result = future.result()

                        # 线程安全地更新结果
                        with self.results_lock:
                            self.results['task_results'].append(task_result)

                            if task_result['status'] == 'completed':
                                completed_count += 1
                                self.results['summary']['completed_tasks'] = completed_count
                            else:
                                failed_count += 1
                                self.results['summary']['failed_tasks'] = failed_count

                        logger.info(f"✅ 任务 {task_index} 完成: {task_result['status']}")

                    except Exception as e:
                        logger.exception(f"❌ 任务 {task_index} 执行异常: {e}")

                        # 记录失败任务
                        with self.results_lock:
                            failed_count += 1
                            self.results['summary']['failed_tasks'] = failed_count

                            self.results['task_results'].append({
                                'task_id': f"task_{task_index:05d}",
                                'task_index': task_index,
                                'status': 'failed',
                                'error': str(e),
                                'duration': 0
                            })

                        if not self.continue_on_failure:
                            logger.error("❌ 任务失败且配置为不继续执行，停止并行评测")
                            break

        except Exception as e:
            logger.exception(f"❌ 并行评测执行失败: {e}")
            self.results['error'] = str(e)

        finally:
            # 完成评测
            self.results['run_info']['end_time'] = datetime.now().isoformat()
            self.results['run_info']['total_duration'] = time.time() - start_time

            # 计算统计信息
            self._calculate_summary_statistics()

            # 保存结果
            self._save_parallel_results()

            logger.info(f"🎯 并行评测完成")
            logger.info(f"📊 总任务数: {self.results['summary']['total_tasks']}")
            logger.info(f"✅ 完成任务: {self.results['summary']['completed_tasks']}")
            logger.info(f"❌ 失败任务: {self.results['summary']['failed_tasks']}")
            logger.info(f"⏱️ 总耗时: {self.results['run_info']['total_duration']:.2f}秒")
            logger.info(f"📈 并行效率: {self.results['summary']['parallel_efficiency']:.2f}")

        return self.results

    def _calculate_summary_statistics(self):
        """计算汇总统计信息"""
        task_results = self.results['task_results']

        if not task_results:
            return

        # 计算平均执行时间
        total_duration = sum(result.get('duration', 0) for result in task_results)
        self.results['summary']['average_duration'] = total_duration / len(task_results)

        # 计算并行效率（理论上串行执行时间 vs 实际并行执行时间）
        theoretical_serial_time = total_duration
        actual_parallel_time = self.results['run_info']['total_duration']

        if actual_parallel_time > 0:
            self.results['summary']['parallel_efficiency'] = theoretical_serial_time / actual_parallel_time
        else:
            self.results['summary']['parallel_efficiency'] = 0

        # 计算成功率
        completed_tasks = self.results['summary']['completed_tasks']
        total_tasks = self.results['summary']['total_tasks']

        if total_tasks > 0:
            self.results['summary']['success_rate'] = completed_tasks / total_tasks
        else:
            self.results['summary']['success_rate'] = 0

    def _save_parallel_results(self):
        """保存并行评测结果"""
        try:
            # 保存详细结果
            results_file = os.path.join(self.output_dir, "parallel_results.json")
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)

            # 保存运行摘要
            summary_file = os.path.join(self.output_dir, "run_summary.json")
            summary_data = {
                'run_info': self.results['run_info'],
                'summary': self.results['summary'],
                'task_count_by_status': self._get_task_count_by_status(),
                'task_count_by_category': self._get_task_count_by_category()
            }

            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, ensure_ascii=False, indent=2)

            logger.info(f"📊 并行评测结果已保存: {results_file}")
            logger.info(f"📋 运行摘要已保存: {summary_file}")

        except Exception as e:
            logger.exception(f"❌ 保存并行评测结果失败: {e}")

    def _get_task_count_by_status(self) -> Dict[str, int]:
        """获取按状态分组的任务数量统计"""
        status_counts = {}
        for result in self.results['task_results']:
            status = result.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        return status_counts

    def _get_task_count_by_category(self) -> Dict[str, int]:
        """获取按类别分组的任务数量统计"""
        category_counts = {}
        for result in self.results['task_results']:
            category = result.get('task_category', 'unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
        return category_counts
