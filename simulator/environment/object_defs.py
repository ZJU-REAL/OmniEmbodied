from typing import Dict, List, Optional, Set, Any
try:
    from ..core.enums import ObjectType
except ValueError:
    # 如果相对导入失败，尝试绝对导入
    try:
        from simulator.core.enums import ObjectType
    except ImportError:
        # 如果还是失败，尝试从utils.embodied_simulator导入
        from utils.embodied_simulator import ObjectType

class BaseObject:
    """基础物体类"""
    
    def __init__(self, obj_id: str, name: str, object_type: ObjectType, 
                 states: Optional[Dict[str, Any]] = None,
                 properties: Optional[Dict[str, Any]] = None):
        """
        初始化基础物体
        
        Args:
            obj_id: 物体唯一ID
            name: 物体名称
            object_type: 物体类型枚举值
            states: 物体状态字典，如 {'is_open': False, 'is_on': True}
            properties: 物体属性字典，如 {'color': 'red', 'size': 'small'}
        """
        self.id = obj_id
        self.name = name
        self.object_type = object_type
        self.states = states or {}
        self.properties = properties or {}
        self.location_id = None  # 物体所在位置的ID
        self.is_discovered = False  # 是否被发现
    
    def to_dict(self) -> Dict[str, Any]:
        """将物体对象转换为字典表示"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.object_type.name,
            "states": self.states,
            "properties": self.properties,
            "location_id": self.location_id,
            "is_discovered": self.is_discovered
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseObject':
        """从字典创建物体对象"""
        obj_type = ObjectType[data["type"]] if isinstance(data["type"], str) else data["type"]
        
        obj = cls(
            obj_id=data["id"],
            name=data["name"],
            object_type=obj_type,
            states=data.get("states", {}),
            properties=data.get("properties", {})
        )
        
        obj.location_id = data.get("location_id")
        obj.is_discovered = data.get("is_discovered", False)
        return obj

class StaticObject(BaseObject):
    """静态物体类"""
    
    def __init__(self, obj_id: str, name: str, 
                 states: Optional[Dict[str, Any]] = None,
                 properties: Optional[Dict[str, Any]] = None):
        """
        初始化静态物体
        
        Args:
            obj_id: 物体唯一ID
            name: 物体名称
            states: 物体状态字典
            properties: 物体属性字典
        """
        super().__init__(obj_id, name, ObjectType.STATIC, states, properties)

class InteractableObject(BaseObject):
    """可交互物体类"""
    
    def __init__(self, obj_id: str, name: str, 
                 states: Optional[Dict[str, Any]] = None,
                 properties: Optional[Dict[str, Any]] = None):
        """
        初始化可交互物体
        
        Args:
            obj_id: 物体唯一ID
            name: 物体名称
            states: 物体状态字典，如 {'is_open': False, 'is_on': True}
            properties: 物体属性字典
        """
        super().__init__(obj_id, name, ObjectType.INTERACTABLE, states, properties)
        
        # 常见可交互物体状态
        if "is_container" in self.properties and self.properties["is_container"]:
            if "is_open" not in self.states:
                self.states["is_open"] = False
        
        # 初始化is_on状态，如果状态中已包含"is_on"字段则表明这是一个可开关的物体
        if "is_on" in self.states:
            # 状态已存在，不需要初始化
            pass
        # 可选：如果特定属性暗示这是一个可开关物体但没有is_on状态，可以在这里添加初始化逻辑

class GrabbableObject(BaseObject):
    """可抓取物体类"""
    
    def __init__(self, obj_id: str, name: str, 
                 states: Optional[Dict[str, Any]] = None,
                 properties: Optional[Dict[str, Any]] = None):
        """
        初始化可抓取物体
        
        Args:
            obj_id: 物体唯一ID
            name: 物体名称
            states: 物体状态字典
            properties: 物体属性字典，如 {'weight': 0.5, 'size': 'small'}
        """
        super().__init__(obj_id, name, ObjectType.GRABBABLE, states, properties)

class FurnitureObject(BaseObject):
    """家具类，有尺寸和重量属性"""
    
    def __init__(self, obj_id: str, name: str, 
                 states: Optional[Dict[str, Any]] = None,
                 properties: Optional[Dict[str, Any]] = None):
        """
        初始化家具
        
        Args:
            obj_id: 家具唯一ID
            name: 家具名称
            states: 家具状态字典
            properties: 家具属性字典，包含 size([长,宽,高]), weight 等
        """
        super().__init__(obj_id, name, ObjectType.FURNITURE, states, properties)
        
        # 确保尺寸和重量属性存在
        if "size" not in self.properties:
            self.properties["size"] = [1.0, 1.0, 1.0]  # 默认[长,宽,高](米)
        if "weight" not in self.properties:
            self.properties["weight"] = 10.0 # 默认重量(千克)
        
        # 是否为容器
        if "is_container" in self.properties and self.properties["is_container"]:
            if "is_open" not in self.states:
                self.states["is_open"] = False

class ItemObject(BaseObject):
    """物品类，有易碎性等特殊属性"""
    
    def __init__(self, obj_id: str, name: str, 
                 states: Optional[Dict[str, Any]] = None,
                 properties: Optional[Dict[str, Any]] = None):
        """
        初始化物品
        
        Args:
            obj_id: 物品唯一ID
            name: 物品名称
            states: 物品状态字典
            properties: 物品属性字典，包含 fragile, weight, size([长,宽,高]) 等
        """
        super().__init__(obj_id, name, ObjectType.ITEM, states, properties)
        
        # 确保必要属性存在
        if "fragile" not in self.properties:
            self.properties["fragile"] = False  # 默认不易碎
        if "weight" not in self.properties:
            self.properties["weight"] = 0.5     # 默认重量(千克)
        if "size" not in self.properties:
            self.properties["size"] = [0.1, 0.1, 0.1]  # 默认[长,宽,高](米)

def create_object_from_dict(data: Dict[str, Any]) -> BaseObject:
    """
    根据字典数据创建合适类型的物体对象
    
    Args:
        data: 物体数据字典
        
    Returns:
        创建的物体对象
    
    Raises:
        ValueError: 当物体类型无效时
    """
    obj_type_str = data.get("type", "").upper()
    if not obj_type_str:
        raise ValueError(f"物体必须指定类型: {data}")
    
    try:
        object_type = ObjectType[obj_type_str]
    except KeyError:
        raise ValueError(f"无效的物体类型: {obj_type_str}")
    
    if object_type == ObjectType.STATIC:
        return StaticObject(
            obj_id=data["id"],
            name=data["name"],
            states=data.get("states", {}),
            properties=data.get("properties", {})
        )
    elif object_type == ObjectType.INTERACTABLE:
        return InteractableObject(
            obj_id=data["id"],
            name=data["name"],
            states=data.get("states", {}),
            properties=data.get("properties", {})
        )
    elif object_type == ObjectType.GRABBABLE:
        return GrabbableObject(
            obj_id=data["id"],
            name=data["name"],
            states=data.get("states", {}),
            properties=data.get("properties", {})
        )
    elif object_type == ObjectType.FURNITURE:
        return FurnitureObject(
            obj_id=data["id"],
            name=data["name"],
            states=data.get("states", {}),
            properties=data.get("properties", {})
        )
    elif object_type == ObjectType.ITEM:
        return ItemObject(
            obj_id=data["id"],
            name=data["name"],
            states=data.get("states", {}),
            properties=data.get("properties", {})
        )
    else:
        # 默认创建基础物体
        return BaseObject(
            obj_id=data["id"],
            name=data["name"],
            object_type=object_type,
            states=data.get("states", {}),
            properties=data.get("properties", {})
        ) 