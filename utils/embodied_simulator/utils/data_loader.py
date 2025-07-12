"""
数据加载器 - 从data文件夹加载场景和任务数据
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class DataLoader:
    """数据加载器 - 负责加载场景、任务和验证数据"""
    
    def __init__(self, data_dir: str = None):
        """
        初始化数据加载器
        
        Args:
            data_dir: 数据目录路径，默认为项目根目录下的data文件夹
        """
        if data_dir is None:
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            data_dir = os.path.join(project_root, 'data')
        
        self.data_dir = data_dir
        self.scene_dir = os.path.join(data_dir, 'scene')
        self.task_dir = os.path.join(data_dir, 'task')
        self.verify_dir = os.path.join(data_dir, 'verify')
        
        logger.info(f"数据加载器初始化，数据目录: {data_dir}")
    
    def load_scene(self, scene_id: str) -> Optional[Dict[str, Any]]:
        """
        加载场景数据
        
        Args:
            scene_id: 场景ID
            
        Returns:
            Dict[str, Any]: 场景数据，如果加载失败返回None
        """
        scene_file = os.path.join(self.scene_dir, f"{scene_id}_scene.json")
        
        if not os.path.exists(scene_file):
            logger.error(f"场景文件不存在: {scene_file}")
            return None
        
        try:
            with open(scene_file, 'r', encoding='utf-8') as f:
                scene_data = json.load(f)
            
            logger.info(f"成功加载场景: {scene_id}")
            return scene_data
            
        except Exception as e:
            logger.error(f"加载场景文件失败: {scene_file}, 错误: {e}")
            return None
    
    def load_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        加载任务数据
        
        Args:
            task_id: 任务ID
            
        Returns:
            Dict[str, Any]: 任务数据，如果加载失败返回None
        """
        task_file = os.path.join(self.task_dir, f"{task_id}_task.json")
        
        if not os.path.exists(task_file):
            logger.error(f"任务文件不存在: {task_file}")
            return None
        
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                task_data = json.load(f)
            
            logger.info(f"成功加载任务: {task_id}")
            return task_data
            
        except Exception as e:
            logger.error(f"加载任务文件失败: {task_file}, 错误: {e}")
            return None
    
    def load_verification(self, verify_id: str) -> Optional[Dict[str, Any]]:
        """
        加载验证数据
        
        Args:
            verify_id: 验证ID
            
        Returns:
            Dict[str, Any]: 验证数据，如果加载失败返回None
        """
        verify_file = os.path.join(self.verify_dir, f"{verify_id}_verify.json")
        
        if not os.path.exists(verify_file):
            logger.error(f"验证文件不存在: {verify_file}")
            return None
        
        try:
            with open(verify_file, 'r', encoding='utf-8') as f:
                verify_data = json.load(f)
            
            logger.info(f"成功加载验证数据: {verify_id}")
            return verify_data
            
        except Exception as e:
            logger.error(f"加载验证文件失败: {verify_file}, 错误: {e}")
            return None
    
    def load_complete_scenario(self, scenario_id: str) -> Optional[Tuple[Dict, Dict]]:
        """
        加载完整的场景数据（场景+任务）

        Args:
            scenario_id: 场景ID

        Returns:
            Tuple[Dict, Dict]: (场景数据, 任务数据)，如果任何一个加载失败返回None
        """
        scene_data = self.load_scene(scenario_id)
        task_data = self.load_task(scenario_id)

        if scene_data is None or task_data is None:
            logger.error(f"无法加载完整场景数据: {scenario_id}")
            return None

        return scene_data, task_data
    
    def get_available_scenarios(self) -> List[str]:
        """
        获取所有可用的场景ID
        
        Returns:
            List[str]: 可用的场景ID列表
        """
        scenarios = []
        
        if not os.path.exists(self.scene_dir):
            logger.warning(f"场景目录不存在: {self.scene_dir}")
            return scenarios
        
        for filename in os.listdir(self.scene_dir):
            if filename.endswith('_scene.json'):
                scenario_id = filename.replace('_scene.json', '')
                scenarios.append(scenario_id)
        
        scenarios.sort()
        logger.info(f"找到 {len(scenarios)} 个可用场景: {scenarios}")
        return scenarios
    
    def get_scene_abilities(self, scene_id: str) -> List[str]:
        """
        获取场景中定义的abilities

        Args:
            scene_id: 场景ID

        Returns:
            List[str]: 能力列表
        """
        scene_data = self.load_scene(scene_id)
        if scene_data is None:
            return []

        abilities = scene_data.get('abilities', [])
        logger.info(f"场景 {scene_id} 的abilities: {abilities}")
        return abilities
    
    def get_agent_configs(self, task_id: str) -> List[Dict[str, Any]]:
        """
        获取任务中定义的智能体配置
        
        Args:
            task_id: 任务ID
            
        Returns:
            List[Dict[str, Any]]: 智能体配置列表
        """
        task_data = self.load_task(task_id)
        if task_data is None:
            return []
        
        agent_configs = task_data.get('agents_config', [])
        logger.info(f"任务 {task_id} 的智能体配置: {len(agent_configs)} 个智能体")
        return agent_configs
    
    def get_task_list(self, task_id: str, task_category: str = None) -> List[Dict[str, Any]]:
        """
        获取任务列表

        Args:
            task_id: 任务ID
            task_category: 任务类别（如'direct_command', 'tool_use'等），如果为None则返回所有任务

        Returns:
            List[Dict[str, Any]]: 任务列表
        """
        task_data = self.load_task(task_id)
        if task_data is None:
            return []

        tasks = task_data.get('tasks', [])

        if task_category is None:
            # 返回所有任务
            logger.info(f"任务 {task_id} 的所有任务: {len(tasks)} 个")
            return tasks
        else:
            # 返回指定类别的任务
            filtered_tasks = [task for task in tasks if task.get('task_category') == task_category]
            logger.info(f"任务 {task_id} 的{task_category}任务: {len(filtered_tasks)} 个")
            return filtered_tasks
    
    def validate_scenario_integrity(self, scenario_id: str) -> bool:
        """
        验证场景数据的完整性
        
        Args:
            scenario_id: 场景ID
            
        Returns:
            bool: 是否完整
        """
        scene_data, task_data = self.load_complete_scenario(scenario_id)

        if scene_data is None or task_data is None:
            return False
        
        # 检查场景数据必要字段
        required_scene_fields = ['rooms', 'objects']
        for field in required_scene_fields:
            if field not in scene_data:
                logger.error(f"场景数据缺少必要字段: {field}")
                return False
        
        # 检查任务数据必要字段
        required_task_fields = ['agents_config', 'tasks']
        for field in required_task_fields:
            if field not in task_data:
                logger.error(f"任务数据缺少必要字段: {field}")
                return False

        # 检查场景数据必要字段（包括abilities）
        required_scene_fields_extended = ['rooms', 'objects', 'abilities']
        for field in required_scene_fields_extended:
            if field not in scene_data:
                logger.error(f"场景数据缺少必要字段: {field}")
                return False
        
        # 检查场景ID一致性
        if task_data.get('scene_id') != scenario_id:
            logger.error(f"任务数据中的scene_id ({task_data.get('scene_id')}) 与场景ID ({scenario_id}) 不匹配")
            return False
        
        logger.info(f"场景 {scenario_id} 数据完整性验证通过")
        return True


# 创建全局数据加载器实例
default_data_loader = DataLoader()


def load_scenario_for_testing(scenario_id: str = "00001") -> Tuple[Dict, Dict]:
    """
    为测试加载场景数据的便捷函数

    Args:
        scenario_id: 场景ID，默认为"00001"

    Returns:
        Tuple[Dict, Dict]: (场景数据, 任务数据)
    """
    return default_data_loader.load_complete_scenario(scenario_id)
