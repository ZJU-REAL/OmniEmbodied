"""
近邻关系管理器 - 统一管理智能体与物体的近邻关系
"""

from typing import Set, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ProximityManager:
    """
    近邻关系管理器 - 负责统一管理智能体的near_objects
    
    这个类将原本分散在Agent类和各个动作类中的近邻关系管理逻辑
    集中到一个地方，提供一致的接口和行为。
    """
    
    def __init__(self, env_manager):
        """
        初始化近邻关系管理器
        
        Args:
            env_manager: 环境管理器实例
        """
        self.env_manager = env_manager
    
    def update_agent_proximity(self, agent, target_id: Optional[str] = None) -> Set[str]:
        """
        更新智能体的近邻关系
        
        Args:
            agent: 智能体对象
            target_id: 靠近的目标ID（可选）
            
        Returns:
            Set[str]: 更新后的near_objects集合
        """
        # 记录更新前的状态
        old_near_objects = set(agent.near_objects) if agent.near_objects else set()
        
        # 重置near_objects，初始包含库存和当前位置
        agent.near_objects = set(agent.inventory)
        agent.near_objects.add(agent.location_id)
        
        logger.debug(f"智能体 {agent.id} 更新近邻关系 - 库存: {agent.inventory}, 位置: {agent.location_id}")
        
        if target_id is not None:
            self._add_target_proximity(agent, target_id)
        
        # 记录变化
        new_objects = agent.near_objects - old_near_objects
        removed_objects = old_near_objects - agent.near_objects
        
        if new_objects:
            logger.debug(f"智能体 {agent.id} 新增近邻物体: {new_objects}")
        if removed_objects:
            logger.debug(f"智能体 {agent.id} 移除近邻物体: {removed_objects}")
        
        # 确保返回集合类型
        if not isinstance(agent.near_objects, set):
            agent.near_objects = set(agent.near_objects)
        
        logger.debug(f"智能体 {agent.id} 最终近邻物体: {agent.near_objects}")
        return agent.near_objects
    
    def _add_target_proximity(self, agent, target_id: str):
        """
        添加目标物体及其相关物体到近邻列表
        新逻辑：找到包含目标物品的第一个家具类型节点，智能体near该家具节点的所有子节点

        Args:
            agent: 智能体对象
            target_id: 目标物体ID
        """
        logger.debug(f"智能体 {agent.id} 靠近目标: {target_id}")

        obj = self.env_manager.get_object_by_id(target_id)
        if not obj:
            logger.warning(f"目标物体不存在: {target_id}")
            return

        # 确保目标物体已被发现
        if not obj.get('is_discovered', True):
            logger.debug(f"目标物体未被发现: {target_id}")
            return

        # 如果是房间，只添加房间本身
        if obj.get('type', '').upper() == 'ROOM':
            agent.near_objects.add(target_id)
            return

        # 找到包含目标物品的第一个家具类型节点
        furniture_node_id = self._find_containing_furniture(target_id)

        if furniture_node_id:
            # 添加家具节点本身
            agent.near_objects.add(furniture_node_id)
            logger.debug(f"智能体 {agent.id} 找到包含家具: {furniture_node_id}")

            # 添加家具节点的所有子物体（递归）
            all_children = self._collect_all_children_recursive(furniture_node_id)
            agent.near_objects.update(all_children)

            logger.debug(f"智能体 {agent.id} 添加了家具 {furniture_node_id} 及其 {len(all_children)} 个子物体")
        else:
            # 如果没有找到包含的家具，只添加目标物体本身
            agent.near_objects.add(target_id)
            logger.debug(f"智能体 {agent.id} 未找到包含家具，只添加目标物体: {target_id}")
    
    def _collect_discovered_children(self, obj_id: str) -> Set[str]:
        """
        收集指定物体的所有已发现子物体
        
        Args:
            obj_id: 物体ID
            
        Returns:
            Set[str]: 子物体ID集合
        """
        children = set()
        
        def collect_recursive(current_id):
            for child_id in self.env_manager.world_state.graph.edges.get(current_id, {}):
                child_obj = self.env_manager.get_object_by_id(child_id)
                if child_obj and child_obj.get('is_discovered', True):
                    children.add(child_id)
                    collect_recursive(child_id)
        
        collect_recursive(obj_id)
        return children
    
    def _collect_parents_and_siblings(self, obj_id: str) -> Set[str]:
        """
        收集指定物体的父物体和兄弟物体

        Args:
            obj_id: 物体ID

        Returns:
            Set[str]: 父物体和兄弟物体ID集合
        """
        related = set()

        # 查找父物体
        for parent_id, edges in self.env_manager.world_state.graph.edges.items():
            if obj_id in edges:
                parent_obj = self.env_manager.get_object_by_id(parent_id)
                if parent_obj and parent_obj.get('is_discovered', True):
                    related.add(parent_id)

                    # 只有当父物体不是房间时，才添加兄弟物体
                    if parent_obj.get('type', '').upper() != 'ROOM':
                        # 添加兄弟物体（同一父物体下的其他物体）
                        for sibling_id in edges:
                            if sibling_id != obj_id:
                                sibling_obj = self.env_manager.get_object_by_id(sibling_id)
                                if sibling_obj and sibling_obj.get('is_discovered', True):
                                    related.add(sibling_id)
                                    # 递归添加兄弟物体的子物体
                                    sibling_children = self._collect_discovered_children(sibling_id)
                                    related.update(sibling_children)

        return related
    
    def is_agent_near_object(self, agent, object_id: str) -> bool:
        """
        检查智能体是否靠近指定物体
        
        Args:
            agent: 智能体对象
            object_id: 物体ID
            
        Returns:
            bool: 是否靠近
        """
        return object_id in agent.near_objects or object_id in agent.inventory
    
    def add_object_to_proximity(self, agent, object_id: str):
        """
        将物体添加到智能体的近邻列表
        
        Args:
            agent: 智能体对象
            object_id: 物体ID
        """
        if not hasattr(agent, 'near_objects') or agent.near_objects is None:
            agent.near_objects = set()
        elif not isinstance(agent.near_objects, set):
            agent.near_objects = set(agent.near_objects)
        
        agent.near_objects.add(object_id)
        logger.debug(f"智能体 {agent.id} 添加近邻物体: {object_id}")
    
    def remove_object_from_proximity(self, agent, object_id: str):
        """
        从智能体的近邻列表中移除物体

        Args:
            agent: 智能体对象
            object_id: 物体ID
        """
        if hasattr(agent, 'near_objects') and agent.near_objects:
            agent.near_objects.discard(object_id)
            logger.debug(f"智能体 {agent.id} 移除近邻物体: {object_id}")

    def _find_containing_furniture(self, object_id: str) -> Optional[str]:
        """
        找到包含指定物体的第一个家具类型节点

        Args:
            object_id: 物体ID

        Returns:
            Optional[str]: 包含该物体的家具ID，如果没有找到则返回None
        """
        # 如果目标本身就是家具，直接返回
        obj = self.env_manager.get_object_by_id(object_id)
        if obj and obj.get('type', '').upper() == 'FURNITURE':
            return object_id

        # 向上查找父节点，直到找到家具类型的节点
        current_id = object_id
        visited = set()  # 防止循环引用

        while current_id and current_id not in visited:
            visited.add(current_id)

            # 查找当前物体的父节点
            parent_id = self._find_parent_object(current_id)
            if not parent_id:
                break

            parent_obj = self.env_manager.get_object_by_id(parent_id)
            if parent_obj and parent_obj.get('type', '').upper() == 'FURNITURE':
                logger.debug(f"找到包含物体 {object_id} 的家具: {parent_id}")
                return parent_id

            current_id = parent_id

        logger.debug(f"未找到包含物体 {object_id} 的家具")
        return None

    def _find_parent_object(self, object_id: str) -> Optional[str]:
        """
        找到物体的直接父节点

        Args:
            object_id: 物体ID

        Returns:
            Optional[str]: 父节点ID，如果没有找到则返回None
        """
        # 遍历所有边，找到指向当前物体的边
        for parent_id, edges_dict in self.env_manager.world_state.graph.edges.items():
            if object_id in edges_dict:
                return parent_id
        return None

    def _collect_all_children_recursive(self, object_id: str) -> Set[str]:
        """
        递归收集指定物体的所有子物体（包括子物体的子物体）

        Args:
            object_id: 物体ID

        Returns:
            Set[str]: 所有子物体的ID集合
        """
        all_children = set()
        visited = set()  # 防止循环引用

        def collect_recursive(current_id):
            if current_id in visited:
                return
            visited.add(current_id)

            # 获取直接子物体
            direct_children = self.env_manager.world_state.graph.edges.get(current_id, {})
            for child_id in direct_children:
                child_obj = self.env_manager.get_object_by_id(child_id)
                if child_obj and child_obj.get('is_discovered', True):
                    all_children.add(child_id)
                    # 递归收集子物体的子物体
                    collect_recursive(child_id)

        collect_recursive(object_id)
        logger.debug(f"递归收集物体 {object_id} 的所有子物体: {len(all_children)} 个")
        return all_children
