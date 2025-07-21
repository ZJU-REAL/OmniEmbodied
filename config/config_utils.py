import os
import logging
from typing import Dict, Any, Optional, List
from .config_manager import get_config_manager
from .config_validator import ConfigValidator

logger = logging.getLogger(__name__)

def apply_runtime_overrides_from_env(config_name: str, prefix: str = "OMNI_"):
    """
    从环境变量应用配置覆盖
    
    Args:
        config_name: 配置名称
        prefix: 环境变量前缀
    """
    config_manager = get_config_manager()
    
    for key, value in os.environ.items():
        if key.startswith(prefix):
            # 移除前缀并转换为配置键
            config_key = key[len(prefix):].lower().replace('_', '.')
            
            # 转换值类型
            converted_value = config_manager._convert_value_type(value)
            
            config_manager.set_runtime_override(config_name, config_key, converted_value)
            logger.info(f"从环境变量应用覆盖: {config_key} = {converted_value}")

def load_and_validate_config(config_name: str, validate: bool = True) -> Dict[str, Any]:
    """
    加载并验证配置
    
    Args:
        config_name: 配置名称
        validate: 是否进行验证
        
    Returns:
        Dict[str, Any]: 配置字典
    """
    config_manager = get_config_manager()
    config = config_manager.get_config(config_name)
    
    if validate:
        if not ConfigValidator.validate_config_file(config_manager, config_name):
            logger.warning(f"配置 {config_name} 验证失败，但仍将使用")
    
    return config

def get_llm_config() -> Dict[str, Any]:
    """获取LLM配置"""
    return load_and_validate_config('llm_config')

def get_agent_config(agent_type: str = 'single_agent') -> Dict[str, Any]:
    """
    获取智能体配置
    
    Args:
        agent_type: 智能体类型 ('single_agent', 'centralized', 'decentralized')
        
    Returns:
        Dict[str, Any]: 智能体配置
    """
    config_name = f"{agent_type}_config"
    return load_and_validate_config(config_name)

def get_simulator_config() -> Dict[str, Any]:
    """获取模拟器配置"""
    return load_and_validate_config('simulator_config')

def get_data_dir(config_name: str, dataset_name: str) -> str:
    """
    获取数据集目录路径

    Args:
        config_name: 配置名称
        dataset_name: 数据集名称（必需）

    Returns:
        str: 数据集目录路径
    """
    config_manager = get_config_manager()
    return config_manager.get_data_dir(config_name, dataset_name)

def get_scene_dir(config_name: str, dataset_name: str) -> str:
    """获取场景目录路径"""
    config_manager = get_config_manager()
    return config_manager.get_scene_dir(config_name, dataset_name)

def get_task_dir(config_name: str, dataset_name: str) -> str:
    """获取任务目录路径"""
    config_manager = get_config_manager()
    return config_manager.get_task_dir(config_name, dataset_name)

def get_default_dataset(config_name: str) -> str:
    """获取默认数据集名称"""
    config_manager = get_config_manager()
    return config_manager.get_config_section(config_name, 'dataset.default')

def list_available_datasets(config_name: str = 'base_config') -> List[str]:
    """列出可用的数据集"""
    config_manager = get_config_manager()
    return config_manager.list_datasets(config_name)



def create_config_backup(config_name: str, backup_dir: str = "config_backups") -> bool:
    """
    创建配置备份
    
    Args:
        config_name: 配置名称
        backup_dir: 备份目录
        
    Returns:
        bool: 是否成功创建备份
    """
    try:
        config_manager = get_config_manager()
        
        # 确保备份目录存在
        os.makedirs(backup_dir, exist_ok=True)
        
        # 保存配置到备份目录
        success = config_manager.save_config(config_name, backup_dir)
        
        if success:
            logger.info(f"配置 {config_name} 备份成功")
        else:
            logger.error(f"配置 {config_name} 备份失败")
        
        return success
        
    except Exception as e:
        logger.error(f"创建配置备份时发生异常: {e}")
        return False

def list_available_configs() -> Dict[str, list]:
    """
    列出所有可用配置
    
    Returns:
        Dict[str, list]: 按类型分组的配置列表
    """
    config_manager = get_config_manager()
    all_configs = config_manager.list_configs()
    
    categorized_configs = {
        'agent': [],
        'llm': [],
        'simulator': [],
        'data_generation': [],
        'other': []
    }
    
    for config in all_configs:
        if 'agent' in config:
            categorized_configs['agent'].append(config)
        elif 'llm' in config:
            categorized_configs['llm'].append(config)
        elif 'simulator' in config:
            categorized_configs['simulator'].append(config)
        elif any(keyword in config for keyword in ['gen', 'generation', 'dataset']):
            categorized_configs['data_generation'].append(config)
        else:
            categorized_configs['other'].append(config)
    
    return categorized_configs

def get_effective_config_value(config_name: str, key: str) -> Any:
    """
    获取有效的配置值（考虑覆盖）

    Args:
        config_name: 配置名称
        key: 配置键

    Returns:
        Any: 有效配置值

    Raises:
        KeyError: 当配置项不存在时
    """
    config_manager = get_config_manager()
    return config_manager.get_config_section(config_name, key)

def print_config_summary(config_name: str):
    """
    打印配置摘要
    
    Args:
        config_name: 配置名称
    """
    config_manager = get_config_manager()
    config = config_manager.get_config(config_name)
    
    print(f"\n=== 配置摘要: {config_name} ===")
    
    # 显示关键配置
    key_configs = [
        ('默认数据集', 'dataset.default'),
        ('智能体类', 'agent_config.agent_class'),
        ('最大失败次数', 'agent_config.max_failures'),
        ('最大历史长度', 'agent_config.max_history'),
        ('最大总步数', 'execution.max_total_steps'),
        ('每任务最大步数', 'execution.max_steps_per_task'),
        ('评测类型', 'evaluation.task_type'),
        ('并行启用', 'parallel_evaluation.enabled'),
        ('最大并行场景', 'parallel_evaluation.scenario_parallelism.max_parallel_scenarios')
    ]
    
    for name, key in key_configs:
        try:
            value = config_manager.get_config_section(config_name, key)
            print(f"  {name}: {value}")
        except KeyError:
            print(f"  {name}: [配置项不存在]")

    # 显示数据集配置
    try:
        datasets = config_manager.list_datasets(config_name)
        if datasets:
            print(f"\n  可用数据集:")
            for dataset_name in datasets:
                try:
                    dataset_path = config_manager.get_data_dir(config_name, dataset_name)
                    print(f"    {dataset_name}: {dataset_path}")
                except KeyError:
                    pass

            # 显示当前默认数据集
            try:
                default_dataset = config_manager.get_config_section(config_name, 'dataset.default')
                print(f"\n  当前默认数据集: {default_dataset}")
            except KeyError:
                pass
    except KeyError:
        pass  # 没有数据集配置
    
    # 显示运行时覆盖
    if hasattr(config_manager, 'runtime_overrides') and config_name in config_manager.runtime_overrides:
        print(f"\n  运行时覆盖:")
        overrides = config_manager.runtime_overrides[config_name]
        for key, value in overrides.items():
            print(f"    {key}: {value}")
    
    print()
