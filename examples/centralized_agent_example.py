#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中心化多智能体示例 - 使用新的评测器执行任务

这个示例展示了如何使用重构后的评测器来执行中心化多智能体任务。
评测器提供了完整的日志记录、轨迹记录和评测功能。

主要功能：
1. 从配置文件加载完整配置
2. 支持不同的评测模式配置
3. 自动记录执行轨迹和日志
4. 生成详细的评测报告
5. 支持命令行参数覆盖配置文件设置
6. 中心化协调两个智能体完成任务

使用方法：
python examples/centralized_agent_example.py --mode sequential --scenarios 00001 --suffix demo
python examples/centralized_agent_example.py --mode combined --scenarios 00001-00003 --suffix test
python examples/centralized_agent_example.py --config centralized_config --parallel
"""

import sys
import os
import logging
import argparse

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 导入新的评测器
from evaluation.evaluation_interface import EvaluationInterface
from config.config_manager import ConfigManager


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='中心化多智能体任务执行示例')
    parser.add_argument('--mode', type=str,
                        choices=['sequential', 'combined', 'independent'],
                        help='评测模式: sequential (逐个评测), combined (混合评测), independent (独立评测)')
    parser.add_argument('--scenarios', type=str, default='00001',
                        help='场景选择: all, 00001-00010, 00001,00003,00005')
    parser.add_argument('--suffix', type=str, default='demo',
                        help='运行后缀')
    parser.add_argument('--config', type=str, default='centralized_config',
                        help='配置文件名 (默认: centralized_config)')
    parser.add_argument('--log-level', type=str,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        default='INFO',
                        help='日志级别')
    parser.add_argument('--parallel', action='store_true',
                        help='启用并行评测模式')
    return parser.parse_args()


def run_centralized_evaluation(config_file: str, mode: str, scenarios: str, suffix: str):
    """
    运行中心化多智能体评测

    Args:
        config_file: 配置文件名
        mode: 评测模式
        scenarios: 场景选择字符串
        suffix: 运行后缀

    Returns:
        int: 退出码
    """
    logger = logging.getLogger(__name__)

    try:
        # 加载配置
        config_manager = ConfigManager()
        config = config_manager.get_config(config_file)

        # 严格验证数据目录配置 - 直接抛出异常
        data_dir = config_manager.get_data_dir(config_file)
        scene_dir = config_manager.get_scene_dir(config_file)
        task_dir = config_manager.get_task_dir(config_file)

        logger.info(f"📁 数据目录: {data_dir}")
        logger.info(f"📁 场景目录: {scene_dir}")
        logger.info(f"📁 任务目录: {task_dir}")

        # 解析场景选择
        scenario_selection = EvaluationInterface.parse_scenario_string(scenarios)

        # 运行评测
        logger.info(f"🚀 开始中心化多智能体评测")
        logger.info(f"📋 评测模式: {mode}")
        logger.info(f"🏠 场景选择: {scenarios}")
        logger.info(f"🏷️ 运行后缀: {suffix}")
        logger.info(f"⚙️ 配置文件: {config_file}")
        logger.info(f"🤖 智能体类型: 中心化多智能体 (2个智能体)")

        results = EvaluationInterface.run_evaluation(
            config_file=config_file,
            agent_type='multi',  # 多智能体类型
            task_type=mode,
            scenario_selection=scenario_selection,
            custom_suffix=suffix
        )

        # 显示结果
        run_info = results.get('run_info', {})
        overall_summary = results.get('overall_summary', {})

        logger.info("\n🎉 中心化多智能体评测完成！")
        logger.info("📊 评测结果:")
        logger.info(f"  - 运行名称: {run_info.get('run_name', 'Unknown')}")
        logger.info(f"  - 总耗时: {run_info.get('total_duration', 0):.2f} 秒")
        logger.info(f"  - 场景数量: {overall_summary.get('total_scenarios', 0)}")
        logger.info(f"  - 任务总数: {overall_summary.get('total_tasks', 0)}")
        logger.info(f"  - 完成任务: {overall_summary.get('total_completed_tasks', 0)}")
        logger.info(f"  - 总体完成率: {overall_summary.get('overall_completion_rate', 0):.2%}")
        logger.info(f"  - 模型准确率: {overall_summary.get('overall_completion_accuracy', 0):.2%}")
        logger.info(f"📁 结果保存在: output/{run_info.get('run_name', 'unknown')}/")

        # 显示协作效果评价
        completion_rate = overall_summary.get('overall_completion_rate', 0)
        if completion_rate >= 0.8:
            logger.info("🎊 中心化协作效果优秀！")
        elif completion_rate >= 0.6:
            logger.info("👍 中心化协作效果良好！")
        else:
            logger.info("📈 协作策略还有改进空间")

        return 0

    except Exception as e:
        logger.error(f"❌ 中心化多智能体评测失败: {e}")
        import traceback
        logger.error(f"错误详情:\n{traceback.format_exc()}")
        return 1


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()

    # 设置日志
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # 从配置文件获取默认值
    config_manager = ConfigManager()
    config = config_manager.get_config(args.config)
    eval_config = config.get('evaluation', {})
    run_settings = eval_config.get('run_settings', {})
    parallel_settings = config.get('parallel_evaluation', {})

    # 确定最终参数（命令行参数优先，然后是配置文件，最后是默认值）
    mode = args.mode or eval_config.get('task_type', 'sequential')

    # 场景选择逻辑：如果命令行没有明确指定（使用默认值），则尝试使用配置文件
    if args.scenarios == '00001':  # 默认值，检查配置文件
        scenario_selection = parallel_settings.get('scenario_selection', {})
        selection_mode = scenario_selection.get('mode', 'range')

        if selection_mode == 'all':
            scenarios = 'all'
        elif selection_mode == 'range':
            range_config = scenario_selection.get('range', {})
            start = range_config.get('start', '00001')
            end = range_config.get('end', '00001')
            scenarios = f"{start}-{end}" if start != end else start
        elif selection_mode == 'list':
            scenario_list = scenario_selection.get('list', ['00001'])
            scenarios = ','.join(scenario_list)
        else:
            logger.warning(f"未知的场景选择模式: {selection_mode}, 使用默认场景")
            scenarios = args.scenarios
    else:
        scenarios = args.scenarios

    suffix = args.suffix or run_settings.get('default_suffix', 'demo')

    # 检查是否启用并行模式（命令行参数优先，然后是配置文件）
    parallel_enabled = args.parallel or parallel_settings.get('enabled', False)

    logger.info("🚀 启动中心化多智能体示例（使用新评测器）")
    logger.info(f"📋 评测模式: {mode}")
    logger.info(f"🏠 场景选择: {scenarios}")
    logger.info(f"🏷️ 运行后缀: {suffix}")
    logger.info(f"⚙️ 配置文件: {args.config}")
    logger.info(f"🔄 并行模式: {'启用' if parallel_enabled else '禁用'}")
    logger.info(f"🤖 智能体架构: 中心化协调 (1个协调器控制2个智能体)")

    # 检查是否启用并行模式
    if parallel_enabled:
        logger.info("🔄 并行模式已启用，使用配置文件中的并行设置")

    # 运行评测
    return run_centralized_evaluation(args.config, mode, scenarios, suffix)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
