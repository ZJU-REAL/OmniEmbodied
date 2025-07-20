import os
import yaml
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    配置管理器，用于加载和管理配置文件
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录，如果未指定则使用默认路径
        """
        # 默认使用项目根目录下的config/baseline目录
        self.config_dir = config_dir or os.path.join(os.path.dirname(__file__), 'baseline')
        self.configs = {}
    
    def load_config(self, config_name: str) -> Dict[str, Any]:
        """
        加载指定名称的配置文件
        
        Args:
            config_name: 配置文件名称（不含扩展名）
            
        Returns:
            Dict[str, Any]: 配置字典
        """
        # 如果已加载该配置，直接返回
        if config_name in self.configs:
            return self.configs[config_name]
        
        # 构造完整文件路径
        config_path = os.path.join(self.config_dir, f"{config_name}.yaml")
        
        # 如果配置文件不存在，返回空字典
        if not os.path.exists(config_path):
            logger.warning(f"配置文件不存在: {config_path}")
            self.configs[config_name] = {}
            return {}
        
        try:
            # 打开并解析YAML文件
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 缓存加载的配置
            self.configs[config_name] = config or {}
            return self.configs[config_name]
            
        except Exception as e:
            logger.exception(f"加载配置文件时出错: {e}")
            self.configs[config_name] = {}
            return {}
    
    def get_config(self, config_name: str, reload: bool = False) -> Dict[str, Any]:
        """
        获取配置，如果未加载则自动加载
        
        Args:
            config_name: 配置名称
            reload: 是否强制重新加载
            
        Returns:
            Dict[str, Any]: 配置字典
        """
        if reload or config_name not in self.configs:
            return self.load_config(config_name)
        return self.configs[config_name]
    
    def update_config(self, config_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新配置
        
        Args:
            config_name: 配置名称
            updates: 更新内容
            
        Returns:
            Dict[str, Any]: 更新后的配置字典
        """
        # 如果配置不存在，先加载
        if config_name not in self.configs:
            self.load_config(config_name)
        
        # 更新配置
        self.configs[config_name].update(updates)
        return self.configs[config_name]
        
    def save_config(self, config_name: str, config_dir: Optional[str] = None) -> bool:
        """
        保存配置到文件
        
        Args:
            config_name: 配置名称
            config_dir: 保存目录，如果未指定则使用实例的config_dir
            
        Returns:
            bool: 是否成功保存
        """
        if config_name not in self.configs:
            logger.error(f"配置未加载，无法保存: {config_name}")
            return False
        
        # 确定保存路径
        save_dir = config_dir or self.config_dir
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"{config_name}.yaml")
        
        try:
            # 保存到YAML文件
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(self.configs[config_name], f, default_flow_style=False, allow_unicode=True)
            return True
            
        except Exception as e:
            logger.exception(f"保存配置文件时出错: {e}")
            return False

    def get_data_dir(self, config_name: str) -> str:
        """
        获取数据目录路径

        Args:
            config_name: 配置名称

        Returns:
            str: 数据目录的绝对路径

        Raises:
            KeyError: 配置文件中没有data_dir配置
            FileNotFoundError: 数据目录不存在
        """
        config = self.get_config(config_name)

        # 必须有data_dir配置
        if 'data_dir' not in config:
            raise KeyError(f"配置文件 {config_name} 中缺少必需的 'data_dir' 配置")

        data_dir = config['data_dir']

        # 转换为绝对路径
        if not os.path.isabs(data_dir):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            data_dir = os.path.join(project_root, data_dir)

        # 严格验证路径存在
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"数据目录不存在: {data_dir}")

        return data_dir

    def get_scene_dir(self, config_name: str) -> str:
        """
        获取场景目录路径

        Raises:
            FileNotFoundError: 场景目录不存在
        """
        data_dir = self.get_data_dir(config_name)
        scene_dir = os.path.join(data_dir, 'scene')

        if not os.path.exists(scene_dir):
            raise FileNotFoundError(f"场景目录不存在: {scene_dir}")

        return scene_dir

    def get_task_dir(self, config_name: str) -> str:
        """
        获取任务目录路径

        Raises:
            FileNotFoundError: 任务目录不存在
        """
        data_dir = self.get_data_dir(config_name)
        task_dir = os.path.join(data_dir, 'task')

        if not os.path.exists(task_dir):
            raise FileNotFoundError(f"任务目录不存在: {task_dir}")

        return task_dir