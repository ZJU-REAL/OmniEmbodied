from typing import Dict, List, Optional, Any
import uuid
import random

from ..core.state import WorldState
from .agent import Agent

class AgentManager:
    """智能体管理器 - 负责管理所有智能体"""
    
    def __init__(self, world_state: WorldState, config: Optional[Dict[str, Any]] = None):
        """
        初始化智能体管理器
        
        Args:
            world_state: 世界状态对象
            config: 全局配置字典，可选
        """
        self.world_state = world_state
        self.config = config or {}
        self.agents: Dict[str, Agent] = {}  # agent_id -> Agent实例
        # 如果配置中明确指定了agent_count，则自动生成agent
        if 'agent_count' in self.config and self.config.get('agent_count', 0) > 0:
            self._init_agents_from_config()
    
    def _init_agents_from_config(self):
        agent_count = self.config.get('agent_count', 0)
        agent_types = self.config.get('agent_types', [])
        agent_init_mode = self.config.get('agent_init_mode', 'default')
        # 如果agent_count为0，则不创建任何智能体
        if agent_count <= 0:
            return
        # 获取所有房间ID
        room_ids = list(self.world_state.graph.room_ids)
        if not room_ids:
            return
        # default模式：全部放第一个房间（排序保证一致性）
        if agent_init_mode == 'default':
            init_room = sorted(room_ids)[0]
            for i in range(agent_count):
                agent_type = agent_types[i % len(agent_types)] if agent_types else {}
                agent_id = f"agent_{i+1}"
                agent_name = f"Agent_{i+1}"
                agent_data = {
                    "id": agent_id,
                    "name": agent_name,
                    "location_id": init_room,
                    **agent_type
                }
                self.add_agent(agent_data)
        # random模式：随机分配房间
        elif agent_init_mode == 'random':
            for i in range(agent_count):
                agent_type = agent_types[i % len(agent_types)] if agent_types else {}
                agent_id = f"agent_{i+1}"
                agent_name = f"Agent_{i+1}"
                room_id = random.choice(room_ids)
                agent_data = {
                    "id": agent_id,
                    "name": agent_name,
                    "location_id": room_id,
                    **agent_type
                }
                self.add_agent(agent_data)
    
    def add_agent(self, agent_data: Dict[str, Any]) -> Optional[str]:
        """
        添加智能体
        
        Args:
            agent_data: 智能体数据字典
            
        Returns:
            str: 添加成功则返回智能体ID，否则返回None
        """
        try:
            # 如果没有指定ID，则生成一个
            if 'id' not in agent_data:
                agent_data['id'] = str(uuid.uuid4())
                
            # 创建智能体对象
            # Agent.from_dict会处理max_grasp_limit的默认值以及properties的加载
            agent = Agent.from_dict(agent_data)
            
            # 检查位置是否存在
            if not self.world_state.graph.get_node(agent.location_id):
                print(f"位置不存在: {agent.location_id}")
                return None
                
            # 添加智能体到世界状态 (字典表示)
            self.world_state.add_agent(agent.id, agent.to_dict())
            
            # 同时将智能体添加到图节点中，类型设为"agent" (字典表示)
            agent_dict = agent.to_dict()
            agent_dict['type'] = 'AGENT'  # 确保智能体节点有明确的类型
            self.world_state.graph.add_node(agent.id, agent_dict)
            
            # 建立智能体与位置的关系
            self.world_state.graph.add_edge(agent.location_id, agent.id, {"type": "in"})
            
            # 存储智能体实例
            self.agents[agent.id] = agent
            
            # 初始化near_objects为空
            agent.near_objects = set()
            
            return agent.id
        except Exception as e:
            print(f"添加智能体时出错: {e}")
            return None
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        获取智能体实例
        
        Args:
            agent_id: 智能体ID
            
        Returns:
            Agent: 智能体实例，如果不存在则返回None
        """
        return self.agents.get(agent_id)
    
    def update_agent(self, agent_id: str, update_data: Dict[str, Any]) -> bool:
        """
        更新智能体数据
        
        Args:
            agent_id: 智能体ID
            update_data: 更新数据字典
            
        Returns:
            bool: 更新是否成功
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        
        # 更新智能体实例
        for key, value in update_data.items():
            if hasattr(agent, key):
                # 对于特殊字段，需要确保正确的数据类型
                if key == 'near_objects':
                    # 确保near_objects是集合
                    setattr(agent, key, set(value) if isinstance(value, (list, tuple)) else value)
                elif key == 'abilities':
                    # 确保abilities是集合
                    setattr(agent, key, set(value) if isinstance(value, (list, tuple)) else value)
                elif key == 'ability_sources':
                    # 确保ability_sources的值是集合
                    if isinstance(value, dict):
                        converted_sources = {}
                        for ability, sources in value.items():
                            converted_sources[ability] = set(sources) if isinstance(sources, (list, tuple)) else sources
                        setattr(agent, key, converted_sources)
                    else:
                        setattr(agent, key, value)
                else:
                    setattr(agent, key, value)
        
        # 更新世界状态中的智能体数据
        self.world_state.update_agent(agent_id, agent.to_dict())
        
        return True
    
    def move_agent(self, agent_id: str, new_location_id: str) -> bool:
        """
        移动智能体到新位置
        
        Args:
            agent_id: 智能体ID
            new_location_id: 新位置ID
            
        Returns:
            bool: 移动是否成功
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        
        # 只允许移动到房间
        if new_location_id not in self.world_state.graph.room_ids:
            return False
        
        old_location_id = agent.location_id
        agent.move_to(new_location_id)
        self.world_state.update_agent(agent_id, agent.to_dict())
        if old_location_id:
            self.world_state.graph.remove_edge(old_location_id, agent_id)
        self.world_state.graph.add_edge(new_location_id, agent_id, {"type": "in"})
        agent.update_near_objects()
        return True
    
    def add_to_inventory(self, agent_id: str, object_id: str) -> bool:
        """
        将物体添加到智能体库存
        
        Args:
            agent_id: 智能体ID
            object_id: 物体ID
            
        Returns:
            bool: 添加是否成功
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        
        # 尝试抓取物体
        success = agent.grab_object(object_id)
        if success:
            # 更新世界状态中的智能体数据
            self.world_state.update_agent(agent_id, agent.to_dict())
            
        return success
    
    def remove_from_inventory(self, agent_id: str, object_id: str) -> bool:
        """
        从智能体库存移除物体
        
        Args:
            agent_id: 智能体ID
            object_id: 物体ID
            
        Returns:
            bool: 移除是否成功
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        
        # 尝试放下物体
        success = agent.drop_object(object_id)
        if success:
            # 更新世界状态中的智能体数据
            self.world_state.update_agent(agent_id, agent.to_dict())
            
        return success
    
    def get_agent_inventory(self, agent_id: str) -> List[str]:
        """
        获取智能体库存
        
        Args:
            agent_id: 智能体ID
            
        Returns:
            List[str]: 物体ID列表
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return []
        
        return agent.inventory.copy()
    
    def get_all_agents(self) -> Dict[str, Agent]:
        """
        获取所有智能体
        
        Returns:
            Dict[str, Agent]: 智能体ID到智能体实例的映射
        """
        return self.agents.copy() 