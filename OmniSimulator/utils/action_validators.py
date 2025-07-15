"""
动作验证工具类 - 提供通用的动作验证方法
"""

from typing import Tuple, Dict, Any, Optional, List
from ..core.enums import ObjectType

class ValidationResult:
    """验证结果类，提供更结构化的验证返回值"""

    def __init__(self, is_valid: bool, message: str, data: Optional[Dict[str, Any]] = None):
        self.is_valid = is_valid
        self.message = message
        self.data = data or {}

    def __bool__(self):
        return self.is_valid

class ActionValidator:
    """
    动作验证器 - 提供通用的验证方法来减少重复代码
    """

    @staticmethod
    def validate_object_exists_and_discovered(env_manager, target_id: str) -> ValidationResult:
        """
        验证物体是否存在且已被发现

        Args:
            env_manager: 环境管理器
            target_id: 目标物体ID

        Returns:
            ValidationResult: 验证结果
        """
        if not env_manager:
            return ValidationResult(False, "Environment manager not available")

        if not target_id or not isinstance(target_id, str):
            return ValidationResult(False, "Invalid target object ID")

        try:
            obj = env_manager.get_object_by_id(target_id)
            if not obj:
                return ValidationResult(False, f"Object does not exist: {target_id}")

            if not obj.get('is_discovered', False):
                obj_name = obj.get('name', target_id)
                return ValidationResult(False, f"Object not discovered: {obj_name}")

            return ValidationResult(True, "Object exists and is discovered", {"object": obj})
        except Exception as e:
            return ValidationResult(False, f"Error validating object: {str(e)}")
    
    @staticmethod
    def validate_agent_near_object(env_manager, agent_id: str, target_id: str) -> ValidationResult:
        """
        验证智能体是否靠近目标物体

        Args:
            env_manager: 环境管理器
            agent_id: 智能体ID
            target_id: 目标物体ID

        Returns:
            ValidationResult: 验证结果
        """
        is_near, reason = env_manager.is_agent_near_object(agent_id, target_id)
        if not is_near:
            return ValidationResult(False, reason)
        return ValidationResult(True, "Agent is near target object")

    @staticmethod
    def validate_agent_near_or_holding_object(agent, target_id: str) -> ValidationResult:
        """
        验证智能体是否靠近目标物体或已持有该物体

        Args:
            agent: 智能体对象
            target_id: 目标物体ID

        Returns:
            ValidationResult: 验证结果
        """
        if target_id not in agent.near_objects and target_id not in agent.inventory:
            return ValidationResult(False, f"Agent must approach {target_id} before operating")
        return ValidationResult(True, "Agent can operate this object")

    @staticmethod
    def validate_object_grabbable(obj: Dict[str, Any], agent) -> ValidationResult:
        """
        验证物体是否可抓取

        Args:
            obj: 物体数据
            agent: 智能体对象

        Returns:
            ValidationResult: 验证结果
        """
        obj_type = obj.get('type')
        obj_name = obj.get('name', obj.get('id', 'unknown'))

        if obj_type not in [ObjectType.GRABBABLE.name, ObjectType.ITEM.name]:
            # 家具可以抓取，但要检查尺寸和重量
            if obj_type == ObjectType.FURNITURE.name:
                can_carry, reason = agent.can_carry(obj.get('properties', {}))
                if not can_carry:
                    return ValidationResult(False, reason)
            else:
                return ValidationResult(False, f"Object not grabbable: {obj_name}")

        return ValidationResult(True, "Object is grabbable")

    @staticmethod
    def validate_agent_capacity(agent, additional_items: int = 1) -> ValidationResult:
        """
        验证智能体是否还能抓取更多物体

        Args:
            agent: 智能体对象
            additional_items: 要添加的物体数量

        Returns:
            ValidationResult: 验证结果
        """
        if not agent:
            return ValidationResult(False, "Agent object not available")

        try:
            inventory = getattr(agent, 'inventory', None)
            max_limit = getattr(agent, 'max_grasp_limit', 0)

            if inventory is None:
                return ValidationResult(False, "Agent inventory data not available")

            if len(inventory) + additional_items > max_limit:
                return ValidationResult(False, f"Agent has reached maximum grab limit ({max_limit})")

            return ValidationResult(True, "Agent capacity is sufficient")
        except Exception as e:
            return ValidationResult(False, f"Error validating agent capacity: {str(e)}")
    
    @staticmethod
    def validate_object_accessibility(env_manager, target_id: str, agent_id: str) -> Tuple[bool, str]:
        """
        验证物体对智能体是否可访问
        
        Args:
            env_manager: 环境管理器
            target_id: 目标物体ID
            agent_id: 智能体ID
            
        Returns:
            Tuple[bool, str]: (是否可访问, 错误消息)
        """
        accessible, reason = env_manager.is_object_accessible(target_id, agent_id)
        if not accessible:
            return False, reason
        return True, "Object is accessible"
    
    @staticmethod
    def validate_object_type(obj: Dict[str, Any], allowed_types: list, action_name: str = "operate") -> Tuple[bool, str]:
        """
        验证物体类型是否符合要求

        Args:
            obj: 物体数据
            allowed_types: 允许的物体类型列表
            action_name: 动作名称，用于错误消息

        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        """
        obj_type = obj.get('type')
        if obj_type not in allowed_types:
            obj_name = obj.get('name', obj.get('id', 'unknown object'))
            return False, f"Object cannot be {action_name}d: {obj_name}"
        return True, "Object type meets requirements"
    
    @staticmethod
    def validate_object_property(obj: Dict[str, Any], property_name: str, expected_value: Any = True, action_name: str = "operate") -> Tuple[bool, str]:
        """
        验证物体属性是否符合要求

        Args:
            obj: 物体数据
            property_name: 属性名称
            expected_value: 期望的属性值
            action_name: 动作名称，用于错误消息

        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        """
        properties = obj.get('properties', {})
        if property_name not in properties:
            obj_name = obj.get('name', obj.get('id', 'unknown object'))
            return False, f"Object does not support {action_name}: {obj_name}"

        if properties[property_name] != expected_value:
            obj_name = obj.get('name', obj.get('id', 'unknown object'))
            return False, f"Object does not meet {action_name} conditions: {obj_name}"

        return True, "Object properties meet requirements"
    
    @staticmethod
    def validate_object_state(obj: Dict[str, Any], state_name: str, expected_value: Any, action_name: str = "operate") -> Tuple[bool, str]:
        """
        验证物体状态是否符合要求

        Args:
            obj: 物体数据
            state_name: 状态名称
            expected_value: 期望的状态值
            action_name: 动作名称，用于错误消息

        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        """
        states = obj.get('states', {})
        current_value = states.get(state_name)

        if current_value == expected_value:
            obj_name = obj.get('name', obj.get('id', 'unknown object'))
            status_desc = "already is" if expected_value else "already is not"
            return False, f"Object {status_desc} in {action_name} state: {obj_name}"

        return True, "Object state meets requirements"
    
    @staticmethod
    def validate_agent_ability(agent, ability_name: str) -> Tuple[bool, str]:
        """
        验证智能体是否具有特定能力
        
        Args:
            agent: 智能体对象
            ability_name: 能力名称
            
        Returns:
            Tuple[bool, str]: (是否有能力, 错误消息)
        """
        if not agent.has_ability(ability_name):
            return False, f"Missing ability to execute {ability_name}, need to hold items that provide this ability"
        return True, "Agent has required ability"
    
    @staticmethod
    def validate_basic_object_interaction(env_manager, agent, target_id: str) -> ValidationResult:
        """
        执行基本的物体交互验证（组合验证）

        包括：物体存在性、发现状态、智能体位置、可访问性

        Args:
            env_manager: 环境管理器
            agent: 智能体对象
            target_id: 目标物体ID

        Returns:
            ValidationResult: 验证结果
        """
        # 1. 检查物体是否存在且已被发现
        result = ActionValidator.validate_object_exists_and_discovered(env_manager, target_id)
        if not result:
            return result

        obj = result.data.get("object")

        # 2. 检查智能体是否靠近物体
        result = ActionValidator.validate_agent_near_object(env_manager, agent.id, target_id)
        if not result:
            return result
        
        # 3. 检查物体是否对智能体可访问
        accessible, reason = env_manager.is_object_accessible(target_id, agent.id)
        if not accessible:
            return ValidationResult(False, reason)

        return ValidationResult(True, "Basic interaction validation passed", {"object": obj})

    @staticmethod
    def validate_grab_action(env_manager, agent, target_id: str) -> ValidationResult:
        """
        验证抓取动作的所有前置条件

        Args:
            env_manager: 环境管理器
            agent: 智能体对象
            target_id: 目标物体ID

        Returns:
            ValidationResult: 验证结果
        """
        # 1. 基本交互验证
        result = ActionValidator.validate_basic_object_interaction(env_manager, agent, target_id)
        if not result:
            return result

        obj = result.data.get("object")

        # 2. 检查物体是否可抓取
        result = ActionValidator.validate_object_grabbable(obj, agent)
        if not result:
            return result

        # 3. 检查智能体容量
        result = ActionValidator.validate_agent_capacity(agent)
        if not result:
            return result

        # 4. 检查物体上是否有其他物体
        child_ids = []
        edges = env_manager.world_state.graph.edges.get(target_id, {})
        for child_id, rels in edges.items():
            for rel in rels:
                if rel.get('type') in ('in', 'on'):
                    child_ids.append(child_id)

        if child_ids:
            return ValidationResult(False, f"Object has other objects on/in it {', '.join(child_ids)}, cannot grab")

        return ValidationResult(True, "Grab action validation passed", {"object": obj})

    @staticmethod
    def validate_place_action(env_manager, agent, object_id: str, location_id: str, relation: str) -> ValidationResult:
        """
        验证放置动作的所有前置条件

        Args:
            env_manager: 环境管理器
            agent: 智能体对象
            object_id: 要放置的物体ID
            location_id: 放置位置ID
            relation: 放置关系（on/in）

        Returns:
            ValidationResult: 验证结果
        """
        # 1. 检查物体是否在智能体库存中
        if object_id not in agent.inventory:
            return ValidationResult(False, f"Agent does not hold object: {object_id}")

        # 2. 检查智能体是否靠近放置位置
        if location_id not in agent.near_objects and location_id not in agent.inventory:
            return ValidationResult(False, f"Agent must approach {location_id} before placing object")

        # 3. 检查放置位置是否存在
        location = env_manager.get_object_by_id(location_id) or env_manager.get_room_by_id(location_id)
        if not location:
            return ValidationResult(False, f"Placement location does not exist: {location_id}")

        # 4. 检查放置关系是否合理
        if relation == "in":
            # in关系要求目标是容器或房间
            is_container = location.get('properties', {}).get('is_container', False)
            is_room = location.get('type', '').upper() == 'ROOM'
            if not (is_container or is_room):
                location_name = location.get('name', location_id)
                return ValidationResult(False, f"Target location {location_name} does not support 'in' placement")
        elif relation == "on":
            # on关系不能是房间
            if location.get('type', '').upper() == 'ROOM':
                return ValidationResult(False, "Cannot place object on room")

        return ValidationResult(True, "Place action validation passed", {"location": location})