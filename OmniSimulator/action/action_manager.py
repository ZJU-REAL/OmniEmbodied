from typing import Dict, Optional, Tuple, Any, List, Type

from ..core.enums import ActionType, ActionStatus
from .actions.basic_actions import (
    GotoAction, GrabAction, PlaceAction, LookAction, ExploreAction
)
from .actions.corporate_actions import CorpGrabAction, CorpGotoAction, CorpPlaceAction
from .actions.base_action import BaseAction

class ActionManager:
    """
    动作管理器 - 负责动作的创建、验证和执行
    
    这个类整合了原有的ActionParser, ActionValidator和ActionExecutor的功能，
    采用了面向对象的设计模式，使代码更清晰、易于维护和扩展。
    
    主要职责：
    1. 解析命令字符串，创建动作对象
    2. 验证动作是否可以执行
    3. 执行动作并返回结果
    4. 维护协作动作的状态
    """
    
    # 类级别的字典，存储每个智能体特定的动作映射
    # 格式: {agent_id: {action_name: action_class}}
    agent_action_classes = {}
    
    def __init__(self, world_state, env_manager, agent_manager, scene_abilities=None):
        """
        初始化动作管理器

        Args:
            world_state: 世界状态对象
            env_manager: 环境管理器
            agent_manager: 智能体管理器
            scene_abilities: 场景支持的能力列表，用于注册不需要工具的属性动作
        """
        self.world_state = world_state
        self.env_manager = env_manager
        self.agent_manager = agent_manager

        # 保存合作动作状态
        if not hasattr(self.world_state, 'pending_corporate_actions'):
            setattr(self.world_state, 'pending_corporate_actions', {})

        # 注册所有可用的基础动作类
        self.action_classes = {
            'GOTO': GotoAction,
            'GRAB': GrabAction,
            'PLACE': PlaceAction,
            'LOOK': LookAction,
            'EXPLORE': ExploreAction,
            'CORP_GRAB': CorpGrabAction,
            'CORP_GOTO': CorpGotoAction,
            'CORP_PLACE': CorpPlaceAction
        }

        # 根据场景abilities注册不需要工具的属性动作
        if scene_abilities:
            try:
                from .actions.attribute_actions import AttributeAction
                from .actions.corporate_attribute_actions import CorporateAttributeAction

                # 确保CSV文件已加载
                AttributeAction.load_from_csv()
                CorporateAttributeAction.load_from_csv()

                # 只注册场景中包含的且不需要工具的动作
                self._register_scene_no_tool_actions(scene_abilities)

            except (ImportError, Exception) as e:
                print(f"加载属性动作配置失败: {e}")
    
    @classmethod
    def register_ability_action(cls, action_name: str, agent_id: str):
        """
        为特定智能体注册能力相关动作（仅限需要工具的动作）
        
        Args:
            action_name: 动作名称
            agent_id: 智能体ID
        """
        # 确保属性动作类和配置已加载
        from .actions.attribute_actions import AttributeAction
        if not AttributeAction.action_configs:
            AttributeAction.load_from_csv()
        
        # 确保合作属性动作类和配置已加载
        from .actions.corporate_attribute_actions import CorporateAttributeAction
        if not CorporateAttributeAction.action_configs:
            CorporateAttributeAction.load_from_csv()
        
        # 检查动作是否在配置中且需要工具
        action_name_lower = action_name.lower()
        if action_name_lower in AttributeAction.action_configs:
            config = AttributeAction.action_configs[action_name_lower]
            requires_tool = config.get("requires_tool", True)
            
            # 只注册需要工具的动作
            if requires_tool:
                if agent_id not in cls.agent_action_classes:
                    cls.agent_action_classes[agent_id] = {}
                
                # 注册普通属性动作
                cls.agent_action_classes[agent_id][action_name.upper()] = AttributeAction
                # 注册合作属性动作
                cls.agent_action_classes[agent_id][f"CORP_{action_name.upper()}"] = CorporateAttributeAction
                print(f"为智能体 {agent_id} 注册动作: {action_name} 和 CORP_{action_name}")

    def _register_scene_no_tool_actions(self, scene_abilities: List[str]):
        """
        根据场景abilities注册不需要工具的属性动作

        Args:
            scene_abilities: 场景支持的能力列表
        """
        from .actions.attribute_actions import AttributeAction
        from .actions.corporate_attribute_actions import CorporateAttributeAction

        registered_count = 0
        registered_actions = []

        for ability in scene_abilities:
            ability_lower = ability.lower()

            # 检查是否在配置中且不需要工具
            if ability_lower in AttributeAction.action_configs:
                config = AttributeAction.action_configs[ability_lower]
                requires_tool = config.get('requires_tool', True)

                if not requires_tool:
                    # 注册普通属性动作
                    action_name = ability_lower.upper()
                    self.register_action_class(action_name, AttributeAction)
                    registered_actions.append(action_name)

                    # 注册合作属性动作
                    corp_action_name = f"CORP_{action_name}"
                    self.register_action_class(corp_action_name, CorporateAttributeAction)
                    registered_actions.append(corp_action_name)

                    registered_count += 1

        if registered_count > 0:
            print(f"根据场景abilities注册了 {registered_count} 个不需要工具的动作: {', '.join(registered_actions)}")
        else:
            print("场景中没有不需要工具的属性动作需要注册")

    def _get_agent_current_abilities(self, agent_id: str) -> set:
        """
        获取智能体当前具有的所有能力

        Args:
            agent_id: 智能体ID

        Returns:
            set: 智能体当前能力集合
        """
        try:
            agent = self.agent_manager.get_agent(agent_id)
            if agent and hasattr(agent, 'abilities'):
                # 确保返回集合类型
                if isinstance(agent.abilities, set):
                    return agent.abilities
                elif isinstance(agent.abilities, (list, tuple)):
                    return set(agent.abilities)
                else:
                    return set()
            return set()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"获取智能体 {agent_id} 能力时出错: {e}")
            return set()

    def _get_common_abilities(self, agent_ids: list) -> set:
        """
        获取多个智能体的共同能力

        Args:
            agent_ids: 智能体ID列表

        Returns:
            set: 所有智能体都具有的能力集合
        """
        if not agent_ids:
            return set()

        # 获取第一个智能体的能力作为基准
        common_abilities = self._get_agent_current_abilities(agent_ids[0])

        # 与其他智能体的能力求交集
        for agent_id in agent_ids[1:]:
            agent_abilities = self._get_agent_current_abilities(agent_id)
            common_abilities = common_abilities.intersection(agent_abilities)

        return common_abilities

    @classmethod
    def unregister_ability_action(cls, action_name: str, agent_id: str):
        """
        为特定智能体解绑能力相关动作（仅限需要工具的动作）
        
        Args:
            action_name: 动作名称
            agent_id: 智能体ID
        """
        # 确保属性动作类和配置已加载
        from .actions.attribute_actions import AttributeAction
        if not AttributeAction.action_configs:
            AttributeAction.load_from_csv()
            
        # 检查动作是否在配置中且需要工具
        action_name_lower = action_name.lower()
        if action_name_lower in AttributeAction.action_configs:
            config = AttributeAction.action_configs[action_name_lower]
            requires_tool = config.get("requires_tool", True)
            
            # 只解绑需要工具的动作
            if requires_tool and agent_id in cls.agent_action_classes:
                # 解绑普通属性动作
                if action_name.upper() in cls.agent_action_classes[agent_id]:
                    del cls.agent_action_classes[agent_id][action_name.upper()]
                
                # 解绑合作属性动作
                corp_action_name = f"CORP_{action_name.upper()}"
                if corp_action_name in cls.agent_action_classes[agent_id]:
                    del cls.agent_action_classes[agent_id][corp_action_name]
                
                print(f"为智能体 {agent_id} 解绑动作: {action_name} 和 CORP_{action_name}")
    
    def register_action_class(self, action_name: str, action_class: Type[BaseAction]):
        """
        注册单个动作类
        
        Args:
            action_name: 动作名称，将自动转为大写
            action_class: 动作类，必须是BaseAction的子类
            
        Returns:
            self: 支持链式调用
        """
        if not issubclass(action_class, BaseAction):
            raise TypeError(f"动作类必须是BaseAction的子类: {action_class}")
        
        self.action_classes[action_name.upper()] = action_class
        return self
    
    def register_action_classes(self, action_classes_dict: Dict[str, Type[BaseAction]]):
        """
        批量注册多个动作类
        
        Args:
            action_classes_dict: 动作名称到动作类的映射字典
            
        Returns:
            self: 支持链式调用
        """
        for name, cls in action_classes_dict.items():
            self.register_action_class(name, cls)
        return self

    def is_action_registered(self, action_name: str) -> bool:
        """
        检查动作是否已注册

        Args:
            action_name: 动作名称

        Returns:
            bool: 是否已注册
        """
        return action_name.upper() in self.action_classes
    
    def parse_command(self, command_str: str, agent_id: str) -> Tuple[Optional[BaseAction], Optional[str]]:
        """
        解析命令字符串并创建相应的动作对象
        
        Args:
            command_str: 命令字符串，如"GRAB cup_1"
            agent_id: 执行动作的智能体ID
            
        Returns:
            Tuple[Optional[BaseAction], Optional[str]]: (动作对象, 错误消息)
                如果解析成功，错误消息为None；如果解析失败，动作对象为None
        """
        # 去除命令两端的空白并提取动作名称
        command = command_str.strip().split()[0].upper()
        
        # 首先检查智能体特定的动作类
        agent_actions = self.agent_action_classes.get(agent_id, {})
        if command in agent_actions:
            action_class = agent_actions[command]
            action = action_class.from_command(command_str, agent_id)
            if action:
                return action, None
        
        # 如果没有找到智能体特定的动作，再查找全局动作类
        action_class = self.action_classes.get(command)
        if not action_class:
            return None, f"Unknown command: {command}"

        # 使用动作类解析命令字符串
        action = action_class.from_command(command_str, agent_id)
        if not action:
            return None, f"Invalid command format: {command_str}"
        
        return action, None
    
    def validate_action(self, action: BaseAction) -> Tuple[bool, str]:
        """
        验证动作是否有效
        
        Args:
            action: 动作对象
            
        Returns:
            Tuple[bool, str]: (是否有效, 原因消息)
        """
        # 合作模式全局限制
        agent = self.agent_manager.get_agent(action.agent_id)
        if agent and hasattr(agent, 'corporate_mode_object_id') and agent.corporate_mode_object_id:
            # 直接使用ActionType枚举比较
            from ..core.enums import ActionType
            allowed_actions = [ActionType.CORP_GOTO, ActionType.CORP_PLACE]
            if action.action_type not in allowed_actions:
                return False, "In cooperative mode, only cooperative carrying or placing actions are allowed"
        return action.validate(
            self.world_state,
            self.env_manager,
            self.agent_manager
        )
    
    def execute_action(self, action: BaseAction) -> Tuple[ActionStatus, str, Optional[Dict[str, Any]]]:
        """
        执行动作
        
        Args:
            action: 动作对象
            
        Returns:
            Tuple[ActionStatus, str, Optional[Dict]]: (执行状态, 反馈消息, 额外结果数据)
        """
        return action.execute(
            self.world_state,
            self.env_manager,
            self.agent_manager
        )
    
    def process_command(self, command_str: str, agent_id: str) -> Tuple[ActionStatus, str, Optional[Dict[str, Any]]]:
        """
        处理命令字符串，包括解析、验证和执行
        
        Args:
            command_str: 命令字符串
            agent_id: 执行命令的智能体ID
            
        Returns:
            Tuple[ActionStatus, str, Optional[Dict]]: (执行状态, 反馈消息, 额外结果数据)
        """
        # 解析命令
        action, error = self.parse_command(command_str, agent_id)
        if error or action is None:
            return ActionStatus.INVALID, error or "Failed to parse the command", None
        
        # 验证动作
        valid, reason = self.validate_action(action)
        if not valid:
            return ActionStatus.INVALID, reason, None
        
        # 执行动作
        return self.execute_action(action)

    def get_agent_supported_actions_description(self, agent_ids: List[str]) -> str:
        """
        获取智能体支持的所有动作的字符串描述

        Args:
            agent_ids: 智能体ID列表，支持单个或多个智能体

        Returns:
            str: 包含所有支持动作的描述字符串（英文）
        """
        from .actions.attribute_actions import AttributeAction

        # 确保CSV文件已加载
        AttributeAction.load_from_csv()

        # 参数验证
        if not agent_ids or not isinstance(agent_ids, list):
            return "Error: agent_ids must be a non-empty list"

        # 去重并保持顺序
        unique_agent_ids = []
        for agent_id in agent_ids:
            if agent_id not in unique_agent_ids:
                unique_agent_ids.append(agent_id)

        agent_ids = unique_agent_ids
        is_single_agent = len(agent_ids) == 1

        descriptions = []

        # 根据智能体数量设置标题
        if is_single_agent:
            descriptions.append(f"=== SUPPORTED ACTIONS FOR {agent_ids[0].upper()} ===\n")
        else:
            agent_names = " & ".join([agent_id.upper() for agent_id in agent_ids])
            descriptions.append(f"=== SUPPORTED ACTIONS FOR {agent_names} ===\n")

        # 1. 基础动作描述
        descriptions.append("== Basic Actions ==")
        descriptions.append("GOTO <object_id>")
        descriptions.append("  - Move to a specific location or object")
        descriptions.append("  - Example: GOTO main_workbench_area")
        descriptions.append("")

        descriptions.append("GRAB <object_id>")
        descriptions.append("  - Pick up an object that is nearby")
        descriptions.append("  - Example: GRAB cup_1")
        descriptions.append("")

        descriptions.append("PLACE <object_id> <in|on> <container_id>")
        descriptions.append("  - Place a held object into or onto another object")
        descriptions.append("  - Example: PLACE cup_1 on table_1")
        descriptions.append("")

        # descriptions.append("LOOK <object_id>")
        # descriptions.append("  - Examine an object to get detailed information")
        # descriptions.append("  - Example: LOOK table_1")
        # descriptions.append("")

        descriptions.append("EXPLORE")
        descriptions.append("  - Explore current room to discover objects")
        descriptions.append("  - Example: EXPLORE")
        descriptions.append("")
        
        descriptions.append("DONE")
        descriptions.append("  - Finish the task")
        descriptions.append("  - Example: DONE")
        descriptions.append("")

        # 2. 全局可用的属性动作（不需要工具）
        global_attribute_actions = []
        for action_name, action_class in self.action_classes.items():
            if action_class == AttributeAction and not action_name.startswith('CORP_'):
                action_lower = action_name.lower()
                if action_lower in AttributeAction.action_configs:
                    config = AttributeAction.action_configs[action_lower]
                    # 只显示不需要工具的动作
                    requires_tool = config.get('requires_tool', True)
                    if not requires_tool:
                        description = config.get('description', 'No description available')
                        global_attribute_actions.append((action_name, description))

        if global_attribute_actions:
            descriptions.append("== Attribute Actions (No Tools Required) ==")
            for action_name, description in sorted(global_attribute_actions):
                descriptions.append(f"{action_name} <object_id>")
                descriptions.append(f"  - {description}")
                descriptions.append(f"  - Example: {action_name} device_1")
                descriptions.append("")

        # 3. 智能体特定的动作（需要工具/能力）
        # 收集所有相关智能体的特定动作
        all_agent_specific_actions = {}  # {action_name: (description, agents_list)}

        for current_agent_id in agent_ids:
            # 3.1 静态注册的动作（现有逻辑）
            if current_agent_id in self.agent_action_classes:
                for action_name, action_class in self.agent_action_classes[current_agent_id].items():
                    if action_class == AttributeAction and not action_name.startswith('CORP_'):
                        action_lower = action_name.lower()
                        if action_lower in AttributeAction.action_configs:
                            config = AttributeAction.action_configs[action_lower]
                            description = config.get('description', 'No description available')

                            if action_name not in all_agent_specific_actions:
                                all_agent_specific_actions[action_name] = (description, [])
                            all_agent_specific_actions[action_name][1].append(current_agent_id)

            # 3.2 基于当前能力的动态动作（新增）
            agent_abilities = self._get_agent_current_abilities(current_agent_id)
            for ability in agent_abilities:
                ability_lower = ability.lower()
                if ability_lower in AttributeAction.action_configs:
                    config = AttributeAction.action_configs[ability_lower]
                    requires_tool = config.get('requires_tool', True)

                    if requires_tool:
                        action_name = ability.upper()
                        description = config.get('description', 'No description available')

                        if action_name not in all_agent_specific_actions:
                            all_agent_specific_actions[action_name] = (description, [])
                        if current_agent_id not in all_agent_specific_actions[action_name][1]:
                            all_agent_specific_actions[action_name][1].append(current_agent_id)

        if all_agent_specific_actions:
            if not is_single_agent:
                descriptions.append("== Agent-Specific Actions (Tools Required) ==")
                for action_name, (description, agents_list) in sorted(all_agent_specific_actions.items()):
                    agents_str = " & ".join(agents_list)
                    descriptions.append(f"{action_name} <object_id>")
                    descriptions.append(f"  - {description}")
                    descriptions.append(f"  - Available to: {agents_str}")
                    descriptions.append(f"  - Example: {action_name} device_1")
                    descriptions.append("")
            else:
                descriptions.append("== Agent-Specific Actions (Tools Required) ==")
                for action_name, (description, _) in sorted(all_agent_specific_actions.items()):
                    descriptions.append(f"{action_name} <object_id>")
                    descriptions.append(f"  - {description}")
                    descriptions.append(f"  - Example: {action_name} device_1")
                    descriptions.append("")

        # 4. 合作动作（只在多智能体时显示）
        if not is_single_agent:
            descriptions.append("== Cooperative Actions ==")
            if len(agent_ids) == 2:
                # 两个智能体的具体格式
                agent_pair = ",".join(agent_ids)
                descriptions.append(f"CORP_GRAB {agent_pair} <object_id>")
                descriptions.append("  - Two agents cooperatively grab a heavy object")
                descriptions.append(f"  - Example: CORP_GRAB {agent_pair} heavy_box_1")
                descriptions.append("")

                descriptions.append(f"CORP_GOTO {agent_pair} <location_id>")
                descriptions.append("  - Two agents move together while carrying an object")
                descriptions.append(f"  - Example: CORP_GOTO {agent_pair} storage_area")
                descriptions.append("")

                descriptions.append(f"CORP_PLACE {agent_pair} <object_id> <in|on> <container_id>")
                descriptions.append("  - Two agents cooperatively place a heavy object")
                descriptions.append(f"  - Example: CORP_PLACE {agent_pair} heavy_box_1 on table_1")
                descriptions.append("")
            else:
                # 多个智能体的通用格式
                agent_list = ",".join(agent_ids)
                descriptions.append(f"CORP_GRAB {agent_list} <object_id>")
                descriptions.append("  - Multiple agents cooperatively grab a heavy object")
                descriptions.append(f"  - Example: CORP_GRAB {agent_list} heavy_box_1")
                descriptions.append("")

                descriptions.append(f"CORP_GOTO {agent_list} <location_id>")
                descriptions.append("  - Multiple agents move together while carrying an object")
                descriptions.append(f"  - Example: CORP_GOTO {agent_list} storage_area")
                descriptions.append("")

                descriptions.append(f"CORP_PLACE {agent_list} <object_id> <in|on> <container_id>")
                descriptions.append("  - Multiple agents cooperatively place a heavy object")
                descriptions.append(f"  - Example: CORP_PLACE {agent_list} heavy_box_1 on table_1")
                descriptions.append("")

        # 5. 合作属性动作（只在多智能体时显示）
        if not is_single_agent:
            corp_attribute_actions = {}  # {action_name: (description, agents_list)}

            # 收集全局合作属性动作
            for action_name, action_class in self.action_classes.items():
                if action_class.__name__ == 'CorporateAttributeAction' and action_name.startswith('CORP_'):
                    base_action = action_name[5:].lower()
                    if base_action in AttributeAction.action_configs:
                        config = AttributeAction.action_configs[base_action]
                        description = config.get('description', 'No description available')
                        corp_attribute_actions[action_name] = (description, [])

            # 收集智能体特定的合作动作
            for current_agent_id in agent_ids:
                if current_agent_id in self.agent_action_classes:
                    for action_name, action_class in self.agent_action_classes[current_agent_id].items():
                        if action_class.__name__ == 'CorporateAttributeAction' and action_name.startswith('CORP_'):
                            base_action = action_name[5:].lower()
                            if base_action in AttributeAction.action_configs:
                                config = AttributeAction.action_configs[base_action]
                                description = config.get('description', 'No description available')

                                if action_name not in corp_attribute_actions:
                                    corp_attribute_actions[action_name] = (description, [])
                                corp_attribute_actions[action_name][1].append(current_agent_id)

            if corp_attribute_actions:
                descriptions.append("== Cooperative Attribute Actions ==")
                for action_name, (description, agents_list) in sorted(corp_attribute_actions.items()):
                    if len(agent_ids) == 2:
                        # 两个智能体的具体格式
                        agent_pair = ",".join(agent_ids)
                        if agents_list:  # 如果有特定智能体的动作
                            agents_str = " & ".join(agents_list)
                            descriptions.append(f"{action_name} {agent_pair} <object_id>")
                            descriptions.append(f"  - {description} (cooperative)")
                            descriptions.append(f"  - Available to: {agents_str}")
                            descriptions.append(f"  - Example: {action_name} {agent_pair} device_1")
                        else:  # 全局动作
                            descriptions.append(f"{action_name} {agent_pair} <object_id>")
                            descriptions.append(f"  - {description} (cooperative)")
                            descriptions.append(f"  - Example: {action_name} {agent_pair} device_1")
                    else:
                        # 多个智能体的通用格式
                        agent_list = ",".join(agent_ids)
                        descriptions.append(f"{action_name} {agent_list} <object_id>")
                        descriptions.append(f"  - {description} (cooperative)")
                        descriptions.append(f"  - Example: {action_name} {agent_list} device_1")
                    descriptions.append("")

        # 6. 基于共同能力的协作动作（新增部分）
        if not is_single_agent:
            common_abilities = self._get_common_abilities(agent_ids)

            if common_abilities:
                descriptions.append("== Cooperative Ability Actions ==")

                for ability in sorted(common_abilities):
                    ability_lower = ability.lower()
                    if ability_lower in AttributeAction.action_configs:
                        config = AttributeAction.action_configs[ability_lower]
                        requires_tool = config.get('requires_tool', True)

                        # 只显示需要工具的协作能力动作
                        if requires_tool:
                            action_name = f"CORP_{ability.upper()}"
                            description = config.get('description', 'No description available')

                            if len(agent_ids) == 2:
                                # 两个智能体的具体格式
                                agent_pair = ",".join(agent_ids)
                                descriptions.append(f"{action_name} {agent_pair} <object_id>")
                                descriptions.append(f"  - {description} (cooperative)")
                                descriptions.append(f"  - Both agents have the required ability")
                                descriptions.append(f"  - Example: {action_name} {agent_pair} device_1")
                            else:
                                # 多个智能体的通用格式
                                agent_list = ",".join(agent_ids)
                                descriptions.append(f"{action_name} {agent_list} <object_id>")
                                descriptions.append(f"  - {description} (cooperative)")
                                descriptions.append(f"  - All agents have the required ability")
                                descriptions.append(f"  - Example: {action_name} {agent_list} device_1")
                            descriptions.append("")

        descriptions.append("=== END OF ACTIONS ===")

        return "\n".join(descriptions)