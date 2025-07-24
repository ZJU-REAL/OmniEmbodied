from typing import Dict, Optional, Tuple, Any, List, ClassVar
import re
import random
import logging

from ...core.enums import ActionType, ActionStatus, ObjectType
from .base_action import BaseAction
from ...utils.action_validators import ActionValidator
from ...utils.weight_calculator import calculate_container_weight, has_children

logger = logging.getLogger(__name__)

class GotoAction(BaseAction):
    """GOTO动作 - 移动到指定位置"""
    
    action_type = ActionType.GOTO
    command_pattern = r'^GOTO\s+(\w+)$'
    
    @classmethod
    def _parse_command(cls, match, agent_id: str):
        target_id = match.group(1)
        return cls(agent_id, None, target_id)
    
    def _validate(self, agent, world_state, env_manager, agent_manager):
        if not self.target_id:
            return False, "导航动作需要指定目标位置"
        
        # 允许目标为房间或物体
        target_room = env_manager.get_room_by_id(self.target_id)
        target_object = env_manager.get_object_by_id(self.target_id) if not target_room else None
        if not target_room and not target_object:
            return False, f"Target location does not exist: {self.target_id}"

        # 如果目标是房间，检查是否已在该房间
        if target_room and agent.location_id == self.target_id:
            return True, f"Agent is already in {target_room['name']}"
        
        # 如果目标是物体，检查是否已在同一房间且已靠近
        if target_object:
            # 物体必须已被发现
            if not target_object.get('is_discovered', False):
                return False, f"Target object not discovered: {target_object.get('name', self.target_id)}"
            # 必须在同一房间
            object_room = env_manager.get_object_room(self.target_id)
            if object_room != agent.location_id:
                room = env_manager.get_room_by_id(object_room)
                room_name = room.get('name', object_room) if room else object_room
                return False, f"Must go to {room_name} first, then approach {target_object.get('name', self.target_id)}"

        return True, "Action is valid"
    
    def _execute(self, agent, world_state, env_manager, agent_manager):
        """
        执行GOTO动作
        
        Args:
            agent: 智能体对象
            world_state: 世界状态对象
            env_manager: 环境管理器对象
            agent_manager: 智能体管理器对象
            
        Returns:
            Tuple: (执行状态, 反馈消息, 结果数据)
        """
        logger.debug(f"执行GOTO动作 - 智能体: {agent.id}, 目标: {self.target_id}")
        
        # 判断目标是房间还是物体
        target_room = env_manager.get_room_by_id(self.target_id)
        target_object = env_manager.get_object_by_id(self.target_id) if not target_room else None
        
        # 记录执行前的位置
        old_location_id = agent.location_id
        old_near_objects = set(agent.near_objects) if hasattr(agent, 'near_objects') else set()

        logger.debug(f"GOTO execution before - location: {old_location_id}, nearby objects count: {len(old_near_objects)}")

        if target_room:
            # goto房间，调用move_agent
            logger.debug(f"Target is room: {self.target_id}")
            success = agent_manager.move_agent(agent.id, self.target_id)
            if success:
                room_name = target_room.get('name', self.target_id)
                # 确保near_objects在移动后被更新
                if hasattr(agent, 'near_objects'):
                    agent.update_near_objects(env_manager=env_manager)
                    logger.debug(f"GOTO success - new location: {self.target_id}, nearby objects count: {len(agent.near_objects)}")

                return ActionStatus.SUCCESS, f"{agent.name} successfully moved to {room_name}", {"new_location_id": self.target_id}
            else:
                logger.warning(f"GOTO room failed: {self.target_id}")
                return ActionStatus.FAILURE, f"Movement failed", None
        elif target_object:
            # goto物体，不改变location_id，只更新near_objects
            logger.debug(f"目标是物体: {self.target_id}")
            
            # 检查物体是否已发现
            if not target_object.get('is_discovered', False):
                logger.warning(f"Target object not discovered: {self.target_id}")
                return ActionStatus.FAILURE, f"Target object not discovered: {target_object.get('name', self.target_id)}", None

            # 检查物体是否在同一房间
            object_room = env_manager.get_object_room(self.target_id)
            if object_room != agent.location_id:
                logger.warning(f"Object not in current room - object: {self.target_id}, object room: {object_room}, agent room: {agent.location_id}")
                return ActionStatus.FAILURE, f"Target object not in current room", None
                
            # 更新near_objects集合
            agent.update_near_objects(self.target_id, env_manager)
            
            # 检查更新后的near_objects是否包含目标物体
            if self.target_id not in agent.near_objects:
                logger.warning(f"Target object not in near_objects after update - object: {self.target_id}, near_objects: {agent.near_objects}")
                # 强制添加目标物体到near_objects
                agent.near_objects.add(self.target_id)
                logger.debug(f"Force add target object to near_objects: {self.target_id}")

            obj_name = target_object.get('name', self.target_id)
            room_id = agent.location_id
            room = env_manager.get_room_by_id(room_id)
            room_name = room.get('name', room_id) if room else room_id

            logger.debug(f"GOTO object success - object: {obj_name}, room: {room_name}, nearby objects count: {len(agent.near_objects)}")

            # 确保agent状态被保存
            agent_manager.update_agent(agent.id, agent.to_dict())

            return ActionStatus.SUCCESS, f"{agent.name} approached {obj_name} (in {room_name})", {"near_object_id": self.target_id}
        else:
            logger.error(f"Target location does not exist: {self.target_id}")
            return ActionStatus.FAILURE, f"Target location does not exist: {self.target_id}", None


