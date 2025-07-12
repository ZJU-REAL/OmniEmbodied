from typing import Dict, List, Set, Tuple, Optional, Any
import queue

class EnvironmentGraph:
    """环境图类 - 用于表示环境中的实体（房间、物体）及其关系"""
    
    def __init__(self):
        """初始化环境图"""
        # 节点存储 - 房间和物体都是节点
        self.nodes = {}  # node_id -> node_data
        # 边存储 - 从节点到节点的关系
        self.edges = {}  # from_id -> {to_id -> [relation1, relation2, ...]}
        # 房间ID集合
        self.room_ids = set()
        
    def add_node(self, node_id: str, node_data: Dict, is_room: bool = False) -> None:
        """添加节点到图"""
        self.nodes[node_id] = node_data
        if is_room:
            self.room_ids.add(node_id)
        # 初始化边字典
        if node_id not in self.edges:
            self.edges[node_id] = {}
            
    def add_edge(self, from_id: str, to_id: str, relation: Dict) -> None:
        """添加边到图"""
        if from_id not in self.edges:
            self.edges[from_id] = {}
        if to_id not in self.edges[from_id]:
            self.edges[from_id][to_id] = []
        self.edges[from_id][to_id].append(relation)
    
    def remove_edge(self, from_id: str, to_id: str, relation_type: Optional[str] = None) -> None:
        """从图中移除边"""
        if from_id not in self.edges or to_id not in self.edges[from_id]:
            return
        
        if relation_type is None:
            # 移除所有关系
            del self.edges[from_id][to_id]
        else:
            # 移除指定类型的关系
            self.edges[from_id][to_id] = [
                rel for rel in self.edges[from_id][to_id]
                if rel.get('type') != relation_type
            ]
            if not self.edges[from_id][to_id]:
                del self.edges[from_id][to_id]
    
    def get_node(self, node_id: str) -> Optional[Dict]:
        """获取节点数据"""
        return self.nodes.get(node_id)
    
    def get_edges(self, from_id: str, to_id: Optional[str] = None) -> List[Dict]:
        """获取边关系"""
        if from_id not in self.edges:
            return []
        
        if to_id is not None:
            return self.edges[from_id].get(to_id, [])
        
        # 获取从from_id出发的所有边
        all_edges = []
        for target_id, relations in self.edges[from_id].items():
            for relation in relations:
                edge_info = relation.copy()
                edge_info['from_id'] = from_id
                edge_info['to_id'] = target_id
                all_edges.append(edge_info)
        return all_edges
    
    def get_incoming_edges(self, to_id: str) -> Dict[str, Dict]:
        """获取指向to_id的所有边"""
        incoming = {}
        for from_id, targets in self.edges.items():
            if to_id in targets:
                # 简化：只取第一个关系
                incoming[from_id] = targets[to_id][0]
        return incoming
    
    def get_room_for_object(self, object_id: str) -> Optional[str]:
        """获取物体所在的房间ID"""
        if object_id in self.room_ids:
            return object_id  # 如果是房间，返回自己
        
        # 使用辅助函数递归查找
        visited = set()
        return self._find_container_room(object_id, visited)
        
    def _find_container_room(self, object_id: str, visited: Set[str]) -> Optional[str]:
        """递归查找物体所在的房间"""
        if object_id in visited:
            return None  # 防止循环引用
        visited.add(object_id)
        
        # 查找直接包含该物体的容器
        containers = self.get_incoming_edges(object_id)
        for container_id, edge_data in containers.items():
            # 如果容器是房间，直接返回
            if container_id in self.room_ids:
                return container_id
            
            # 否则递归查找容器的房间
            room_id = self._find_container_room(container_id, visited)
            if room_id:
                return room_id
        
        return None
    
    def get_objects_in_room(self, room_id: str, recursive: bool = True) -> List[str]:
        """获取房间中的所有物体ID"""
        if room_id not in self.room_ids:
            return []
        
        # 获取直接在房间中的物体
        direct_objects = list(self.edges.get(room_id, {}).keys())
        
        if not recursive:
            return direct_objects
        
        # 递归获取容器中的物体
        all_objects = direct_objects.copy()
        visited = set()
        
        def collect_contained_objects(container_id: str, visited: Set[str] = None) -> List[str]:
            """递归收集容器中的所有物体"""
            if visited is None:
                visited = set()
            if container_id in visited:
                return []  # 防止循环引用
            visited.add(container_id)
            
            contained_objects = []
            for object_id in self.edges.get(container_id, {}).keys():
                if object_id not in self.room_ids and object_id not in visited:
                    contained_objects.append(object_id)
                    # 递归获取这个物体中的物体（如果它是容器）
                    contained_objects.extend(collect_contained_objects(object_id, visited))
            
            return contained_objects
        
        # 对每个直接物体，递归获取其中的物体
        for obj_id in direct_objects:
            if obj_id not in self.room_ids:  # 跳过房间
                all_objects.extend(collect_contained_objects(obj_id, visited))
        
        return all_objects
    
    def find_path(self, start_room_id: str, end_room_id: str) -> Optional[List[str]]:
        """
        查找从起始房间到目标房间的路径
        
        Args:
            start_room_id: 起始房间ID
            end_room_id: 目标房间ID
            
        Returns:
            List[str]: 房间ID路径，如果不存在则返回None
        """
        if start_room_id not in self.room_ids or end_room_id not in self.room_ids:
            return None
        
        if start_room_id == end_room_id:
            return [start_room_id]
        
        # 使用BFS查找最短路径
        visited = {start_room_id}
        q = queue.Queue()
        q.put((start_room_id, [start_room_id]))
        
        while not q.empty():
            current_id, path = q.get()
            
            # 获取相连的房间
            for next_room_id in self.edges.get(current_id, {}):
                if next_room_id in self.room_ids and next_room_id not in visited:
                    new_path = path + [next_room_id]
                    if next_room_id == end_room_id:
                        return new_path
                    
                    visited.add(next_room_id)
                    q.put((next_room_id, new_path))
        
        return None
    
    def describe_agent_natural_language(self, agent_id: str, agent: Dict) -> str:
        """
        用自然语言详细描述智能体状态
        
        Args:
            agent_id: 智能体ID
            agent: 智能体数据字典
            
        Returns:
            str: 智能体描述文本
        """
        # 获取基本信息，确保所有属性存在默认值
        name = agent.get('name', agent_id)
        location_id = agent.get('location_id', '未知位置')
        
        # 获取位置名称
        location_node = self.get_node(location_id)
        location_name = location_node.get('name', location_id) if location_node else location_id
        
        # 基本信息部分
        lines = [f"▶ 智能体：{name} (ID: {agent_id})"]
        lines.append(f"  • 位置：{location_name} (ID: {location_id})")
        
        # 物理属性部分
        properties = agent.get('properties', {})
        max_grasp = agent.get('max_grasp_limit', '未知')
        inventory = agent.get('inventory', [])
        inventory_count = len(inventory)
        current_weight = agent.get('current_weight', 0)
        max_weight = properties.get('max_weight', '未知')
        
        lines.append("  • 物理属性：")
        lines.append(f"    - 负载：{current_weight}/{max_weight}kg")
        lines.append(f"    - 抓取容量：{inventory_count}/{max_grasp}个")
        
        # 其他关键属性
        for key, value in properties.items():
            if key not in ['max_weight', 'max_length', 'max_width', 'max_height']:
                lines.append(f"    - {key}: {value}")
        
        # 能力信息部分
        abilities = agent.get('abilities', set())
        if not isinstance(abilities, (set, list)):
            abilities = set()
        ability_sources = agent.get('ability_sources', {})
        
        if abilities:
            lines.append("  • 拥有的能力：")
            for ability in sorted(abilities):
                sources = ability_sources.get(ability, set())
                if not isinstance(sources, (set, list)):
                    sources = set()
                
                source_names = []
                for source_id in sources:
                    source_obj = self.get_node(source_id)
                    source_name = source_obj.get('name', source_id) if source_obj else source_id
                    source_names.append(f"{source_name} (ID: {source_id})")
                
                source_str = f"，来源：{', '.join(source_names)}" if source_names else ""
                lines.append(f"    - {ability}{source_str}")
        else:
            lines.append("  • 拥有的能力：无")
        
        # 库存物品部分
        if inventory:
            lines.append("  • 持有的物品：")
            for obj_id in inventory:
                if obj_id.startswith('corp:'):
                    # 合作持有的物体
                    real_obj_id = obj_id.split(':', 1)[1]
                    obj = self.get_node(real_obj_id)
                    if obj:
                        obj_name = obj.get('name', real_obj_id)
                        obj_type = obj.get('type', '未知类型')
                        holders = obj.get('holders', [])
                        holder_ids = ', '.join(holders)
                        lines.append(f"    - {obj_name} (ID: {real_obj_id}, 类型: {obj_type})")
                        lines.append(f"      合作持有者: {holder_ids}")
                else:
                    # 普通物品
                    obj = self.get_node(obj_id)
                    if obj:
                        obj_name = obj.get('name', obj_id)
                        obj_type = obj.get('type', '未知类型')
                        properties = obj.get('properties', {})
                        
                        lines.append(f"    - {obj_name} (ID: {obj_id}, 类型: {obj_type})")
                        
                        # 物品能力
                        if 'provides_abilities' in properties:
                            abilities = properties['provides_abilities']
                            if isinstance(abilities, list) and abilities:
                                lines.append(f"      提供能力: {', '.join(abilities)}")
                            elif isinstance(abilities, str):
                                lines.append(f"      提供能力: {abilities}")
                        
                        # 物品其他属性
                        for key, value in properties.items():
                            if key != 'provides_abilities':
                                lines.append(f"      {key}: {value}")
        else:
            lines.append("  • 持有的物品：无")
        
        # 近邻物体部分
        # near_objects = agent.get('near_objects', set())
        # if not isinstance(near_objects, (set, list)):
        #     near_objects = set()
        
        # if near_objects:
        #     lines.append("  • 近邻物体（位置接近的物体）：")
        #     for obj_id in sorted(near_objects):
        #         obj = self.get_node(obj_id)
        #         if obj:
        #             obj_name = obj.get('name', obj_id)
        #             obj_type = obj.get('type', '未知类型')
        #             lines.append(f"    - {obj_name} (ID: {obj_id}, 类型: {obj_type})")
        # else:
        #     lines.append("  • 近邻物体（位置接近的物体）：无")
        
        # 合作模式部分
        corporate_mode = agent.get('corporate_mode_object_id')
        if corporate_mode:
            obj = self.get_node(corporate_mode)
            if obj:
                obj_name = obj.get('name', corporate_mode)
                lines.append(f"  • 合作模式：正在合作持有 {obj_name} (ID: {corporate_mode})")
            else:
                lines.append(f"  • 合作模式：正在合作持有物体 (ID: {corporate_mode})")
        
        return '\n'.join(lines)

    def describe_room_natural_language(self, room_id: str, agents: Optional[Dict[str, Dict]] = None, sim_config: Optional[Dict[str, Any]] = None) -> str:
        """
        用自然语言描述房间内容
        
        Args:
            room_id: 房间ID
            agents: 智能体字典 {agent_id -> agent_data}
            sim_config: 模拟器配置
                
        Returns:
            str: 房间描述文本
        """
        if sim_config is None:
            sim_config = getattr(self, 'sim_config', {}) or {}
        show_properties = sim_config.get('nlp_show_object_properties', True)
        only_discovered = sim_config.get('nlp_only_show_discovered', True)
        
        if room_id not in self.room_ids:
            return f"房间 {room_id} 不存在。"
        
        room_node = self.get_node(room_id)
        room_name = room_node.get('name', room_id) if room_node else room_id
        
        # 获取所有物体（递归）
        all_objects = self.get_objects_in_room(room_id, recursive=True)
        if only_discovered:
            all_objects = [oid for oid in all_objects if (self.get_node(oid) or {}).get('is_discovered', False)]
        
        # 获取房间内所有agent
        agent_lines = []
        agent_ids_in_room = set()
        if agents:
            for agent_id, agent in agents.items():
                if agent.get('location_id') == room_id:
                    agent_ids_in_room.add(agent_id)
                    # 简要描述智能体
                    name = agent.get('name', agent_id)
                    inventory = agent.get('inventory', [])
                    inventory_count = len(inventory)
                    
                    abilities = agent.get('abilities', set())
                    if not isinstance(abilities, (set, list)):
                        abilities = set()
                    abilities_count = len(abilities)
                    
                    agent_lines.append(f"- 智能体：{name} (ID: {agent_id})")
                    agent_lines.append(f"  持有物品数: {inventory_count}, 能力数: {abilities_count}")
        
        # 构建物体的空间关系映射（obj_id -> (relation, container_id)）
        spatial_rel = {}
        for from_id, to_dict in self.edges.items():
            for to_id, rels in to_dict.items():
                for rel in rels:
                    if rel.get('type') in ('in', 'on'):
                        spatial_rel[to_id] = (rel.get('type'), from_id)
        
        # 递归输出物体（不包括agent和被agent持有的物体，也不包括被合作持有的物体）
        def output_objects(parent_id, indent=0, visited=None):
            if visited is None:
                visited = set()
            lines = []
            # 只找直接属于parent_id的物体，且不是AGENT也不是ROOM，且（如需）is_discovered为True
            children = [
                oid for oid in self.edges.get(parent_id, {})
                if (self.get_node(oid) or {}).get('type', None) not in ('AGENT', 'ROOM')
                and (not only_discovered or (self.get_node(oid) or {}).get('is_discovered', False))
            ]
            # 排除被agent持有的物体
            inventory_objs = set()
            if agents:
                for agent in agents.values():
                    inventory_objs.update(agent.get('inventory', []))
            # 排除被合作持有的物体
            children = [oid for oid in children if oid not in inventory_objs and not ((self.get_node(oid) or {}).get('holders', []) )]
            
            for oid in children:
                if oid in visited:
                    continue  # 防止递归死循环
                visited.add(oid)
                obj = self.get_node(oid)
                if not obj:
                    continue
                
                obj_name = obj.get('name', oid)
                obj_type = obj.get('type', '未知类型')
                
                # 基本信息
                prefix = '  ' * indent
                lines.append(f"{prefix}◆ {obj_name} (ID: {oid}, 类型: {obj_type})")
                
                # 空间关系
                if oid in spatial_rel:
                    rel, container_id = spatial_rel[oid]
                    container = self.get_node(container_id)
                    container_name = container.get('name', container_id) if container else container_id
                    rel_text = "里面" if rel == "in" else "上面" if rel == "on" else "位置"
                    lines.append(f"{prefix}  • 位置: 在{container_name} (ID: {container_id}) {rel_text}")
                
                # 状态信息
                states = obj.get('states', {})
                if states:
                    lines.append(f"{prefix}  • 状态:")
                    for k, v in states.items():
                        lines.append(f"{prefix}    - {k}: {v}")
                
                # 属性信息
                if show_properties:
                    props = obj.get('properties', {})
                    if props:
                        lines.append(f"{prefix}  • 属性:")
                        
                        # 物理属性（尺寸和重量）
                        size = props.get('size')
                        if size is not None and isinstance(size, (list, tuple)) and len(size) == 3:
                            length, width, height = size  # [长,宽,高]
                            lines.append(f"{prefix}    - 尺寸: 长{length}m × 宽{width}m × 高{height}m")
                        else:
                            if 'length' in props:
                                lines.append(f"{prefix}    - 长: {props['length']}m")
                            if 'width' in props:
                                lines.append(f"{prefix}    - 宽: {props['width']}m")
                            if 'height' in props:
                                lines.append(f"{prefix}    - 高: {props['height']}m")
                        
                        if 'weight' in props:
                            lines.append(f"{prefix}    - 重量: {props['weight']}kg")
                        
                        # 物体提供的能力
                        if 'provides_abilities' in props:
                            abilities = props['provides_abilities']
                            if isinstance(abilities, list) and abilities:
                                lines.append(f"{prefix}    - 提供能力: {', '.join(abilities)}")
                            elif isinstance(abilities, str):
                                lines.append(f"{prefix}    - 提供能力: {abilities}")
                        
                        # 其他所有属性
                        for k, v in props.items():
                            if k not in ['size', 'length', 'width', 'height', 'weight', 'provides_abilities']:
                                lines.append(f"{prefix}    - {k}: {v}")
                
                # 递归输出子物体
                sub_lines = output_objects(oid, indent+1, visited)
                if sub_lines:
                    lines.append(f"{prefix}  • 包含物体:")
                    lines.extend(sub_lines)
            
            return lines
        
        # 构建完整描述
        desc_lines = [f"▶ 房间：{room_name} (ID: {room_id})"]
        
        # 房间属性
        room_props = room_node.get('properties', {})
        if room_props:
            desc_lines.append("  • 房间属性:")
            for k, v in room_props.items():
                desc_lines.append(f"    - {k}: {v}")
        
        # 房间连接
        connected_rooms = []
        for to_id, rels in self.edges.get(room_id, {}).items():
            for rel in rels:
                if rel.get('type') == 'connected_to' and to_id in self.room_ids:
                    room = self.get_node(to_id)
                    room_name = room.get('name', to_id) if room else to_id
                    connected_rooms.append(f"{room_name} (ID: {to_id})")
        
        if connected_rooms:
            desc_lines.append("  • 连接房间: " + ", ".join(connected_rooms))
        
        # 智能体
        if agent_lines:
            desc_lines.append("  • 智能体:")
            desc_lines.extend(['    ' + line for line in agent_lines])
        
        # 物体
        obj_lines = output_objects(room_id)
        if obj_lines:
            desc_lines.append("  • 物体:")
            desc_lines.extend(["    " + line for line in obj_lines])
        else:
            desc_lines.append("  • 物体: 无物体或暂未发现")
        
        # 被合作持有的物体
        cooperative_objs = []
        for obj_id, obj in self.nodes.items():
            holders = obj.get('holders', [])
            if holders and len(holders) > 1:
                # 检查所有holder都在本房间
                if agents and all(agents.get(aid, {}).get('location_id') == room_id for aid in holders if aid in agents):
                    obj_name = obj.get('name', obj_id)
                    obj_type = obj.get('type', '未知类型')
                    holder_names = []
                    for hid in holders:
                        if hid in agents:
                            holder_names.append(f"{agents[hid]['name']} (ID: {hid})")
                        else:
                            holder_names.append(hid)
                    cooperative_objs.append(f"- {obj_name} (ID: {obj_id}, 类型: {obj_type})")
                    cooperative_objs.append(f"  持有者: {', '.join(holder_names)}")
        
        if cooperative_objs:
            desc_lines.append("  • 被合作持有的物体:")
            desc_lines.extend(['    ' + line for line in cooperative_objs])
        
        return '\n'.join(desc_lines)

    def describe_environment_natural_language(self, agents: Optional[Dict[str, Dict]] = None, sim_config: Optional[Dict[str, Any]] = None) -> str:
        """
        用自然语言描述整个环境（所有房间及其内容）和所有智能体状态。
        
        Args:
            agents: 智能体字典 {agent_id -> agent_data}
            sim_config: 模拟器配置
                - nlp_show_object_properties: 是否输出家具和物品的详细属性
                - nlp_only_show_discovered: 只描述已发现内容
                
        Returns:
            str: 环境和智能体描述文本
        """
        if sim_config is None:
            sim_config = getattr(self, 'sim_config', {}) or {}
        
        sections = []
        
        # 环境概述
        sections.append("================ 环境概述 ================")
        room_count = len(self.room_ids)
        object_count = sum(1 for node in self.nodes.values() if node.get('type') not in ['ROOM', 'AGENT'])
        agent_count = len(agents) if agents else 0
        sections.append(f"共有 {room_count} 个房间, {object_count} 个物体, {agent_count} 个智能体")
        sections.append("")
        
        # 房间描述
        sections.append("================ 房间详情 ================")
        for room_id in self.room_ids:
            room_desc = self.describe_room_natural_language(room_id, agents, sim_config=sim_config)
            sections.append(room_desc)
            sections.append("")  # 空行分隔不同房间
        
        # 智能体详细描述
        if agents:
            sections.append("================ 智能体详情 ================")
            for agent_id, agent in agents.items():
                agent_desc = self.describe_agent_natural_language(agent_id, agent)
                sections.append(agent_desc)
                sections.append("")  # 空行分隔不同智能体
        
        return '\n'.join(sections)

