import os
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DataLoader:
    """
    数据加载器，用于加载场景和任务JSON配置
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化数据加载器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        
        # 支持多种可能的目录结构
        self.scene_dir = os.path.join(data_dir, "scene")
        self.scenes_dir = os.path.join(data_dir, "scenes")
        self.task_dir = os.path.join(data_dir, "task")
        self.default_dir = os.path.join(data_dir, "default")  # 新增default目录支持
        
        # 缓存已加载的数据
        self._scenes_cache = {}
        self._tasks_cache = {}
    
    def load_scene(self, scene_id: str) -> Optional[Dict[str, Any]]:
        """
        加载场景配置
        
        Args:
            scene_id: 场景ID（如'00001_scene'）
            
        Returns:
            Dict: 场景配置字典，加载失败返回None
        """
        # 如果已缓存，直接返回
        if scene_id in self._scenes_cache:
            return self._scenes_cache[scene_id]
        
        # 尝试从多个目录加载
        for scene_dir in [self.scene_dir, self.scenes_dir, self.default_dir]:
            scene_path = os.path.join(scene_dir, f"{scene_id}.json")
            if os.path.exists(scene_path):
                try:
                    with open(scene_path, 'r', encoding='utf-8') as f:
                        scene_data = json.load(f)
                        self._scenes_cache[scene_id] = scene_data
                        logger.info(f"成功从 {scene_path} 加载场景: {scene_id}")
                        return scene_data
                except Exception as e:
                    logger.exception(f"从 {scene_path} 加载场景失败: {e}")
        
        logger.error(f"场景文件不存在: {scene_id} (已在 scene, scenes, default 目录中查找)")
        return None
    
    def load_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        加载任务配置
        
        Args:
            task_id: 任务ID（如'00001_task'）
            
        Returns:
            Dict: 任务配置字典，加载失败返回None
        """
        # 如果已缓存，直接返回
        if task_id in self._tasks_cache:
            return self._tasks_cache[task_id]
        
        # 尝试从多个目录加载
        for task_dir in [self.task_dir, self.default_dir]:
            task_path = os.path.join(task_dir, f"{task_id}.json")
            if os.path.exists(task_path):
                try:
                    with open(task_path, 'r', encoding='utf-8') as f:
                        task_data = json.load(f)
                        self._tasks_cache[task_id] = task_data
                        logger.info(f"成功从 {task_path} 加载任务: {task_id}")
                        return task_data
                except Exception as e:
                    logger.exception(f"从 {task_path} 加载任务失败: {e}")
        
        logger.error(f"任务文件不存在: {task_id} (已在 task, default 目录中查找)")
        return None
    
    def get_task_scene(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务对应的场景
        
        Args:
            task_id: 任务ID
            
        Returns:
            Dict: 场景配置字典，加载失败返回None
        """
        task_data = self.load_task(task_id)
        if not task_data:
            return None
        
        scene_id = task_data.get('scene_uid')
        if not scene_id:
            logger.error(f"任务中未指定场景ID: {task_id}")
            return None
        
        return self.load_scene(scene_id)
    
    def get_rooms(self, scene_id: str) -> List[Dict[str, Any]]:
        """
        获取场景中的房间列表
        
        Args:
            scene_id: 场景ID
            
        Returns:
            List: 房间配置列表
        """
        scene_data = self.load_scene(scene_id)
        if not scene_data:
            return []
        
        return scene_data.get('rooms', [])
    
    def get_objects(self, scene_id: str) -> List[Dict[str, Any]]:
        """
        获取场景中的物体列表
        
        Args:
            scene_id: 场景ID
            
        Returns:
            List: 物体配置列表
        """
        scene_data = self.load_scene(scene_id)
        if not scene_data:
            return []
        
        return scene_data.get('objects', [])
    
    def get_agents_config(self, task_id: str) -> List[Dict[str, Any]]:
        """
        获取任务中的智能体配置
        
        Args:
            task_id: 任务ID
            
        Returns:
            List: 智能体配置列表
        """
        task_data = self.load_task(task_id)
        if not task_data:
            return []
        
        return task_data.get('agents_config', [])
    
    def get_task_description(self, task_id: str) -> Optional[str]:
        """
        获取任务描述
        
        Args:
            task_id: 任务ID
            
        Returns:
            str: 任务描述文本
        """
        task_data = self.load_task(task_id)
        if not task_data:
            return None
        
        return task_data.get('task_description')


# 创建一个默认实例，方便直接导入使用
default_loader = DataLoader()

def load_scene(scene_id: str) -> Optional[Dict[str, Any]]:
    """便捷函数：加载场景"""
    return default_loader.load_scene(scene_id)

def load_task(task_id: str) -> Optional[Dict[str, Any]]:
    """便捷函数：加载任务"""
    return default_loader.load_task(task_id)

def get_task_scene(task_id: str) -> Optional[Dict[str, Any]]:
    """便捷函数：获取任务对应的场景"""
    return default_loader.get_task_scene(task_id) 