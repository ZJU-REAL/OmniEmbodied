#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于配置文件的评测示例
展示如何使用配置文件中的默认参数进行评测，减少命令行参数的使用
"""

import os
import sys
import argparse
import logging

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from utils.task_evaluator import TaskEvaluator
from config import ConfigManager


def parse_arguments():
    """解析命令行参数 - 只保留必要的参数，其他从配置文件读取"""
    parser = argparse.ArgumentParser(
        description='基于配置文件的评测示例',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用说明:
  大部分参数都可以在配置文件中设置，命令行参数只用于覆盖配置文件中的值。
  
配置文件中可设置的参数:
  - evaluation.task_type: 评测模式 (sequential/combined/independent)
  - evaluation.default_scenario: 默认场景ID
  - evaluation.run_settings.default_suffix: 默认运行后缀
  - evaluation.run_settings.log_level: 日志级别
  - task_evaluator.max_steps_per_task: 每个子任务最大步数
  - execution.max_total_steps: 总最大步数

示例:
  # 使用配置文件中的所有默认值
  python examples/config_based_evaluation.py --config single_agent_config
  
  # 只覆盖场景ID，其他使用配置文件默认值
  python examples/config_based_evaluation.py --config single_agent_config --scenario 00002
  
  # 覆盖评测模式和后缀
  python examples/config_based_evaluation.py --config single_agent_config --mode independent --suffix my_test
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        required=True,
        help='配置文件名 (必需，如: single_agent_config, centralized_config)'
    )
    
    parser.add_argument(
        '--mode', '-m',
        choices=['sequential', 'combined', 'independent'],
        help='评测模式 (可选，默认从配置文件读取)'
    )
    
    parser.add_argument(
        '--scenario', '-s',
        type=str,
        help='场景ID (可选，默认从配置文件读取)'
    )
    
    parser.add_argument(
        '--suffix',
        type=str,
        help='运行后缀 (可选，默认从配置文件读取)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='干运行模式，只检查配置不执行评测'
    )
    
    return parser.parse_args()


def determine_agent_type(config: dict) -> str:
    """根据配置文件内容确定智能体类型"""
    if 'coordinator' in config or 'worker_agents' in config:
        return 'multi'
    elif 'autonomous_agent' in config or 'communication' in config:
        return 'multi'
    else:
        return 'single'


def main():
    """主函数"""
    args = parse_arguments()
    
    # 加载配置
    config_manager = ConfigManager()
    config = config_manager.get_config(args.config)
    
    # 从配置文件读取默认值
    eval_config = config.get('evaluation', {})
    run_settings = eval_config.get('run_settings', {})
    
    # 确定参数值（命令行参数优先，否则使用配置文件默认值）
    task_type = args.mode or eval_config.get('task_type', 'sequential')
    scenario_id = args.scenario or eval_config.get('default_scenario', '00001')
    custom_suffix = args.suffix or run_settings.get('default_suffix', 'demo')
    log_level = run_settings.get('log_level', 'INFO')
    
    # 确定智能体类型
    agent_type = determine_agent_type(config)
    
    # 设置日志
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # 显示配置信息
    print("📋 评测配置信息:")
    print(f"   配置文件: {args.config}")
    print(f"   智能体类型: {agent_type}")
    print(f"   评测模式: {task_type}")
    print(f"   场景ID: {scenario_id}")
    print(f"   运行后缀: {custom_suffix}")
    print(f"   日志级别: {log_level}")
    print()
    
    # 显示从配置文件读取的其他重要参数
    max_steps_per_task = config.get('task_evaluator', {}).get('max_steps_per_task', 30)
    max_total_steps = config.get('execution', {}).get('max_total_steps', 300)
    print("📊 执行参数:")
    print(f"   每个子任务最大步数: {max_steps_per_task}")
    print(f"   总最大步数: {max_total_steps}")
    print()
    
    # 干运行模式
    if args.dry_run:
        print("✅ 干运行完成 - 配置验证通过")
        return 0
    
    try:
        # 创建评测器（使用配置文件中的默认值）
        logger.info(f"🚀 启动基于配置文件的评测器")
        evaluator = TaskEvaluator(
            config_file=args.config,
            agent_type=agent_type,
            task_type=task_type,
            scenario_id=scenario_id,
            custom_suffix=custom_suffix
        )
        
        # 运行评测
        results = evaluator.run()
        
        # 显示结果摘要
        print("\n📊 评测完成!")
        print(f"   运行名称: {evaluator.run_name}")
        print(f"   输出目录: {evaluator.output_dir}")
        print(f"   完成率: {results['summary']['completion_rate']:.1%}")
        print(f"   总步数: {results['summary']['total_steps']}")
        
        return 0
        
    except Exception as e:
        logger.exception(f"❌ 评测执行失败: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
