import csv
import os
import re
from typing import Dict, Optional, Tuple, Any, List, ClassVar, Type, Set

from ...core.enums import ActionType, ActionStatus
from .base_action import BaseAction
from .attribute_actions import AttributeAction
from ...utils.action_validators import ActionValidator

class CorporateAttributeAction(BaseAction):
    """
    合作属性动作 - 多智能体共同执行的属性动作
    
    命令格式: corp_<action_name> <agent_1,agent_2> <object_id>
    
    与AttributeAction类似，但需要明确指定的多个智能体共同执行。
    基于同样的CSV配置，但使用不同的命令前缀和验证逻辑。
    
    两种类型的动作：
    1. requires_tool=true：需要所有参与智能体拥有相应能力，动态注册
    2. requires_tool=false：不需要工具，在初始化时一次性注册
    """
    
    action_type = ActionType.ATTRIBUTE
    command_pattern = r'^corp_(\w+)\s+([\w,]+)\s+(\w+)$'  # 匹配 "corp_动词 智能体列表 物体"
    
    # 使用与AttributeAction相同的配置
    action_configs = {}
    
    # 存储不需要工具的动作列表
    no_tool_actions = set()
    
    @classmethod
    def load_from_csv(cls, csv_path=None):
        """从CSV文件加载动作配置（复用AttributeAction的配置）"""
        # 确保AttributeAction的配置已加载
        from .attribute_actions import AttributeAction
        AttributeAction.load_from_csv(csv_path)
        
        # 复制配置到本类
        cls.action_configs = AttributeAction.action_configs.copy()
        cls.no_tool_actions = AttributeAction.no_tool_actions.copy()
    
    @classmethod
    def register_scene_no_tool_actions_to_manager(cls, action_manager, scene_abilities):
        """
        根据场景abilities注册不需要工具的合作属性动作到动作管理器

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
                    # 将动作名称转为大写，并添加corp_前缀，符合ActionManager中的命名约定
                    corp_action_name = f"CORP_{ability_lower.upper()}"
                    action_manager.register_action_class(corp_action_name, cls)
                    registered_actions.append(corp_action_name)
                    registered_count += 1

        print(f"根据场景abilities注册了 {registered_count} 个不需要工具的合作动作: {', '.join(registered_actions)}")
        return action_manager

    @classmethod
    def register_task_specific_actions(cls, action_manager, task_abilities):
        """
        根据任务abilities注册特定的合作动作

        Args:
            action_manager: ActionManager实例
            task_abilities: 任务能力列表

        Returns:
            action_manager: 支持链式调用
        """
        # 确保CSV文件已加载
        cls.load_from_csv()

        registered_count = 0
        registered_actions = []

        for action_name, config in cls.action_configs.items():
            if config['requires_tool'] and action_name in task_abilities:
                corp_action_type = f"CORP_{action_name.upper()}"
                action_manager.register_action_class(corp_action_type, cls)
                registered_actions.append(corp_action_type)
                registered_count += 1

        if registered_count > 0:
            print(f"根据任务abilities注册了 {registered_count} 个需要工具的合作动作: {', '.join(registered_actions)}")

        return action_manager
    
    @classmethod
    def register_to_action_manager(cls, action_manager, scene_abilities=None):
        """
        加载CSV配置并根据场景abilities注册不需要工具的合作属性动作

        Args:
            action_manager: ActionManager实例
            scene_abilities: 场景支持的能力列表，如果为None则不注册任何动作

        Returns:
            action_manager: 支持链式调用
        """
        # 确保CSV文件已加载
        cls.load_from_csv()

        # 只有当提供了scene_abilities时才注册动作
        if scene_abilities:
            cls.register_scene_no_tool_actions_to_manager(action_manager, scene_abilities)
        else:
            print("未提供场景abilities，跳过合作属性动作注册")

        return action_manager
    
    @classmethod
    def from_command(cls, command_str: str, agent_id: str) -> Optional['BaseAction']:
        """从命令字符串创建动作实例"""
        match = re.match(cls.command_pattern, command_str, re.IGNORECASE)
        if not match:
            return None
            
        action_name, agent_list_str, target_id = match.groups()
        action_name = action_name.lower()
        
        # 检查动作是否在配置中
        if action_name not in cls.action_configs:
            return None
        
        # 解析智能体列表
        agent_ids = [aid.strip() for aid in agent_list_str.split(',') if aid.strip()]

        action_instance = cls(agent_id, target_id=target_id, params={
            "action_name": action_name,
            "agent_ids": agent_ids
        })
        return action_instance
    
    def _validate(self, agent, world_state, env_manager, agent_manager):
        """验证合作属性动作是否可执行"""
        action_name = self.params.get("action_name", "").lower()
        agent_ids = self.params.get("agent_ids", [])
        
        # 1. 发起者必须在agent_ids中
        if agent.id not in agent_ids:
            return False, "Initiator must be included in the cooperation list"
        
        # 使用通用验证工具检查物体存在性和发现状态
        result = ActionValidator.validate_object_exists_and_discovered(env_manager, self.target_id)
        if not result.is_valid:
            return False, result.message

        # 获取物体数据
        obj = env_manager.get_object_by_id(self.target_id)
        
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
        if attr_name not in states and attr_name not in props:
            return False, f"Object does not support {action_name} operation (missing {attr_name} attribute)"
        
        # 6. 检查属性值是否符合预期（先检查states，再检查properties）
        current_value = None
        if attr_name in states:
            current_value = states.get(attr_name)
        elif attr_name in props:
            current_value = props.get(attr_name)

        if current_value != expected_value:
            return False, f"Object does not need {action_name} operation ({attr_name}={current_value})"
        
        # 7. 检查所有指定的智能体是否存在
        for aid in agent_ids:
            ag = agent_manager.get_agent(aid)
            if not ag:
                return False, f"Agent {aid} does not exist"
        
        # 8. 检查所有智能体是否都靠近目标物体
        for aid in agent_ids:
            ag = agent_manager.get_agent(aid)
            is_near, reason = env_manager.is_agent_near_object(aid, self.target_id)
            if not is_near:
                return False, f"Agent {aid} must be near {self.target_id} before cooperative operation: {reason}"
        
        # 9. 对于需要工具的动作，检查所有智能体是否都有相应能力
        if requires_tool:
            for aid in agent_ids:
                ag = agent_manager.get_agent(aid)
                valid, message = ActionValidator.validate_agent_ability(ag, action_name)
                if not valid:
                    return False, f"Agent {aid} {message}"
        
        return True, "Action is valid"

    def _update_object_attribute_with_cooperation_mark(self, env_manager, obj, attr_name):
        """
        更新物体属性并添加合作标记的通用方法

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

        # 添加合作标记
        if 'cooperative_modified_attributes' not in states:
            states['cooperative_modified_attributes'] = []
        if attr_name not in states['cooperative_modified_attributes']:
            states['cooperative_modified_attributes'].append(attr_name)

        # 更新物体属性
        update_data = {'states': states}
        if update_location == 'properties':
            update_data['properties'] = props

        env_manager.update_object_attributes(self.target_id, update_data)
        return current_value, new_value

    def _execute(self, agent, world_state, env_manager, agent_manager):
        """执行合作属性动作"""
        action_name = self.params.get("action_name", "").lower()
        agent_ids = self.params.get("agent_ids", [])

        obj = env_manager.get_object_by_id(self.target_id)
        obj_name = obj.get('name', self.target_id)

        # 获取配置
        config = self.action_configs[action_name]
        attr_name = config["attribute"]

        # 执行属性更新（使用通用方法）
        current_value, new_value = self._update_object_attribute_with_cooperation_mark(
            env_manager, obj, attr_name
        )

        # 获取参与智能体名称
        agent_names = []
        for agent_id in agent_ids:
            ag = agent_manager.get_agent(agent_id)
            if ag:
                agent_names.append(ag.name)

        # 生成描述性消息
        message = f"{','.join(agent_names)} successfully cooperated to perform {action_name} operation on {obj_name}, {attr_name} changed from {current_value} to {new_value}"

        return ActionStatus.SUCCESS, message, {
            "object_id": self.target_id,
            "attribute": attr_name,
            "old_value": current_value,
            "new_value": new_value,
            "cooperating_agents": agent_ids
        }

# 在模块导入时自动加载CSV文件
# CorporateAttributeAction.load_from_csv() 