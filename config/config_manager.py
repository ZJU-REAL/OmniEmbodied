import os
import yaml
import logging
import threading
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import re

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    统一配置管理器
    支持配置继承、环境变量替换、命令行参数覆盖等功能
    """

    def __init__(self, config_root: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_root: 配置根目录，默认为当前文件所在目录
        """
        self.config_root = config_root or os.path.dirname(__file__)
        self.configs = {}
        self.config_metadata = {}  # 存储配置元数据（如文件路径等）
        self.runtime_overrides = {}  # 运行时覆盖配置
        self._lock = threading.RLock()

        # 配置目录映射
        self.config_dirs = {
            'baseline': os.path.join(self.config_root, 'baseline'),
            'simulator': os.path.join(self.config_root, 'simulator'),
            'data_generation': os.path.join(self.config_root, 'data_generation')
        }

    def _find_config_file(self, config_name: str) -> Optional[str]:
        """查找配置文件"""
        # 移除 _config 后缀（如果存在）
        clean_name = config_name.replace('_config', '')

        # 可能的文件名
        possible_names = [
            f"{config_name}.yaml",
            f"{clean_name}.yaml",
            f"{clean_name}_config.yaml"
        ]

        # 在所有配置目录中查找
        for dir_name, dir_path in self.config_dirs.items():
            for filename in possible_names:
                file_path = os.path.join(dir_path, filename)
                if os.path.exists(file_path):
                    return file_path

        return None

    def _resolve_environment_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析环境变量"""
        def resolve_value(value):
            if isinstance(value, str):
                # 只支持 ${VAR_NAME} 语法，不支持默认值
                pattern = r'\$\{([^}]+)\}'

                def replace_env_var(match):
                    var_name = match.group(1)
                    env_value = os.environ.get(var_name, '')
                    if not env_value:
                        logger.debug(f"环境变量未设置或为空: {var_name}")
                    return env_value

                return re.sub(pattern, replace_env_var, value)
            elif isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve_value(item) for item in value]
            else:
                return value

        return resolve_value(config)

    def _merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并配置"""
        result = base_config.copy()

        for key, value in override_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def _parse_override_key(self, key: str, value: Any) -> Dict[str, Any]:
        """
        解析覆盖键值对，支持嵌套路径

        Args:
            key: 配置键，支持点号分隔的嵌套路径，如 "api.custom.temperature"
            value: 配置值

        Returns:
            Dict[str, Any]: 嵌套的配置字典
        """
        keys = key.split('.')
        result = {}
        current = result

        for i, k in enumerate(keys):
            if i == len(keys) - 1:
                # 最后一个键，设置值
                current[k] = value
            else:
                # 中间键，创建嵌套字典
                current[k] = {}
                current = current[k]

        return result

    def _convert_value_type(self, value: str) -> Any:
        """
        转换字符串值为合适的类型

        Args:
            value: 字符串值

        Returns:
            Any: 转换后的值
        """
        # 布尔值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'

        # 整数
        try:
            return int(value)
        except ValueError:
            pass

        # 浮点数
        try:
            return float(value)
        except ValueError:
            pass

        # 列表（逗号分隔）
        if ',' in value:
            return [item.strip() for item in value.split(',')]

        # 字符串
        return value

    def _load_config_file(self, config_path: str) -> Dict[str, Any]:
        """加载单个配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}

            # 处理配置继承
            if 'extends' in config:
                base_config_name = config.pop('extends')
                base_config = self.get_config(base_config_name)
                config = self._merge_configs(base_config, config)

            # 解析环境变量
            config = self._resolve_environment_variables(config)

            return config

        except Exception as e:
            logger.error(f"加载配置文件失败 {config_path}: {e}")
            return {}

    def load_config(self, config_name: str, force_reload: bool = False) -> Dict[str, Any]:
        """
        加载配置文件

        Args:
            config_name: 配置名称
            force_reload: 是否强制重新加载

        Returns:
            Dict[str, Any]: 配置字典
        """
        with self._lock:
            # 如果已缓存且不强制重载，直接返回
            if config_name in self.configs and not force_reload:
                config = self.configs[config_name]
            else:
                # 查找配置文件
                config_path = self._find_config_file(config_name)
                if not config_path:
                    logger.warning(f"配置文件不存在: {config_name}")
                    config = {}
                else:
                    # 加载配置
                    config = self._load_config_file(config_path)

                    # 缓存配置和元数据
                    self.config_metadata[config_name] = {
                        'path': config_path
                    }

                    logger.debug(f"配置已加载: {config_name} from {config_path}")

            # 应用运行时覆盖
            if config_name in self.runtime_overrides:
                config = self._merge_configs(config, self.runtime_overrides[config_name])
                logger.debug(f"已应用运行时覆盖: {config_name}")

            # 缓存最终配置
            self.configs[config_name] = config
            return config

    def get_config(self, config_name: str, reload: bool = False) -> Dict[str, Any]:
        """
        获取配置

        Args:
            config_name: 配置名称
            reload: 是否重新加载

        Returns:
            Dict[str, Any]: 配置字典
        """
        return self.load_config(config_name, force_reload=reload)

    def set_runtime_override(self, config_name: str, key: str, value: Any):
        """
        设置运行时配置覆盖

        Args:
            config_name: 配置名称
            key: 配置键，支持点号分隔的嵌套路径
            value: 配置值
        """
        with self._lock:
            if config_name not in self.runtime_overrides:
                self.runtime_overrides[config_name] = {}

            override_dict = self._parse_override_key(key, value)
            self.runtime_overrides[config_name] = self._merge_configs(
                self.runtime_overrides[config_name],
                override_dict
            )

            # 如果配置已加载，需要重新加载以应用覆盖
            if config_name in self.configs:
                self.load_config(config_name, force_reload=True)

            logger.info(f"设置运行时覆盖: {config_name}.{key} = {value}")

    def set_runtime_overrides_from_dict(self, config_name: str, overrides: Dict[str, Any]):
        """
        从字典设置运行时配置覆盖

        Args:
            config_name: 配置名称
            overrides: 覆盖配置字典
        """
        with self._lock:
            if config_name not in self.runtime_overrides:
                self.runtime_overrides[config_name] = {}

            self.runtime_overrides[config_name] = self._merge_configs(
                self.runtime_overrides[config_name],
                overrides
            )

            # 如果配置已加载，需要重新加载以应用覆盖
            if config_name in self.configs:
                self.load_config(config_name, force_reload=True)

            logger.info(f"设置运行时覆盖字典: {config_name}")

    def clear_runtime_overrides(self, config_name: Optional[str] = None):
        """
        清除运行时配置覆盖

        Args:
            config_name: 配置名称，如果为None则清除所有覆盖
        """
        with self._lock:
            if config_name:
                if config_name in self.runtime_overrides:
                    del self.runtime_overrides[config_name]
                    # 重新加载配置
                    if config_name in self.configs:
                        self.load_config(config_name, force_reload=True)
                    logger.info(f"已清除运行时覆盖: {config_name}")
            else:
                self.runtime_overrides.clear()
                # 重新加载所有已缓存的配置
                for config_name in list(self.configs.keys()):
                    self.load_config(config_name, force_reload=True)
                logger.info("已清除所有运行时覆盖")


    def get_config_section(self, config_name: str, section: str) -> Any:
        """
        获取配置的特定部分

        Args:
            config_name: 配置名称
            section: 配置节名称，支持点号分隔的嵌套路径

        Returns:
            Any: 配置值

        Raises:
            KeyError: 当配置项不存在时
        """
        config = self.get_config(config_name)

        # 支持嵌套路径，如 "agent.max_failures"
        keys = section.split('.')
        value = config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                raise KeyError(f"配置项不存在: {config_name}.{section}")

        return value

    def update_config(self, config_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新配置（仅内存中）

        Args:
            config_name: 配置名称
            updates: 更新内容

        Returns:
            Dict[str, Any]: 更新后的配置字典
        """
        with self._lock:
            if config_name not in self.configs:
                self.load_config(config_name)

            self.configs[config_name] = self._merge_configs(self.configs[config_name], updates)
            return self.configs[config_name]

    def save_config(self, config_name: str, config_dir: Optional[str] = None) -> bool:
        """
        保存配置到文件

        Args:
            config_name: 配置名称
            config_dir: 保存目录，如果未指定则使用原目录

        Returns:
            bool: 是否成功保存
        """
        if config_name not in self.configs:
            logger.error(f"配置未加载，无法保存: {config_name}")
            return False

        try:
            # 确定保存路径
            if config_dir:
                save_path = os.path.join(config_dir, f"{config_name}.yaml")
            else:
                metadata = self.config_metadata.get(config_name, {})
                save_path = metadata.get('path')
                if not save_path:
                    save_path = os.path.join(self.config_dirs['baseline'], f"{config_name}.yaml")

            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # 保存配置
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(
                    self.configs[config_name],
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2
                )

            logger.info(f"配置已保存: {config_name} to {save_path}")
            return True

        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False

    def get_data_dir(self, config_name: str, dataset_name: str) -> str:
        """
        获取数据集目录路径

        Args:
            config_name: 配置名称
            dataset_name: 数据集名称（必需）

        Returns:
            str: 数据集目录的绝对路径
        """
        config = self.get_config(config_name)

        if 'data' not in config:
            raise KeyError(f"配置文件 {config_name} 中缺少必需的 'data' 配置")

        data_config = config['data']

        if 'datasets' not in data_config:
            raise KeyError(f"配置文件 {config_name} 中缺少 'data.datasets' 配置")

        datasets = data_config['datasets']
        if dataset_name not in datasets:
            raise KeyError(f"数据集 '{dataset_name}' 不存在，可用数据集: {list(datasets.keys())}")

        data_dir = datasets[dataset_name]

        # 转换为绝对路径
        if not os.path.isabs(data_dir):
            project_root = os.path.dirname(self.config_root)
            data_dir = os.path.join(project_root, data_dir)

        return data_dir


    def get_scene_dir(self, config_name: str, dataset_name: str) -> str:
        """
        获取场景目录路径

        Args:
            config_name: 配置名称
            dataset_name: 数据集名称（必需）

        Returns:
            str: 场景目录的绝对路径
        """
        data_dir = self.get_data_dir(config_name, dataset_name)

        # 获取场景子目录名称
        config = self.get_config(config_name)
        scene_subdir = 'scene'  # 默认值

        if 'data' in config and 'subdirs' in config['data']:
            scene_subdir = config['data']['subdirs'].get('scene', 'scene')

        scene_dir = os.path.join(data_dir, scene_subdir)
        return scene_dir

    def get_task_dir(self, config_name: str, dataset_name: str) -> str:
        """
        获取任务目录路径

        Args:
            config_name: 配置名称
            dataset_name: 数据集名称（必需）

        Returns:
            str: 任务目录的绝对路径
        """
        data_dir = self.get_data_dir(config_name, dataset_name)

        # 获取任务子目录名称
        config = self.get_config(config_name)
        task_subdir = 'task'  # 默认值

        if 'data' in config and 'subdirs' in config['data']:
            task_subdir = config['data']['subdirs'].get('task', 'task')

        task_dir = os.path.join(data_dir, task_subdir)
        return task_dir

    def list_datasets(self, config_name: str) -> List[str]:
        """
        列出所有可用的数据集

        Args:
            config_name: 配置名称

        Returns:
            List[str]: 数据集名称列表
        """
        config = self.get_config(config_name)

        if 'data' not in config or 'datasets' not in config['data']:
            return []

        return list(config['data']['datasets'].keys())

    def get_subdir_name(self, config_name: str, subdir_type: str) -> str:
        """
        获取子目录名称

        Args:
            config_name: 配置名称
            subdir_type: 子目录类型 ('scene', 'task')

        Returns:
            str: 子目录名称
        """
        config = self.get_config(config_name)

        if 'data' not in config or 'subdirs' not in config['data']:
            return subdir_type  # 返回默认名称

        return config['data']['subdirs'].get(subdir_type, subdir_type)

    def list_configs(self) -> List[str]:
        """列出所有可用的配置文件"""
        configs = []

        for dir_name, dir_path in self.config_dirs.items():
            if os.path.exists(dir_path):
                for filename in os.listdir(dir_path):
                    if filename.endswith('.yaml'):
                        config_name = filename[:-5]  # 移除 .yaml 后缀
                        if config_name not in configs:
                            configs.append(config_name)

        return sorted(configs)

    def clear_cache(self):
        """清空配置缓存"""
        with self._lock:
            self.configs.clear()
            self.config_metadata.clear()
            logger.info("配置缓存已清空")


