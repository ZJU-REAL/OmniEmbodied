"""
评测接口 - 为baseline提供的统一评测接口
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class EvaluationInterface:
    """为baseline提供的统一评测接口"""
    
    @staticmethod
    def run_evaluation(config_file: str, agent_type: str, task_type: str,
                      scenario_selection: Dict[str, Any] = None,
                      custom_suffix: str = None) -> Dict[str, Any]:
        """
        统一评测入口

        Args:
            config_file: 配置文件名 ('single_agent_config', 'centralized_config', 'decentralized_config')
            agent_type: 智能体类型 ('single', 'multi')
            task_type: 任务类型 ('sequential', 'combined', 'independent')
            scenario_selection: 场景选择配置
                {
                    'mode': 'range',  # 'all', 'range', 'list'
                    'range': {'start': '00001', 'end': '00010'},
                    'list': ['00001', '00003', '00005'],
                    'task_filter': {
                        'categories': ['direct_command', 'attribute_reasoning']  # 任务类别筛选
                    }
                }
            custom_suffix: 自定义后缀
            
        Returns:
            Dict: 评测结果摘要
        """
        try:
            # 验证参数
            EvaluationInterface._validate_parameters(
                config_file, agent_type, task_type, scenario_selection
            )
            
            # 合并配置文件中的场景选择和任务筛选设置
            merged_scenario_selection = EvaluationInterface._merge_scenario_selection_with_config(
                config_file, scenario_selection
            )

            # 创建评测管理器
            from .evaluation_manager import EvaluationManager

            manager = EvaluationManager(
                config_file=config_file,
                agent_type=agent_type,
                task_type=task_type,
                scenario_selection=merged_scenario_selection,
                custom_suffix=custom_suffix
            )
            
            # 运行评测
            logger.info(f"🚀 开始评测: {config_file} - {agent_type} - {task_type}")
            result = manager.run_evaluation()
            
            # 检查返回结果的结构
            if 'runinfo' in result:
                run_name = result['runinfo'].get('run_id', 'unknown')
                logger.info(f"✅ 评测完成: {run_name}")
            else:
                logger.info("✅ 评测完成")

            return result
            
        except Exception as e:
            logger.error(f"❌ 评测失败: {e}")
            raise

    @staticmethod
    def _merge_scenario_selection_with_config(config_file: str,
                                            scenario_selection: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        合并配置文件中的场景选择和任务筛选设置

        Args:
            config_file: 配置文件名
            scenario_selection: 命令行或API传入的场景选择配置

        Returns:
            Dict: 合并后的场景选择配置
        """
        from config.config_manager import ConfigManager

        # 加载配置文件
        config_manager = ConfigManager()
        config = config_manager.get_config(config_file)

        # 获取配置文件中的场景选择设置
        config_scenario_selection = config.get('parallel_evaluation', {}).get('scenario_selection', {})

        # 如果没有传入scenario_selection，使用配置文件中的设置
        if scenario_selection is None:
            merged_selection = config_scenario_selection.copy()
        else:
            # 合并设置，命令行参数优先
            merged_selection = config_scenario_selection.copy()
            merged_selection.update(scenario_selection)

        # 处理任务筛选：配置文件中的task_filter与传入的task_filter合并
        config_task_filter = config_scenario_selection.get('task_filter', {})
        input_task_filter = scenario_selection.get('task_filter', {}) if scenario_selection else {}

        if config_task_filter or input_task_filter:
            # 合并任务筛选配置
            merged_task_filter = config_task_filter.copy()
            merged_task_filter.update(input_task_filter)

            # 只有在有实际筛选条件时才添加task_filter
            if merged_task_filter.get('categories'):
                merged_selection['task_filter'] = merged_task_filter

        return merged_selection

    @staticmethod
    def _validate_parameters(config_file: str, agent_type: str, task_type: str,
                           scenario_selection: Optional[Dict[str, Any]]):
        """验证参数有效性"""
        # 验证配置文件
        valid_configs = ['single_agent_config', 'centralized_config', 'decentralized_config']
        if config_file not in valid_configs:
            raise ValueError(f"无效的配置文件: {config_file}, 支持的配置: {valid_configs}")
        
        # 验证智能体类型
        valid_agent_types = ['single', 'multi']
        if agent_type not in valid_agent_types:
            raise ValueError(f"无效的智能体类型: {agent_type}, 支持的类型: {valid_agent_types}")
        
        # 验证任务类型
        valid_task_types = ['sequential', 'combined', 'independent']
        if task_type not in valid_task_types:
            raise ValueError(f"无效的任务类型: {task_type}, 支持的类型: {valid_task_types}")
        
        # 验证场景选择
        if scenario_selection is not None:
            from .scenario_selector import ScenarioSelector
            if not ScenarioSelector.validate_scenario_selection(scenario_selection):
                raise ValueError(f"无效的场景选择配置: {scenario_selection}")
    
    @staticmethod
    def parse_scenario_string(scenarios_str: str) -> Dict[str, Any]:
        """
        解析场景选择字符串
        
        Args:
            scenarios_str: 场景选择字符串
                - 'all': 所有场景
                - '00001-00010': 范围场景
                - '00001,00003,00005': 列表场景
                - '00001': 单个场景
        
        Returns:
            Dict: 场景选择配置
        """
        from .scenario_selector import ScenarioSelector
        return ScenarioSelector.parse_scenario_selection_string(scenarios_str)
    
    @staticmethod
    def get_scenario_count(scenario_selection: Dict[str, Any] = None) -> int:
        """获取场景数量"""
        from .scenario_selector import ScenarioSelector
        return ScenarioSelector.get_scenario_count(scenario_selection)
    
    @staticmethod
    def validate_config_file(config_file: str) -> bool:
        """验证配置文件是否存在"""
        from config.config_manager import ConfigManager
        config_manager = ConfigManager()
        try:
            config = config_manager.get_config(config_file)
            return config is not None
        except:
            return False
    
    @staticmethod
    def list_available_configs() -> list:
        """列出可用的配置文件"""
        import os
        import glob

        config_dir = "config/baseline"
        if not os.path.exists(config_dir):
            return []

        config_files = glob.glob(os.path.join(config_dir, "*.yaml"))
        config_names = []

        for config_file in config_files:
            config_name = os.path.basename(config_file)[:-5]  # 移除.yaml后缀
            config_names.append(config_name)

        return sorted(config_names)
    
    @staticmethod
    def get_evaluation_status(run_name: str) -> Dict[str, Any]:
        """获取评测状态"""
        import os
        import json
        
        output_dir = os.path.join('output', run_name)
        if not os.path.exists(output_dir):
            return {'status': 'not_found', 'message': f'运行目录不存在: {run_name}'}
        
        # 检查运行摘要文件
        summary_file = os.path.join(output_dir, 'run_summary.json')
        if os.path.exists(summary_file):
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                return {
                    'status': 'completed',
                    'run_info': summary.get('run_info', {}),
                    'overall_summary': summary.get('overall_summary', {})
                }
            except Exception as e:
                return {'status': 'error', 'message': f'读取摘要文件失败: {e}'}
        else:
            return {'status': 'running', 'message': '评测正在进行中'}