class GrabAction(BaseAction):
    """GRAB动作 - 抓取物体"""
    
    action_type = ActionType.GRAB
    command_pattern = r'^GRAB\s+(\w+)$'
    
    @classmethod
    def _parse_command(cls, match, agent_id: str):
        target_id = match.group(1)
        return cls(agent_id, None, target_id)
    
    def _validate(self, agent, world_state, env_manager, agent_manager):
        if not self.target_id:
            return False, "Grab action requires a target object"

        # 使用新的验证系统进行基本验证
        result = ActionValidator.validate_grab_action(env_manager, agent, self.target_id)
        if not result:
            return False, result.message

        # 检查该物体是否已被其他agent持有
        for other_agent in agent_manager.get_all_agents().values():
            if other_agent.id != agent.id and self.target_id in other_agent.inventory:
                return False, f"Object is already held by {other_agent.name}, cannot grab again"

        return True, "Action is valid"
    
    def _execute(self, agent, world_state, env_manager, agent_manager):
        """
        执行GRAB动作
        
        Args:
            agent: 智能体对象
            world_state: 世界状态对象
            env_manager: 环境管理器对象
            agent_manager: 智能体管理器对象
            
        Returns:
            Tuple: (执行状态, 反馈消息, 结果数据)
        """
        logger.debug(f"Executing GRAB action - agent: {agent.id}, target: {self.target_id}")

        # 记录执行前的状态
        inventory_before = set(agent.inventory)
        near_objects_before = set(agent.near_objects) if hasattr(agent, 'near_objects') else set()

        logger.debug(f"GRAB before execution - inventory: {inventory_before}, nearby objects count: {len(near_objects_before)}")

        # 获取物体
        obj = env_manager.get_object_by_id(self.target_id)
        if not obj:
            logger.warning(f"Object does not exist: {self.target_id}")
            return ActionStatus.FAILURE, f"Object does not exist: {self.target_id}", None

        obj_name = obj.get('name', self.target_id)

        # 检查物体是否已发现
        if not obj.get('is_discovered', False):
            logger.warning(f"Object not discovered: {self.target_id}")
            return ActionStatus.FAILURE, f"Object not discovered: {obj_name}", None

        # 检查物体是否在近邻列表中
        if self.target_id not in agent.near_objects:
            logger.warning(f"Object not in nearby list - object: {self.target_id}, nearby: {agent.near_objects}")
            return ActionStatus.FAILURE, f"Agent must approach {obj_name} before grabbing", None
        
        # 记录抓取前的容器id
        container_id = None
        if 'location_id' in obj:
            from ...utils.parse_location import parse_location_id
            _, container_id = parse_location_id(obj['location_id'])
            logger.debug(f"Object current container: {container_id}")

        # 检查物体是否可以被智能体承载
        properties = obj.get('properties', {})

        # Check if cooperative mode
        is_cooperative = hasattr(agent, 'corporate_mode_object_id') and agent.corporate_mode_object_id is not None

        if is_cooperative:
            # Cooperative mode: use original weight
            effective_properties = properties
            logger.info(f"Cooperative grab: {obj_name}, skip weight check")
        else:
            # Single mode: calculate total weight if has children
            if has_children(env_manager, self.target_id):
                total_weight = calculate_container_weight(env_manager, self.target_id)
                effective_properties = properties.copy()
                effective_properties['weight'] = total_weight
                logger.info(f"Grab container {obj_name}: total weight {total_weight}kg (including children)")
            else:
                effective_properties = properties

        # Check carrying capacity
        can_carry, reason = agent.can_carry(effective_properties)
        if not can_carry:
            logger.warning(f"Cannot carry object: {reason}")
            return ActionStatus.FAILURE, reason, None

        # Add object to agent inventory
        success, message = agent.grab_object(self.target_id, effective_properties)
        if not success:
            logger.warning(f"Grab failed: {message}")
            return ActionStatus.FAILURE, message, None

        logger.debug(f"Grab successful - object: {obj_name}")
        
        # 检查物体是否赋予智能体特定能力
        abilities = properties.get('provides_abilities', [])
        if abilities:
            if isinstance(abilities, str):
                abilities = [abilities]  # 如果是单个字符串，转为列表
            
            for ability in abilities:
                logger.debug(f"Object provides ability: {ability}")
                agent.add_ability_from_object(ability, self.target_id)

        # 更新智能体数据
        agent_manager.update_agent(agent.id, agent.to_dict())

        # 更新物体位置
        env_success = env_manager.move_object(self.target_id, agent.id)
        if not env_success:
            # 如果环境更新失败，要回滚智能体状态
            logger.error(f"Failed to update object position - object: {self.target_id}")
            success, _ = agent.drop_object(self.target_id, properties)
            # 同时移除已授予的能力
            abilities = properties.get('provides_abilities', [])
            if abilities:
                if isinstance(abilities, str):
                    abilities = [abilities]
                for ability in abilities:
                    agent.remove_ability_from_object(ability, self.target_id)
            agent_manager.update_agent(agent.id, agent.to_dict())
            return ActionStatus.FAILURE, f"Failed to update object position", None

        # 抓取成功后，near_objects包含原容器
        if container_id:
            logger.debug(f"Update nearby list, include original container: {container_id}")
            agent.update_near_objects(container_id, env_manager)
        else:
            agent.update_near_objects()

        # 记录执行后的状态
        inventory_after = set(agent.inventory)
        near_objects_after = set(agent.near_objects) if hasattr(agent, 'near_objects') else set()

        logger.debug(f"GRAB after execution - inventory: {inventory_after}, nearby objects count: {len(near_objects_after)}")
        logger.debug(f"Inventory changes: added {inventory_after - inventory_before}, removed {inventory_before - inventory_after}")
        logger.debug(f"Nearby changes: added {near_objects_after - near_objects_before}, removed {near_objects_before - near_objects_after}")
        
        return ActionStatus.SUCCESS, f"{agent.name} successfully grabbed {obj_name}", {
            "object_id": self.target_id
        }