# 全局配置管理器实例和锁
_global_config_manager = None
_global_config_manager_lock = threading.RLock()

def get_config_manager() -> ConfigManager:
    """
    获取全局配置管理器实例（线程安全的单例模式）

    Returns:
        ConfigManager: 全局唯一的配置管理器实例
    """
    global _global_config_manager

    # 双重检查锁定模式，确保线程安全的单例
    if _global_config_manager is None:
        with _global_config_manager_lock:
            if _global_config_manager is None:
                _global_config_manager = ConfigManager()
                logger.debug("创建全局配置管理器实例")

    return _global_config_manager

def reset_config_manager():
    """
    重置全局配置管理器（主要用于测试）

    注意：这会清除所有运行时覆盖和缓存的配置
    """
    global _global_config_manager
    with _global_config_manager_lock:
        if _global_config_manager is not None:
            logger.debug("重置全局配置管理器实例")
        _global_config_manager = None

def ensure_runtime_overrides_applied():
    """
    确保运行时覆盖已应用到全局配置管理器

    这个函数在配置覆盖应用后调用，确保所有后续的配置获取都包含覆盖
    """
    config_manager = get_config_manager()

    # 强制重新加载所有已缓存的配置，以应用运行时覆盖
    with config_manager._lock:
        cached_configs = list(config_manager.configs.keys())
        for config_name in cached_configs:
            if config_name in config_manager.runtime_overrides:
                config_manager.load_config(config_name, force_reload=True)
                logger.debug(f"重新加载配置以应用覆盖: {config_name}")

    logger.info("✅ 运行时覆盖已确保应用到全局配置管理器")