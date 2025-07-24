from typing import Dict, List, Optional, Any, Tuple
from ..utils.parse_location import parse_location_id
import logging

logger = logging.getLogger(__name__)

class Agent:
    """智能体类 - 表示模拟环境中的智能体"""
    
    def __init__(self, agent_id: str, name: str, location_id: str, 
                 max_grasp_limit: int = 2,
                 properties: Optional[Dict[str, Any]] = None):
        """
        初始化智能体
        
        Args:
            agent_id: 智能体唯一ID
            name: 智能体名称
            location_id: 智能体初始位置ID (房间ID)
            max_grasp_limit: 最大可抓取物体数量
            properties: 其他属性字典，包含max_length/width/height/weight等
        """
        self.id = agent_id
        self.name = name
        self.location_id = location_id
        self.inventory: List[str] = []  # 持有物品的ID列表
        self.max_grasp_limit = max_grasp_limit
        self.properties = properties or {}
        self.current_action = None  # 当前正在执行的动作（如需要多回合的动作）
        
        # 设置智能体的重量限制（默认值）
        if "max_weight" not in self.properties:
            self.properties["max_weight"] = 10.0 # 最大重量(千克)
        
        # 当前负载
        self.current_weight = 0.0
        # 确保near_objects是集合类型
        if not hasattr(self, 'near_objects') or self.near_objects is None:
            self.near_objects = set()
        elif not isinstance(self.near_objects, set):
            self.near_objects = set(self.near_objects if isinstance(self.near_objects, (list, tuple)) else [])
        # 新增：合作模式下的物体ID，None表示未合作
        self.corporate_mode_object_id = None
    
        # 新增：智能体当前拥有的能力
        self.abilities = set()
        # 新增：跟踪每个能力来自哪些物体 {ability: set(object_ids)}
        self.ability_sources = {}
    
    def can_grab(self) -> bool:
        """
        检查智能体是否还能抓取更多物体（数量限制）
        
        Returns:
            bool: 是否可以抓取
        """
        return len(self.inventory) < self.max_grasp_limit
    
    def can_carry(self, object_properties: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if agent can carry the object (weight limit only)
        Cooperative mode has no weight limit

        Args:
            object_properties: 物体属性字典，包含weight等

        Returns:
            Tuple[bool, str]: (是否可以承载, 原因)
        """
        # Check cooperative mode
        if hasattr(self, 'corporate_mode_object_id') and self.corporate_mode_object_id is not None:
            return True, "Cooperative mode: no weight limit"

        # Single agent mode: check weight limit
        obj_weight = object_properties.get("weight", 0.0)
        agent_max_weight = self.properties.get("max_weight", 50.0)  # 使用get方法避免KeyError，默认50kg
        if self.current_weight + obj_weight > agent_max_weight:
            return False, f"Weight limit exceeded (current:{self.current_weight}kg + object:{obj_weight}kg > max:{agent_max_weight}kg)"

        # 移除尺寸限制检查 - 智能体可以抓取任何尺寸的物体，只要重量允许
        return True, "Can carry"
    
    def grab_object(self, object_id: str, object_properties: Dict[str, Any]) -> Tuple[bool, str]:
        """
        抓取物体
        
        Args:
            object_id: 物体ID
            object_properties: 物体属性
            
        Returns:
            Tuple[bool, str]: (是否成功抓取, 原因)
        """
        if not self.can_grab():
            return False, f"Maximum grab limit reached ({self.max_grasp_limit})"

        if object_id in self.inventory:
            return False, "Already holding this object"  # 已经持有该物体

        # 检查是否能承载该物体
        can_carry, reason = self.can_carry(object_properties)
        if not can_carry:
            return False, reason

        # 更新当前负载
        self.current_weight += object_properties.get("weight", 0.0)
        self.inventory.append(object_id)
        return True, "Successfully grabbed object"
    
    def drop_object(self, object_id: str, object_properties: Dict[str, Any]) -> Tuple[bool, str]:
        """
        放下物体
        
        Args:
            object_id: 物体ID
            object_properties: 物体属性
            
        Returns:
            Tuple[bool, str]: (是否成功放下, 原因)
        """
        if object_id not in self.inventory:
            return False, "Not holding this object"

        # 更新当前负载
        self.current_weight -= object_properties.get("weight", 0.0)
        self.inventory.remove(object_id)
        return True, "Successfully dropped object"
    
    def move_to(self, new_location_id: str) -> None:
        """
        移动到新位置
        
        Args:
            new_location_id: 新位置ID
        """
        self.location_id = new_location_id
    
    def update_near_objects(self, near_id: Optional[str] = None, env_manager=None):
        """
        更新智能体可交互的物体集合

        Args:
            near_id: 靠近的物体ID，如果为None则只保留库存和位置
            env_manager: 环境管理器实例，用于查询物体关系
        """
        if env_manager is not None:
            # 使用ProximityManager统一管理近邻关系
            try:
                # 尝试多种导入路径
                try:
                    from OmniEmbodied.simulator.utils.proximity_manager import ProximityManager
                except ImportError:
                    from utils.proximity_manager import ProximityManager

                proximity_manager = ProximityManager(env_manager)
                proximity_manager.update_agent_proximity(self, near_id)
            except ImportError as e:
                # 如果ProximityManager不可用，使用原有逻辑
                print(f"ProximityManager导入失败，使用原有逻辑: {e}")
                self._legacy_update_near_objects(near_id, env_manager)
        else:
            # 如果没有env_manager，只保留基本的库存和位置
            self.near_objects = set(self.inventory)
            self.near_objects.add(self.location_id)

    def _legacy_update_near_objects(self, near_id: Optional[str] = None, env_manager=None):
        """
        原有的近邻关系更新逻辑（作为备用）
        """
        # 记录更新前的near_objects状态
        old_near_objects = set(self.near_objects) if self.near_objects else set()

        # 重置near_objects集合，初始包含库存和当前位置
        self.near_objects = set(self.inventory)
        self.near_objects.add(self.location_id)

        logger.debug(f"智能体 {self.id} 更新可交互物体 - 库存: {self.inventory}, 位置: {self.location_id}")

        if near_id is not None and env_manager is not None:
            logger.debug(f"智能体 {self.id} 靠近物体: {near_id}")

            def collect_children(obj_id):
                """收集指定物体的所有子物体"""
                children = []
                for child_id in env_manager.world_state.graph.edges.get(obj_id, {}):
                    # 过滤掉未发现的物体
                    child_obj = env_manager.get_object_by_id(child_id)
                    if child_obj and child_obj.get('is_discovered', True):
                        children.append(child_id)
                        children.extend(collect_children(child_id))
                return children

            def collect_parents_and_siblings(obj_id, visited=None):
                """收集指定物体的父物体及其同级物体"""
                if visited is None:
                    visited = set()
                result = set()
                obj = env_manager.get_object_by_id(obj_id)
                if not obj or 'location_id' not in obj:
                    return result
                preposition, parent_id = parse_location_id(obj['location_id'])
                if not parent_id or parent_id in visited:
                    return result
                visited.add(parent_id)

                # 确保父物体已被发现
                parent_obj = env_manager.get_object_by_id(parent_id)
                if parent_obj and parent_obj.get('is_discovered', True):
                    result.add(parent_id)
                    # 如果父物体不是房间，收集其所有子物体
                    if parent_obj and parent_obj.get('type', '').upper() != 'ROOM':
                        # 只收集已发现的子物体
                        discovered_children = []
                        for child_id in collect_children(parent_id):
                            child_obj = env_manager.get_object_by_id(child_id)
                            if child_obj and child_obj.get('is_discovered', True):
                                discovered_children.append(child_id)
                        result.update(discovered_children)
                        # 递归向上
                        result.update(collect_parents_and_siblings(parent_id, visited))
                return result

            all_near = set()
            obj = env_manager.get_object_by_id(near_id)
            if obj:
                # 确保靠近的物体已被发现
                if obj.get('is_discovered', True):
                    if obj.get('type', '').upper() == 'ROOM':
                        all_near.add(near_id)
                    else:
                        all_near.add(near_id)
                        # 收集已发现的子物体
                        for child_id in collect_children(near_id):
                            child_obj = env_manager.get_object_by_id(child_id)
                            if child_obj and child_obj.get('is_discovered', True):
                                all_near.add(child_id)
                        # 收集已发现的父物体和兄弟物体
                        all_near.update(collect_parents_and_siblings(near_id))

                    logger.debug(f"智能体 {self.id} 可交互物体更新: 添加 {len(all_near)} 个物体")
                    self.near_objects.update(all_near)
                else:
                    logger.debug(f"智能体 {self.id} 靠近的物体 {near_id} 未被发现，不添加到可交互列表")
            else:
                logger.warning(f"智能体 {self.id} 靠近的物体 {near_id} 不存在")

        # 记录更新后的near_objects变化
        new_near_objects = self.near_objects - old_near_objects
        removed_near_objects = old_near_objects - self.near_objects

        if new_near_objects:
            logger.debug(f"智能体 {self.id} 新增可交互物体: {new_near_objects}")
        if removed_near_objects:
            logger.debug(f"智能体 {self.id} 移除可交互物体: {removed_near_objects}")

        # 确保near_objects是集合类型
        if not isinstance(self.near_objects, set):
            self.near_objects = set(self.near_objects)

        logger.debug(f"智能体 {self.id} 最终可交互物体集合: {self.near_objects}")
    
    def add_ability_from_object(self, ability: str, object_id: str) -> None:
        """
        从物体获取能力
        
        Args:
            ability: 能力名称
            object_id: 提供能力的物体ID
        """
        # 确保abilities是集合
        if not isinstance(self.abilities, set):
            self.abilities = set(self.abilities) if self.abilities else set()
        
        self.abilities.add(ability)
        
        # 确保ability_sources的值是集合
        if ability not in self.ability_sources:
            self.ability_sources[ability] = set()
        elif not isinstance(self.ability_sources[ability], set):
            self.ability_sources[ability] = set(self.ability_sources[ability])
        
        self.ability_sources[ability].add(object_id)
        
        # 动态注册对应的动作能力
        try:
            from OmniEmbodied.simulator.action.action_manager import ActionManager
            ActionManager.register_ability_action(ability, self.id)
        except Exception as e:
            print(f"Failed to register action {ability} for agent {self.id}: {e}")
    
    def remove_ability_from_object(self, ability: str, object_id: str) -> None:
        """
        移除来自特定物体的能力
        
        Args:
            ability: 能力名称
            object_id: 提供能力的物体ID
        """
        # 如果能力不存在，直接返回
        if ability not in self.ability_sources:
            return
            
        # 确保ability_sources的值是集合
        if not isinstance(self.ability_sources[ability], set):
            self.ability_sources[ability] = set(self.ability_sources[ability])
        
        # 移除物体作为能力来源
        self.ability_sources[ability].discard(object_id)
        
        # 只有当没有任何物体提供此能力时，才从智能体能力集合中移除
        if not self.ability_sources[ability]:
            # 确保abilities是集合
            if not isinstance(self.abilities, set):
                self.abilities = set(self.abilities) if self.abilities else set()
                
            self.abilities.discard(ability)
            del self.ability_sources[ability]
            
            # 解绑对应的动作能力
            try:
                from OmniEmbodied.simulator.action.action_manager import ActionManager
                ActionManager.unregister_ability_action(ability, self.id)
            except Exception as e:
                print(f"Failed to unregister action {ability} for agent {self.id}: {e}")
    
    def has_ability(self, ability: str) -> bool:
        """
        检查是否拥有特定能力
        
        Args:
            ability: 能力名称
            
        Returns:
            bool: 是否拥有该能力
        """
        if isinstance(self.abilities, set):
            return ability in self.abilities
        elif isinstance(self.abilities, list):
            return ability in self.abilities
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将智能体转换为字典表示
        
        Returns:
            Dict: 智能体数据字典
        """
        # 确保abilities是集合后再转为列表
        abilities_list = list(self.abilities) if isinstance(self.abilities, set) else self.abilities
        
        # 处理ability_sources，确保值是集合后再转为列表
        ability_sources_dict = {}
        for k, v in self.ability_sources.items():
            if isinstance(v, set):
                ability_sources_dict[k] = list(v)
            elif isinstance(v, list):
                ability_sources_dict[k] = v
            else:
                ability_sources_dict[k] = []
        
        return {
            "id": self.id,
            "name": self.name,
            "location_id": self.location_id,
            "inventory": self.inventory.copy(),
            "max_grasp_limit": self.max_grasp_limit,
            "properties": self.properties.copy(),
            "current_weight": self.current_weight,
            "abilities": abilities_list,
            "ability_sources": ability_sources_dict,
            "corporate_mode_object_id": self.corporate_mode_object_id,
            "near_objects": list(self.near_objects) if hasattr(self, 'near_objects') and self.near_objects is not None else []
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Agent':
        """
        从字典创建智能体对象

        Args:
            data: 智能体数据字典

        Returns:
            Agent: 智能体对象
        """
        # 处理properties，将顶层的物理属性移动到properties中
        properties = data.get('properties', {}).copy()

        # 将顶层的物理属性移动到properties中（如果properties中没有的话）
        physical_attrs = ['max_weight', 'max_length', 'max_width', 'max_height', 'max_size']
        for attr in physical_attrs:
            if attr in data and attr not in properties:
                properties[attr] = data[attr]

        agent = cls(
            agent_id=data.get('id', ''),
            name=data.get('name', ''),
            location_id=data.get('location_id', ''),
            max_grasp_limit=data.get('max_grasp_limit', 2),
            properties=properties
        )
        
        # 还原其他字段
        agent.inventory = data.get('inventory', []).copy()
        agent.current_weight = data.get('current_weight', 0.0)
        agent.corporate_mode_object_id = data.get('corporate_mode_object_id')
        
        # 还原能力
        abilities = data.get('abilities', [])
        agent.abilities = set(abilities) if isinstance(abilities, (list, tuple)) else set()
        
        # 还原能力来源
        ability_sources = data.get('ability_sources', {})
        agent.ability_sources = {}
        for ability, sources in ability_sources.items():
            agent.ability_sources[ability] = set(sources) if isinstance(sources, (list, tuple)) else set()
        
        # 还原近邻物体列表到集合
        near_objects = data.get('near_objects', [])
        agent.near_objects = set(near_objects) if isinstance(near_objects, (list, tuple)) else set()
        
        return agent 