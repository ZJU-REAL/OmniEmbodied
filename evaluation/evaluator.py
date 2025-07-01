#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务评测器主程序
支持四种评测模式：
1. 单智能体逐个评测 (single_sequential)
2. 单智能体混合评测 (single_combined)
3. 多智能体逐个评测 (multi_sequential)
4. 多智能体混合评测 (multi_combined)

使用方法:
python evaluator.py --mode single_sequential --scenario 00001
python evaluator.py --config custom_evaluator_config.yaml
"""

import os
import sys
import argparse
import logging
from typing import Optional

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from utils.task_evaluator import TaskEvaluator
from utils.parallel_task_evaluator import ParallelTaskEvaluator
from config import ConfigManager


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="任务评测器 - 支持六种评测模式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
评测模式说明:
  single_sequential   - 单智能体逐个评测：只加载agent1，每个子任务独立执行
  single_combined     - 单智能体混合评测：只加载agent1，所有子任务拼接执行
  single_independent  - 单智能体独立评测：只加载agent1，每个子任务在全新环境中执行
  multi_sequential    - 多智能体逐个评测：加载所有智能体，每个子任务独立执行
  multi_combined      - 多智能体混合评测：加载所有智能体，所有子任务拼接执行
  multi_independent   - 多智能体独立评测：加载所有智能体，每个子任务在全新环境中执行

示例:
  python evaluator.py --mode single_sequential --scenario 00001
  python evaluator.py --mode single_independent --scenario 00001
  python evaluator.py --mode multi_combined --scenario 00002 --config my_config.yaml
  python evaluator.py --list-modes
        """
    )
    
    parser.add_argument(
        '--mode', '-m',
        choices=['single_sequential', 'single_combined', 'single_independent',
                'multi_sequential', 'multi_combined', 'multi_independent', 'parallel'],
        help='评测模式'
    )
    
    parser.add_argument(
        '--scenario', '-s',
        type=str,
        help='场景ID (如: 00001)'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='配置文件名 (可选，默认根据模式自动选择)'
    )

    parser.add_argument(
        '--suffix',
        type=str,
        help='自定义运行后缀'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别 (默认: INFO)'
    )
    
    parser.add_argument(
        '--list-modes',
        action='store_true',
        help='列出所有可用的评测模式'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='干运行模式，只检查配置不执行评测'
    )
    
    return parser.parse_args()


def list_evaluation_modes():
    """列出所有评测模式"""
    modes = {
        'single_sequential': '单智能体逐个评测 - 只加载agent1，每个子任务独立执行，任务间清空历史',
        'single_combined': '单智能体混合评测 - 只加载agent1，将所有子任务拼接成一个长任务执行',
        'single_independent': '单智能体独立评测 - 只加载agent1，每个子任务在全新环境中独立执行',
        'multi_sequential': '多智能体逐个评测 - 加载所有智能体，每个子任务独立执行，任务间清空历史',
        'multi_combined': '多智能体混合评测 - 加载所有智能体，将所有子任务拼接成一个长任务执行',
        'multi_independent': '多智能体独立评测 - 加载所有智能体，每个子任务在全新环境中独立执行',
        'parallel': '并行任务评测 - 多个任务同时并行执行，每个任务使用独立的模拟器实例'
    }

    print("📋 可用的评测模式:")
    print("=" * 80)
    for mode, description in modes.items():
        print(f"  {mode:<20} - {description}")
    print("=" * 80)


def parse_mode(mode: str) -> tuple:
    """解析评测模式"""
    # 并行模式
    if mode == 'parallel':
        return 'single', 'sequential', 'single_agent_config', True

    # 常规模式
    if mode.startswith('single_'):
        agent_type = 'single'
        task_type = mode.replace('single_', '')
        config_file = 'single_agent_config'
    elif mode.startswith('multi_'):
        agent_type = 'multi'
        task_type = mode.replace('multi_', '')
        config_file = 'centralized_config'  # 默认使用中心化配置
    else:
        raise ValueError(f"无效的评测模式: {mode}")

    return agent_type, task_type, config_file, False


def validate_config(config: dict, agent_type: str, task_type: str) -> bool:
    """验证配置的有效性"""
    try:
        # 检查必要的配置项
        required_keys = ['evaluation']

        for key in required_keys:
            if key not in config:
                print(f"❌ 配置文件缺少必要项: {key}")
                return False

        # 检查评测配置
        eval_config = config['evaluation']
        if 'output' not in eval_config:
            print("⚠️ 配置文件缺少输出配置，将使用默认值")

        print(f"✅ 配置验证通过 - 模式: {agent_type}_{task_type}")
        return True

    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False


def main():
    """主函数"""
    args = parse_arguments()
    
    # 设置日志
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # 列出模式
    if args.list_modes:
        list_evaluation_modes()
        return 0
    
    # 检查必要参数
    if not args.mode:
        print("❌ 请指定评测模式，使用 --list-modes 查看可用模式")
        return 1
    
    try:
        # 解析模式
        parse_result = parse_mode(args.mode)
        if len(parse_result) == 4:
            agent_type, task_type, default_config, is_parallel = parse_result
        else:
            agent_type, task_type, default_config = parse_result
            is_parallel = False

        # 确定配置文件
        config_file = args.config or default_config

        # 加载配置
        config_manager = ConfigManager()
        config = config_manager.get_config(config_file)

        # 验证配置
        if not validate_config(config, agent_type, task_type):
            return 1

        # 干运行模式
        if args.dry_run:
            mode_desc = "并行评测" if is_parallel else f"{agent_type}_{task_type}"
            print(f"✅ 干运行完成 - 配置有效，模式: {mode_desc}")
            print(f"📋 配置文件: {config_file}")
            print(f"🎯 场景: {args.scenario or 'default'}")
            return 0

        # 创建评测器
        logger.info(f"🚀 启动任务评测器 - 模式: {args.mode}")

        if is_parallel:
            # 并行评测模式
            evaluator = ParallelTaskEvaluator(
                config_file=config_file,
                agent_type=agent_type,
                task_type=task_type,
                scenario_id=args.scenario,
                custom_suffix=args.suffix
            )
            # 运行并行评测
            results = evaluator.run_parallel_evaluation()
        else:
            # 常规评测模式
            evaluator = TaskEvaluator(
                config_file=config_file,
                agent_type=agent_type,
                task_type=task_type,
                scenario_id=args.scenario,
                custom_suffix=args.suffix
            )
            # 运行评测
            results = evaluator.run_evaluation(args.scenario)

        # 显示结果摘要
        summary = results['summary']
        print(f"\n🎉 评测完成!")
        print(f"🏃 运行名称: {results['run_name']}")
        print(f"📊 完成率: {summary['completion_rate']:.1%} ({summary['completed_tasks']}/{summary['total_tasks']})")
        print(f"📊 总步数: {summary['total_steps']}")
        print(f"📊 耗时: {results['total_duration']:.2f}秒")
        print(f"📁 输出文件:")
        print(f"   轨迹: {results['output_files']['trajectory_file']}")
        print(f"   日志: {results['output_files']['log_file']}")

        if 'error' in results:
            print(f"❌ 评测过程中出现错误: {results['error']}")
            return 1

        return 0
        
    except KeyboardInterrupt:
        logger.info("🛑 用户中断评测")
        return 1
    except Exception as e:
        logger.exception(f"❌ 评测器运行失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
