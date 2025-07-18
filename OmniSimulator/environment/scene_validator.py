import os
import json
from typing import Dict, List, Tuple, Any, Optional

class SceneValidator:
    """场景验证器 - 用于检查场景数据的合法性"""
    
    @staticmethod
    def validate_scene(scene_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证场景数据的合法性
        
        Args:
            scene_data: 场景数据字典
            
        Returns:
            Tuple[bool, List[str]]: (是否合法, 错误信息列表)
        """
        errors = []
        
        # 检查基本结构
        if not isinstance(scene_data, dict):
            errors.append("Scene data must be a dictionary")
            return False, errors

        # 检查rooms字段
        if "rooms" not in scene_data:
            errors.append("Scene data must contain 'rooms' field")
            return False, errors

        if not isinstance(scene_data["rooms"], list):
            errors.append("'rooms' field must be a list")
            return False, errors
        
        # 验证每个房间
        room_ids = set()
        for i, room in enumerate(scene_data["rooms"]):
            room_errors = SceneValidator._validate_room(room, i)
            if room_errors:
                errors.extend(room_errors)
            
            # 检查房间ID唯一性
            if room.get("id") in room_ids:
                errors.append(f"Duplicate room ID: {room.get('id')}")
            else:
                room_ids.add(room.get("id"))

        # 验证objects字段(如果存在)
        if "objects" in scene_data:
            if not isinstance(scene_data["objects"], list):
                errors.append("'objects' field must be a list")
            else:
                container_ids = set(room_ids)  # 初始化为房间ID集合
                object_ids = set()
                location_conflicts = []
                
                for i, obj in enumerate(scene_data["objects"]):
                    obj_errors, obj_id = SceneValidator._validate_object(obj, i, room_ids)
                    if obj_errors:
                        errors.extend(obj_errors)
                    
                    # 如果对象是容器，将其ID添加到容器ID集合中
                    if obj.get("properties", {}).get("is_container", False):
                        container_ids.add(obj_id)
                    
                    # 检查对象ID唯一性
                    if obj_id in object_ids:
                        errors.append(f"Duplicate object ID: {obj_id}")
                    else:
                        object_ids.add(obj_id)
                        
                    # 记录存放位置问题(第二轮检查时使用)
                    location_id = obj.get("location_id", "")
                    if location_id:
                        preposition, target_id = SceneValidator._parse_location_id(location_id)
                        if target_id not in container_ids and target_id not in room_ids:
                            location_conflicts.append((obj_id, location_id, target_id))
                
                # 第二轮检查：确认所有对象都有有效的存放位置
                for obj_id, location_id, target_id in location_conflicts:
                    if target_id not in container_ids and target_id not in room_ids:
                        errors.append(f"物体 {obj_id} 的位置 {location_id} 不存在")
                
                # 检查容器关系
                container_errors = SceneValidator.validate_container_relationships(scene_data)
                errors.extend(container_errors)
        
        # 检查是否有错误
        is_valid = len(errors) == 0
        return is_valid, errors
    
    @staticmethod
    def _validate_room(room: Dict[str, Any], index: int) -> List[str]:
        """验证单个房间数据"""
        errors = []
        
        # 检查必要字段
        if not isinstance(room, dict):
            return [f"房间 #{index} 必须是字典类型"]
            
        if "id" not in room:
            errors.append(f"房间 #{index} 缺少'id'字段")
        elif not isinstance(room["id"], str):
            errors.append(f"房间 #{index} 的'id'字段必须是字符串类型")
            
        if "name" not in room:
            errors.append(f"房间 #{index} 缺少'name'字段")
        elif not isinstance(room["name"], str):
            errors.append(f"房间 #{index} 的'name'字段必须是字符串类型")
            
        # 检查properties字段(如果存在)
        if "properties" in room and not isinstance(room["properties"], dict):
            errors.append(f"房间 #{index} 的'properties'字段必须是字典类型")
            
        # 检查连接房间ID列表(如果存在)
        if "connected_to_room_ids" in room:
            if not isinstance(room["connected_to_room_ids"], list):
                errors.append(f"房间 #{index} 的'connected_to_room_ids'字段必须是列表类型")
            else:
                for connected_id in room["connected_to_room_ids"]:
                    if not isinstance(connected_id, str):
                        errors.append(f"房间 #{index} 的连接房间ID必须是字符串类型")
        
        return errors
    
    @staticmethod
    def _validate_object(obj: Dict[str, Any], index: int, room_ids: set) -> Tuple[List[str], str]:
        """验证单个物体数据"""
        errors = []
        obj_id = obj.get("id", f"unknown_{index}")
        
        # 检查必要字段
        if not isinstance(obj, dict):
            return [f"物体 #{index} 必须是字典类型"], obj_id
            
        if "id" not in obj:
            errors.append(f"物体 #{index} 缺少'id'字段")
        elif not isinstance(obj["id"], str):
            errors.append(f"物体 #{index} 的'id'字段必须是字符串类型")
            
        if "name" not in obj:
            errors.append(f"物体 #{index} 缺少'name'字段")
        elif not isinstance(obj["name"], str):
            errors.append(f"物体 #{index} 的'name'字段必须是字符串类型")
            
        if "type" not in obj:
            errors.append(f"物体 #{index} 缺少'type'字段")
        elif not isinstance(obj["type"], str):
            errors.append(f"物体 #{index} 的'type'字段必须是字符串类型")
        elif obj["type"].upper() not in ["FURNITURE", "ITEM", "INTERACTABLE", "GRABBABLE", "STATIC"]:
            errors.append(f"物体 #{index} 的'type'字段值无效: {obj['type']}")
        
        # 检查location_id字段
        if "location_id" not in obj:
            errors.append(f"物体 {obj_id} 缺少'location_id'字段")
        elif not isinstance(obj["location_id"], str):
            errors.append(f"物体 {obj_id} 的'location_id'字段必须是字符串类型")
            
        # 检查properties字段
        if "properties" not in obj:
            errors.append(f"物体 {obj_id} 缺少'properties'字段")
        elif not isinstance(obj["properties"], dict):
            errors.append(f"物体 {obj_id} 的'properties'字段必须是字典类型")
        else:
            # 检查属性字段的合法性
            props = obj["properties"]
            obj_type = obj.get("type", "").upper()
            
            # 注意：我们不再在这里检查物体是否作为容器使用，而是在下面的第二轮检查中进行
                
            # 检查家具类型的必要属性
            if obj_type == "FURNITURE":
                if "size" not in props:
                    errors.append(f"家具物体 {obj_id} 缺少'size'属性")
                elif not isinstance(props["size"], list) or len(props["size"]) != 3:
                    errors.append(f"家具物体 {obj_id} 的'size'属性必须是包含3个元素的列表")
                    
                if "weight" not in props:
                    errors.append(f"家具物体 {obj_id} 缺少'weight'属性")
                    
                # 不再检查is_container属性，当物体in:FURNITURE时，才要
                # if "is_container" not in props:
                #     errors.append(f"家具物体 {obj_id} 缺少'is_container'属性")
            
            # 检查可抓取物品的属性
            if obj_type == "ITEM":
                if "weight" not in props:
                    errors.append(f"物品 {obj_id} 缺少'weight'属性")
        
        # 检查states字段(如果存在)
        if "states" in obj and not isinstance(obj["states"], dict):
            errors.append(f"物体 {obj_id} 的'states'字段必须是字典类型")
        
        return errors, obj_id
    
    @staticmethod
    def _parse_location_id(location_id: str) -> Tuple[str, str]:
        """解析位置ID，提取前置词和实际ID"""
        if isinstance(location_id, str) and ':' in location_id:
            preposition, real_id = location_id.split(':', 1)
            return preposition, real_id
        return "", location_id
    
    @staticmethod
    def validate_scene_file(file_path: str) -> Tuple[bool, List[str]]:
        """
        验证场景文件
        
        Args:
            file_path: 场景文件路径
            
        Returns:
            Tuple[bool, List[str]]: (是否合法, 错误信息列表)
        """
        try:
            if not os.path.exists(file_path):
                return False, [f"文件不存在: {file_path}"]
                
            _, ext = os.path.splitext(file_path.lower())
            if ext not in ['.json', '.yaml', '.yml']:
                return False, [f"不支持的文件格式: {ext}"]
                
            # 解析文件
            if ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    scene_data = json.load(f)
            else:  # yaml格式
                import yaml
                with open(file_path, 'r', encoding='utf-8') as f:
                    scene_data = yaml.safe_load(f)
                    
            # 验证场景数据
            return SceneValidator.validate_scene(scene_data)
        except Exception as e:
            return False, [f"验证场景文件时出错: {e}"]

    @staticmethod
    def validate_agent_config(agent_config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证智能体配置
        
        Args:
            agent_config: 智能体配置字典
            
        Returns:
            Tuple[bool, List[str]]: (是否合法, 错误信息列表)
        """
        errors = []
        
        # 检查基本结构
        if not isinstance(agent_config, dict):
            errors.append("智能体配置必须是字典类型")
            return False, errors
        
        # 如果存在agents_config字段
        if "agents_config" in agent_config:
            if not isinstance(agent_config["agents_config"], list):
                errors.append("'agents_config'字段必须是列表类型")
            else:
                for i, agent in enumerate(agent_config["agents_config"]):
                    agent_errors = SceneValidator._validate_agent(agent, i)
                    errors.extend(agent_errors)
        
        # 检查任务描述字段(如果存在)
        if "task_description" in agent_config and not isinstance(agent_config["task_description"], str):
            errors.append("'task_description'字段必须是字符串类型")
            
        # 检查场景ID字段(如果存在)
        if "scene_uid" in agent_config and not isinstance(agent_config["scene_uid"], str):
            errors.append("'scene_uid'字段必须是字符串类型")
        
        # 检查是否有错误
        is_valid = len(errors) == 0
        return is_valid, errors
    
    @staticmethod
    def _validate_agent(agent: Dict[str, Any], index: int) -> List[str]:
        """验证单个智能体配置"""
        errors = []
        
        if not isinstance(agent, dict):
            return [f"智能体配置 #{index} 必须是字典类型"]
        
        # 检查必要字段
        if "name" not in agent:
            errors.append(f"智能体配置 #{index} 缺少'name'字段")
        elif not isinstance(agent["name"], str):
            errors.append(f"智能体配置 #{index} 的'name'字段必须是字符串类型")
        
        # 检查可选但常见的字段
        if "max_grasp_limit" in agent and not isinstance(agent["max_grasp_limit"], int):
            errors.append(f"智能体配置 #{index} 的'max_grasp_limit'字段必须是整数类型")
            
        if "max_weight" in agent:
            if not isinstance(agent["max_weight"], (int, float)):
                errors.append(f"智能体配置 #{index} 的'max_weight'字段必须是数值类型")
        
        if "max_size" in agent:
            if not isinstance(agent["max_size"], list) or len(agent["max_size"]) != 3:
                errors.append(f"智能体配置 #{index} 的'max_size'字段必须是包含3个元素的列表")
        
        return errors
        
    @staticmethod
    def validate_agent_file(file_path: str) -> Tuple[bool, List[str]]:
        """
        验证智能体配置文件
        
        Args:
            file_path: 智能体配置文件路径
            
        Returns:
            Tuple[bool, List[str]]: (是否合法, 错误信息列表)
        """
        try:
            if not os.path.exists(file_path):
                return False, [f"文件不存在: {file_path}"]
                
            _, ext = os.path.splitext(file_path.lower())
            if ext not in ['.json', '.yaml', '.yml']:
                return False, [f"不支持的文件格式: {ext}"]
                
            # 解析文件
            if ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    agent_config = json.load(f)
            else:  # yaml格式
                import yaml
                with open(file_path, 'r', encoding='utf-8') as f:
                    agent_config = yaml.safe_load(f)
                    
            # 验证智能体配置
            return SceneValidator.validate_agent_config(agent_config)
        except Exception as e:
            return False, [f"验证智能体配置文件时出错: {e}"]

    @staticmethod
    def validate_container_relationships(scene_data: Dict[str, Any]) -> List[str]:
        """验证场景中的容器关系合法性"""
        errors = []
        objects_dict = {obj.get("id"): obj for obj in scene_data.get("objects", [])}
        
        # 检查每个物体的location_id，如果是容器关系，则检查容器的is_container属性
        for obj in scene_data.get("objects", []):
            location_id = obj.get("location_id", "")
            obj_id = obj.get("id", "unknown")
            
            # 检查是否是容器位置关系（on:或in:）
            if location_id and ":" in location_id:
                preposition, target_id = SceneValidator._parse_location_id(location_id)
                
                # 如果是房间，则不需要验证is_container
                if preposition in ["on", "in"] and target_id in objects_dict:
                    container_obj = objects_dict[target_id]
                    container_props = container_obj.get("properties", {})
                    
                    # 检查容器是否有is_container属性且为true
                    if not container_props.get("is_container", False):
                        errors.append(f"物体 {obj_id} 的位置为 '{location_id}'，但物体 {target_id} 不是容器（缺少'is_container'属性或该属性为false）")
        
        return errors 