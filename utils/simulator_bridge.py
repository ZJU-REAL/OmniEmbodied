import os
import logging
from typing import Dict, List, Any, Optional, Tuple

from simulator.core import SimulationEngine, ActionStatus
from .data_loader import default_loader as framework_data_loader

logger = logging.getLogger(__name__)

class SimulatorBridge:
    """
    模拟器桥接类 - 为框架提供对模拟器功能的统一访问接口
    简化架构，避免重复实现模拟器已有的功能
    """

    def __init__(self, simulator: Optional[SimulationEngine] = None, config: Optional[Dict[str, Any]] = None):
        """
        初始化模拟器桥接

        Args:
            simulator: 模拟引擎实例，如果为None则创建新实例
            config: 模拟器配置字典
        """
        self.config = config or {}
        self.simulator = simulator or SimulationEngine(config=self.config)
        
    def initialize_with_task(self, task_file: str) -> bool:
        """
        使用任务文件初始化模拟器

        Args:
            task_file: 任务文件路径

        Returns:
            bool: 是否成功初始化
        """
        return self.simulator.initialize_with_task(task_file)

    def initialize_with_data(self, data: Dict[str, Any]) -> bool:
        """
        使用数据字典初始化模拟器（新API）

        Args:
            data: 包含场景、任务和验证数据的字典
                  格式: {
                      'scene': scene_data,
                      'task': task_data,
                      'verify': verify_data (可选)
                  }

        Returns:
            bool: 是否成功初始化
        """
        return self.simulator.initialize_with_data(data)

    def initialize_with_scenario(self, scenario_id: str) -> bool:
        """
        使用场景ID初始化模拟器（推荐，新数据结构）

        Args:
            scenario_id: 场景ID（如'00001'）

        Returns:
            bool: 是否成功初始化
        """
        try:
            # 使用框架的数据加载器加载完整场景数据
            result = framework_data_loader.load_complete_scenario(scenario_id)
            if result is None:
                logger.error(f"无法加载场景数据: {scenario_id}")
                return False

            # 解包结果（可能是2元组或3元组）
            if len(result) == 2:
                scene_data, task_data = result
                verify_data = None
            else:
                scene_data, task_data, verify_data = result

            # 从场景数据中提取abilities（新的数据结构）
            scene_abilities = scene_data.get('abilities', [])
            if scene_abilities:
                # 重新创建带有scene_abilities的模拟器
                self.simulator = SimulationEngine(config=self.config, scene_abilities=scene_abilities)

            # 构建数据字典
            data = {
                'scene': scene_data,
                'task': task_data
            }
            if verify_data:
                data['verify'] = verify_data

            # 使用新的initialize_with_data方法
            success = self.initialize_with_data(data)

            # 确保任务验证器正确传递到action_handler，支持DONE命令
            if success and hasattr(self.simulator, 'action_handler') and hasattr(self.simulator, 'task_verifier'):
                if self.simulator.action_handler and self.simulator.task_verifier:
                    self.simulator.action_handler.task_verifier = self.simulator.task_verifier
                    logger.debug("已将任务验证器设置到action_handler，支持DONE命令")

            return success

        except Exception as e:
            logger.exception(f"使用场景ID初始化失败: {e}")
            return False
    
    def get_task_info(self) -> Optional[Dict[str, Any]]:
        """
        获取当前任务信息

        Returns:
            Dict: 任务信息字典
        """
        # 适配新API：如果有task_config属性则使用，否则尝试旧方法
        if hasattr(self.simulator, 'task_config') and self.simulator.task_config:
            return self.simulator.task_config
        elif hasattr(self.simulator, 'get_task_info'):
            return self.simulator.get_task_info()
        else:
            logger.warning("无法获取任务信息，模拟器可能未正确初始化")
            return None
    
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
    
    def _normalize_command(self, command: str) -> str:
        """
        标准化命令，将常见的错误命令映射到正确的命令

        Args:
            command: 原始命令字符串

        Returns:
            str: 标准化后的命令字符串
        """
        # 命令映射表：错误命令 -> 正确命令
        command_mappings = {
            # 移动命令
            'MOVE_TO': 'GOTO',
            'MOVETO': 'GOTO',
            'GO_TO': 'GOTO',
            'NAVIGATE': 'GOTO',
            'TRAVEL': 'GOTO',

            # 抓取命令
            'PICKUP': 'GRAB',
            'PICK_UP': 'GRAB',
            'TAKE': 'GRAB',
            'GET': 'GRAB',

            # 放置命令
            'PUT': 'PLACE',
            'DROP': 'PLACE',
            'SET': 'PLACE',
            'PUT_DOWN': 'PLACE',

            # 观察命令
            'INSPECT': 'LOOK',
            'INSPECT_OBJECT': 'LOOK',
            'EXAMINE': 'LOOK',
            'CHECK': 'LOOK',
            'OBSERVE': 'LOOK',
            'VIEW': 'LOOK',
            'LOOK_AT': 'LOOK',

            # 其他命令
            'SEARCH': 'EXPLORE',
            'SCAN': 'EXPLORE',
            'INVESTIGATE': 'EXPLORE',
            'END_TASK': 'DONE',
            'FINISH': 'DONE',
            'COMPLETE': 'DONE',
        }

        # 分割命令获取第一个词（动作）
        parts = command.strip().split()
        if not parts:
            return command

        action = parts[0].upper()

        # 检查是否需要映射
        if action in command_mappings:
            # 替换动作部分
            parts[0] = command_mappings[action]
            normalized_command = ' '.join(parts)
            logger.debug(f"命令映射: '{command}' -> '{normalized_command}'")
            return normalized_command

        return command

    def process_command(self, agent_id: str, command: str) -> Tuple[ActionStatus, str, Optional[Dict[str, Any]]]:
        """
        处理智能体命令

        Args:
            agent_id: 智能体ID
            command: 命令字符串

        Returns:
            Tuple: (状态, 消息, 结果数据)
        """
        # 标准化命令
        normalized_command = self._normalize_command(command)

        if logger.level <= logging.DEBUG:
            logger.debug("处理命令 - 智能体: %s, 原始命令: '%s', 标准化命令: '%s'", agent_id, command, normalized_command)
            # 记录命令前的智能体状态
            agent_info = self.get_agent_info(agent_id)
            if agent_info:
                location_id = agent_info.get('location_id', '未知')
                location_name = self.get_room_info(location_id).get('name', '未知') if location_id else '未知'
                inventory = agent_info.get('inventory', [])
                logger.debug("命令前状态 - 位置: %s(%s), 库存: %s", location_name, location_id, inventory)

        # 尝试解析和执行命令
        try:
            # 检查模拟器是否已初始化
            if not hasattr(self.simulator, 'action_handler') and not hasattr(self.simulator, 'process_command'):
                logger.warning("模拟器未正确初始化")
                return ActionStatus.FAILURE, "模拟器未初始化", None

            # 适配新API：使用action_handler处理命令
            if hasattr(self.simulator, 'action_handler') and self.simulator.action_handler:
                result = self.simulator.action_handler.process_command(agent_id, normalized_command)
            else:
                # 回退到旧API
                if hasattr(self.simulator, 'process_command'):
                    result = self.simulator.process_command(agent_id, normalized_command)
                else:
                    logger.warning("模拟器没有可用的命令处理方法")
                    return ActionStatus.FAILURE, "模拟器未初始化", None

            # 检查返回值
            if result is None:
                logger.warning("模拟器返回None，可能未正确初始化")
                return ActionStatus.FAILURE, "模拟器未初始化", None

            # 检查返回值类型
            if isinstance(result, tuple) and len(result) == 3:
                status, message, data = result
            elif isinstance(result, dict):
                # 新版本API可能返回字典
                status = result.get('status', ActionStatus.FAILURE)
                message = result.get('message', '')
                data = result.get('data', {})
            else:
                logger.warning(f"模拟器返回了未知格式的结果: {type(result)}")
                return ActionStatus.FAILURE, f"未知返回格式: {type(result)}", None

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
            return ActionStatus.FAILURE, f"处理命令出错: {str(e)}", None
    
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

    def get_available_actions(self, agent_id: str) -> List[str]:
        """
        获取指定智能体的所有可执行动作

        Args:
            agent_id: 智能体ID

        Returns:
            List[str]: 可执行动作名称列表
        """
        if not hasattr(self.simulator, 'action_handler') or not self.simulator.action_handler:
            logger.warning("Action handler未初始化")
            return []

        action_manager = self.simulator.action_handler.action_manager

        # 获取全局动作
        all_actions = set(action_manager.action_classes.keys())

        # 获取智能体特定动作
        agent_actions = action_manager.agent_action_classes.get(agent_id, {})
        all_actions.update(agent_actions.keys())

        return sorted(list(all_actions))

    def get_basic_actions(self) -> List[str]:
        """
        获取基础动作列表（不包括属性动作和协作动作）

        Returns:
            List[str]: 基础动作名称列表
        """
        basic_actions = ['GOTO', 'GRAB', 'PLACE', 'LOOK', 'EXPLORE', 'DONE']
        return basic_actions

    def get_attribute_actions(self, agent_id: str) -> List[str]:
        """
        获取智能体的属性动作列表

        Args:
            agent_id: 智能体ID

        Returns:
            List[str]: 属性动作名称列表
        """
        all_actions = self.get_available_actions(agent_id)

        # 过滤出属性动作（排除基础动作和协作动作）
        basic_actions = set(self.get_basic_actions())
        attribute_actions = []

        for action in all_actions:
            if action not in basic_actions and not action.startswith('CORP_'):
                attribute_actions.append(action)

        return attribute_actions

    def get_collaborative_actions(self, agent_id: str) -> List[str]:
        """
        获取智能体的协作动作列表

        Args:
            agent_id: 智能体ID

        Returns:
            List[str]: 协作动作名称列表
        """
        all_actions = self.get_available_actions(agent_id)

        # 过滤出协作动作（以CORP_开头）
        collaborative_actions = [action for action in all_actions if action.startswith('CORP_')]

        return collaborative_actions

    def get_agent_supported_actions_description(self, agent_ids) -> str:
        """
        获取智能体支持的动作的完整描述（使用模拟器提供的新API）

        Args:
            agent_ids: 智能体ID或智能体ID列表
                      - 如果是字符串，会自动转换为单元素列表
                      - 如果是列表，直接使用

        Returns:
            str: 动作描述字符串，包含所有支持的动作和使用说明
        """
        if not hasattr(self.simulator, 'action_handler') or not self.simulator.action_handler:
            logger.warning("Action handler未初始化")
            return ""

        try:
            # 兼容旧API：如果传入的是字符串，转换为列表
            if isinstance(agent_ids, str):
                agent_ids = [agent_ids]
            elif not isinstance(agent_ids, list):
                logger.error(f"agent_ids必须是字符串或列表，收到: {type(agent_ids)}")
                return ""

            # 使用模拟器提供的新API获取动作描述
            description = self.simulator.action_handler.get_agent_supported_actions_description(agent_ids)
            return description
        except Exception as e:
            logger.error(f"获取动作描述失败: {e}")
            return ""
    
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