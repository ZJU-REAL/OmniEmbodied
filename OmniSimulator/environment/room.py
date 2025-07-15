from typing import Dict, List, Optional, Set, Any

class Room:
    """房间类 - 表示模拟环境中的房间"""
    
    def __init__(self, room_id: str, name: str, 
                 properties: Optional[Dict[str, Any]] = None):
        """
        初始化房间
        
        Args:
            room_id: 房间唯一ID
            name: 房间名称
            properties: 房间属性字典，如 {'size': 'large', 'type': 'kitchen'}
        """
        self.id = room_id
        self.name = name
        self.properties = properties or {}
        self.connected_to_room_ids: Set[str] = set()  # 连接到的房间ID集合
    
    def connect_to(self, room_id: str) -> None:
        """
        连接到另一个房间
        
        Args:
            room_id: 要连接的房间ID
        """
        self.connected_to_room_ids.add(room_id)
    
    def disconnect_from(self, room_id: str) -> None:
        """
        断开与另一个房间的连接
        
        Args:
            room_id: 要断开连接的房间ID
        """
        if room_id in self.connected_to_room_ids:
            self.connected_to_room_ids.remove(room_id)
    
    def is_connected_to(self, room_id: str) -> bool:
        """
        检查是否连接到特定房间
        
        Args:
            room_id: 要检查的房间ID
            
        Returns:
            bool: 是否连接
        """
        return room_id in self.connected_to_room_ids
    
    def to_dict(self) -> Dict[str, Any]:
        """将房间对象转换为字典表示"""
        return {
            "id": self.id,
            "name": self.name,
            "properties": self.properties,
            "connected_to_room_ids": list(self.connected_to_room_ids)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Room':
        """从字典创建房间对象"""
        room = cls(
            room_id=data["id"],
            name=data["name"],
            properties=data.get("properties", {})
        )
        
        connected_rooms = data.get("connected_to_room_ids", [])
        if isinstance(connected_rooms, list):
            for connected_room_id in connected_rooms:
                room.connect_to(connected_room_id)
        
        return room 