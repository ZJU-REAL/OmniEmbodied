#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单智能体示例 - 使用任务验证器执行任务

这个示例展示了如何使用任务验证器来执行单智能体任务。
任务验证器提供了完整的日志记录、轨迹记录和评测功能。

主要功能：
1. 从配置文件加载完整配置
2. 支持不同的评测模式配置
3. 自动记录执行轨迹和日志
4. 生成详细的评测报告
5. 支持命令行参数覆盖配置文件设置

使用方法：
python examples/single_agent_example.py --mode sequential --scenario 00001 --suffix demo
python examples/single_agent_example.py --mode combined --scenario 00001 --suffix test
python examples/single_agent_example.py --config my_config.yaml
"""

import os
import sys
import logging
import argparse

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logger
from utils.task_evaluator import TaskEvaluator
from config import ConfigManager


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='单智能体任务执行示例')
    parser.add_argument('--mode', type=str,
                        choices=['sequential', 'combined', 'independent'],
                        help='评测模式: sequential (逐个评测), combined (混合评测), independent (独立评测)')
    parser.add_argument('--scenario', type=str,
                        help='场景ID')
    parser.add_argument('--suffix', type=str,
                        help='运行后缀')
    parser.add_argument('--config', type=str, default='single_agent_config',
                        help='配置文件名 (默认: single_agent_config)')
    parser.add_argument('--log-level', type=str,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='日志级别')
    parser.add_argument('--max-steps', type=int,
                        help='最大执行步数')
    parser.add_argument('--max-steps-per-task', type=int,
                        help='每个子任务的最大步数')
    return parser.parse_args()


def load_config_with_overrides(config_file: str, args) -> dict:
    """
    加载配置文件并应用命令行参数覆盖

    Args:
        config_file: 配置文件名
        args: 命令行参数

    Returns:
        dict: 合并后的配置
    """
    # 加载基础配置
    config_manager = ConfigManager()
    config = config_manager.get_config(config_file)

    # 应用命令行参数覆盖
    if args.mode:
        config.setdefault('evaluation', {})['task_type'] = args.mode

    if args.scenario:
        config.setdefault('evaluation', {})['default_scenario'] = args.scenario

    if args.suffix:
        config.setdefault('evaluation', {}).setdefault('run_settings', {})['default_suffix'] = args.suffix

    if args.log_level:
        config.setdefault('evaluation', {}).setdefault('run_settings', {})['log_level'] = args.log_level

    if args.max_steps:
        config.setdefault('execution', {})['max_total_steps'] = args.max_steps

    if args.max_steps_per_task:
        config.setdefault('task_evaluator', {})['max_steps_per_task'] = args.max_steps_per_task

    return config


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()

    # 加载配置文件并应用命令行覆盖
    config = load_config_with_overrides(args.config, args)

    # 从配置中获取设置
    eval_config = config.get('evaluation', {})
    run_settings = eval_config.get('run_settings', {})

    # 确定最终参数（命令行参数优先，然后是配置文件，最后是默认值）
    mode = args.mode or eval_config.get('task_type', 'sequential')
    scenario = args.scenario or eval_config.get('default_scenario', '00001')
    suffix = args.suffix or run_settings.get('default_suffix', 'demo')
    log_level = args.log_level or run_settings.get('log_level', 'INFO')

    # 设置日志
    setup_logger(log_level=getattr(logging, log_level))
    logger = logging.getLogger(__name__)

    logger.info("🚀 启动单智能体示例（使用任务验证器）")
    logger.info(f"📋 评测模式: {mode}")
    logger.info(f"🏠 场景ID: {scenario}")
    logger.info(f"🏷️ 运行后缀: {suffix}")
    logger.info(f"⚙️ 配置文件: {args.config}")
    logger.info(f"📊 日志级别: {log_level}")

    # 显示关键配置信息
    execution_config = config.get('execution', {})
    task_evaluator_config = config.get('task_evaluator', {})
    env_desc_config = config.get('environment_description', {})
    history_config = config.get('history', {})

    logger.info("⚙️ 配置信息:")
    logger.info(f"  - 最大总步数: {execution_config.get('max_total_steps', 200)}")
    logger.info(f"  - 每任务最大步数: {task_evaluator_config.get('max_steps_per_task', 20)}")
    logger.info(f"  - 环境描述级别: {env_desc_config.get('detail_level', 'full')}")
    logger.info(f"  - 历史记录长度: {history_config.get('max_history_length', -1)}")
    logger.info(f"  - 任务超时时间: {execution_config.get('timeout_seconds', 900)}秒")

    try:
        # 创建任务验证器
        evaluator = TaskEvaluator(
            config_file=args.config,
            agent_type='single',
            task_type=mode,
            scenario_id=scenario,
            custom_suffix=suffix
        )

        logger.info("✅ 任务验证器初始化成功")
        logger.info(f"📁 输出目录: {evaluator.output_dir}")
        logger.info(f"📝 轨迹文件: {evaluator.trajectory_recorder.trajectory_file}")
        logger.info(f"📄 日志文件: {evaluator.trajectory_recorder.log_file}")

        # 执行评测
        logger.info("🎬 开始执行任务评测...")
        results = evaluator.run_evaluation(scenario)

        # 显示结果
        logger.info("\n🎉 任务评测完成！")

        # 获取汇总信息
        summary = results.get('summary', {})

        # 显示基本结果
        logger.info("📊 评测结果:")
        logger.info(f"  - 总任务数: {summary.get('total_tasks', 0)}")
        logger.info(f"  - 完成任务数: {summary.get('completed_tasks', 0)}")
        logger.info(f"  - 失败任务数: {summary.get('failed_tasks', 0)}")
        logger.info(f"  - 完成率: {summary.get('completion_rate', 0):.1%}")

        # 显示详细结果
        logger.info(f"  - 总步数: {summary.get('total_steps', 0)}")
        logger.info(f"  - 平均每任务步数: {summary.get('average_steps_per_task', 0):.1f}")
        logger.info(f"  - 执行时长: {summary.get('total_duration', 0):.2f}秒")

        # 显示性能评价
        completion_rate = summary.get('completion_rate', 0)
        if completion_rate >= 0.8:
            logger.info("🎊 评测结果优秀！")
        elif completion_rate >= 0.6:
            logger.info("👍 评测结果良好！")
        else:
            logger.info("📈 还有改进空间")

        return 0

    except Exception as e:
        logger.error(f"❌ 执行过程中发生错误: {e}")
        import traceback
        logger.error(f"错误详情:\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    exit(main())
