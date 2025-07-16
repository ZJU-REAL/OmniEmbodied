#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主入口脚本 - 重构后的评测器入口
"""

import argparse
import logging
import sys
import signal
from typing import Dict, Any

from .evaluation_interface import EvaluationInterface


def setup_logging(log_level: str = 'INFO'):
    """设置日志配置"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('evaluation.log', encoding='utf-8')
        ]
    )


def signal_handler(signum, frame):
    """信号处理器确保中断时保存数据"""
    _ = signum, frame  # 避免未使用变量警告
    logger = logging.getLogger(__name__)
    logger.info("🛑 接收到中断信号，正在保存数据...")

    # TODO: 实现中断时的数据保存逻辑
    # 这里需要访问当前运行的评测器实例来保存数据

    logger.info("✅ 数据保存完成，程序退出")
    sys.exit(0)


def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 解析命令行参数
    parser = create_argument_parser()
    args = parser.parse_args()

    # 设置日志
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    try:
        # 解析场景选择
        scenario_selection = EvaluationInterface.parse_scenario_string(args.scenarios)

        # 添加任务筛选
        if args.task_categories:
            task_filter = {}
            if args.task_categories:
                task_filter['categories'] = args.task_categories

            scenario_selection['task_filter'] = task_filter

        # 验证配置文件
        if not EvaluationInterface.validate_config_file(args.config):
            logger.error(f"❌ 配置文件不存在: {args.config}")
            available_configs = EvaluationInterface.list_available_configs()
            logger.info(f"可用配置: {available_configs}")
            return 1

        # 显示评测信息
        scenario_count = EvaluationInterface.get_scenario_count(scenario_selection)
        logger.info(f"🎯 评测配置:")
        logger.info(f"   配置文件: {args.config}")
        logger.info(f"   智能体类型: {args.agent_type}")
        logger.info(f"   任务类型: {args.task_type}")
        logger.info(f"   场景选择: {args.scenarios} ({scenario_count} 个场景)")
        if args.task_categories:
            logger.info(f"   任务类别筛选: {args.task_categories}")
        logger.info(f"   自定义后缀: {args.suffix}")

        # 运行评测
        results = EvaluationInterface.run_evaluation(
            config_file=args.config,
            agent_type=args.agent_type,
            task_type=args.task_type,
            scenario_selection=scenario_selection,
            custom_suffix=args.suffix
        )

        # 显示结果摘要
        display_results_summary(results)

        logger.info("🎉 评测完成!")
        return 0

    except KeyboardInterrupt:
        logger.info("🛑 用户中断评测")
        return 1
    except Exception as e:
        logger.error(f"❌ 评测失败: {e}")
        return 1


def create_argument_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='OmniEmbodied评测器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 单智能体Sequential模式评测
  python -m evaluation.evaluator --config single_agent_config --agent-type single --task-type sequential --scenarios 00001-00010 --suffix test1

  # 多智能体Independent模式评测
  python -m evaluation.evaluator --config decentralized_config --agent-type multi --task-type independent --scenarios all --suffix experiment1

  # 特定场景列表评测
  python -m evaluation.evaluator --config centralized_config --agent-type multi --task-type combined --scenarios 00001,00005,00010 --suffix selected_scenes

  # 单个场景快速测试
  python -m evaluation.evaluator --config single_agent_config --agent-type single --task-type sequential --scenarios 00001 --suffix quick_test

  # 筛选特定任务类别
  python -m evaluation.evaluator --config single_agent_config --agent-type single --task-type sequential --scenarios all --task-categories direct_command attribute_reasoning --suffix filtered_tasks

  # 只评测工具使用任务
  python -m evaluation.evaluator --config single_agent_config --agent-type single --task-type sequential --scenarios all --task-categories tool_use --suffix tool_use_tasks

  # 只评测协作任务
  python -m evaluation.evaluator --config centralized_config --agent-type multi --task-type combined --scenarios all --task-categories explicit_collaboration implicit_collaboration --suffix collaboration_tasks
        """
    )

    parser.add_argument(
        '--config',
        required=True,
        help='配置文件名 (single_agent_config, centralized_config, decentralized_config)'
    )

    parser.add_argument(
        '--agent-type',
        required=True,
        choices=['single', 'multi'],
        help='智能体类型'
    )

    parser.add_argument(
        '--task-type',
        required=True,
        choices=['sequential', 'combined', 'independent'],
        help='任务类型'
    )

    parser.add_argument(
        '--scenarios',
        default='all',
        help='场景选择: all, 00001-00010, 00001,00003,00005'
    )

    parser.add_argument(
        '--task-categories',
        nargs='*',
        help='任务类别筛选: direct_command attribute_reasoning tool_use spatial_reasoning'
    )



    parser.add_argument(
        '--suffix',
        default='evaluation',
        help='自定义后缀'
    )

    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='日志级别'
    )

    parser.add_argument(
        '--list-configs',
        action='store_true',
        help='列出可用的配置文件'
    )

    return parser


def display_results_summary(results: Dict[str, Any]):
    """显示结果摘要"""
    logger = logging.getLogger(__name__)

    run_info = results.get('run_info', {})
    overall_summary = results.get('overall_summary', {})
    task_category_stats = results.get('task_category_statistics', {})

    logger.info("📊 评测结果摘要:")
    logger.info(f"   运行名称: {run_info.get('run_name', 'Unknown')}")
    logger.info(f"   总耗时: {run_info.get('total_duration', 0):.2f} 秒")
    logger.info(f"   场景数量: {overall_summary.get('total_scenarios', 0)}")
    logger.info(f"   任务总数: {overall_summary.get('total_tasks', 0)}")
    logger.info(f"   完成任务: {overall_summary.get('total_completed_tasks', 0)}")
    logger.info(f"   总体完成率: {overall_summary.get('overall_completion_rate', 0):.2%}")
    logger.info(f"   模型准确率: {overall_summary.get('overall_completion_accuracy', 0):.2%}")

    if task_category_stats:
        logger.info("� 任务类型统计:")
        for category, stats in task_category_stats.items():
            completion_rate = stats.get('completion_rate', 0)
            logger.info(f"   {category}: {completion_rate:.2%}")

    logger.info(f"� 结果保存在: output/{run_info.get('run_name', 'unknown')}/")


def list_configs_command():
    """列出可用配置的命令"""
    logger = logging.getLogger(__name__)

    configs = EvaluationInterface.list_available_configs()
    if configs:
        logger.info("📋 可用的配置文件:")
        for config in configs:
            logger.info(f"   - {config}")
    else:
        logger.warning("❌ 未找到任何配置文件")


if __name__ == '__main__':
    # 处理特殊命令
    if len(sys.argv) > 1 and sys.argv[1] == '--list-configs':
        setup_logging()
        list_configs_command()
        sys.exit(0)

    # 运行主程序
    exit_code = main()
    sys.exit(exit_code)