class PlaceAction(BaseAction):
    """PLACE动作 - 放置物体"""
    
    action_type = ActionType.PLACE
    command_pattern = r'^PLACE\s+(\w+)(?:\s+(on|in)\s+(\w+))?$'
    
    @classmethod
    def _parse_command(cls, match, agent_id: str):
        obj_id, rel, location_id = match.groups()
        params = {}
        if rel and location_id:
            params['relation'] = rel
            params['location_id'] = location_id
        return cls(agent_id, None, obj_id, params)
    
    def _validate(self, agent, world_state, env_manager, agent_manager):
        if not self.target_id:
            return False, "PLACE action requires target object"

        # 检查是否提供了必要的relation和location_id参数
        relation = self.params.get('relation')
        location_id = self.params.get('location_id')
        if not relation or not location_id:
            return False, "PLACE action must specify placement method (on/in) and location, format: PLACE <object_id> <on|in> <location_id>"

        # 使用新的验证系统进行验证
        result = ActionValidator.validate_place_action(env_manager, agent, self.target_id, location_id, relation)
        if not result:
            return False, result.message

        # 检查智能体是否与目标位置在同一房间（额外的位置检查）
        if location_id != agent.location_id and location_id not in world_state.graph.room_ids:
            location_room = env_manager.get_object_room(location_id)
            if location_room != agent.location_id:
                location = env_manager.get_object_by_id(location_id)
                location_name = location.get('name', location_id) if location else location_id
                room = env_manager.get_room_by_id(location_room)
                room_name = room.get('name', location_room) if room else location_room
                return False, f"Agent must go to {room_name} first to place object on {location_name}"

        return True, "Action is valid"
    
    def _execute(self, agent, world_state, env_manager, agent_manager):
        # 获取物体
        obj = env_manager.get_object_by_id(self.target_id)
        if not obj:
            return ActionStatus.FAILURE, f"Object does not exist: {self.target_id}", None
        
        obj_name = obj.get('name', self.target_id)
        obj_properties = obj.get('properties', {})
        
        # 确定放置位置
        relation = self.params.get('relation')
        location_id = self.params.get('location_id')
        
        # 添加关系前缀到位置ID
        location_id = f"{relation}:{location_id}"
        
        # 获取位置名称
        location_name = None
        if location_id.split(':', 1)[1] == agent.location_id:
            room = env_manager.get_room_by_id(agent.location_id)
            location_name = room.get('name', agent.location_id) if room else agent.location_id
        else:
            location = env_manager.get_object_by_id(location_id.split(':', 1)[1])
            location_name = location.get('name', location_id.split(':', 1)[1]) if location else location_id.split(':', 1)[1]
        
        # 从智能体库存移除物体 - 计算正确的重量
        is_cooperative = hasattr(agent, 'corporate_mode_object_id') and agent.corporate_mode_object_id is not None

        if is_cooperative:
            effective_properties = obj_properties
        else:
            if has_children(env_manager, self.target_id):
                total_weight = calculate_container_weight(env_manager, self.target_id)
                effective_properties = obj_properties.copy()
                effective_properties['weight'] = total_weight
            else:
                effective_properties = obj_properties

        success, message = agent.drop_object(self.target_id, effective_properties)
        if not success:
            return ActionStatus.FAILURE, message, None
        
        # 物体放置成功，再移除能力
        abilities = obj_properties.get('provides_abilities', [])
        if abilities:
            if isinstance(abilities, str):
                abilities = [abilities]  # 如果是单个字符串，转为列表
            
            for ability in abilities:
                agent.remove_ability_from_object(ability, self.target_id)
        
        # 更新智能体数据
        agent_manager.update_agent(agent.id, agent.to_dict())
        
        # 将物体移动到新位置
        env_success = env_manager.move_object(self.target_id, location_id)
        if not env_success:
            # 如果环境更新失败，要回滚智能体状态
            success, _ = agent.grab_object(self.target_id, obj_properties)
            # 同时恢复能力
            if abilities:
                for ability in abilities:
                    agent.add_ability_from_object(ability, self.target_id)
            agent_manager.update_agent(agent.id, agent.to_dict())
            return ActionStatus.FAILURE, f"Cannot place {obj_name} on {location_name}", None

        # 放下后，near_objects包含刚刚放下的物体及其父/子物体
        agent.update_near_objects(self.target_id, env_manager)

        return ActionStatus.SUCCESS, f"{agent.name} placed {obj_name} on {location_name}", {
            "object_id": self.target_id,
            "location_id": location_id
        }


