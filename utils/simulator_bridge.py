import os
import logging
from typing import Dict, List, Any, Optional, Tuple

from embodied_simulator import SimulationEngine, ActionStatus

logger = logging.getLogger(__name__)

class SimulatorBridge:
    """
    模拟器桥接类 - 为框架提供对模拟器功能的统一访问接口
    简化架构，避免重复实现模拟器已有的功能
    """
    
    def __init__(self, simulator: Optional[SimulationEngine] = None):
        """
        初始化模拟器桥接
        
        Args:
            simulator: 模拟引擎实例，如果为None则创建新实例
        """
        self.simulator = simulator or SimulationEngine()
        
    def initialize_with_task(self, task_file: str) -> bool:
        """
        使用任务文件初始化模拟器
        
        Args:
            task_file: 任务文件路径
            
        Returns:
            bool: 是否成功初始化
        """
        return self.simulator.initialize_with_task(task_file)
    
    def get_task_info(self) -> Optional[Dict[str, Any]]:
        """
        获取当前任务信息
        
        Returns:
            Dict: 任务信息字典
        """
        return self.simulator.get_task_info()
    
    def get_task_description(self) -> str:
        """
        获取任务描述
        
        Returns:
            str: 任务描述文本
        """
        task_info = self.get_task_info()
        return task_info.get('task_description', '') if task_info else ''
    
    def get_agents_config(self) -> List[Dict[str, Any]]:
        """
        获取智能体配置
        
        Returns:
            List: 智能体配置列表
        """
        task_info = self.get_task_info()
        return task_info.get('agents_config', []) if task_info else []
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        获取智能体信息
        
        Args:
            agent_id: 智能体ID
            
        Returns:
            Dict: 智能体信息字典
        """
        return self.simulator.get_agent_info(agent_id)
    
    def get_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有智能体信息
        
        Returns:
            Dict: 智能体ID到智能体信息字典的映射
        """
        agents = {}
        if hasattr(self.simulator, 'agent_manager'):
            for agent_id in self.simulator.agent_manager.get_all_agents().keys():
                agent_info = self.simulator.get_agent_info(agent_id)
                if agent_info:
                    agents[agent_id] = agent_info
        return agents
    
    def get_scene_id(self) -> Optional[str]:
        """
        获取当前场景ID
        
        Returns:
            str: 场景ID
        """
        task_info = self.get_task_info()
        return task_info.get('scene_uid') if task_info else None
    
    def get_rooms(self) -> List[Dict[str, Any]]:
        """
        获取所有房间信息
        
        Returns:
            List: 房间信息列表
        """
        rooms = []
        if hasattr(self.simulator, 'world_state') and hasattr(self.simulator.world_state, 'graph'):
            for room_id in self.simulator.world_state.graph.room_ids:
                room_info = self.simulator.get_room_info(room_id)
                if room_info:
                    rooms.append(room_info)
        return rooms
    
    def get_room_info(self, room_id: str) -> Optional[Dict[str, Any]]:
        """
        获取房间信息
        
        Args:
            room_id: 房间ID
            
        Returns:
            Dict: 房间信息字典
        """
        return self.simulator.get_room_info(room_id)
    
    def get_objects_in_room(self, room_id: str) -> List[Dict[str, Any]]:
        """
        获取房间中的所有物体
        
        Args:
            room_id: 房间ID
            
        Returns:
            List: 物体信息列表
        """
        objects = []
        if hasattr(self.simulator, 'env_manager'):
            objects = self.simulator.env_manager.get_objects_in_room(room_id)
        return objects or []
    
    def get_object_info(self, object_id: str) -> Optional[Dict[str, Any]]:
        """
        获取物体信息
        
        Args:
            object_id: 物体ID
            
        Returns:
            Dict: 物体信息字典
        """
        return self.simulator.get_object_info(object_id)
    
    def get_all_objects(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有物体信息
        
        Returns:
            Dict: 物体ID到物体信息字典的映射
        """
        objects = {}
        if hasattr(self.simulator, 'env_manager'):
            # 使用反射获取模拟器中的所有物体
            if hasattr(self.simulator.env_manager, 'objects'):
                return self.simulator.env_manager.objects
        return objects
    
    def process_command(self, agent_id: str, command: str) -> Tuple[ActionStatus, str, Optional[Dict[str, Any]]]:
        """
        处理智能体命令
        
        Args:
            agent_id: 智能体ID
            command: 命令字符串
            
        Returns:
            Tuple: (状态, 消息, 结果数据)
        """
        if logger.level <= logging.DEBUG:
            logger.debug("处理命令 - 智能体: %s, 命令: '%s'", agent_id, command)
            # 记录命令前的智能体状态
            agent_info = self.get_agent_info(agent_id)
            if agent_info:
                location_id = agent_info.get('location_id', '未知')
                location_name = self.get_room_info(location_id).get('name', '未知') if location_id else '未知'
                inventory = agent_info.get('inventory', [])
                logger.debug("命令前状态 - 位置: %s(%s), 库存: %s", location_name, location_id, inventory)
        
        # 尝试解析和执行命令
        try:
            # 这里我们应该区分不同类型的命令，例如基础动作和属性动作
            # 目前我们简单地转发给模拟器
            result = self.simulator.process_command(agent_id, command)
            
            # 检查返回值类型是否为tuple，表示老版本API
            if isinstance(result, tuple) and len(result) == 3:
                status, message, data = result
            else:
                # 新版本API返回字典
                status = result.get('status', ActionStatus.FAILURE)
                message = result.get('message', '')
                data = result.get('data', {})
            
            if logger.level <= logging.DEBUG:
                logger.debug("命令处理结果 - 状态: %s, 消息: %s", status, message)
                
                # 记录命令后的智能体状态变化
                agent_info_after = self.get_agent_info(agent_id)
                if agent_info_after:
                    location_id = agent_info_after.get('location_id', '未知')
                    location_name = self.get_room_info(location_id).get('name', '未知') if location_id else '未知'
                    inventory = agent_info_after.get('inventory', [])
                    logger.debug("命令后状态 - 位置: %s(%s), 库存: %s", location_name, location_id, inventory)
                
                # 尝试分析命令和结果之间的关系
                if status == ActionStatus.FAILURE or status == ActionStatus.INVALID:
                    command_parts = command.split()
                    command_type = command_parts[0].upper() if command_parts else ''
                    
                    # 检测常见错误模式
                    if command_type == 'GOTO' and 'must be near' in message:
                        logger.debug("GOTO命令失败原因分析: 智能体尝试移动到不可达位置")
                    elif command_type == 'GRAB' and 'must be near' in message:
                        logger.debug("GRAB命令失败原因分析: 智能体尝试抓取不在近邻范围内的物体")
                    elif command_type == 'PLACE' and 'does not have' in message:
                        logger.debug("PLACE命令失败原因分析: 智能体尝试放置未持有的物体")
                    elif 'invalid command' in message.lower():
                        logger.debug("命令失败原因分析: 无效命令格式")
            
            return status, message, data
            
        except Exception as e:
            logger.exception(f"处理命令时出错: {e}")
            return ActionStatus.ERROR, f"处理命令出错: {str(e)}", None
    
    def find_objects_by_name(self, name: str) -> List[Dict[str, Any]]:
        """
        按名称查找物体
        
        Args:
            name: 物体名称
            
        Returns:
            List: 符合条件的物体列表
        """
        result = []
        all_objects = self.get_all_objects()
        for obj_id, obj in all_objects.items():
            if obj.get('name') == name:
                result.append(obj)
        return result
    
    def find_objects_by_name_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        按名称关键词查找物体
        
        Args:
            keyword: 名称关键词
            
        Returns:
            List: 符合条件的物体列表
        """
        result = []
        all_objects = self.get_all_objects()
        for obj_id, obj in all_objects.items():
            name = obj.get('name', '')
            if keyword.lower() in name.lower():
                result.append(obj)
        return result
    
    def find_objects_by_type(self, object_type: str) -> List[Dict[str, Any]]:
        """
        按类型查找物体
        
        Args:
            object_type: 物体类型
            
        Returns:
            List: 符合条件的物体列表
        """
        result = []
        all_objects = self.get_all_objects()
        for obj_id, obj in all_objects.items():
            if obj.get('type') == object_type:
                result.append(obj)
        return result
    
    def find_objects_by_property(self, property_name: str, property_value: Any) -> List[Dict[str, Any]]:
        """
        按属性查找物体
        
        Args:
            property_name: 属性名称
            property_value: 属性值
            
        Returns:
            List: 符合条件的物体列表
        """
        result = []
        all_objects = self.get_all_objects()
        for obj_id, obj in all_objects.items():
            props = obj.get('properties', {})
            if property_name in props and props[property_name] == property_value:
                result.append(obj)
        return result
    
    def get_objects_on_furniture(self, furniture_id: str) -> List[Dict[str, Any]]:
        """
        获取家具上的所有物体
        
        Args:
            furniture_id: 家具ID
            
        Returns:
            List: 物体信息列表
        """
        result = []
        all_objects = self.get_all_objects()
        for obj_id, obj in all_objects.items():
            location_id = obj.get('location_id', '')
            if location_id.startswith('on:') and location_id[3:] == furniture_id:
                result.append(obj)
        return result
    
    def describe_agent_natural_language(self, agent_id: str, agent: Dict = None) -> str:
        """
        用自然语言描述智能体状态
        
        Args:
            agent_id: 智能体ID
            agent: 智能体数据字典（可选，如不提供则自动获取）
            
        Returns:
            str: 智能体描述文本
        """
        if hasattr(self.simulator, 'world_state'):
            if agent is None:
                agent = self.get_agent_info(agent_id)
            return self.simulator.world_state.describe_agent_natural_language(agent_id, agent)
        return f"无法描述智能体 {agent_id}，世界状态不可用"
    
    def describe_room_natural_language(self, room_id: str, agents: Optional[Dict[str, Dict]] = None, 
                                      sim_config: Optional[Dict[str, Any]] = None) -> str:
        """
        用自然语言详细描述房间内容
        
        Args:
            room_id: 房间ID
            agents: 智能体字典 {agent_id -> agent_data}，如不提供则使用所有智能体
            sim_config: 模拟器配置
                
        Returns:
            str: 房间描述文本
        """
        if hasattr(self.simulator, 'world_state'):
            if agents is None:
                agents = self.get_all_agents()
            return self.simulator.world_state.describe_room_natural_language(room_id, agents, sim_config)
        return f"无法描述房间 {room_id}，世界状态不可用"
    
    def describe_environment_natural_language(self, agents: Optional[Dict[str, Dict]] = None, 
                                             sim_config: Optional[Dict[str, Any]] = None) -> str:
        """
        用自然语言描述整个环境（所有房间及其内容）和所有智能体状态
        
        Args:
            agents: 智能体字典 {agent_id -> agent_data}，如不提供则使用所有智能体
            sim_config: 模拟器配置
                - nlp_show_object_properties: 是否输出家具和物品的详细属性
                - nlp_only_show_discovered: 只描述已发现内容
                - nlp_detail_level: 详细程度 'full'/'room'/'brief'
                
        Returns:
            str: 环境和智能体描述文本
        """
        if hasattr(self.simulator, 'world_state'):
            if agents is None:
                agents = self.get_all_agents()
            
            # 检查是否指定了详细级别
            sim_config = sim_config or {}
            detail_level = sim_config.get('nlp_detail_level', 'full')
            
            # 根据详细级别决定返回什么样的描述
            if detail_level == 'room' and agents:
                # 如果是room级别且有智能体，则只描述智能体所在的房间
                first_agent_id = next(iter(agents))
                agent_info = agents[first_agent_id]
                room_id = agent_info.get('location_id', '')
                if room_id:
                    return self.describe_room_natural_language(room_id, agents, sim_config)
            elif detail_level == 'brief' and agents:
                # 如果是brief级别，则只描述智能体状态
                descriptions = []
                for agent_id, agent_data in agents.items():
                    descriptions.append(self.describe_agent_natural_language(agent_id, agent_data))
                return "\n\n".join(descriptions)
            
            # 默认返回完整环境描述（full级别）
            return self.simulator.world_state.describe_environment_natural_language(agents, sim_config)
        return "无法描述环境，世界状态不可用" 