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
import time
import json
import logging
import argparse
import multiprocessing
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logger
from utils.task_evaluator import TaskEvaluator
from utils.run_naming import RunNamingManager
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
    parser.add_argument('--parallel', action='store_true',
                        help='启用并行评测模式')
    parser.add_argument('--max-steps', type=int,
                        help='最大执行步数')
    parser.add_argument('--max-steps-per-task', type=int,
                        help='每个子任务的最大步数')
    return parser.parse_args()


def execute_single_scenario(args_tuple):
    """
    在独立进程中执行单个场景的评测

    Args:
        args_tuple: (config_file, mode, scenario_id, suffix, output_dir, run_name)

    Returns:
        Dict[str, Any]: 场景评测结果
    """
    config_file, mode, scenario_id, suffix, output_dir, main_run_name = args_tuple

    import time
    import os
    import sys
    import logging

    scenario_start_time = time.time()

    # 直接使用主输出目录，不创建场景子目录
    scenario_output_dir = output_dir

    try:
        # 确保路径正确
        project_root = os.path.dirname(os.path.dirname(__file__))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        # 导入TaskEvaluator和相关模块
        from utils.task_evaluator import TaskEvaluator
        from utils.logger import setup_logger

        # 设置独立的日志记录器（避免冲突）
        setup_logger(log_level=logging.INFO)
        scenario_logger = logging.getLogger(f"scenario_{scenario_id}")

        scenario_logger.info(f"🚀 启动场景 {scenario_id} 评测（进程内执行）")

        # 设置环境变量，让TaskEvaluator使用指定的输出目录
        os.environ['SCENARIO_OUTPUT_DIR'] = scenario_output_dir
        os.environ['DISABLE_AUTO_OUTPUT_DIR'] = 'true'  # 禁用自动输出目录创建

        # 创建TaskEvaluator实例，不使用custom_suffix避免自动生成目录
        evaluator = TaskEvaluator(
            config_file=config_file,
            agent_type='single',
            task_type=mode,
            scenario_id=scenario_id,
            custom_suffix=None  # 不使用后缀，避免自动生成独立目录
        )

        # 强制覆盖输出目录和运行名称，使所有场景输出到同一个主目录
        evaluator.output_dir = scenario_output_dir
        scenario_run_name = f"scenario_{scenario_id}"
        evaluator.run_name = scenario_run_name

        # 重新初始化轨迹记录器，使用场景前缀的文件名和正确的scenario_id
        from utils.trajectory_recorder import TrajectoryRecorder
        evaluator.trajectory_recorder = TrajectoryRecorder(scenario_output_dir, scenario_run_name, scenario_id)

        # 清理环境变量
        if 'SCENARIO_OUTPUT_DIR' in os.environ:
            del os.environ['SCENARIO_OUTPUT_DIR']
        if 'DISABLE_AUTO_OUTPUT_DIR' in os.environ:
            del os.environ['DISABLE_AUTO_OUTPUT_DIR']

        # 运行评测
        scenario_logger.info(f"📋 开始执行场景 {scenario_id} 的任务评测")
        results = evaluator.run_evaluation(scenario_id)

        # 处理评测结果
        scenario_logger.info(f"✅ 场景 {scenario_id} 评测执行完成")

        # 构建场景结果
        summary = results.get('summary', {})
        output_files = results.get('output_files', {})
        # 判断成功标准：对于independent模式，检查子任务完成情况
        success = False
        if mode == 'independent':
            # 对于independent模式，只要有完成的任务就算成功
            success = summary.get('completed_tasks', 0) > 0
        else:
            success = summary.get('completed_tasks', 0) > 0

        scenario_result = {
            'scenario_id': scenario_id,
            'success': success,
            'total_duration': time.time() - scenario_start_time,
            'summary': summary,
            'output_dir': scenario_output_dir,
            'trajectory_file': output_files.get('trajectory_file'),
            'log_file': output_files.get('log_file')
        }

        # 对于independent模式，添加子任务结果
        if mode == 'independent':
            subtask_results = []
            task_results = results.get('task_results', [])
            for task_result in task_results:
                if 'subtask_results' in task_result:
                    subtask_results.extend(task_result['subtask_results'])
            scenario_result['subtask_results'] = subtask_results

        scenario_logger.info(f"🎯 场景 {scenario_id} 完成率: {summary.get('completion_rate', 0):.1%}")
        return scenario_result

    except Exception as e:
        return {
            'scenario_id': scenario_id,
            'success': False,
            'error': str(e),
            'total_duration': time.time() - scenario_start_time,
            'summary': {},
            'output_dir': scenario_output_dir
        }


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


