"""
可视化数据接口模块
提供模拟器状态的可视化数据格式化和获取功能
"""

from typing import Dict, List, Optional, Any
import time
from ..core.state import WorldState


class VisualizationDataProvider:
    """可视化数据提供器"""

    def __init__(self, world_state: WorldState, config: Optional[Dict] = None, engine=None):
        """
        初始化可视化数据提供器

        Args:
            world_state: 世界状态对象
            config: 可视化配置
            engine: 模拟引擎实例，用于获取任务信息
        """
        self.world_state = world_state
        self.config = config or {}
        self.engine = engine
        
    def get_complete_visualization_data(self) -> Dict[str, Any]:
        """
        获取完整的可视化数据

        Returns:
            Dict: 包含所有可视化信息的字典
        """
        current_time = time.time()

        data = {
            'timestamp': current_time,
            'rooms': self._get_rooms_data(),
            'objects': self._get_objects_data(),
            'agents': self._get_agents_data(),
            'relationships': self._get_relationships_data(),
            'metadata': self._get_metadata(),
            'supported_actions': self._get_supported_actions(),
            'detailed_tasks': self._get_detailed_tasks()
        }

        return data
    
    def _get_rooms_data(self) -> List[Dict[str, Any]]:
        """获取房间数据"""
        rooms = []
        
        for room_id in self.world_state.graph.room_ids:
            room_node = self.world_state.graph.get_node(room_id)
            if room_node:
                room_data = {
                    'id': room_id,
                    'name': room_node.get('name', room_id),
                    'type': room_node.get('properties', {}).get('type', 'unknown'),
                    'properties': room_node.get('properties', {}),
                    'connected_rooms': self._get_connected_rooms(room_id),
                    'objects_count': len(self._get_objects_in_room(room_id)),
                    'agents_count': len(self._get_agents_in_room(room_id))
                }
                rooms.append(room_data)
        
        return rooms
    
    def _get_objects_data(self) -> List[Dict[str, Any]]:
        """获取物体数据，使用层次结构而非精确坐标"""
        objects = []

        # 构建物体层级关系
        object_hierarchy = self._build_object_hierarchy()

        for node_id, node_data in self.world_state.graph.nodes.items():
            if node_id not in self.world_state.graph.room_ids:  # 不是房间
                location_info = self._get_object_location_info(node_id)

                obj_data = {
                    'id': node_id,
                    'name': node_data.get('name', node_id),
                    'type': node_data.get('type', 'UNKNOWN'),
                    'location': location_info,
                    'properties': node_data.get('properties', {}),
                    'states': node_data.get('states', {}),
                    'is_discovered': node_data.get('is_discovered', False),
                    # 移除精确坐标，改为层次信息
                    'layout_info': self._get_layout_info(node_id, location_info),
                    'container_info': self._get_container_info(node_id, location_info),
                    'contained_objects': object_hierarchy.get(node_id, []),
                    # 添加工具标识
                    'is_tool': self._is_tool_object(node_data),
                    # 添加关系类型用于边框颜色
                    'relation_type': location_info.get('type', 'unknown')
                }

                # 添加能力信息
                if 'provides_abilities' in node_data.get('properties', {}):
                    obj_data['provides_abilities'] = node_data['properties']['provides_abilities']

                # 添加尺寸信息用于可视化
                size = node_data.get('properties', {}).get('size', [0.1, 0.1, 0.1])
                obj_data['visual_size'] = {
                    'width': max(size[0] * 10, 8),  # 转换为像素，最小8px
                    'height': max(size[1] * 10, 8),
                    'depth': max(size[2] * 10, 8)
                }

                objects.append(obj_data)

        return objects
    
    def _get_agents_data(self) -> List[Dict[str, Any]]:
        """获取智能体数据，使用布局信息而非精确坐标"""
        agents = []

        for agent_id, agent_data in self.world_state.agents.items():
            location_id = agent_data.get('location_id', '')

            agent_info = {
                'id': agent_id,
                'name': agent_data.get('name', agent_id),
                'location': location_id,
                'layout_info': self._get_agent_layout_info(agent_id, location_id),
                'status': agent_data.get('status', 'idle'),
                'inventory': agent_data.get('inventory', []),
                'capabilities': agent_data.get('capabilities', []),
                'properties': {
                    'max_grasp_limit': agent_data.get('max_grasp_limit', 1),
                    'max_weight': agent_data.get('max_weight', 10.0),
                    'max_size': agent_data.get('max_size', [0.5, 0.5, 0.5])
                },
                'current_action': agent_data.get('current_action', None)
            }
            agents.append(agent_info)

        return agents
    
    def _get_relationships_data(self) -> List[Dict[str, Any]]:
        """获取关系数据"""
        relationships = []
        
        if not self.config.get('display', {}).get('show_relationships', True):
            return relationships
        
        for from_id, edges in self.world_state.graph.edges.items():
            for to_id, relations in edges.items():
                for relation in relations:
                    rel_data = {
                        'from': from_id,
                        'to': to_id,
                        'type': relation.get('type', 'unknown'),
                        'properties': relation
                    }
                    relationships.append(rel_data)
        
        return relationships
    
    def _get_metadata(self) -> Dict[str, Any]:
        """获取元数据"""
        return {
            'total_rooms': len(self.world_state.graph.room_ids),
            'total_objects': len(self.world_state.graph.nodes) - len(self.world_state.graph.room_ids),
            'total_agents': len(self.world_state.agents),
            'request_interval': self.config.get('request_interval', 2000)
        }

    def _get_supported_actions(self) -> List[Dict[str, Any]]:
        """获取支持的动作列表"""
        if not self.engine or not hasattr(self.engine, 'action_handler'):
            return []

        action_handler = self.engine.action_handler
        if not hasattr(action_handler, 'action_manager'):
            return []

        action_manager = action_handler.action_manager
        actions = []

        # 获取所有注册的动作
        if hasattr(action_manager, 'actions'):
            for action_name, action_class in action_manager.actions.items():
                # 检查是否需要工具
                requires_tool = hasattr(action_class, 'requires_tool') and action_class.requires_tool

                actions.append({
                    'name': action_name,
                    'requires_tool': requires_tool,
                    'description': getattr(action_class, '__doc__', '').strip() if hasattr(action_class, '__doc__') else ''
                })

        return sorted(actions, key=lambda x: (x['requires_tool'], x['name']))



    def _get_detailed_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务的详细列表，基于task.json中的validation_checks"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("开始获取详细任务信息")

        if not self.engine:
            logger.warning("引擎不存在，返回空任务列表")
            return []

        # 获取任务验证器（现在直接从引擎中获取）
        task_verifier = getattr(self.engine, 'task_verifier', None)

        if not task_verifier:
            logger.warning("任务验证器不存在，返回空任务列表")
            return []

        try:
            # 获取所有任务的验证结果（新格式返回列表）
            all_results = task_verifier.verify_all_tasks()
            logger.info(f"获取到验证结果，任务数: {len(all_results)}")

            all_tasks = []

            # 直接处理任务列表
            for i, result in enumerate(all_results):
                # 从任务数据中获取类别信息
                task_category = "unknown"
                for task in task_verifier.tasks:
                    if task.get("task_description") == result.task_description:
                        task_category = task.get("task_category", "unknown")
                        break

                category_name = self._get_category_display_name(task_category)

                task_info = {
                    'id': result.task_id,
                    'description': result.task_description,
                    'is_completed': result.is_completed,
                    'completion_details': result.completion_details,
                    'error_message': result.error_message,
                    'category': task_category,
                    'category_name': category_name,
                    'task_index': i + 1  # 任务序号
                }
                all_tasks.append(task_info)

            logger.info(f"成功获取 {len(all_tasks)} 个详细任务")
            for i, task in enumerate(all_tasks[:3]):  # 只显示前3个任务的信息
                logger.info(f"任务 {i+1}: {task['description'][:50]}... 完成状态: {task['is_completed']}")

            return all_tasks

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"获取详细任务信息时出错: {e}")
            logger.error(f"详细错误信息: {e.__class__.__name__}: {str(e)}")
            import traceback
            logger.error(f"堆栈跟踪: {traceback.format_exc()}")
            return []

    def _get_category_display_name(self, category: str) -> str:
        """获取类别的显示名称"""
        # 新格式的类别名称映射
        category_names = {
            'direct_command': '🤖 直接命令',
            'attribute_reasoning': '🤖 属性推理',
            'tool_use': '🤖 工具使用',
            'compound_reasoning': '🤖 复合推理',
            'explicit_collaboration': '👥 显式协作',
            'implicit_collaboration': '👥 隐式协作',
            'compound_collaboration': '👥 复合协作'
        }

        return category_names.get(category, f"📋 {category}")
    
    def _get_connected_rooms(self, room_id: str) -> List[str]:
        """获取连接的房间"""
        connected = []
        room_node = self.world_state.graph.get_node(room_id)
        if room_node and 'connected_to_room_ids' in room_node:
            connected = room_node['connected_to_room_ids']
        return connected
    
    def _get_objects_in_room(self, room_id: str) -> List[str]:
        """获取房间内的物体"""
        objects = []
        for node_id, node_data in self.world_state.graph.nodes.items():
            if node_id not in self.world_state.graph.room_ids:
                location = node_data.get('location_id', '')
                if location.startswith(f'in:{room_id}'):
                    objects.append(node_id)
        return objects
    
    def _get_agents_in_room(self, room_id: str) -> List[str]:
        """获取房间内的智能体"""
        agents = []
        for agent_id, agent_data in self.world_state.agents.items():
            if agent_data.get('location_id') == room_id:
                agents.append(agent_id)
        return agents
    
    def _parse_location(self, location_id: str) -> Dict[str, str]:
        """解析位置信息"""
        if not location_id:
            return {'type': 'unknown', 'target': ''}

        if ':' in location_id:
            location_type, target = location_id.split(':', 1)
            return {'type': location_type, 'target': target}
        else:
            return {'type': 'in', 'target': location_id}

    def _get_object_location_info(self, object_id: str) -> Dict[str, str]:
        """从图的边结构中获取物体的位置信息"""
        # 查找指向该物体的边（即包含该物体的容器）
        incoming_edges = self.world_state.graph.get_incoming_edges(object_id)

        if not incoming_edges:
            return {'type': 'unknown', 'target': ''}

        # 取第一个容器关系
        container_id, edge_data = next(iter(incoming_edges.items()))
        relation_type = edge_data.get('type', 'unknown')

        return {'type': relation_type, 'target': container_id}
    


    def _get_objects_in_room(self, room_id: str) -> List[str]:
        """获取房间内的所有物体ID列表"""
        objects_in_room = []
        for obj_id, obj_data in self.world_state.graph.nodes.items():
            if obj_data.get('type') == 'OBJECT':
                location = obj_data.get('location_id', '')
                location_info = self._parse_location(location)
                if location_info['type'] == 'in' and location_info['target'] == room_id:
                    objects_in_room.append(obj_id)
        return sorted(objects_in_room)  # 排序确保一致性

    def _get_objects_on_container(self, container_id: str) -> List[str]:
        """获取容器上的所有物体ID列表"""
        objects_on_container = []
        for obj_id, obj_data in self.world_state.graph.nodes.items():
            if obj_data.get('type') == 'OBJECT':
                location = obj_data.get('location_id', '')
                location_info = self._parse_location(location)
                if location_info['type'] == 'on' and location_info['target'] == container_id:
                    objects_on_container.append(obj_id)
        return sorted(objects_on_container)  # 排序确保一致性

    def _build_object_hierarchy(self) -> Dict[str, List[str]]:
        """构建物体层级关系，返回每个容器包含的物体列表"""
        hierarchy = {}

        for node_id in self.world_state.graph.nodes.keys():
            if node_id not in self.world_state.graph.room_ids:
                location_info = self._get_object_location_info(node_id)

                # 如果物体在另一个物体内部或上面
                if location_info['type'] in ['in', 'on'] and location_info['target']:
                    container_id = location_info['target']
                    # 只有当容器也是物体时才记录（不是房间）
                    if container_id not in self.world_state.graph.room_ids:
                        if container_id not in hierarchy:
                            hierarchy[container_id] = []
                        hierarchy[container_id].append(node_id)

        return hierarchy

    def _get_layout_info(self, obj_id: str, location_info: Dict[str, str]) -> Dict[str, Any]:
        """获取物体的布局信息，用于前端自动布局"""
        layout_info = {
            'container_type': location_info['type'],  # 'in', 'on', 'inside'
            'parent_id': location_info['target'],
            'is_root_level': location_info['type'] == 'in' and location_info['target'] in self.world_state.graph.room_ids,
            'depth_level': self._calculate_depth_level(obj_id),
            'sibling_index': self._calculate_sibling_index(obj_id, location_info)
        }
        return layout_info

    def _calculate_depth_level(self, obj_id: str) -> int:
        """计算物体的嵌套深度级别"""
        depth = 0
        current_id = obj_id
        visited = set()

        while current_id and current_id not in visited:
            visited.add(current_id)
            node_data = self.world_state.graph.get_node(current_id)
            if not node_data:
                break

            location = node_data.get('location_id', '')
            location_info = self._parse_location(location)

            if location_info['target'] in self.world_state.graph.room_ids:
                # 到达房间级别
                break
            elif location_info['target']:
                # 继续向上查找
                current_id = location_info['target']
                depth += 1
            else:
                break

        return depth

    def _calculate_sibling_index(self, obj_id: str, location_info: Dict[str, str]) -> int:
        """计算物体在同级物体中的索引位置"""
        if not location_info['target']:
            return 0

        # 获取同一容器中的所有物体
        siblings = []
        for node_id, node_data in self.world_state.graph.nodes.items():
            if node_id != obj_id and node_id not in self.world_state.graph.room_ids:
                other_location = node_data.get('location_id', '')
                other_location_info = self._parse_location(other_location)

                if (other_location_info['type'] == location_info['type'] and
                    other_location_info['target'] == location_info['target']):
                    siblings.append(node_id)

        siblings.append(obj_id)
        siblings.sort()  # 确保一致的排序

        return siblings.index(obj_id)

    def _get_agent_layout_info(self, agent_id: str, location_id: str) -> Dict[str, Any]:
        """获取智能体的布局信息"""
        # 获取同一房间内的所有智能体
        agents_in_room = []
        for aid, adata in self.world_state.agents.items():
            if adata.get('location_id') == location_id:
                agents_in_room.append(aid)

        agents_in_room.sort()  # 确保一致的排序
        agent_index = agents_in_room.index(agent_id) if agent_id in agents_in_room else 0

        return {
            'room_id': location_id,
            'agent_index': agent_index,
            'total_agents_in_room': len(agents_in_room)
        }

    def _get_container_info(self, obj_id: str, location_info: Dict[str, str]) -> Dict[str, Any]:
        """获取物体的容器信息"""
        container_info = {
            'is_contained': False,
            'container_id': None,
            'container_name': None,
            'relation_type': None
        }

        if location_info['type'] in ['in', 'on'] and location_info['target']:
            target_id = location_info['target']
            # 检查目标是否是物体（不是房间）
            if target_id not in self.world_state.graph.room_ids:
                target_node = self.world_state.graph.get_node(target_id)
                if target_node:
                    container_info.update({
                        'is_contained': True,
                        'container_id': target_id,
                        'container_name': target_node.get('name', target_id),
                        'relation_type': location_info['type']
                    })

        return container_info

    def _is_tool_object(self, node_data: Dict[str, Any]) -> bool:
        """判断物体是否是工具"""
        properties = node_data.get('properties', {})

        # 检查是否提供能力（工具通常提供能力）
        if 'provides_abilities' in properties:
            return True

        # 检查物体类型是否为工具类型
        obj_type = node_data.get('type', '').lower()
        tool_types = ['tool', 'instrument', 'device', 'equipment']
        if any(tool_type in obj_type for tool_type in tool_types):
            return True

        # 检查名称是否包含工具关键词
        name = node_data.get('name', '').lower()
        tool_keywords = ['tool', 'knife', 'hammer', 'screwdriver', 'wrench', 'saw']
        if any(keyword in name for keyword in tool_keywords):
            return True

        return False


    def get_room_layout_data(self, room_id: str) -> Dict[str, Any]:
        """获取特定房间的布局数据"""
        room_node = self.world_state.graph.get_node(room_id)
        if not room_node:
            return {}
        
        return {
            'room': {
                'id': room_id,
                'name': room_node.get('name', room_id),
                'properties': room_node.get('properties', {})
            },
            'objects': [obj for obj in self._get_objects_data() 
                       if obj['location']['target'] == room_id or 
                       (obj['location']['type'] == 'in' and obj['location']['target'] == room_id)],
            'agents': [agent for agent in self._get_agents_data() 
                      if agent['location'] == room_id]
        }