class WorldState:
    """世界状态类 - 维护整个模拟世界的状态"""
    
    def __init__(self):
        self.graph = EnvironmentGraph()
        self.agents = {}  # agent_id -> agent_data
        
    def add_agent(self, agent_id: str, agent_data: Dict) -> None:
        """添加智能体到世界状态"""
        self.agents[agent_id] = agent_data
        
    def update_agent(self, agent_id: str, update_data: Dict) -> None:
        """更新智能体状态"""
        if agent_id in self.agents:
            self.agents[agent_id].update(update_data)
            
    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """获取智能体数据"""
        return self.agents.get(agent_id)
    
    def get_object(self, object_id: str) -> Optional[Dict]:
        """获取物体数据"""
        return self.graph.get_node(object_id)
    
    def is_object_accessible_to_agent(self, object_id: str, agent_id: str) -> Tuple[bool, str]:
        """检查物体是否对智能体可访问"""
        agent = self.get_agent(agent_id)
        if not agent:
            return False, f"智能体 {agent_id} 不存在"
        
        obj = self.get_object(object_id)
        if not obj:
            return False, f"物体 {object_id} 不存在"
        
        # 注释掉检查同一房间的代码，由上层功能执行
        # 检查智能体和物体是否在同一房间
        # agent_room = agent.get("location_id")
        # obj_room = self.graph.get_room_for_object(object_id)
        # 
        # if agent_room != obj_room:
        #    return False, f"智能体 {agent_id} 不在物体 {object_id} 所在的房间"
        
        # 检查物体是否在封闭容器中
        # 只有 "in" 关系的物品需要检查容器是否打开
        # "on" 关系的物品可以直接拿取，不需要打开容器

        # 查找物体的直接容器和关系类型
        for potential_container_id, edges_dict in self.graph.edges.items():
            if object_id in edges_dict:
                relations_list = edges_dict[object_id]
                # relations_list 是一个关系列表，每个关系是一个字典
                if isinstance(relations_list, list) and relations_list:
                    # 取第一个关系（通常一个物体只有一个位置关系）
                    relation = relations_list[0]
                    relation_type = relation.get("type", "in")

                    # 只有 "in" 关系才需要检查容器是否打开
                    # "on" 关系的物品可以直接拿取
                    if relation_type == "in":
                        container = self.get_object(potential_container_id)
                        if container and "states" in container:
                            # 检查容器是否有 is_open 状态且为 False
                            if container["states"].get("is_open") is False:
                                return False, f"物体 {object_id} 在封闭的容器 {container['name']} 中"
        
        return True, "物体可访问"

    def describe_agent_natural_language(self, agent_id: str, agent: Dict = None) -> str:
        """转发到EnvironmentGraph的describe_agent_natural_language方法"""
        if agent is None:
            agent = self.get_agent(agent_id)
            if not agent:
                return f"智能体 {agent_id} 不存在"
        return self.graph.describe_agent_natural_language(agent_id, agent)

    def describe_room_natural_language(self, room_id: str, agents: Optional[Dict[str, Dict]] = None, sim_config: Optional[Dict[str, Any]] = None) -> str:
        """转发到EnvironmentGraph的describe_room_natural_language方法"""
        if agents is None:
            agents = self.agents
        return self.graph.describe_room_natural_language(room_id, agents, sim_config)

    def describe_environment_natural_language(self, agents: Optional[Dict[str, Dict]] = None, sim_config: Optional[Dict[str, Any]] = None) -> str:
        """转发到EnvironmentGraph的describe_environment_natural_language方法"""
        if agents is None:
            agents = self.agents
        return self.graph.describe_environment_natural_language(agents, sim_config) 