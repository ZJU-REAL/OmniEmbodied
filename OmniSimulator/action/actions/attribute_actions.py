import csv
import os
from typing import Dict, Optional, Tuple, Any, List, ClassVar, Type
import re

from ...core.enums import ActionType, ActionStatus
from .base_action import BaseAction
from ...utils.action_validators import ActionValidator

class AttributeAction(BaseAction):
    """
    基于属性的动作 - 从CSV文件自动导入的动作定义
    
    CSV格式: action_name,attribute,value,requires_tool
    
    当物体的属性名=属性值时，可以执行Action操作，且会把属性值取反
    
    两种类型的动作：
    1. requires_tool=true：需要智能体拥有相应能力，动态注册
    2. requires_tool=false：不需要工具，在初始化时一次性注册
    """
    
    action_type = ActionType.ATTRIBUTE
    command_pattern = r'^(\w+)\s+(\w+)$'  # 匹配 "动词 物体"
    
    # 存储从CSV导入的动作配置
    # 格式: {action_name: {"attribute": attr_name, "value": bool_value, "requires_tool": bool_value}}
    action_configs = {}
    
    # 存储不需要工具的动作列表
    no_tool_actions = set()
    
    @classmethod
    def load_from_csv(cls, csv_path=None):
        """从CSV文件加载动作配置"""
        # 如果已经加载过配置，避免重复加载
        if cls.action_configs:
            return
            
        # 如果未指定路径，使用默认路径（项目根目录下的data/attribute_actions.csv）
        if csv_path is None:
            # 从OmniSimulator/action/actions向上三级到项目根目录，然后到data目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            csv_path = os.path.join(project_root, 'data', 'attribute_actions.csv')
            
        if not os.path.exists(csv_path):
            print(f"Warning: Configuration file does not exist {csv_path}")
            return
            
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                # 跳过标题行
                try:
                    header = next(reader)
                    if not (header[0].lower() == 'action_name' and 
                            header[1].lower() == 'attribute' and 
                            header[2].lower() == 'value'):
                        # 如果不是标题行，重置文件指针
                        file.seek(0)
                except StopIteration:
                    # 文件为空
                    return
                
                for row in reader:
                    if len(row) >= 4:  # 确保至少有4列
                        action_name = row[0].strip().lower()
                        attr_name = row[1].strip()
                        # 将字符串转换为布尔值
                        attr_value = row[2].strip().lower() == 'true'
                        # 读取第四列：是否需要工具
                        requires_tool = row[3].strip().lower() == 'true'
                        # 读取第五列：描述（如果存在）
                        description = row[4].strip().strip('"') if len(row) >= 5 else "No description available"

                        cls.action_configs[action_name] = {
                            "attribute": attr_name,
                            "value": attr_value,
                            "requires_tool": requires_tool,
                            "description": description
                        }

                        # 如果不需要工具，添加到no_tool_actions集合
                        if not requires_tool:
                            cls.no_tool_actions.add(action_name)
                    else:
                        print(f"Warning: Ignoring invalid row: {row}")
        except Exception as e:
            print(f"Error loading CSV file: {e}")
    
    @classmethod
    def register_scene_no_tool_actions_to_manager(cls, action_manager, scene_abilities):
        """
        根据场景abilities注册不需要工具的动作到动作管理器

        Args:
            action_manager: ActionManager实例
            scene_abilities: 场景支持的能力列表

        Returns:
            action_manager: 支持链式调用
        """
        # 确保CSV文件已加载
        cls.load_from_csv()

        registered_count = 0
        registered_actions = []

        for ability in scene_abilities:
            ability_lower = ability.lower()

            # 检查是否在配置中且不需要工具
            if ability_lower in cls.action_configs:
                config = cls.action_configs[ability_lower]
                requires_tool = config.get('requires_tool', True)

                if not requires_tool:
                    # 将动作名称转为大写，符合ActionManager中的命名约定
                    action_manager.register_action_class(ability_lower.upper(), cls)
                    registered_actions.append(ability_lower.upper())
                    registered_count += 1

        print(f"根据场景abilities注册了 {registered_count} 个不需要工具的动作: {', '.join(registered_actions)}")
        return action_manager

    @classmethod
    def register_task_specific_actions(cls, action_manager, task_abilities: List[str]):
        """
        根据任务的abilities动态注册需要工具的动作

        Args:
            action_manager: ActionManager实例
            task_abilities: 任务中指定的能力列表
        """
        # 确保CSV文件已加载
        cls.load_from_csv()

        registered_count = 0
        registered_actions = []

        for action_name, config in cls.action_configs.items():
            if config['requires_tool'] and action_name in task_abilities:
                action_type = action_name.upper()
                action_manager.register_action_class(action_type, cls)
                registered_actions.append(action_type)

                # 同时注册合作版本
                corp_action_type = f"CORP_{action_type}"
                action_manager.register_action_class(corp_action_type, cls)
                registered_actions.append(corp_action_type)

                registered_count += 1

        if registered_count > 0:
            print(f"根据任务abilities注册了 {registered_count} 个需要工具的动作: {', '.join(registered_actions)}")

        return action_manager

    @classmethod
    def get_available_actions_for_abilities(cls, abilities: List[str]) -> List[str]:
        """
        获取指定能力列表对应的可用动作

        Args:
            abilities: 能力列表

        Returns:
            List[str]: 可用的动作名称列表
        """
        cls.load_from_csv()

        available_actions = []
        for action_name, config in cls.action_configs.items():
            if action_name in abilities:
                available_actions.append(action_name)

        return available_actions

    @classmethod
    def from_command(cls, command_str: str, agent_id: str) -> Optional['BaseAction']:
        """从命令字符串创建动作实例"""
        match = re.match(cls.command_pattern, command_str, re.IGNORECASE)
        if not match:
            return None
            
        action_name, target_id = match.groups()
        action_name = action_name.lower()
        
        # 检查动作是否在配置中
        if action_name not in cls.action_configs:
            return None
            
        return cls(agent_id, None, target_id, {"action_name": action_name})
    
    def _validate(self, agent, world_state, env_manager, agent_manager):
        """验证动作是否可执行"""
        action_name = self.params.get("action_name", "").lower()
        
        # 1. 检查物体是否存在
        obj = env_manager.get_object_by_id(self.target_id)
        if not obj:
            return False, f"Object does not exist: {self.target_id}"

        # 2. 检查物体是否已被发现
        if not obj.get('is_discovered', False):
            return False, f"Object not discovered: {obj.get('name', self.target_id)}"
        
        # 3. 检查智能体是否与物体在同一房间/靠近物体
        is_near, reason = env_manager.is_agent_near_object(agent.id, self.target_id)
        if not is_near:
            return False, reason
        
        # 4. 检查动作配置
        if action_name not in self.action_configs:
            return False, f"Unknown action: {action_name}"
            
        config = self.action_configs[action_name]
        attr_name = config["attribute"]
        expected_value = config["value"]
        requires_tool = config.get("requires_tool", True)  # 默认需要工具
        
        # 5. 检查物体是否有指定属性（先检查states，再检查properties）
        states = obj.get('states', {})
        props = obj.get('properties', {})

        current_value = None
        if attr_name in states:
            current_value = states.get(attr_name)
        elif attr_name in props:
            current_value = props.get(attr_name)
        else:
            return False, f"Object does not support {action_name} operation (missing {attr_name} attribute)"

        # 6. 检查属性值是否符合预期
        if current_value != expected_value:
            return False, f"Object does not need {action_name} operation ({attr_name}={current_value})"
        
        # 7. 只对需要工具的动作检查智能体能力
        if requires_tool:
            valid, message = ActionValidator.validate_agent_ability(agent, action_name)
            if not valid:
                return False, message
        
        return True, "Action is valid"

    def _update_object_attribute_and_clear_cooperation_mark(self, env_manager, obj, attr_name):
        """
        更新物体属性并清除合作标记的通用方法

        Args:
            env_manager: 环境管理器
            obj: 物体对象
            attr_name: 属性名称

        Returns:
            Tuple[Any, Any]: (原值, 新值)
        """
        states = obj.get('states', {}).copy()
        props = obj.get('properties', {}).copy()

        # 查找属性并获取当前值
        current_value = None
        if attr_name in states:
            current_value = states[attr_name]
            # 对于布尔值执行取反操作
            new_value = not current_value if isinstance(current_value, bool) else current_value
            states[attr_name] = new_value
            update_location = 'states'
        elif attr_name in props:
            current_value = props[attr_name]
            # 对于布尔值执行取反操作
            new_value = not current_value if isinstance(current_value, bool) else current_value
            props[attr_name] = new_value
            update_location = 'properties'
        else:
            raise ValueError(f"Attribute {attr_name} not found in object {self.target_id}")

        # 从合作标记列表中移除该属性（如果存在）
        if 'cooperative_modified_attributes' in states and attr_name in states['cooperative_modified_attributes']:
            states['cooperative_modified_attributes'].remove(attr_name)

        # 更新物体属性
        update_data = {'states': states}
        if update_location == 'properties':
            update_data['properties'] = props

        env_manager.update_object_attributes(self.target_id, update_data)
        return current_value, new_value

    def _execute(self, agent, world_state, env_manager, agent_manager):
        """执行动作"""
        action_name = self.params.get("action_name", "").lower()
        obj = env_manager.get_object_by_id(self.target_id)
        obj_name = obj.get('name', self.target_id)
        
        # 获取配置
        config = self.action_configs[action_name]
        attr_name = config["attribute"]

        # 执行属性更新（使用通用方法）
        current_value, new_value = self._update_object_attribute_and_clear_cooperation_mark(
            env_manager, obj, attr_name
        )
        
        # 生成描述性消息
        # if action_name == "repair":
        #     message = f"{agent.name} successfully repaired {obj_name}"
        # elif action_name == "clean":
        #     message = f"{agent.name} successfully cleaned {obj_name}"
        # else:
        message = f"{agent.name} successfully performed {action_name} on {obj_name}, {attr_name} changed from {current_value} to {new_value}"
        
        return ActionStatus.SUCCESS, message, {
            "object_id": self.target_id,
            "attribute": attr_name,
            "old_value": current_value,
            "new_value": new_value
        }

# 在模块导入时自动加载CSV文件
# AttributeAction.load_from_csv() 