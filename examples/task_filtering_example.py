#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务筛选评测示例 - 演示如何按任务类型筛选评测

这个示例展示了如何使用新的任务筛选功能来评测特定类型的任务。

主要功能：
1. 按任务类别筛选 (direct_command, attribute_reasoning, tool_use, spatial_reasoning)
2. 按智能体数量筛选 (single, multi)
3. 组合筛选条件

使用方法：
python examples/task_filtering_example.py --mode direct_command
python examples/task_filtering_example.py --mode single_agent_only
python examples/task_filtering_example.py --mode multi_agent_only
python examples/task_filtering_example.py --mode combined_filter
"""

import argparse
import logging
from typing import List, Dict, Any

# 使用标准导入方式
from evaluation.evaluation_interface import EvaluationInterface, run_filtered_evaluation
from utils.logger import setup_logger

logger = logging.getLogger(__name__)


def run_direct_command_evaluation() -> Dict[str, Any]:
    """只评测direct_command类型的任务"""
    logger.info("🎯 运行direct_command任务评测")
    
    return run_filtered_evaluation(
        config_file='single_agent_config',
        agent_type='single',
        task_type='sequential',
        scenarios='all',
        task_categories=['direct_command'],
        agent_count_filter='all',
        suffix='direct_command_only'
    )


def run_reasoning_tasks_evaluation() -> Dict[str, Any]:
    """只评测推理类任务"""
    logger.info("🧠 运行推理任务评测")
    
    return run_filtered_evaluation(
        config_file='single_agent_config',
        agent_type='single',
        task_type='sequential',
        scenarios='all',
        task_categories=['attribute_reasoning', 'spatial_reasoning'],
        agent_count_filter='all',
        suffix='reasoning_tasks'
    )


def run_single_agent_tasks_only() -> Dict[str, Any]:
    """只评测单智能体任务"""
    logger.info("👤 运行单智能体任务评测")
    
    return run_filtered_evaluation(
        config_file='single_agent_config',
        agent_type='single',
        task_type='sequential',
        scenarios='all',
        task_categories=None,  # 不限制任务类别
        agent_count_filter='single',
        suffix='single_agent_tasks_only'
    )


def run_multi_agent_tasks_only() -> Dict[str, Any]:
    """只评测多智能体任务"""
    logger.info("👥 运行多智能体任务评测")
    
    return run_filtered_evaluation(
        config_file='centralized_config',
        agent_type='multi',
        task_type='combined',
        scenarios='all',
        task_categories=None,  # 不限制任务类别
        agent_count_filter='multi',
        suffix='multi_agent_tasks_only'
    )


def run_combined_filter_evaluation() -> Dict[str, Any]:
    """组合筛选：只评测多智能体的direct_command任务"""
    logger.info("🔄 运行组合筛选评测")
    
    return run_filtered_evaluation(
        config_file='centralized_config',
        agent_type='multi',
        task_type='combined',
        scenarios='all',
        task_categories=['direct_command'],
        agent_count_filter='multi',
        suffix='multi_agent_direct_command'
    )


def run_tool_use_evaluation() -> Dict[str, Any]:
    """只评测工具使用任务"""
    logger.info("🔧 运行工具使用任务评测")
    
    return run_filtered_evaluation(
        config_file='single_agent_config',
        agent_type='single',
        task_type='sequential',
        scenarios='all',
        task_categories=['tool_use'],
        agent_count_filter='all',
        suffix='tool_use_tasks'
    )


def display_filtering_results(results: Dict[str, Any], filter_description: str):
    """显示筛选结果"""
    run_info = results.get('run_info', {})
    overall_summary = results.get('overall_summary', {})
    task_category_stats = results.get('task_category_statistics', {})
    
    logger.info(f"📊 {filter_description} 评测结果:")
    logger.info(f"   运行名称: {run_info.get('run_name', 'Unknown')}")
    logger.info(f"   场景数量: {overall_summary.get('total_scenarios', 0)}")
    logger.info(f"   任务总数: {overall_summary.get('total_tasks', 0)}")
    logger.info(f"   完成任务: {overall_summary.get('total_completed_tasks', 0)}")
    logger.info(f"   完成率: {overall_summary.get('overall_completion_rate', 0):.2%}")
    
    if task_category_stats:
        logger.info("   任务类型分布:")
        for category, stats in task_category_stats.items():
            task_count = stats.get('total_tasks', 0)
            completion_rate = stats.get('completion_rate', 0)
            logger.info(f"     {category}: {task_count} 个任务, 完成率 {completion_rate:.2%}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='任务筛选评测示例',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
筛选模式:
  direct_command    - 只评测直接命令任务
  reasoning         - 只评测推理类任务 (attribute_reasoning + spatial_reasoning)
  tool_use          - 只评测工具使用任务
  single_agent_only - 只评测单智能体任务
  multi_agent_only  - 只评测多智能体任务
  combined_filter   - 组合筛选 (多智能体 + direct_command)

使用示例:
  python examples/task_filtering_example.py --mode direct_command
  python examples/task_filtering_example.py --mode single_agent_only
  python examples/task_filtering_example.py --mode combined_filter
        """
    )
    
    parser.add_argument(
        '--mode',
        required=True,
        choices=['direct_command', 'reasoning', 'tool_use', 'single_agent_only', 'multi_agent_only', 'combined_filter'],
        help='筛选模式'
    )
    
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='日志级别'
    )
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logger(log_level=getattr(logging, args.log_level))
    
    try:
        # 根据模式运行相应的评测
        if args.mode == 'direct_command':
            results = run_direct_command_evaluation()
            display_filtering_results(results, "Direct Command任务")
            
        elif args.mode == 'reasoning':
            results = run_reasoning_tasks_evaluation()
            display_filtering_results(results, "推理任务")
            
        elif args.mode == 'tool_use':
            results = run_tool_use_evaluation()
            display_filtering_results(results, "工具使用任务")
            
        elif args.mode == 'single_agent_only':
            results = run_single_agent_tasks_only()
            display_filtering_results(results, "单智能体任务")
            
        elif args.mode == 'multi_agent_only':
            results = run_multi_agent_tasks_only()
            display_filtering_results(results, "多智能体任务")
            
        elif args.mode == 'combined_filter':
            results = run_combined_filter_evaluation()
            display_filtering_results(results, "多智能体Direct Command任务")
        
        logger.info("🎉 筛选评测完成!")
        return 0
        
    except KeyboardInterrupt:
        logger.info("🛑 用户中断评测")
        return 1
    except Exception as e:
        logger.error(f"❌ 评测失败: {e}")
        return 1


if __name__ == '__main__':
    import sys
    exit_code = main()
    sys.exit(exit_code)
