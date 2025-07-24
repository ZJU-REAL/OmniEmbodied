#!/usr/bin/env python3
"""
批量更新任务文件的脚本
功能：
1. 重新修改智能体的重量：
   - 非move任务：max_weight为5-30之间的随机整数
   - move任务：max_weight为[0, 物体重量-1]之间的随机整数
2. 对于compound_collaboration任务，修改任务描述：
   - 删除开头的"Cooperatively"
   - 如果命令中有"and"，则在"and"后添加"Cooperatively"
"""

import json
import os
import random
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

class TaskFileUpdater:
    def __init__(self, task_dir: str, scene_dir: str):
        """
        初始化更新器
        
        Args:
            task_dir: 任务文件目录路径
            scene_dir: 场景文件目录路径
        """
        self.task_dir = Path(task_dir)
        self.scene_dir = Path(scene_dir)
        self.scene_cache = {}  # 缓存场景文件数据
        
    def load_scene_file(self, scene_id: str) -> Optional[Dict[str, Any]]:
        """
        加载场景文件数据
        
        Args:
            scene_id: 场景ID
            
        Returns:
            场景数据字典，如果文件不存在则返回None
        """
        if scene_id in self.scene_cache:
            return self.scene_cache[scene_id]
            
        scene_file = self.scene_dir / f"{scene_id}_scene.json"
        if not scene_file.exists():
            print(f"警告: 场景文件 {scene_file} 不存在")
            return None
            
        try:
            with open(scene_file, 'r', encoding='utf-8') as f:
                scene_data = json.load(f)
                self.scene_cache[scene_id] = scene_data
                return scene_data
        except Exception as e:
            print(f"错误: 无法加载场景文件 {scene_file}: {e}")
            return None
    
    def get_object_weight(self, scene_data: Dict[str, Any], object_id: str) -> Optional[float]:
        """
        从场景数据中获取物体重量
        
        Args:
            scene_data: 场景数据
            object_id: 物体ID
            
        Returns:
            物体重量，如果找不到则返回None
        """
        if not scene_data or 'objects' not in scene_data:
            return None
            
        for obj in scene_data['objects']:
            if obj.get('id') == object_id:
                return obj.get('properties', {}).get('weight')
        
        return None
    
    def is_move_task(self, task: Dict[str, Any]) -> bool:
        """
        判断是否为move任务（验证location_id的任务）
        
        Args:
            task: 任务数据
            
        Returns:
            如果是move任务返回True，否则返回False
        """
        validation_checks = task.get('validation_checks', [])
        for check in validation_checks:
            if 'location_id' in check:
                return True
        return False
    
    def get_moved_object_ids(self, task: Dict[str, Any]) -> List[str]:
        """
        获取被搬运物体的ID列表
        
        Args:
            task: 任务数据
            
        Returns:
            物体ID列表
        """
        object_ids = []
        validation_checks = task.get('validation_checks', [])
        for check in validation_checks:
            if 'location_id' in check and 'id' in check:
                object_ids.append(check['id'])
        return object_ids
    
    def calculate_max_weight_for_move_task(self, task_data: Dict[str, Any]) -> int:
        """
        为move任务计算max_weight
        
        Args:
            task_data: 任务数据
            
        Returns:
            计算出的max_weight值
        """
        scene_id = task_data.get('scene_id')
        if not scene_id:
            print("警告: 任务文件中没有scene_id，使用默认值")
            return random.randint(5, 30)
        
        scene_data = self.load_scene_file(scene_id)
        if not scene_data:
            print(f"警告: 无法加载场景文件 {scene_id}，使用默认值")
            return random.randint(5, 30)
        
        # 获取所有被搬运物体的重量
        max_object_weight = 0
        for task in task_data.get('tasks', []):
            if self.is_move_task(task):
                object_ids = self.get_moved_object_ids(task)
                for object_id in object_ids:
                    weight = self.get_object_weight(scene_data, object_id)
                    if weight is not None:
                        max_object_weight = max(max_object_weight, weight)
        
        if max_object_weight > 0:
            # 返回[0, 物体重量-1]之间的随机整数，但至少为1
            return max(1, random.randint(0, max(1, int(max_object_weight) - 1)))
        else:
            print("警告: 未找到物体重量信息，使用默认值")
            return random.randint(5, 30)
    
    def update_agent_weights(self, task_data: Dict[str, Any]) -> None:
        """
        更新智能体的重量限制
        
        Args:
            task_data: 任务数据
        """
        # 检查是否有move任务
        has_move_task = False
        for task in task_data.get('tasks', []):
            if self.is_move_task(task):
                has_move_task = True
                break
        
        # 计算新的max_weight
        if has_move_task:
            new_weight = self.calculate_max_weight_for_move_task(task_data)
        else:
            new_weight = random.randint(5, 30)
        
        # 更新所有智能体的max_weight
        for agent in task_data.get('agents_config', []):
            agent['max_weight'] = float(new_weight)
    
    def update_compound_collaboration_description(self, task: Dict[str, Any]) -> None:
        """
        更新compound_collaboration任务的描述
        
        Args:
            task: 任务数据
        """
        if task.get('task_category') != 'compound_collaboration':
            return
        
        description = task.get('task_description', '')
        if not description:
            return
        
        # 删除开头的"Cooperatively"
        if description.startswith('Cooperatively '):
            description = description[len('Cooperatively '):]
        
        # 如果有"and"，在"and"后添加"Cooperatively"
        if ' and ' in description:
            # 使用正则表达式找到第一个" and "并在其后添加"Cooperatively"
            description = re.sub(r' and ', ' and cooperatively ', description, count=1)
        
        task['task_description'] = description
    
    def update_task_file(self, task_file_path: Path) -> bool:
        """
        更新单个任务文件
        
        Args:
            task_file_path: 任务文件路径
            
        Returns:
            更新成功返回True，否则返回False
        """
        try:
            # 读取任务文件
            with open(task_file_path, 'r', encoding='utf-8') as f:
                task_data = json.load(f)
            
            # 更新智能体重量
            self.update_agent_weights(task_data)
            
            # 更新compound_collaboration任务描述
            for task in task_data.get('tasks', []):
                self.update_compound_collaboration_description(task)
            
            # 写回文件
            with open(task_file_path, 'w', encoding='utf-8') as f:
                json.dump(task_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"错误: 更新文件 {task_file_path} 失败: {e}")
            return False
    
    def update_all_task_files(self) -> None:
        """
        更新所有任务文件
        """
        if not self.task_dir.exists():
            print(f"错误: 任务目录 {self.task_dir} 不存在")
            return
        
        task_files = list(self.task_dir.glob("*_task.json"))
        if not task_files:
            print(f"警告: 在目录 {self.task_dir} 中没有找到任务文件")
            return
        
        print(f"找到 {len(task_files)} 个任务文件")
        
        success_count = 0
        for task_file in sorted(task_files):
            print(f"正在处理: {task_file.name}")
            if self.update_task_file(task_file):
                success_count += 1
        
        print(f"完成! 成功更新了 {success_count}/{len(task_files)} 个文件")

def main():
    """
    主函数
    """
    # 设置随机种子以便复现结果（可选）
    random.seed(42)
    
    # 设置目录路径
    base_dir = "/home/wzx/workspace/OmniEmbodied/data/eval/multi-independent"
    task_dir = f"{base_dir}/task"
    scene_dir = f"{base_dir}/scene"
    
    # 创建更新器并执行更新
    updater = TaskFileUpdater(task_dir, scene_dir)
    updater.update_all_task_files()

if __name__ == "__main__":
    main()
