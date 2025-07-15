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