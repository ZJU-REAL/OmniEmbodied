from typing import Dict, Optional, Any
try:
    from ..core.enums import ActionStatus
except ValueError:
    # 如果相对导入失败，尝试绝对导入
    try:
        from simulator.core.enums import ActionStatus
    except ImportError:
        # 如果还是失败，尝试从utils.embodied_simulator导入
        from utils.embodied_simulator import ActionStatus

class FeedbackGenerator:
    """反馈生成器 - 负责生成用户友好的反馈信息"""
    
    def __init__(self, verbose: bool = False):
        """
        初始化反馈生成器
        
        Args:
            verbose: 是否生成详细反馈
        """
        self.verbose = verbose
    
    def format_feedback(self, status: ActionStatus, message: str, 
                       result_data: Optional[Dict[str, Any]] = None) -> str:
        """
        格式化反馈消息
        
        Args:
            status: 动作执行状态
            message: 原始反馈消息
            result_data: 额外的结果数据
            
        Returns:
            str: 格式化后的反馈消息
        """
        formatted_message = message
        
        # 如果设置为详细模式且有结果数据，则添加额外信息
        if self.verbose and result_data:
            # 根据不同的动作类型和结果添加额外信息
            if "visible_objects" in result_data:
                # LOOK动作的详细物体信息
                objects = result_data["visible_objects"]
                if objects:
                    formatted_message += "\nVisible objects:"
                    for obj in objects:
                        obj_desc = f"\n- {obj['name']} ({obj['id']})"
                        # 添加状态信息
                        states = obj.get('states', {})
                        if states:
                            state_strs = []
                            for key, value in states.items():
                                if key == "is_open":
                                    state_strs.append("open" if value else "closed")
                                elif key == "is_on":
                                    state_strs.append("on" if value else "off")
                                else:
                                    state_strs.append(f"{key}: {value}")
                            if state_strs:
                                obj_desc += f" [{', '.join(state_strs)}]"
                        formatted_message += obj_desc
            
            if "contained_objects" in result_data:
                # 容器内的物体
                objects = result_data["contained_objects"]
                if objects:
                    formatted_message += "\nContained objects:"
                    for obj in objects:
                        formatted_message += f"\n- {obj['name']} ({obj['id']})"
        
        # 为不同的状态添加前缀或颜色（在文本环境中可以用特殊符号或标签）
        if status == ActionStatus.SUCCESS:
            # 成功状态，可以添加√或[成功]前缀
            return f"✓ {formatted_message}"
        elif status == ActionStatus.FAILURE:
            # 失败状态，可以添加×或[失败]前缀
            return f"✗ {formatted_message}"
        elif status == ActionStatus.INVALID:
            # 无效动作，可以添加!或[无效]前缀
            return f"! {formatted_message}"
        
        return formatted_message
    
    def generate_observation(self, agent_id: str, location_data: Dict[str, Any],
                           objects_data: Dict[str, Any]) -> str:
        """
        生成环境观察描述
        
        Args:
            agent_id: 智能体ID
            location_data: 位置数据
            objects_data: 物体数据
            
        Returns:
            str: 观察描述
        """
        room_name = location_data.get('name', 'unknown location')
        observation = f"You are in {room_name}."
        
        # 描述房间中的物体
        visible_objects = []
        for obj_id, obj in objects_data.items():
            if obj.get('location_id') == location_data.get('id'):
                obj_desc = obj.get('name', obj_id)
                # 添加状态描述
                states = obj.get('states', {})
                if states:
                    state_strs = []
                    for key, value in states.items():
                        if key == "is_open":
                            state_strs.append("open" if value else "closed")
                        elif key == "is_on":
                            state_strs.append("on" if value else "off")
                    if state_strs:
                        obj_desc += f"（{', '.join(state_strs)}）"
                visible_objects.append(obj_desc)
        
        if visible_objects:
            observation += f"\nYou see: {', '.join(visible_objects)}."
        else:
            observation += "\nThere are no objects here."
        
        return observation 