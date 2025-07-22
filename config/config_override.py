import argparse
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from .config_manager import get_config_manager

logger = logging.getLogger(__name__)

class ConfigOverrideParser:
    """配置覆盖参数解析器"""

    @staticmethod
    def _get_available_providers(config_manager=None):
        """动态获取可用的供应商列表"""
        if not config_manager:
            try:
                config_manager = get_config_manager()
            except:
                return ['openai', 'volcengine', 'bailian', 'custom']

        try:
            llm_config = config_manager.get_config('llm_config')
            api_config = llm_config.get('api', {})

            # 优先使用新的 providers 结构
            if 'providers' in api_config:
                providers = list(api_config['providers'].keys())
                logger.debug(f"从新配置结构获取供应商列表: {providers}")
                return providers
            else:
                # 向后兼容：从旧结构中提取
                providers = []
                for key in api_config.keys():
                    if key not in ['provider', 'providers'] and isinstance(api_config[key], dict):
                        providers.append(key)
                logger.debug(f"从旧配置结构获取供应商列表: {providers}")
                return providers or ['openai', 'volcengine', 'bailian', 'custom']
        except Exception as e:
            logger.warning(f"获取供应商列表失败: {e}")
            return ['openai', 'volcengine', 'bailian', 'custom']

    @staticmethod
    def add_config_override_args(parser: argparse.ArgumentParser, config_manager=None):
        """
        为ArgumentParser添加配置覆盖参数

        Args:
            parser: ArgumentParser实例
            config_manager: 配置管理器实例，用于动态获取可用选项
        """
        # 通用配置覆盖参数
        parser.add_argument('--config-override', '-co', action='append',
                          metavar='KEY=VALUE',
                          help='覆盖配置值，格式: key=value，支持嵌套路径如 api.custom.temperature=0.2')

        # 动态获取可用的供应商列表
        available_providers = ConfigOverrideParser._get_available_providers(config_manager)

        # LLM相关覆盖参数
        llm_group = parser.add_argument_group('LLM配置覆盖')
        llm_group.add_argument('--llm-provider', type=str,
                             choices=available_providers,
                             help=f'LLM提供商，可选: {", ".join(available_providers)}')
        llm_group.add_argument('--llm-model', type=str,
                             help='LLM模型名称 (如: gpt-3.5-turbo, deepseek-chat, qwen2.5-72b-instruct)')
        llm_group.add_argument('--llm-temperature', type=float,
                             help='LLM温度参数 (0.0-2.0)')
        llm_group.add_argument('--llm-max-tokens', type=int,
                             help='LLM最大token数')
        llm_group.add_argument('--llm-api-key', type=str,
                             help='LLM API密钥')
        llm_group.add_argument('--llm-endpoint', type=str,
                             help='LLM API端点 (如: https://api.deepseek.com)')
        
        # 提示词覆盖参数
        prompt_group = parser.add_argument_group('提示词配置覆盖')
        prompt_group.add_argument('--system-prompt', type=str,
                                help='系统提示词')
        prompt_group.add_argument('--action-prompt', type=str,
                                help='动作选择提示词')
        prompt_group.add_argument('--coordinator-prompt', type=str,
                                help='协调器提示词 (仅中心化模式)')
        prompt_group.add_argument('--worker-prompt', type=str,
                                help='工作智能体提示词 (仅中心化模式)')
        prompt_group.add_argument('--prompt-file', type=str,
                                help='从文件加载提示词 (JSON格式)')
        
        # 执行相关覆盖参数
        exec_group = parser.add_argument_group('执行配置覆盖')
        exec_group.add_argument('--max-total-steps', type=int,
                              help='最大总执行步数')
        exec_group.add_argument('--max-steps-per-task', type=int,
                              help='每个任务的最大步数')
        exec_group.add_argument('--timeout-seconds', type=int,
                              help='超时时间（秒）')
        
        # 智能体相关覆盖参数
        agent_group = parser.add_argument_group('智能体配置覆盖')
        agent_group.add_argument('--max-failures', type=int,
                               help='最大失败次数')
        agent_group.add_argument('--max-history', type=int,
                               help='最大历史记录长度')
        
        # 并行评测相关覆盖参数
        parallel_group = parser.add_argument_group('并行评测配置覆盖')
        parallel_group.add_argument('--parallel-enabled', action='store_true',
                                  help='启用并行评测')
        parallel_group.add_argument('--parallel-disabled', action='store_true',
                                  help='禁用并行评测')
        parallel_group.add_argument('--max-parallel-scenarios', type=int,
                                  help='最大并行场景数')
        
        # 场景选择相关覆盖参数
        scenario_group = parser.add_argument_group('场景选择配置覆盖')
        scenario_group.add_argument('--scenario-mode', type=str,
                                  choices=['all', 'range', 'list'],
                                  help='场景选择模式')
        scenario_group.add_argument('--scenario-start', type=str,
                                  help='场景范围起始ID')
        scenario_group.add_argument('--scenario-end', type=str,
                                  help='场景范围结束ID')
        scenario_group.add_argument('--scenario-list', type=str,
                                  help='场景ID列表，逗号分隔')

        # 数据集相关覆盖参数
        data_group = parser.add_argument_group('数据集配置覆盖')
        data_group.add_argument('--dataset', type=str,
                              choices=['source', 'eval_single', 'eval_multi', 'sft_single', 'sft_multi'],
                              help='选择使用的数据集')
        data_group.add_argument('--dataset-dir', type=str,
                              help='自定义数据集目录路径（覆盖选定数据集的路径）')

    
    @staticmethod
    def parse_config_override_string(override_str: str) -> Tuple[str, Any]:
        """
        解析配置覆盖字符串
        
        Args:
            override_str: 覆盖字符串，格式为 "key=value"
            
        Returns:
            Tuple[str, Any]: (键, 值)
        """
        if '=' not in override_str:
            raise ValueError(f"无效的配置覆盖格式: {override_str}，应为 key=value")
        
        key, value = override_str.split('=', 1)
        key = key.strip()
        value = value.strip()
        
        # 转换值类型
        config_manager = get_config_manager()
        converted_value = config_manager._convert_value_type(value)
        
        return key, converted_value
    
    @staticmethod
    def load_prompts_from_file(prompt_file: str) -> Dict[str, str]:
        """
        从文件加载提示词
        
        Args:
            prompt_file: 提示词文件路径
            
        Returns:
            Dict[str, str]: 提示词字典
        """
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompts = json.load(f)
            logger.info(f"从文件加载提示词: {prompt_file}")
            return prompts
        except Exception as e:
            logger.error(f"Failed to load prompt file {prompt_file}: {e}")
            return {}
    
    @staticmethod
    def _determine_agent_mode(config_name: str) -> str:
        """
        根据配置名称确定智能体模式
        
        Args:
            config_name: 配置名称
            
        Returns:
            str: 智能体模式
        """
        if 'single' in config_name.lower():
            return 'single_agent'
        elif 'centralized' in config_name.lower():
            return 'centralized'
        elif 'decentralized' in config_name.lower():
            return 'decentralized'
        else:
            return 'single_agent'  # 默认


    @staticmethod
    def apply_config_overrides(args: argparse.Namespace, config_name: str):
        """
        应用配置覆盖到指定配置

        Args:
            args: 解析后的命令行参数
            config_name: 目标配置名称
        """
        config_manager = get_config_manager()

        # 处理通用配置覆盖
        if hasattr(args, 'config_override') and args.config_override:
            for override_str in args.config_override:
                try:
                    key, value = ConfigOverrideParser.parse_config_override_string(override_str)

                    # 检查是否为跨配置文件覆盖（如 llm_config.api.provider）
                    if '.' in key:
                        parts = key.split('.', 1)  # 只分割第一个点
                        potential_config_name = parts[0]
                        remaining_key = parts[1]

                        # 检查是否为已知的配置文件名
                        known_configs = ['llm_config', 'prompts_config', 'simulator_config',
                                       'single_agent_config', 'centralized_config', 'decentralized_config']
                        if potential_config_name in known_configs:
                            # 跨配置文件覆盖：应用到目标配置文件
                            config_manager.set_runtime_override(potential_config_name, remaining_key, value)
                            logger.debug(f"跨配置覆盖: {potential_config_name}.{remaining_key} = {value}")
                        else:
                            # 普通覆盖：应用到当前配置文件
                            config_manager.set_runtime_override(config_name, key, value)
                            logger.debug(f"普通覆盖: {config_name}.{key} = {value}")
                    else:
                        # 普通覆盖：应用到当前配置文件
                        config_manager.set_runtime_override(config_name, key, value)
                        logger.debug(f"普通覆盖: {config_name}.{key} = {value}")

                except Exception as e:
                    logger.error(f"应用配置覆盖失败 {override_str}: {e}")

        # 处理LLM相关覆盖
        llm_overrides = {}
        current_provider = None

        if hasattr(args, 'llm_provider') and args.llm_provider:
            llm_overrides['api.provider'] = args.llm_provider
            current_provider = args.llm_provider
        else:
            # 获取当前provider
            current_provider = config_manager.get_config_section('llm_config', 'api.provider')

        # 检查是否使用新的 providers 结构
        llm_config = config_manager.get_config('llm_config')
        api_config = llm_config.get('api', {})
        use_providers_structure = 'providers' in api_config

        if current_provider:
            # 根据配置结构选择路径
            if use_providers_structure:
                provider_path = f'api.providers.{current_provider}'
            else:
                provider_path = f'api.{current_provider}'

            if hasattr(args, 'llm_model') and args.llm_model:
                llm_overrides[f'{provider_path}.model'] = args.llm_model
            if hasattr(args, 'llm_temperature') and args.llm_temperature is not None:
                llm_overrides[f'{provider_path}.temperature'] = args.llm_temperature
            if hasattr(args, 'llm_max_tokens') and args.llm_max_tokens:
                llm_overrides[f'{provider_path}.max_tokens'] = args.llm_max_tokens
            if hasattr(args, 'llm_api_key') and args.llm_api_key:
                llm_overrides[f'{provider_path}.api_key'] = args.llm_api_key
            if hasattr(args, 'llm_endpoint') and args.llm_endpoint:
                llm_overrides[f'{provider_path}.endpoint'] = args.llm_endpoint

        # 应用LLM覆盖到llm_config
        if llm_overrides:
            for key, value in llm_overrides.items():
                config_manager.set_runtime_override('llm_config', key, value)
                logger.debug(f"应用LLM配置覆盖: {key} = {value}")

        # 处理提示词覆盖
        prompt_overrides = {}

        # 从文件加载提示词
        if hasattr(args, 'prompt_file') and args.prompt_file:
            file_prompts = ConfigOverrideParser.load_prompts_from_file(args.prompt_file)
            prompt_overrides.update(file_prompts)

        # 处理单个提示词参数
        agent_mode = ConfigOverrideParser._determine_agent_mode(config_name)

        if hasattr(args, 'system_prompt') and args.system_prompt:
            if agent_mode == 'single_agent':
                prompt_overrides['single_agent.system_prompt'] = args.system_prompt
            elif agent_mode == 'centralized':
                prompt_overrides['centralized.coordinator_system_prompt'] = args.system_prompt
            elif agent_mode == 'decentralized':
                prompt_overrides['decentralized.agent_system_prompt'] = args.system_prompt

        if hasattr(args, 'action_prompt') and args.action_prompt:
            if agent_mode == 'single_agent':
                prompt_overrides['single_agent.action_prompt'] = args.action_prompt

        if hasattr(args, 'coordinator_prompt') and args.coordinator_prompt:
            if agent_mode == 'centralized':
                prompt_overrides['centralized.coordinator_system_prompt'] = args.coordinator_prompt

        if hasattr(args, 'worker_prompt') and args.worker_prompt:
            if agent_mode == 'centralized':
                prompt_overrides['centralized.worker_system_prompt'] = args.worker_prompt

        # 应用提示词覆盖到prompts_config
        if prompt_overrides:
            for key, value in prompt_overrides.items():
                config_manager.set_runtime_override('prompts_config', key, value)

        # 处理执行相关覆盖
        if hasattr(args, 'max_total_steps') and args.max_total_steps:
            config_manager.set_runtime_override(config_name, 'execution.max_total_steps', args.max_total_steps)
        if hasattr(args, 'max_steps_per_task') and args.max_steps_per_task:
            config_manager.set_runtime_override(config_name, 'execution.max_steps_per_task', args.max_steps_per_task)
        if hasattr(args, 'timeout_seconds') and args.timeout_seconds:
            config_manager.set_runtime_override(config_name, 'execution.timeout_seconds', args.timeout_seconds)

        # 处理智能体相关覆盖
        if hasattr(args, 'max_failures') and args.max_failures:
            config_manager.set_runtime_override(config_name, 'agent_config.max_failures', args.max_failures)
        if hasattr(args, 'max_history') and args.max_history:
            config_manager.set_runtime_override(config_name, 'agent_config.max_history', args.max_history)

        # 处理并行评测相关覆盖
        if hasattr(args, 'parallel_enabled') and args.parallel_enabled:
            config_manager.set_runtime_override(config_name, 'parallel_evaluation.enabled', True)
        if hasattr(args, 'parallel_disabled') and args.parallel_disabled:
            config_manager.set_runtime_override(config_name, 'parallel_evaluation.enabled', False)
        if hasattr(args, 'max_parallel_scenarios') and args.max_parallel_scenarios:
            config_manager.set_runtime_override(config_name, 'parallel_evaluation.scenario_parallelism.max_parallel_scenarios', args.max_parallel_scenarios)

        # 处理场景选择相关覆盖
        if hasattr(args, 'scenario_mode') and args.scenario_mode:
            config_manager.set_runtime_override(config_name, 'parallel_evaluation.scenario_selection.mode', args.scenario_mode)
        if hasattr(args, 'scenario_start') and args.scenario_start:
            config_manager.set_runtime_override(config_name, 'parallel_evaluation.scenario_selection.range.start', args.scenario_start)
        if hasattr(args, 'scenario_end') and args.scenario_end:
            config_manager.set_runtime_override(config_name, 'parallel_evaluation.scenario_selection.range.end', args.scenario_end)
        if hasattr(args, 'scenario_list') and args.scenario_list:
            scenario_ids = [s.strip() for s in args.scenario_list.split(',')]
            config_manager.set_runtime_override(config_name, 'parallel_evaluation.scenario_selection.list', scenario_ids)

        # 处理数据集相关覆盖
        if hasattr(args, 'dataset') and args.dataset:
            config_manager.set_runtime_override(config_name, 'dataset.default', args.dataset)
        if hasattr(args, 'dataset_dir') and args.dataset_dir:
            # 如果指定了数据集名称，覆盖对应的数据集目录
            if hasattr(args, 'dataset') and args.dataset:
                config_manager.set_runtime_override(config_name, f'data.datasets.{args.dataset}', args.dataset_dir)
            else:
                # 如果没有指定数据集，需要先获取当前默认数据集
                current_dataset = config_manager.get_config_section(config_name, 'dataset.default')
                config_manager.set_runtime_override(config_name, f'data.datasets.{current_dataset}', args.dataset_dir)


        logger.info(f"配置覆盖已应用到: {config_name}")

        # 确保运行时覆盖已应用到全局配置管理器
        from .config_manager import ensure_runtime_overrides_applied
        ensure_runtime_overrides_applied()


def create_config_aware_parser(description: str = None) -> argparse.ArgumentParser:
    """
    创建支持配置覆盖的ArgumentParser

    Args:
        description: 程序描述

    Returns:
        argparse.ArgumentParser: 配置了覆盖参数的解析器
    """
    parser = argparse.ArgumentParser(description=description)
    ConfigOverrideParser.add_config_override_args(parser)
    return parser
