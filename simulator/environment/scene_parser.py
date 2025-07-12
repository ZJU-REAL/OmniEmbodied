import os
import json
from typing import Dict, List, Optional, Any
import yaml

class SceneParser:
    """场景解析器 - 用于解析场景和（已废弃：智能体只能通过simulator_config.yaml加载）"""
    
    def __init__(self):
        """初始化场景解析器"""
        self.supported_formats = {
            '.json': self._parse_json,
            '.yaml': self._parse_yaml,
            '.yml': self._parse_yaml
        }
    
    def _parse_json(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        解析JSON文件
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            解析后的数据字典，解析失败则返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            return None
        except Exception as e:
            print(f"读取文件时出错: {e}")
            return None
    
    def _parse_yaml(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        解析YAML文件
        
        Args:
            file_path: YAML文件路径
            
        Returns:
            解析后的数据字典，解析失败则返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"YAML解析错误: {e}")
            return None
        except Exception as e:
            print(f"读取文件时出错: {e}")
            return None
    
    def parse_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        根据文件扩展名选择适当的解析方法
        
        Args:
            file_path: 文件路径
            
        Returns:
            解析后的数据字典，解析失败则返回None
        """
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return None
        
        _, ext = os.path.splitext(file_path.lower())
        if ext not in self.supported_formats:
            print(f"不支持的文件格式: {ext}")
            return None
        
        return self.supported_formats[ext](file_path)
    
    def parse_scene_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        解析场景配置文件
        
        Args:
            file_path: 场景配置文件路径
            
        Returns:
            解析后的场景数据字典，解析失败则返回None
        """
        data = self.parse_file(file_path)
        if not data:
            return None
        
        # 验证场景数据的基本结构
        if 'rooms' not in data:
            print("场景配置缺少 'rooms' 字段")
            return None
        
        # 可以在这里添加更多的验证逻辑
        
        return data 