class LookAction(BaseAction):
    """LOOK动作 - 观察环境或物体"""
    
    action_type = ActionType.LOOK
    command_pattern = r'^LOOK(?:\s+(\w+))?$'
    
    @classmethod
    def _parse_command(cls, match, agent_id: str):
        target = match.group(1)
        params = {}
        if target and target.upper() == "AROUND":
            params['scope'] = "room"
            target = None
        return cls(agent_id, None, target, params)
    
    def _validate(self, agent, world_state, env_manager, agent_manager):
        # 如果指定了目标物体，使用验证系统检查
        if self.target_id:
            result = ActionValidator.validate_basic_object_interaction(env_manager, agent, self.target_id)
            if not result:
                return False, result.message

        return True, "Action is valid"
    
    def _execute(self, agent, world_state, env_manager, agent_manager):
        # 查看范围
        scope = self.params.get('scope', 'target')
        
        if scope == 'room':
            # 查看整个房间
            room_id = agent.location_id
            room = env_manager.get_room_by_id(room_id)
            if not room:
                return ActionStatus.FAILURE, f"Current location is not a valid room", None
            
            room_name = room.get('name', room_id)
            objects = env_manager.get_objects_in_room(room_id)
            
            # 提取已发现的物体信息
            visible_objects = []
            for obj in objects:
                if obj.get('is_discovered', False):
                    visible_objects.append({
                        "id": obj.get('id'),
                        "name": obj.get('name'),
                        "type": obj.get('type'),
                        "states": obj.get('states', {})
                    })
            
            return ActionStatus.SUCCESS, f"{agent.name} looked around {room_name}", {
                "room_id": room_id,
                "room_name": room_name,
                "visible_objects": visible_objects
            }
            
        elif self.target_id:
            # 查看特定物体
            obj = env_manager.get_object_by_id(self.target_id)
            if not obj:
                return ActionStatus.FAILURE, f"Object does not exist: {self.target_id}", None
            
            obj_name = obj.get('name', self.target_id)
            
            # 检查物体是否为容器，如果是，列出其中的已发现物体
            contained_objects = []
            if obj.get('properties', {}).get('is_container', False) and \
               obj.get('states', {}).get('is_open', False):
                # 查找容器中的物体
                for obj_id, edges in world_state.graph.edges.items():
                    if obj_id == self.target_id:
                        for contained_id in edges:
                            contained_obj = env_manager.get_object_by_id(contained_id)
                            if contained_obj and contained_obj.get('is_discovered', False):
                                contained_objects.append({
                                    "id": contained_obj.get('id'),
                                    "name": contained_obj.get('name'),
                                    "type": contained_obj.get('type')
                                })
            
            return ActionStatus.SUCCESS, f"{agent.name} looked at {obj_name}", {
                "object_id": self.target_id,
                "object_name": obj_name,
                "object_type": obj.get('type'),
                "object_states": obj.get('states', {}),
                "contained_objects": contained_objects
            }
        
        else:
            # 如果没有指定目标，默认环顾四周
            self.params['scope'] = 'room'
            return self._execute(agent, world_state, env_manager, agent_manager)



