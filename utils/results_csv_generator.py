#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV结果生成器
支持为不同评测模式生成相应格式的CSV统计文件
"""

import os
import csv
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ResultsCSVGenerator:
    """
    CSV结果生成器
    根据评测模式生成相应格式的CSV统计文件
    """
    
    def __init__(self, output_dir: str):
        """
        初始化CSV生成器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        
    def generate_csv(self, results: Dict[str, Any], evaluation_type: str, 
                    csv_filename: str = 'run_summary.csv') -> str:
        """
        根据评测类型生成相应的CSV文件
        
        Args:
            results: 评测结果数据
            evaluation_type: 评测类型 ('sequential', 'combined', 'independent')
            csv_filename: CSV文件名
            
        Returns:
            str: 生成的CSV文件路径
        """
        csv_path = os.path.join(self.output_dir, csv_filename)
        
        try:
            if evaluation_type in ['sequential', 'combined']:
                return self._generate_scenario_level_csv(results, csv_path, evaluation_type)
            elif evaluation_type == 'independent':
                return self._generate_subtask_level_csv(results, csv_path)
            else:
                raise ValueError(f"不支持的评测类型: {evaluation_type}")
                
        except Exception as e:
            logger.exception(f"❌ 生成CSV文件失败: {e}")
            return ""
    
    def _generate_scenario_level_csv(self, results: Dict[str, Any], csv_path: str, 
                                   evaluation_type: str) -> str:
        """
        为sequential/combined模式生成场景级CSV

        CSV格式:
        scenario_id,task_category,agent_type,evaluation_type,total_tasks,completed_tasks,failed_tasks,completion_rate,total_steps,average_steps_per_task,duration_seconds
        """
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'scenario_id', 'task_category', 'agent_type', 'evaluation_type', 'total_tasks', 'completed_tasks',
                    'failed_tasks', 'completion_rate', 'total_steps',
                    'average_steps_per_task', 'duration_seconds'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                # 处理场景结果
                scenario_results = results.get('scenario_results', [])
                for scenario_result in scenario_results:
                    scenario_id = scenario_result.get('scenario_id', 'unknown')
                    summary = scenario_result.get('summary', {})

                    # 获取任务类别和智能体类型信息
                    task_category = self._get_task_category_from_scenario(scenario_result)
                    agent_type = self._determine_agent_type_from_scenario(scenario_result)

                    total_tasks = summary.get('total_tasks', 0)
                    completed_tasks = summary.get('completed_tasks', 0)
                    failed_tasks = summary.get('failed_tasks', 0)
                    completion_rate = summary.get('completion_rate', 0.0)
                    total_steps = summary.get('total_steps', 0)
                    average_steps = summary.get('average_steps_per_task', 0.0)
                    duration = scenario_result.get('total_duration', 0.0)
                    
                    writer.writerow({
                        'scenario_id': scenario_id,
                        'task_category': task_category,
                        'agent_type': agent_type,
                        'evaluation_type': evaluation_type,
                        'total_tasks': total_tasks,
                        'completed_tasks': completed_tasks,
                        'failed_tasks': failed_tasks,
                        'completion_rate': round(completion_rate, 3),
                        'total_steps': total_steps,
                        'average_steps_per_task': round(average_steps, 1),
                        'duration_seconds': round(duration, 1)
                    })
            
            logger.info(f"📊 场景级CSV文件已生成: {csv_path}")
            return csv_path
            
        except Exception as e:
            logger.exception(f"❌ 生成场景级CSV失败: {e}")
            return ""
    
    def _generate_subtask_level_csv(self, results: Dict[str, Any], csv_path: str) -> str:
        """
        为independent模式生成子任务级CSV
        
        CSV格式:
        scenario_id,subtask_index,subtask_id,task_description,task_category,status,completion_rate,steps_taken,duration_seconds
        """
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'scenario_id', 'subtask_index', 'subtask_id', 'task_description',
                    'task_category', 'agent_type', 'status', 'completion_rate', 'steps_taken',
                    'duration_seconds'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                # 处理场景结果
                scenario_results = results.get('scenario_results', [])
                for scenario_result in scenario_results:
                    scenario_id = scenario_result.get('scenario_id', 'unknown')
                    
                    # 获取子任务结果
                    subtask_results = scenario_result.get('subtask_results', [])
                    for subtask_result in subtask_results:
                        subtask_index = subtask_result.get('subtask_index', 0)
                        subtask_id = subtask_result.get('subtask_id', f'subtask_{subtask_index:03d}')
                        task_description = subtask_result.get('subtask_description', '')
                        task_category = subtask_result.get('task_category', 'unknown')

                        # 获取智能体类型信息
                        agent_type = self._determine_agent_type_from_scenario(scenario_result)

                        # 获取执行结果
                        result_info = subtask_result.get('result', {})
                        status = 'completed' if result_info.get('status') == 'success' else 'failed'
                        completion_rate = result_info.get('completion_rate', 0.0)
                        steps_taken = result_info.get('steps_taken', 0)
                        
                        # 获取执行时间
                        execution_info = subtask_result.get('execution_info', {})
                        duration = execution_info.get('duration', 0.0)
                        
                        writer.writerow({
                            'scenario_id': scenario_id,
                            'subtask_index': subtask_index,
                            'subtask_id': subtask_id,
                            'task_description': task_description,
                            'task_category': task_category,
                            'agent_type': agent_type,
                            'status': status,
                            'completion_rate': round(completion_rate, 3),
                            'steps_taken': steps_taken,
                            'duration_seconds': round(duration, 1)
                        })
            
            logger.info(f"📊 子任务级CSV文件已生成: {csv_path}")
            return csv_path
            
        except Exception as e:
            logger.exception(f"❌ 生成子任务级CSV失败: {e}")
            return ""

    def _determine_agent_type_from_scenario(self, scenario_result: Dict[str, Any]) -> str:
        """
        从场景结果中确定智能体类型

        Args:
            scenario_result: 场景结果数据

        Returns:
            str: 智能体类型 ('single_agent' 或 'multi_agent')
        """
        # 方法1: 从scenario_id推断（基于任务配置）
        scenario_id = scenario_result.get('scenario_id', '')
        if scenario_id:
            try:
                # 尝试加载任务配置
                from utils.data_loader import default_loader
                task_data = default_loader.load_task(scenario_id)
                if task_data:
                    agents_config = task_data.get('agents_config', [])
                    # 如果配置了多个智能体，则为多智能体任务
                    if len(agents_config) > 1:
                        return 'multi_agent'
                    else:
                        return 'single_agent'
            except Exception:
                pass

        # 方法2: 从任务类别推断（如果有协作类任务，则为多智能体）
        subtask_results = scenario_result.get('subtask_results', [])
        for subtask in subtask_results:
            task_category = subtask.get('task_category', '')
            if 'collaboration' in task_category:
                return 'multi_agent'

        # 默认返回单智能体
        return 'single_agent'

    def _get_task_category_from_scenario(self, scenario_result: Dict[str, Any]) -> str:
        """
        从场景结果中获取任务类别

        Args:
            scenario_result: 场景结果数据

        Returns:
            str: 任务类别
        """
        # 方法1: 从子任务结果中获取任务类别
        subtask_results = scenario_result.get('subtask_results', [])
        if subtask_results:
            # 取第一个子任务的类别作为整个场景的类别
            first_subtask = subtask_results[0]
            task_category = first_subtask.get('task_category', 'unknown')
            if task_category != 'unknown':
                return task_category

        # 方法2: 从scenario_id推断（基于任务配置）
        scenario_id = scenario_result.get('scenario_id', '')
        if scenario_id:
            try:
                # 尝试加载任务配置
                from utils.data_loader import default_loader
                task_data = default_loader.load_task(scenario_id)
                if task_data and 'tasks' in task_data:
                    tasks = task_data['tasks']
                    if tasks:
                        # 返回第一个任务的类别
                        return tasks[0].get('task_category', 'unknown')
            except Exception:
                pass

        # 方法3: 尝试从汇总信息中获取
        summary = scenario_result.get('summary', {})
        task_category_stats = summary.get('task_category_stats', {})
        if task_category_stats:
            # 返回出现次数最多的任务类别
            most_common_category = max(task_category_stats.keys(), key=lambda k: task_category_stats[k])
            return most_common_category

        # 默认返回unknown
        return 'unknown'

    def generate_summary_report(self, results: Dict[str, Any], evaluation_type: str) -> str:
        """
        生成汇总报告
        
        Args:
            results: 评测结果数据
            evaluation_type: 评测类型
            
        Returns:
            str: 报告文件路径
        """
        report_path = os.path.join(self.output_dir, 'parallel_summary_report.txt')
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("并行评测汇总报告\n")
                f.write("=" * 60 + "\n\n")
                
                # 基本信息
                run_info = results.get('run_info', {})
                f.write(f"运行名称: {run_info.get('run_name', 'unknown')}\n")
                f.write(f"评测类型: {evaluation_type}\n")
                f.write(f"开始时间: {run_info.get('start_time', 'unknown')}\n")
                f.write(f"结束时间: {run_info.get('end_time', 'unknown')}\n")
                f.write(f"总耗时: {run_info.get('total_duration', 0):.1f} 秒\n\n")
                
                # 整体统计
                overall_summary = results.get('overall_summary', {})
                f.write("整体统计:\n")
                f.write("-" * 30 + "\n")
                f.write(f"总场景数: {overall_summary.get('total_scenarios', 0)}\n")
                f.write(f"成功场景数: {overall_summary.get('successful_scenarios', 0)}\n")
                f.write(f"失败场景数: {overall_summary.get('failed_scenarios', 0)}\n")
                f.write(f"场景成功率: {overall_summary.get('scenario_success_rate', 0):.1%}\n\n")
                
                if evaluation_type == 'independent':
                    f.write(f"总子任务数: {overall_summary.get('total_subtasks', 0)}\n")
                    f.write(f"成功子任务数: {overall_summary.get('successful_subtasks', 0)}\n")
                    f.write(f"子任务成功率: {overall_summary.get('subtask_success_rate', 0):.1%}\n\n")
                
                # 详细场景信息
                f.write("场景详情:\n")
                f.write("-" * 30 + "\n")
                scenario_results = results.get('scenario_results', [])
                for scenario_result in scenario_results:
                    scenario_id = scenario_result.get('scenario_id', 'unknown')
                    summary = scenario_result.get('summary', {})
                    duration = scenario_result.get('total_duration', 0)
                    
                    f.write(f"场景 {scenario_id}:\n")
                    f.write(f"  完成率: {summary.get('completion_rate', 0):.1%}\n")
                    f.write(f"  总步数: {summary.get('total_steps', 0)}\n")
                    f.write(f"  耗时: {duration:.1f} 秒\n\n")
            
            logger.info(f"📄 汇总报告已生成: {report_path}")
            return report_path
            
        except Exception as e:
            logger.exception(f"❌ 生成汇总报告失败: {e}")
            return ""
