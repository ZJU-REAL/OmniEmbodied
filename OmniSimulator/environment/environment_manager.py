from typing import Dict, List, Optional, Tuple, Any
import uuid
import random

from ..core.state import WorldState
from .room import Room
from .object_defs import BaseObject, StaticObject, InteractableObject, GrabbableObject, FurnitureObject, ItemObject, create_object_from_dict

class EnvironmentManager:
    """
    环境管理器 - 负责管理模拟环境中的所有实体（房间、物体、家具）
    """
    
    def __init__(self, world_state: WorldState, sim_config: Optional[Dict[str, Any]] = None):
        """
        初始化环境管理器
        
        Args:
            world_state: 世界状态对象
            sim_config: 全局配置字典，可选
        """
        self.world_state = world_state
        self.sim_config = sim_config or {}
    
    def load_scene(self, scene_data: Dict[str, Any]) -> bool:
        """
        从场景数据加载环境
        
        Args:
            scene_data: 场景数据字典
            
        Returns:
            bool: 加载是否成功
        """
        try:
            self._clear_pending_locations()
            self._load_rooms(scene_data)
            self._load_objects(scene_data)
            self._resolve_pending_locations()
            return True
        except Exception as e:
            print(f"Failed to load scene: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_scene_old(self, scene_data: Dict[str, Any]) -> bool:
        """
        从场景数据加载环境
        
        Args:
            scene_data: 场景数据字典
            
        Returns:
            bool: 加载是否成功
        """
        try:
            
            # 清除之前的待处理位置
            if hasattr(self, '_pending_locations'):
                del self._pending_locations
            self._pending_locations = []
            
            # 加载房间 - 房间默认对智能体可见
            rooms_data = scene_data.get('rooms', [])
            for room_data in rooms_data:
                room = Room.from_dict(room_data)
                self.add_room(room)
            
            # 处理房间之间的连接关系
            for room_data in rooms_data:
                room_id = room_data['id']
                for connected_room_id in room_data.get('connected_to_room_ids', []):
                    self.connect_rooms(room_id, connected_room_id)
            
            # 首先加载没有复杂依赖关系的物体（直接放在房间中的物体）
            objects_data = scene_data.get('objects', [])
            independent_objects = []
            dependent_objects = []
            
            # 将物体分为两组：直接在房间中的物体和在其他物体中的物体
            for obj_data in objects_data:
                location_id = obj_data.get('location_id', '')
                preposition, real_id = self.parse_location_id(location_id)
                
                if real_id in self.world_state.graph.room_ids:
                    independent_objects.append(obj_data)
                else:
                    dependent_objects.append(obj_data)
            
            # 先加载独立物体
            for obj_data in independent_objects:
                # 设置物体的发现状态
                obj_type = obj_data.get('type', '').upper()
                if obj_type in ['FURNITURE', 'ITEM', 'INTERACTABLE', 'GRABBABLE']:
                    # 直接从模拟器配置文件读取全局观察设置
                    from config.config_manager import ConfigManager
                    config_manager = ConfigManager()
                    simulator_config = config_manager.get_config('simulator_config', {})
                    global_observation = simulator_config.get('global_observation', False)
                    obj_data['is_discovered'] = global_observation
                
                location_id = obj_data.get('location_id')
                object_id = obj_data.get('id', 'unknown')
                if location_id:
                    self.add_object(obj_data, location_id)
                else:
                    print(f"Warning: Object {object_id} has no specified location")
            
            # 然后在多轮中加载依赖物体，直到所有物体都被加载
            remaining = dependent_objects
            max_iterations = 10  # 避免无限循环
            iteration = 0
            
            while remaining and iteration < max_iterations:
                iteration += 1
                next_remaining = []
                
                for obj_data in remaining:
                    object_id = obj_data.get('id', 'unknown')
                    location_id = obj_data.get('location_id')
                    preposition, real_id = self.parse_location_id(location_id)
                    
                    # 检查位置是否存在
                    location_exists = self.world_state.graph.get_node(real_id) is not None
                    
                    if location_exists:
                        # 设置物体的发现状态
                        obj_type = obj_data.get('type', '').upper()
                        if obj_type in ['FURNITURE', 'ITEM', 'INTERACTABLE', 'GRABBABLE']:
                            # 直接从模拟器配置文件读取全局观察设置
                            from config.config_manager import ConfigManager
                            config_manager = ConfigManager()
                            global_observation = config_manager.get_config('simulator_config', {}).get('global_observation', False)
                            obj_data['is_discovered'] = global_observation
                        
                        self.add_object(obj_data, location_id)
                    else:
                        next_remaining.append(obj_data)
                
                # 如果没有进展，跳出循环
                if len(next_remaining) == len(remaining):
                    break
                
                remaining = next_remaining
            
            # 如果仍然有未加载的物体，尝试强制加载
            if remaining:
                for obj_data in remaining:
                    object_id = obj_data.get('id', 'unknown')
                    location_id = obj_data.get('location_id', '')
                    
                    # 设置物体的发现状态
                    obj_type = obj_data.get('type', '').upper()
                    if obj_type in ['FURNITURE', 'ITEM', 'INTERACTABLE', 'GRABBABLE']:
                        # 直接从模拟器配置文件读取全局观察设置
                        from config.config_manager import ConfigManager
                        config_manager = ConfigManager()
                        global_observation = config_manager.get_config('simulator_config', {}).get('global_observation', False)
                        obj_data['is_discovered'] = global_observation
                    
                    # 将物体放在第一个房间中
                    first_room_id = next(iter(self.world_state.graph.room_ids))
                    alternative_location = f"in:{first_room_id}"
                    
                    self.add_object(obj_data, alternative_location)
            
            # 解析待处理的位置关系（这个可能不再需要，因为我们已经处理了依赖关系）
            if self._pending_locations:
                resolved = []
                still_pending = []
                
                for object_id, location_id, preposition in self._pending_locations:
                    location = self.world_state.graph.get_node(location_id)
                    if location:
                        relation_type = preposition if preposition else "in"
                        self.world_state.graph.add_edge(location_id, object_id, {"type": relation_type})
                        resolved.append((obj_id, location_id))
                    else:
                        still_pending.append((obj_id, location_id, preposition))
                
                if still_pending:
                    for obj_id, location_id, _ in still_pending:
                        print(f"Warning: Object {obj_id} references non-existent location {location_id}")
                # 所有待处理的位置关系已成功解析
                
                del self._pending_locations
            
            return True
        except Exception as e:
            print(f"Error loading scene: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _clear_pending_locations(self):
        """清除之前的待处理位置"""
        if hasattr(self, '_pending_locations'):
            del self._pending_locations
        self._pending_locations = []
    
    def _load_rooms(self, scene_data: Dict[str, Any]):
        """加载房间和房间连接关系"""
        rooms_data = scene_data.get('rooms', [])
        
        # 加载房间
        for room_data in rooms_data:
            room = Room.from_dict(room_data)
            self.add_room(room)
        
        # 处理房间之间的连接关系
        for room_data in rooms_data:
            room_id = room_data['id']
            for connected_room_id in room_data.get('connected_to_room_ids', []):
                self.connect_rooms(room_id, connected_room_id)
    
    def _load_objects(self, scene_data: Dict[str, Any]):
        """加载所有物体"""
        objects_data = scene_data.get('objects', [])
        independent_objects, dependent_objects = self._categorize_objects(objects_data)
        
        self._load_independent_objects(independent_objects)
        self._load_dependent_objects_iteratively(dependent_objects)
    
    def _categorize_objects(self, objects_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """将物体分为独立物体（在房间中）和依赖物体（在其他物体中）"""
        independent_objects = []
        dependent_objects = []
        
        for obj_data in objects_data:
            location_id = obj_data.get('location_id', '')
            preposition, real_id = self.parse_location_id(location_id)
            
            if real_id in self.world_state.graph.room_ids:
                independent_objects.append(obj_data)
            else:
                dependent_objects.append(obj_data)
        
        return independent_objects, dependent_objects
    
    def _load_independent_objects(self, independent_objects: List[Dict[str, Any]]):
        """加载独立物体（直接在房间中的物体）"""
        for obj_data in independent_objects:
            self._set_object_discovery_state(obj_data)
            
            location_id = obj_data.get('location_id')
            object_id = obj_data.get('id', 'unknown')
            if location_id:
                self.add_object(obj_data, location_id)
            else:
                print(f"Warning: Object {object_id} has no specified location")
    
    def _load_dependent_objects_iteratively(self, dependent_objects: List[Dict[str, Any]]):
        """迭代加载依赖物体，直到所有物体都被加载"""
        remaining = dependent_objects
        max_iterations = 10  # 避免无限循环
        iteration = 0
        
        while remaining and iteration < max_iterations:
            iteration += 1
            next_remaining = []
            
            for obj_data in remaining:
                if self._try_load_dependent_object(obj_data):
                    # 成功加载
                    continue
                else:
                    # 未能加载，保留到下一轮
                    next_remaining.append(obj_data)
            
            # 如果没有进展，跳出循环
            if len(next_remaining) == len(remaining):
                break
            
            remaining = next_remaining
        
        # 强制加载剩余的物体
        if remaining:
            self._force_load_remaining_objects(remaining)
    
    def _try_load_dependent_object(self, obj_data: Dict[str, Any]) -> bool:
        """尝试加载一个依赖物体"""
        object_id = obj_data.get('id', 'unknown')
        location_id = obj_data.get('location_id')
        preposition, real_id = self.parse_location_id(location_id)
        
        # 检查位置是否存在
        location_exists = self.world_state.graph.get_node(real_id) is not None
        
        if location_exists:
            self._set_object_discovery_state(obj_data)
            self.add_object(obj_data, location_id)
            return True
        
        return False
    
    def _force_load_remaining_objects(self, remaining: List[Dict[str, Any]]):
        """强制加载剩余的无法解析位置的物体"""
        if not self.world_state.graph.room_ids:
            return
        
        first_room_id = next(iter(self.world_state.graph.room_ids))
        alternative_location = f"in:{first_room_id}"
        
        for obj_data in remaining:
            self._set_object_discovery_state(obj_data)
            self.add_object(obj_data, alternative_location)
    
    def _set_object_discovery_state(self, obj_data: Dict[str, Any]):
        """设置物体的发现状态"""
        obj_type = obj_data.get('type', '').upper()
        if obj_type in ['FURNITURE', 'ITEM', 'INTERACTABLE', 'GRABBABLE']:
            # 直接从模拟器配置文件读取全局观察设置
            from config.config_manager import ConfigManager
            config_manager = ConfigManager()
            global_observation = config_manager.get_config('simulator_config', {}).get('global_observation', False)
            obj_data['is_discovered'] = global_observation

        # 清空合作标记（在场景重新加载时）
        if 'states' in obj_data and 'cooperative_modified_attributes' in obj_data['states']:
            obj_data['states']['cooperative_modified_attributes'] = []
    
    def _resolve_pending_locations(self):
        """解析待处理的位置关系"""
        if not self._pending_locations:
            return
        
        resolved = []
        still_pending = []
        
        for object_id, location_id, preposition in self._pending_locations:
            location = self.world_state.graph.get_node(location_id)
            if location:
                relation_type = "in" if preposition == "in" else "on"
                self.world_state.graph.add_edge(location_id, object_id, {"type": relation_type})
                resolved.append((object_id, location_id))
            else:
                still_pending.append((object_id, location_id, preposition))
        
        if still_pending:
            self._pending_locations = still_pending

    def add_room(self, room: Room) -> bool:
        """
        添加房间到环境
        
        Args:
            room: 房间对象
            
        Returns:
            bool: 添加是否成功
        """
        if self.world_state.graph.get_node(room.id):
            print(f"Room ID already exists: {room.id}")
            return False
        
        # 添加房间到环境图
        room_dict = room.to_dict()
        # 确保房间有明确的type属性
        if 'type' not in room_dict:
            room_dict['type'] = 'ROOM'
        self.world_state.graph.add_node(room.id, room_dict, is_room=True)
        return True
    
    def parse_location_id(self, location_id: str):
        if isinstance(location_id, str) and ':' in location_id:
            preposition, real_id = location_id.split(':', 1)
            return preposition, real_id
        return None, location_id
    
    def add_object(self, obj_data: Dict[str, Any], location_id: str) -> Optional[str]:
        """
        添加物体到环境
        
        Args:
            obj_data: 物体数据字典
            location_id: 物体位置ID (房间ID或容器物体ID)
            
        Returns:
            str: 添加成功则返回物体ID，否则返回None
        """
        try:
            if 'id' not in obj_data:
                obj_data['id'] = str(uuid.uuid4())
            obj_id = obj_data['id']
            
            # 解析位置
            preposition, real_location_id = self.parse_location_id(location_id)
            location = self.world_state.graph.get_node(real_location_id)
            
            if not location:
                # 如果位置不存在但是我们当前正在加载场景，可能是物体定义的顺序问题
                # 我们先将物体添加到图中，稍后再处理位置关系
                print(f"Location does not exist: {real_location_id}")

                # 我们仍然创建对象并添加到图中，但是不建立位置关系
                obj = create_object_from_dict(obj_data)
                obj.location_id = location_id  # 保留原始位置ID以便稍后处理
                self.world_state.graph.add_node(obj.id, obj.to_dict())

                # 将此对象标记为需要稍后解析位置
                if not hasattr(self, '_pending_locations'):
                    self._pending_locations = []
                self._pending_locations.append((obj.id, real_location_id, preposition))
                
                return obj.id
            
            # 正常情况下，位置存在，直接添加物体和关系
            obj = create_object_from_dict(obj_data)
            obj.location_id = location_id
            self.world_state.graph.add_node(obj.id, obj.to_dict())
            
            # 添加关系边
            relation_type = preposition if preposition else "in"
            self.world_state.graph.add_edge(real_location_id, obj.id, {"type": relation_type})
            
            return obj.id
        except Exception as e:
            print(f"Error adding object: {e}")
            return None
    
    def connect_rooms(self, room_id1: str, room_id2: str) -> bool:
        """
        连接两个房间
        
        Args:
            room_id1: 第一个房间ID
            room_id2: 第二个房间ID
            
        Returns:
            bool: 连接是否成功
        """
        # 检查两个房间是否都存在
        room1 = self.world_state.graph.get_node(room_id1)
        room2 = self.world_state.graph.get_node(room_id2)
        
        if not room1 or not room2:
            print(f"Room does not exist: {room_id1 if not room1 else room_id2}")
            return False
        
        # 建立双向连接关系
        self.world_state.graph.add_edge(room_id1, room_id2, {"type": "connected"})
        self.world_state.graph.add_edge(room_id2, room_id1, {"type": "connected"})
        return True
    
    def get_room_by_id(self, room_id: str) -> Optional[Dict[str, Any]]:
        """
        获取房间数据
        
        Args:
            room_id: 房间ID
            
        Returns:
            Dict: 房间数据字典，如果不存在则返回None
        """
        _, real_room_id = self.parse_location_id(room_id)
        if real_room_id not in self.world_state.graph.room_ids:
            return None
        return self.world_state.graph.get_node(real_room_id)
    
    def get_object_by_id(self, object_id: str) -> Optional[Dict[str, Any]]:
        """
        获取物体数据
        
        Args:
            object_id: 物体ID
            
        Returns:
            Dict: 物体数据字典，如果不存在则返回None
        """
        _, real_object_id = self.parse_location_id(object_id)
        return self.world_state.graph.get_node(real_object_id)
    
    def get_objects_in_room(self, room_id: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """
        获取房间中的所有物体
        
        Args:
            room_id: 房间ID
            recursive: 是否递归获取容器中的物体
            
        Returns:
            List[Dict]: 物体数据字典列表
        """
        object_ids = self.world_state.graph.get_objects_in_room(room_id, recursive)
        objects = []
        for obj_id in object_ids:
            obj = self.world_state.graph.get_node(obj_id)
            if obj:
                objects.append(obj)
        return objects
    
    def get_discovered_objects_in_room(self, room_id: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """
        获取房间中的所有已发现物体
        
        Args:
            room_id: 房间ID
            recursive: 是否递归获取容器中的物体
            
        Returns:
            List[Dict]: 已发现物体数据字典列表
        """
        all_objects = self.get_objects_in_room(room_id, recursive)
        return [obj for obj in all_objects if obj.get('is_discovered', False)]
    
    def update_object_state(self, object_id: str, state_updates: Dict[str, Any]) -> bool:
        """
        更新物体状态
        
        Args:
            object_id: 物体ID
            state_updates: 状态更新字典
            
        Returns:
            bool: 更新是否成功
        """
        obj = self.world_state.graph.get_node(object_id)
        if not obj:
            return False
        
        if 'states' not in obj:
            obj['states'] = {}
        
        # 处理特殊的is_discovered字段
        if 'is_discovered' in state_updates:
            obj['is_discovered'] = state_updates.pop('is_discovered')
        
        # 更新普通状态
        obj['states'].update(state_updates)
        
        return True
    
    def discover_object(self, object_id: str) -> bool:
        """
        将物体标记为已发现
        
        Args:
            object_id: 物体ID
            
        Returns:
            bool: 更新是否成功
        """
        obj = self.world_state.graph.get_node(object_id)
        if not obj:
            return False
        
        obj['is_discovered'] = True
        return True
    
    def discover_objects_in_room(self, room_id: str, percentage: float = 1.0) -> List[str]:
        """
        随机发现房间中的某个百分比的物体
        
        Args:
            room_id: 房间ID
            percentage: 要发现的物体百分比 (0.0-1.0)
            
        Returns:
            List[str]: 新发现的物体ID列表
        """
        # 获取房间中所有未发现的物体
        all_objects = self.get_objects_in_room(room_id)
        undiscovered = [obj for obj in all_objects if not obj.get('is_discovered', False)]
        
        # 计算要发现的物体数量
        discover_count = max(1, int(len(undiscovered) * percentage))
        discover_count = min(discover_count, len(undiscovered))
        
        # 如果没有未发现的物体，返回空列表
        if not undiscovered:
            return []
        
        # 随机选择要发现的物体
        to_discover = random.sample(undiscovered, discover_count)
        
        # 标记物体为已发现
        discovered_ids = []
        for obj in to_discover:
            obj_id = obj.get('id')
            self.discover_object(obj_id)
            discovered_ids.append(obj_id)
        
        return discovered_ids
    
    def move_object(self, object_id: str, new_location_id: str) -> bool:
        """
        移动物体到新位置（location_id始终为房间ID，on/in关系通过图结构维护）
        """
        obj = self.world_state.graph.get_node(object_id)
        if not obj:
            return False
        
        preposition, real_location_id = self.parse_location_id(new_location_id)
        if real_location_id in self.world_state.graph.room_ids:
            room_id = real_location_id
        else:
            room_id = self.get_object_room(real_location_id)
            if not room_id:
                return False
        
        obj['location_id'] = new_location_id
        
        # 维护图结构的边关系
        # 先移除旧的边
        for from_id in list(self.world_state.graph.edges):
            if object_id in self.world_state.graph.edges[from_id]:
                self.world_state.graph.remove_edge(from_id, object_id)
        
        # 建立新边
        relation_type = preposition if preposition else "in"
        self.world_state.graph.add_edge(real_location_id, object_id, {"type": relation_type})
        
        return True
    
    def get_object_location(self, object_id: str) -> Optional[Dict[str, Any]]:
        """
        获取物体位置
        
        Args:
            object_id: 物体ID
            
        Returns:
            Dict: 位置数据字典，如果物体不存在则返回None
        """
        obj = self.world_state.graph.get_node(object_id)
        if not obj or 'location_id' not in obj:
            return None
        
        _, real_location_id = self.parse_location_id(obj['location_id'])
        return self.world_state.graph.get_node(real_location_id)
    
    def find_path(self, start_room_id: str, end_room_id: str) -> Optional[List[str]]:
        """
        查找从一个房间到另一个房间的路径
        
        Args:
            start_room_id: 起始房间ID
            end_room_id: 目标房间ID
            
        Returns:
            List[str]: 路径房间ID列表，如果不存在路径则返回None
        """
        return self.world_state.graph.find_path(start_room_id, end_room_id)
    
    def is_object_accessible(self, object_id: str, agent_id: str) -> Tuple[bool, str]:
        """
        检查物体是否对智能体可访问
        
        Args:
            object_id: 物体ID
            agent_id: 智能体ID
            
        Returns:
            Tuple[bool, str]: (是否可访问, 原因消息)
        """
        # 首先检查物体是否已被发现
        obj = self.world_state.graph.get_node(object_id)
        if obj and not obj.get('is_discovered', False):
            return False, f"Object {obj.get('name', object_id)} has not been discovered yet"
        
        # 检查智能体是否与物体在同一位置
        is_near, reason = self.is_agent_near_object(agent_id, object_id)
        if not is_near:
            return False, reason
        
        return self.world_state.is_object_accessible_to_agent(object_id, agent_id) 
    
    def get_object_room(self, object_id: str) -> Optional[str]:
        """
        获取物体所在的房间ID
        
        Args:
            object_id: 物体ID
            
        Returns:
            str: 房间ID，如果物体不存在或不在任何房间则返回None
        """
        obj = self.world_state.graph.get_node(object_id)
        if not obj:
            return None
        if 'location_id' in obj:
            preposition, real_location_id = self.parse_location_id(obj['location_id'])
            if real_location_id in self.world_state.graph.room_ids:
                return real_location_id
            else:
                return self.get_object_room(real_location_id)
        return self.world_state.graph.get_room_for_object(object_id)
    
    def is_agent_near_object(self, agent_id: str, object_id: str) -> Tuple[bool, str]:
        """
        检查智能体是否与物体在同一房间
        
        Args:
            agent_id: 智能体ID
            object_id: 物体ID
            
        Returns:
            Tuple[bool, str]: (是否在同一房间, 消息)
        """
        agent = self.world_state.get_agent(agent_id)
        if not agent:
            return False, f"Agent does not exist: {agent_id}"

        # 获取智能体所在的房间
        agent_room_id = agent.get('location_id')
        if not agent_room_id:
            return False, f"Agent {agent_id} is not in any room"

        # 如果物体在智能体的库存中，则视为在同一位置
        if 'inventory' in agent and object_id in agent['inventory']:
            return True, "Object is in agent's inventory"

        # 获取物体所在的房间
        object_room_id = self.get_object_room(object_id)
        if not object_room_id:
            return False, f"Cannot determine location of object {object_id}"
            
        # 检查是否在同一房间
        if agent_room_id != object_room_id:
            obj = self.world_state.graph.get_node(object_id)
            obj_name = obj.get('name', object_id) if obj else object_id
            room = self.world_state.graph.get_node(object_room_id)
            room_name = room.get('name', object_room_id) if room else object_room_id
            return False, f"Agent must go to {room_name} first to interact with {obj_name}"

        return True, "Agent and object are in the same room"
    
    def update_object_attributes(self, object_id: str, updates: Dict[str, Any]) -> bool:
        """
        通用物体属性更新方法，可更新任意顶层字段（如 holders, location_id 等）
        """
        obj = self.world_state.graph.get_node(object_id)
        if not obj:
            return False
        obj.update(updates)
        return True 