def run_parallel_evaluation(config, config_file, mode, suffix):
    """
    运行并行评测

    Args:
        config: 配置字典
        config_file: 配置文件名
        mode: 评测模式
        suffix: 运行后缀

    Returns:
        int: 退出码
    """
    logger = logging.getLogger(__name__)

    # 获取并行评测配置
    parallel_config = config.get('parallel_evaluation', {})
    if not parallel_config.get('enabled', False):
        logger.error("❌ 并行评测未启用，请在配置文件中设置 parallel_evaluation.enabled = true")
        return 1

    # 场景级并行配置
    scenario_config = parallel_config.get('scenario_parallelism', {})
    max_parallel_scenarios = scenario_config.get('max_parallel_scenarios', 4)

    # 场景选择配置
    scenario_selection = parallel_config.get('scenario_selection', {})

    # 生成运行名称和输出目录
    run_name = RunNamingManager.generate_run_name(
        agent_type='single',
        task_type=f"parallel_{mode}",
        scenario_id="multi",
        config_name=config_file,
        custom_suffix=suffix
    )

    # 创建主输出目录
    base_output_dir = config.get('output_dir', 'output')
    output_dir = RunNamingManager.generate_output_directory(base_output_dir, run_name)
    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"🚀 开始场景级并行评测 - 模式: single_{mode}")
    logger.info(f"📁 输出目录: {output_dir}")

    start_time = time.time()

    try:
        # 获取要评测的场景列表
        scenario_list = get_scenario_list(scenario_selection)
        if not scenario_list:
            logger.error("❌ 没有找到要评测的场景")
            return 1

        logger.info(f"📋 准备并行评测 {len(scenario_list)} 个场景: {scenario_list}")

        # 执行并行评测
        with ProcessPoolExecutor(max_workers=max_parallel_scenarios) as executor:
            # 提交所有场景任务
            future_to_scenario = {
                executor.submit(execute_single_scenario,
                               (config_file, mode, scenario_id, suffix, output_dir, run_name)): scenario_id
                for scenario_id in scenario_list
            }

            # 收集结果
            scenario_results = []
            successful_scenarios = 0
            failed_scenarios = 0

            for future in as_completed(future_to_scenario):
                scenario_id = future_to_scenario[future]

                try:
                    scenario_result = future.result()
                    scenario_results.append(scenario_result)

                    if scenario_result.get('success', False):
                        successful_scenarios += 1
                    else:
                        failed_scenarios += 1

                    logger.info(f"✅ 场景 {scenario_id} 评测完成")

                except Exception as e:
                    logger.exception(f"❌ 场景 {scenario_id} 评测失败: {e}")
                    failed_scenarios += 1

                    # 记录失败场景
                    scenario_results.append({
                        'scenario_id': scenario_id,
                        'success': False,
                        'error': str(e),
                        'total_duration': 0,
                        'summary': {}
                    })

        # 对于independent模式，计算子任务统计
        total_subtasks = 0
        successful_subtasks = 0
        if mode == 'independent':
            for result in scenario_results:
                summary = result.get('summary', {})
                total_subtasks += summary.get('total_tasks', 0)
                successful_subtasks += summary.get('completed_tasks', 0)

        # 生成结果
        total_duration = time.time() - start_time
        results = {
            'run_info': {
                'run_name': run_name,
                'agent_type': 'single',
                'evaluation_type': mode,
                'config_file': config_file,
                'output_dir': output_dir,
                'start_time': datetime.now().isoformat(),
                'total_duration': total_duration,
                'parallel_config': parallel_config
            },
            'scenario_results': scenario_results,
            'overall_summary': {
                'total_scenarios': len(scenario_list),
                'successful_scenarios': successful_scenarios,
                'failed_scenarios': failed_scenarios,
                'scenario_success_rate': successful_scenarios / len(scenario_list) if scenario_list else 0.0
            }
        }

        # 为independent模式添加子任务统计
        if mode == 'independent':
            results['overall_summary'].update({
                'total_subtasks': total_subtasks,
                'successful_subtasks': successful_subtasks,
                'subtask_success_rate': successful_subtasks / total_subtasks if total_subtasks > 0 else 0.0
            })

        # 保存结果
        save_parallel_results(results, output_dir, mode)

        # 显示结果
        logger.info(f"🎯 并行评测完成")
        logger.info(f"📊 总场景数: {len(scenario_list)}")
        logger.info(f"✅ 成功场景: {successful_scenarios}")
        logger.info(f"❌ 失败场景: {failed_scenarios}")
        logger.info(f"📊 场景成功率: {successful_scenarios / len(scenario_list):.1%}")
        logger.info(f"📊 总耗时: {total_duration:.2f}秒")
        logger.info(f"📁 输出目录: {output_dir}")

        return 0

    except Exception as e:
        logger.exception(f"❌ 并行评测执行失败: {e}")
        return 1


