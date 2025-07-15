"""
可视化管理器模块
负责管理整个可视化系统的生命周期和配置
"""

import logging
import yaml
import os
from typing import Dict, Optional, Any
from .visualization_data import VisualizationDataProvider
from .web_server import VisualizationWebServer


class VisualizationManager:
    """可视化管理器 - 统一管理可视化系统"""
    
    def __init__(self, world_state, agent_manager, env_manager, config_path: Optional[str] = None, engine=None):
        """
        初始化可视化管理器

        Args:
            world_state: 世界状态对象
            agent_manager: 智能体管理器
            env_manager: 环境管理器
            config_path: 配置文件路径
            engine: 模拟引擎实例
        """
        self.world_state = world_state
        self.agent_manager = agent_manager
        self.env_manager = env_manager
        self.engine = engine

        # 加载配置
        self.config = self._load_config(config_path)
        self.visualization_config = self.config.get('visualization', {})

        # 组件
        self.data_provider = None
        self.web_server = None
        self.is_enabled = False
        self.is_running = False
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """加载配置文件"""
        if config_path is None:
            # 使用根目录下的config/simulator/simulator_config.yaml
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'simulator', 'simulator_config.yaml')
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                print(f"已加载配置文件: {config_path}")
                return config
            else:
                print(f"配置文件不存在: {config_path}，使用默认配置")
                return {}
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}
    
    def initialize(self) -> bool:
        """
        初始化可视化系统
        
        Returns:
            bool: 是否成功初始化
        """
        try:
            # 检查是否启用可视化
            self.is_enabled = self.visualization_config.get('enabled', False)
            
            if not self.is_enabled:
                print("可视化系统已禁用")
                return True

            print("正在初始化可视化系统...")
            
            # 创建数据提供器
            self.data_provider = VisualizationDataProvider(
                self.world_state,
                self.visualization_config,
                self.engine
            )
            
            # 创建Web服务器
            self.web_server = VisualizationWebServer(
                self.data_provider,
                self.visualization_config
            )
            
            print("可视化系统初始化完成")
            return True

        except Exception as e:
            print(f"可视化系统初始化失败: {e}")
            return False
    
    def start(self) -> bool:
        """
        启动可视化系统
        
        Returns:
            bool: 是否成功启动
        """
        if not self.is_enabled:
            return True
        
        if self.is_running:
            print("可视化系统已在运行")
            return True

        try:
            if not self.data_provider or not self.web_server:
                print("可视化系统未正确初始化")
                return False

            # 启动Web服务器
            self.web_server.start()
            self.is_running = True

            server_url = self.web_server.get_server_url()
            print(f"可视化系统已启动，访问地址: {server_url}")

            return True

        except Exception as e:
            print(f"启动可视化系统失败: {e}")
            return False
    
    def stop(self):
        """停止可视化系统"""
        if not self.is_enabled or not self.is_running:
            return
        
        try:
            if self.web_server:
                self.web_server.stop()
            
            self.is_running = False
            print("可视化系统已停止")

        except Exception as e:
            print(f"停止可视化系统失败: {e}")
    
    def is_visualization_enabled(self) -> bool:
        """检查可视化是否启用"""
        return self.is_enabled
    
    def is_visualization_running(self) -> bool:
        """检查可视化是否在运行"""
        return self.is_running
    
    def get_server_url(self) -> Optional[str]:
        """获取Web服务器URL"""
        if self.web_server and self.is_running:
            return self.web_server.get_server_url()
        return None
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        更新配置
        
        Args:
            new_config: 新的配置字典
        """
        self.visualization_config.update(new_config)
        
        # 如果数据提供器存在，更新其配置
        if self.data_provider:
            self.data_provider.config = self.visualization_config
    
    def get_visualization_data(self) -> Optional[Dict[str, Any]]:
        """
        获取当前可视化数据
        
        Returns:
            Dict: 可视化数据，如果未启用则返回None
        """
        if not self.is_enabled or not self.data_provider:
            return None
        
        try:
            return self.data_provider.get_complete_visualization_data()
        except Exception as e:
            print(f"获取可视化数据失败: {e}")
            return None
    
    def get_room_data(self, room_id: str) -> Optional[Dict[str, Any]]:
        """
        获取特定房间的数据
        
        Args:
            room_id: 房间ID
            
        Returns:
            Dict: 房间数据，如果未启用则返回None
        """
        if not self.is_enabled or not self.data_provider:
            return None
        
        try:
            return self.data_provider.get_room_layout_data(room_id)
        except Exception as e:
            print(f"获取房间数据失败: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取可视化系统状态
        
        Returns:
            Dict: 状态信息
        """
        return {
            'enabled': self.is_enabled,
            'running': self.is_running,
            'server_url': self.get_server_url(),
            'config': self.visualization_config,
            'data_provider_available': self.data_provider is not None,
            'web_server_available': self.web_server is not None
        }
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()


def create_visualization_manager(world_state, agent_manager, env_manager,
                               config_path: Optional[str] = None, engine=None) -> VisualizationManager:
    """
    创建可视化管理器的便捷函数

    Args:
        world_state: 世界状态对象
        agent_manager: 智能体管理器
        env_manager: 环境管理器
        config_path: 配置文件路径
        engine: 模拟引擎实例

    Returns:
        VisualizationManager: 可视化管理器实例
    """
    manager = VisualizationManager(world_state, agent_manager, env_manager, config_path, engine)
    
    # 自动初始化
    if not manager.initialize():
        logging.warning("可视化管理器初始化失败")
    
    return manager
