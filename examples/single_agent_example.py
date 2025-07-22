#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单智能体示例 - 使用新的评测器执行任务

这个示例展示了如何使用重构后的评测器来执行单智能体任务。
评测器提供了完整的日志记录、轨迹记录和评测功能。

主要功能：
1. 从配置文件加载完整配置
2. 支持不同的评测模式配置
3. 自动记录执行轨迹和日志
4. 生成详细的评测报告
5. 支持命令行参数覆盖配置文件设置

使用方法：
python examples/single_agent_example.py --mode sequential --scenarios 00001 --suffix demo
python examples/single_agent_example.py --mode combined --scenarios 00001-00003 --suffix test
python examples/single_agent_example.py --config single_agent_config --parallel
"""

import sys
import os
import logging
import argparse

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 导入新的评测器
from evaluation.evaluation_interface import EvaluationInterface
from config.config_manager import get_config_manager
from config.config_override import ConfigOverrideParser


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='单智能体任务执行示例')
    parser.add_argument('--mode', type=str,
                        choices=['sequential', 'combined', 'independent'],
                        help='评测模式: sequential (逐个评测), combined (混合评测), independent (独立评测)')
    parser.add_argument('--scenarios', type=str, default=None,
                        help='场景选择: all, 00001-00010, 00001,00003,00005 (如果未指定，将使用配置文件设置)')
    parser.add_argument('--suffix', type=str, default='demo',
                        help='运行后缀')
    parser.add_argument('--config', type=str, default='single_agent_config',
                        help='配置文件名 (默认: single_agent_config)')
    parser.add_argument('--log-level', type=str,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        default='INFO',
                        help='日志级别')
    parser.add_argument('--parallel', action='store_true',
                        help='启用并行评测模式')

    # 便捷的模型选择参数
    model_group = parser.add_argument_group('便捷模型选择')
    model_group.add_argument('--model', type=str,
                           choices=['deepseek', 'deepseekv3', 'deepseekr1', 'qwen3b', 'qwen7b', 'qwen72b','llama8b', 'openai', 'volcengine', 'bailian'],
                           help='快速选择模型: deepseek, deepseekv3, deepseekr1, qwen3b, qwen7b, qwen72b, llama8b, openai, volcengine, bailian')
    model_group.add_argument('--observation-mode', type=str,
                           choices=['explore', 'global'],
                           help='观察模式: explore (探索模式，只显示已发现物体), global (全局模式，显示所有物体)')

    # 添加配置覆盖支持（使用全局单例）
    config_manager = get_config_manager()
    ConfigOverrideParser.add_config_override_args(parser, config_manager)

    return parser.parse_args()


def run_single_evaluation(config_file: str, mode: str, scenarios: str, suffix: str):
    """
    运行单次评测

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
        # 加载配置（使用全局单例）
        config_manager = get_config_manager()
        config = config_manager.get_config(config_file)

        # 获取数据集配置
        dataset_name = config.get('dataset', {}).get('default', 'eval_single')

        # 严格验证数据目录配置 - 直接抛出异常
        data_dir = config_manager.get_data_dir(config_file, dataset_name)
        scene_dir = config_manager.get_scene_dir(config_file, dataset_name)
        task_dir = config_manager.get_task_dir(config_file, dataset_name)

        logger.info(f"📁 使用数据集: {dataset_name}")
        logger.info(f"📁 数据目录: {data_dir}")
        logger.info(f"📁 场景目录: {scene_dir}")
        logger.info(f"📁 任务目录: {task_dir}")

        # 解析场景选择
        scenario_selection = EvaluationInterface.parse_scenario_string(scenarios)

        # 运行评测
        logger.info(f"🚀 开始单智能体评测")
        logger.info(f"📋 评测模式: {mode}")
        logger.info(f"🏠 场景选择: {scenarios}")
        logger.info(f"🏷️ 运行后缀: {suffix}")
        logger.info(f"⚙️ 配置文件: {config_file}")
        logger.info(f"🤖 智能体类型: 单智能体")

        results = EvaluationInterface.run_evaluation(
            config_file=config_file,
            agent_type='single',
            task_type=mode,
            scenario_selection=scenario_selection,
            custom_suffix=suffix
        )

        # 显示结果 - 使用正确的字段名
        run_info = results.get('runinfo', {})
        overall_summary = results.get('overall_summary', {})

        logger.info("\n🎉 评测完成！")
        logger.info("📊 评测结果:")
        logger.info(f"  - 运行名称: {run_info.get('run_id', 'Unknown')}")
        logger.info(f"  - 总耗时: {run_info.get('duration_seconds', 0):.2f} 秒")
        logger.info(f"  - 场景数量: {run_info.get('total_scenarios', 0)}")
        logger.info(f"  - 任务总数: {overall_summary.get('total_tasks', 0)}")
        logger.info(f"  - 完成任务: {overall_summary.get('actually_completed', 0)}")
        logger.info(f"  - 总体完成率: {overall_summary.get('completion_rate', 0):.2%}")
        logger.info(f"  - 模型声称完成: {overall_summary.get('model_claimed_completed', 0)}")
        logger.info(f"📁 结果保存在: output/{run_info.get('run_id', 'unknown')}/")

        # 显示性能评价
        completion_rate = overall_summary.get('completion_rate', 0)
        if completion_rate >= 0.8:
            logger.info("🎊 评测结果优秀！")
        elif completion_rate >= 0.6:
            logger.info("👍 评测结果良好！")
        else:
            logger.info("📈 还有改进空间")

        return 0

    except Exception as e:
        logger.error(f"❌ 评测失败: {e}")
        import traceback
        logger.error(f"错误详情:\n{traceback.format_exc()}")
        return 1


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()

    # 从配置文件获取日志设置（使用全局单例）
    config_manager = get_config_manager()
    config = config_manager.get_config(args.config)
    logging_config = config.get('logging', {})

    # 确定日志级别（命令行参数优先，然后是配置文件，最后是默认值）
    log_level = args.log_level or logging_config.get('level', 'INFO')

    # 设置日志
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    if logging_config.get('show_llm_details', False):
        logger.info("🔍 LLM详细日志已启用")

    # 处理便捷参数，转换为配置覆盖
    if hasattr(args, 'model') and args.model:
        # 将便捷模型参数转换为配置覆盖
        if not hasattr(args, 'config_override') or args.config_override is None:
            args.config_override = []
        args.config_override.append(f'llm_config.api.provider={args.model}')
        logger.info(f"🎯 便捷模型选择: {args.model}")

    if hasattr(args, 'observation_mode') and args.observation_mode:
        # 将观察模式参数转换为配置覆盖
        if not hasattr(args, 'config_override') or args.config_override is None:
            args.config_override = []

        only_show_discovered = 'true' if args.observation_mode == 'explore' else 'false'
        args.config_override.append(f'{args.config}.agent_config.environment_description.only_show_discovered={only_show_discovered}')
        logger.info(f"👁️ 观察模式: {args.observation_mode} ({'探索模式' if args.observation_mode == 'explore' else '全局模式'})")

    # 应用配置覆盖
    ConfigOverrideParser.apply_config_overrides(args, args.config)
    logger.info("配置覆盖已应用到: %s", args.config)

    # 重新获取配置（包含覆盖后的值）
    config = config_manager.get_config(args.config)
    eval_config = config.get('evaluation', {})
    run_settings = eval_config.get('run_settings', {})
    parallel_settings = config.get('parallel_evaluation', {})

    # 确定最终参数（命令行参数优先，然后是配置文件，最后是默认值）
    mode = args.mode or eval_config.get('task_type', 'sequential')

    # 场景选择逻辑：优先使用命令行参数，否则使用配置文件设置
    if args.scenarios is None:  # 命令行未指定，使用配置文件
        scenario_selection = parallel_settings.get('scenario_selection', {})
        scenario_mode = scenario_selection.get('mode', 'list')

        if scenario_mode == 'all':
            scenarios = 'all'  # 使用'all'执行所有场景
        elif scenario_mode == 'range':
            range_config = scenario_selection.get('range', {})
            start = range_config.get('start', '00001')
            end = range_config.get('end', '00001')
            scenarios = f"{start}-{end}" if start != end else start
        elif scenario_mode == 'list':
            scenario_list = scenario_selection.get('list', ['00001'])
            scenarios = ','.join(scenario_list)
        else:
            # 如果配置文件也没有有效设置，使用单个场景作为最后的回退
            scenarios = '00001'
            logger.warning("配置文件中没有有效的场景选择设置，使用默认场景 00001")
    else:
        scenarios = args.scenarios  # 使用命令行指定的场景

    suffix = args.suffix or run_settings.get('default_suffix', 'demo')

    # 检查是否启用并行模式（命令行参数优先，然后是配置文件）
    parallel_enabled = args.parallel or parallel_settings.get('enabled', False)

    logger.info("🚀 启动单智能体示例（使用新评测器）")
    logger.info(f"📋 评测模式: {mode}")
    logger.info(f"🏠 场景选择: {scenarios}")
    logger.info(f"🏷️ 运行后缀: {suffix}")
    logger.info(f"⚙️ 配置文件: {args.config}")
    logger.info(f"🔄 并行模式: {'启用' if parallel_enabled else '禁用'}")

    # 检查是否启用并行模式
    if parallel_enabled:
        logger.info("🔄 并行模式已启用，使用配置文件中的并行设置")

    # 运行评测
    return run_single_evaluation(args.config, mode, scenarios, suffix)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