class ExploreAction(BaseAction):
    """EXPLORE动作 - 探索当前房间"""
    
    action_type = ActionType.EXPLORE
    command_pattern = r'^EXPLORE(?:\s+(\w+))?$'
    
    @classmethod
    def _parse_command(cls, match, agent_id: str):
        exploration_level = match.group(1)
        params = {}
        # 检查是否指定了房间或探索级别
        if exploration_level:
            if exploration_level.upper() == "THOROUGH":
                params['exploration_level'] = "thorough"
            else:
                # 假设是房间ID
                params['room_id'] = exploration_level
                params['exploration_level'] = "thorough"
        # else: 不要设置 exploration_level，留给_execute读取配置
        return cls(agent_id, None, None, params)
    
    def _validate(self, agent, world_state, env_manager, agent_manager):
        # EXPLORE只能探索当前房间
        room_id = self.params.get('room_id')
        if room_id and room_id != agent.location_id:
            room = env_manager.get_room_by_id(room_id)
            room_name = room.get('name', room_id) if room else room_id
            return False, f"Agent must go to {room_name} before exploring that room"

        return True, "Action is valid"
    
    def _execute(self, agent, world_state, env_manager, agent_manager):
        # 获取要探索的房间（默认为当前房间）
        room_id = self.params.get('room_id', agent.location_id)
        room = env_manager.get_room_by_id(room_id)
        if not room:
            return ActionStatus.FAILURE, f"Specified location is not a valid room", None
        
        room_name = room.get('name', room_id)
        
        # 获取房间中所有未发现的物体，排除房间节点
        objects = env_manager.get_objects_in_room(room_id)
        undiscovered_objects = []
        for obj in objects:
            # 确保物体不是房间，也不是agent
            obj_id = obj.get('id')
            obj_type = obj.get('type', '').upper()
            if not obj.get('is_discovered', False) and obj_id not in world_state.graph.room_ids and obj_type != 'AGENT':
                undiscovered_objects.append(obj)
        
        # 决定发现多少物体
        exploration_level = self.params.get('exploration_level')
        if not exploration_level:
            sim_config = getattr(env_manager, 'sim_config', {}) or getattr(world_state, 'sim_config', {}) or {}
            exploration_level = sim_config.get('explore_mode', 'thorough')  # 默认改为thorough，发现所有物品
        
        logger.debug(f"EXPLORE - exploration level: {exploration_level}, undiscovered objects count: {len(undiscovered_objects)}")
        
        if exploration_level == 'thorough':
            # 彻底探索 - 发现所有物体
            discovery_percentage = 1.0
            # 确保是所有物体
            discovery_count = len(undiscovered_objects)
            to_discover = undiscovered_objects
        else:
            # 普通探索 - 随机发现部分物体
            discovery_percentage = random.uniform(0.5, 0.8)
            # 计算实际发现的数量
            discovery_count = int(len(undiscovered_objects) * discovery_percentage)
            # 随机选择要发现的物体
            to_discover = random.sample(undiscovered_objects, min(discovery_count, len(undiscovered_objects)))
        
        logger.debug(f"EXPLORE - objects to be discovered: {len(to_discover)}")

        # 标记物体为已发现并收集物体信息（包括所属关系）
        discovered_objects = []
        for obj in to_discover:
            obj_id = obj.get('id')
            # 确保物体被标记为已发现
            env_manager.update_object_state(obj_id, {"is_discovered": True})

            # 查找物体的所属关系（在哪个物体上/中）
            container_info = ""
            for potential_container_id, edges in world_state.graph.edges.items():
                if obj_id in edges and potential_container_id != room_id and potential_container_id not in world_state.graph.room_ids:
                    container = world_state.graph.get_node(potential_container_id)
                    if container and container.get('is_discovered', False):  # 只显示已发现的容器
                        relation_type = edges[obj_id][0].get('type', 'at') if edges[obj_id] else 'at'
                        relation_text = 'on' if relation_type == 'on' else 'in' if relation_type == 'in' else 'at'
                        container_info = f"({relation_text} {container.get('name', potential_container_id)})"
                        break
            
            discovered_objects.append({
                "id": obj_id,
                "name": obj.get('name'),
                "type": obj.get('type'),
                "container_info": container_info
            })
        
        # 确保近邻物体集合已初始化
        if not hasattr(agent, 'near_objects') or agent.near_objects is None:
            agent.near_objects = set()
        elif not isinstance(agent.near_objects, set):
            agent.near_objects = set(agent.near_objects if isinstance(agent.near_objects, (list, tuple)) else [])

        # 探索只是发现物体，不应该自动将所有物体添加到near_objects
        # 只将当前房间添加到near_objects，物体需要通过goto靠近才能交互
        agent.near_objects.add(room_id)
        
        # 确保near_objects仍然是集合类型
        if not isinstance(agent.near_objects, set):
            agent.near_objects = set(agent.near_objects)
            
        # 更新智能体数据确保near_objects被保存
        agent_manager.update_agent(agent.id, agent.to_dict())
        
        # 根据发现数量决定状态
        if not discovered_objects:
            if discovery_count == 0:
                return ActionStatus.SUCCESS, f"{agent.name} explored {room_name} but found no new objects", {
                    "room_id": room_id,
                    "discovery_count": 0
                }
            else:
                return ActionStatus.PARTIAL, f"{agent.name} explored {room_name} but temporarily found no new objects", {
                    "room_id": room_id,
                    "discovery_count": 0
                }
        elif discovery_count < len(undiscovered_objects) and exploration_level != 'thorough':
            return ActionStatus.PARTIAL, f"{agent.name} discovered {len(discovered_objects)} new objects in {room_name}", {
                "room_id": room_id,
                "discovered_objects": discovered_objects,
                "discovery_count": len(discovered_objects)
            }
        else:
            return ActionStatus.SUCCESS, f"{agent.name} thoroughly explored {room_name} and discovered {len(discovered_objects)} new objects", {
                "room_id": room_id,
                "discovered_objects": discovered_objects,
                "discovery_count": len(discovered_objects),
                "is_complete": True
            }