def get_scenario_list(scenario_selection):
    """
    根据配置获取要评测的场景列表

    Args:
        scenario_selection: 场景选择配置

    Returns:
        List[str]: 场景ID列表
    """
    mode = scenario_selection.get('mode', 'range')

    if mode == 'all':
        # 扫描data/scene目录获取所有场景
        scene_dir = 'data/scene'
        if not os.path.exists(scene_dir):
            raise RuntimeError(f"场景目录不存在: {scene_dir}")

        scenarios = []
        for filename in os.listdir(scene_dir):
            if filename.endswith('_scene.json'):
                scenario_id = filename.replace('_scene.json', '')
                scenarios.append(scenario_id)
        scenarios.sort()
        return scenarios

    elif mode == 'range':
        range_config = scenario_selection.get('range', {})
        start = range_config.get('start', '00001')
        end = range_config.get('end', '00010')

        # 生成范围内的场景ID
        start_num = int(start)
        end_num = int(end)
        scenarios = [f"{i:05d}" for i in range(start_num, end_num + 1)]
        return scenarios

    elif mode == 'list':
        return scenario_selection.get('list', ['00001'])

    else:
        raise ValueError(f"不支持的场景选择模式: {mode}")


def save_parallel_results(results, output_dir, evaluation_type):
    """
    保存并行评测结果（合并为meta信息文件）

    Args:
        results: 评测结果数据
        output_dir: 输出目录
        evaluation_type: 评测类型
    """
    try:
        # 只保存一个包含关键meta信息的文件
        meta_file = os.path.join(output_dir, "parallel_evaluation_meta.json")

        # 提取关键meta信息
        run_info = results.get('run_info', {})
        overall_summary = results.get('overall_summary', {})
        scenario_results = results.get('scenario_results', [])

        meta_data = {
            'evaluation_info': {
                'run_name': run_info.get('run_name', 'unknown'),
                'evaluation_type': evaluation_type,
                'agent_type': run_info.get('agent_type', 'unknown'),
                'start_time': run_info.get('start_time', ''),
                'total_duration': run_info.get('total_duration', 0),
                'output_dir': run_info.get('output_dir', '')
            },
            'overall_statistics': {
                'total_scenarios': overall_summary.get('total_scenarios', 0),
                'successful_scenarios': overall_summary.get('successful_scenarios', 0),
                'failed_scenarios': overall_summary.get('failed_scenarios', 0),
                'scenario_success_rate': overall_summary.get('scenario_success_rate', 0.0)
            },
            'scenario_summary': []
        }

        # 添加independent模式的子任务统计
        if evaluation_type == 'independent':
            meta_data['overall_statistics'].update({
                'total_subtasks': overall_summary.get('total_subtasks', 0),
                'successful_subtasks': overall_summary.get('successful_subtasks', 0),
                'subtask_success_rate': overall_summary.get('subtask_success_rate', 0.0)
            })

            # 计算任务类别统计
            category_stats = {}
            for scenario_result in scenario_results:
                subtask_results = scenario_result.get('subtask_results', [])
                for subtask in subtask_results:
                    category = subtask.get('task_category', 'unknown')
                    if category not in category_stats:
                        category_stats[category] = {'total': 0, 'completed': 0}
                    category_stats[category]['total'] += 1
                    if subtask.get('completed', False):
                        category_stats[category]['completed'] += 1

            # 计算每个类别的完成率
            for category, stats in category_stats.items():
                stats['completion_rate'] = stats['completed'] / stats['total'] if stats['total'] > 0 else 0.0

            meta_data['task_category_statistics'] = category_stats

        # 添加场景级别的汇总信息
        for scenario_result in scenario_results:
            scenario_summary = {
                'scenario_id': scenario_result.get('scenario_id', 'unknown'),
                'success': scenario_result.get('success', False),
                'duration': scenario_result.get('total_duration', 0)
            }

            summary = scenario_result.get('summary', {})
            scenario_summary.update({
                'completion_rate': summary.get('completion_rate', 0.0),
                'total_steps': summary.get('total_steps', 0),
                'completed_tasks': summary.get('completed_tasks', 0),
                'total_tasks': summary.get('total_tasks', 0)
            })

            meta_data['scenario_summary'].append(scenario_summary)

        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=2)

        logger = logging.getLogger(__name__)
        logger.info(f"📊 并行评测meta信息已保存: {meta_file}")

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception(f"❌ 保存结果失败: {e}")


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

    # 检查是否启用并行模式（命令行参数或配置文件）
    parallel_enabled = args.parallel
    if not parallel_enabled:
        # 检查配置文件中的并行设置
        parallel_config = config.get('parallel_evaluation', {})
        parallel_enabled = parallel_config.get('enabled', False)
        if parallel_enabled:
            logger.info("🔄 检测到配置文件中启用了并行评测模式")

    if parallel_enabled:
        if args.parallel:
            logger.info("🔄 通过命令行参数启用并行评测模式")
        return run_parallel_evaluation(config, args.config, mode, suffix)

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

        # 如果设置了环境变量，使用指定的输出目录
        scenario_output_dir = os.environ.get('SCENARIO_OUTPUT_DIR')
        if scenario_output_dir:
            evaluator.output_dir = scenario_output_dir
            # 重新初始化轨迹记录器到指定目录，传递正确的scenario_id
            from utils.trajectory_recorder import TrajectoryRecorder
            evaluator.trajectory_recorder = TrajectoryRecorder(scenario_output_dir, evaluator.run_name, scenario)
            logger.info(f"📁 使用指定输出目录: {scenario_output_dir}")

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