# 便利函数
def run_single_agent_evaluation(task_type: str = 'sequential', 
                               scenarios: str = 'all',
                               suffix: str = 'baseline') -> Dict[str, Any]:
    """运行单智能体评测的便利函数"""
    scenario_selection = EvaluationInterface.parse_scenario_string(scenarios)
    
    return EvaluationInterface.run_evaluation(
        config_file='single_agent_config',
        agent_type='single',
        task_type=task_type,
        scenario_selection=scenario_selection,
        custom_suffix=suffix
    )


def run_multi_agent_evaluation(config_type: str = 'centralized',
                              task_type: str = 'sequential',
                              scenarios: str = 'all',
                              suffix: str = 'baseline') -> Dict[str, Any]:
    """运行多智能体评测的便利函数"""
    config_file = f"{config_type}_config"
    scenario_selection = EvaluationInterface.parse_scenario_string(scenarios)

    return EvaluationInterface.run_evaluation(
        config_file=config_file,
        agent_type='multi',
        task_type=task_type,
        scenario_selection=scenario_selection,
        custom_suffix=suffix
    )


def run_filtered_evaluation(config_file: str, agent_type: str, task_type: str,
                           scenarios: str = 'all',
                           task_categories: List[str] = None,
                           suffix: str = 'filtered') -> Dict[str, Any]:
    """
    运行带任务筛选的评测

    Args:
        config_file: 配置文件名
        agent_type: 智能体类型 ('single', 'multi')
        task_type: 任务类型 ('sequential', 'combined', 'independent')
        scenarios: 场景选择字符串
        task_categories: 任务类别筛选列表，如 ['direct_command', 'attribute_reasoning']
        suffix: 自定义后缀

    Returns:
        Dict: 评测结果
    """
    scenario_selection = EvaluationInterface.parse_scenario_string(scenarios)

    # 添加任务筛选
    if task_categories:
        task_filter = {}
        if task_categories:
            task_filter['categories'] = task_categories

        scenario_selection['task_filter'] = task_filter

    return EvaluationInterface.run_evaluation(
        config_file=config_file,
        agent_type=agent_type,
        task_type=task_type,
        scenario_selection=scenario_selection,
        custom_suffix=suffix
    )


def run_comparison_evaluation(scenarios: str = '00001-00010') -> Dict[str, Any]:
    """运行对比评测的便利函数"""
    scenario_selection = EvaluationInterface.parse_scenario_string(scenarios)
    
    results = {}
    
    # 定义评测配置
    evaluation_configs = [
        {
            'name': 'single_sequential',
            'config_file': 'single_agent_config',
            'agent_type': 'single',
            'task_type': 'sequential'
        },
        {
            'name': 'single_combined',
            'config_file': 'single_agent_config',
            'agent_type': 'single',
            'task_type': 'combined'
        },
        {
            'name': 'single_independent',
            'config_file': 'single_agent_config',
            'agent_type': 'single',
            'task_type': 'independent'
        }
    ]
    
    # 运行所有评测
    for config in evaluation_configs:
        logger.info(f"🚀 运行 {config['name']} 评测...")
        
        try:
            result = EvaluationInterface.run_evaluation(
                config_file=config['config_file'],
                agent_type=config['agent_type'],
                task_type=config['task_type'],
                scenario_selection=scenario_selection,
                custom_suffix=f"comparison_{config['name']}"
            )
            
            results[config['name']] = result
            logger.info(f"✅ {config['name']} 评测完成")
            
        except Exception as e:
            logger.error(f"❌ {config['name']} 评测失败: {e}")
            results[config['name']] = {'status': 'failed', 'error': str(e)}
    
    return results
