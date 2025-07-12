import os
import yaml
from typing import Dict, Optional, Any, Tuple, List

from .state import WorldState

class SimulationEngine:
    """模拟引擎类 - 整个模拟器的核心控制器"""

    def _deep_merge_dict(self, target: dict, source: dict):
        """深度合并字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge_dict(target[key], value)
            else:
                target[key] = value

    def __init__(self, config: Optional[Dict[str, Any]] = None, scene_abilities: List[str] = None):
        """
        初始化模拟引擎

        Args:
            config: 全局配置字典，可选
            scene_abilities: 场景特定的能力列表，用于动态注册需要工具的动作
        """
        # 设置默认配置
        default_config = {
            'explore_mode': 'thorough',  # 设置默认探索模式为彻底探索
        }

        # 合并用户提供的配置与默认配置
        self.config = default_config.copy()
        if config:
            self._deep_merge_dict(self.config, config)

        self.world_state = WorldState()
        self.env_manager = None
        self.agent_manager = None
        self.action_handler = None
        self.task_config = None
        self.scene_abilities = scene_abilities or []

        # 验证系统
        self.task_verifier = None

        # 可视化系统
        self.visualization_manager = None
        self._load_global_config()

    def _load_global_config(self):
        """加载全局配置文件"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'simulator_config.yaml')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    global_config = yaml.safe_load(f) or {}

                # 合并全局配置到当前配置（用户配置优先）
                for key, value in global_config.items():
                    if key not in self.config:
                        self.config[key] = value
                    elif isinstance(value, dict) and isinstance(self.config.get(key), dict):
                        # 深度合并字典，但保持用户配置优先
                        merged_dict = value.copy()
                        self._deep_merge_dict(merged_dict, self.config[key])
                        self.config[key] = merged_dict
                    else:
                        # 如果用户没有提供该配置，使用全局配置
                        if key not in self.config:
                            self.config[key] = value

        except Exception as e:
            print(f"加载全局配置失败: {e}")

    def _initialize_visualization(self):
        """初始化可视化系统（仅在需要时）"""
        try:
            # 检查是否启用可视化
            viz_config = self.config.get('visualization', {})
            if not viz_config.get('enabled', False):
                return True

            # 延迟导入以避免循环依赖
            from visualization.visualization_manager import VisualizationManager
            self.visualization_manager = VisualizationManager(
                self.world_state,
                self.agent_manager,
                self.env_manager,
                engine=self
            )

            # 更新可视化管理器的配置
            self.visualization_manager.config = self.config
            self.visualization_manager.visualization_config = self.config.get('visualization', {})

            # 初始化可视化管理器
            if not self.visualization_manager.initialize():
                print("可视化管理器初始化失败")
                return False

            # 启动可视化系统
            if self.visualization_manager:
                success = self.visualization_manager.start()
                if success:
                    print(f"可视化系统已启动: {self.visualization_manager.get_server_url()}")
                else:
                    print("可视化系统启动失败")
                    return False

            return True

        except ImportError:
            print("可视化模块不可用，跳过可视化初始化")
            return True
        except Exception as e:
            print(f"初始化可视化系统失败: {e}")
            return True  # 可视化失败不应该影响核心功能
    
    def initialize(self, scene_file: str, agent_file: Optional[str] = None) -> bool:
        """
        初始化模拟器
        Args:
            scene_file: 场景文件路径
            agent_file: 智能体文件路径（已废弃，不再使用）
        Returns:
            bool: 是否成功初始化
        """
        try:
            # 导入需要的模块
            # 注意：这些导入放在这里而不是文件顶部，是为了避免循环导入
            from environment.environment_manager import EnvironmentManager
            from environment.scene_parser import SceneParser
            from agent.agent_manager import AgentManager
            from action.action_handler import ActionHandler
            
            # 创建环境管理器
            self.env_manager = EnvironmentManager(self.world_state, sim_config=self.config)
            
            # 创建场景解析器并加载场景
            scene_parser = SceneParser()
            scene_data = scene_parser.parse_scene_file(scene_file)
            if not scene_data:
                print(f"无法解析场景文件: {scene_file}")
                return False
            
            # 使用环境管理器从场景数据加载环境
            success = self.env_manager.load_scene(scene_data)
            if not success:
                print("加载场景失败")
                return False
            
            # 创建智能体管理器（只通过yaml配置初始化）
            self.agent_manager = AgentManager(self.world_state, self.config)

            # 从场景数据中提取abilities
            scene_abilities = None
            if scene_data and 'abilities' in scene_data:
                self.scene_abilities = scene_data['abilities']
                scene_abilities = self.scene_abilities

            # 创建动作处理器，传递scene_abilities
            self.action_handler = ActionHandler(
                self.world_state,
                self.env_manager,
                self.agent_manager,
                scene_abilities=scene_abilities,
                config=self.config
            )

            # 注册需要工具的动作
            if scene_abilities:
                self._register_scene_specific_actions()

            # 初始化可视化系统
            self._initialize_visualization()

            return True
        except Exception as e:
            print(f"初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def initialize_with_task(self, task_file: str) -> bool:
        """
        使用任务文件初始化模拟器（包括场景和智能体）
        
        Args:
            task_file: 任务文件路径
            
        Returns:
            bool: 是否成功初始化
        """
        try:
            # 导入需要的模块
            from environment.scene_parser import SceneParser
            from environment.scene_validator import SceneValidator
            
            # 解析任务文件
            scene_parser = SceneParser()
            task_data = scene_parser.parse_file(task_file)
            if not task_data:
                print(f"无法解析任务文件: {task_file}")
                return False
            
            # 验证任务数据
            is_valid, errors = SceneValidator.validate_agent_config(task_data)
            if not is_valid:
                print("任务数据无效:")
                for error in errors:
                    print(f"  - {error}")
                return False
            
            # 保存任务配置
            self.task_config = task_data

            # 注意：abilities现在从scene.json读取，不再从task.json读取

            # 获取关联的场景文件
            scene_uid = task_data.get("scene_uid")
            if not scene_uid:
                print("任务数据缺少scene_uid字段")
                return False

            # 构建场景文件路径
            scene_file = self._find_scene_file(scene_uid)
            if not scene_file:
                print(f"找不到场景文件: {scene_uid}")
                return False

            # 初始化模拟器
            success = self.initialize(scene_file)
            if not success:
                return False
            
            # 加载智能体
            if "agents_config" in task_data:
                success = self.load_agents(task_data["agents_config"])
                if not success:
                    print("加载智能体失败")
                    return False

            # 初始化可视化系统
            self._initialize_visualization()

            return True
        except Exception as e:
            print(f"使用任务初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def initialize_with_data(self, data: Dict[str, Any]) -> bool:
        """
        使用数据字典初始化模拟器
        
        Args:
            data: 包含场景、任务和动作配置的数据字典
                  格式: {
                      'scene': scene_data,          # 场景数据
                      'task': task_data,            # 任务数据 (可选)
                      'actions': action_config_data # 动作配置数据 (可选)
                  }
                  
        Returns:
            bool: 是否成功初始化
        """
        try:
            # 导入需要的模块
            from environment.environment_manager import EnvironmentManager
            from environment.scene_validator import SceneValidator
            from agent.agent_manager import AgentManager
            from action.action_handler import ActionHandler
            
            # 获取各部分数据
            scene_data = data.get('scene')
            task_data = data.get('task')
            action_config = data.get('actions')
            
            if not scene_data:
                print("数据中缺少场景信息")
                return False
            
            # 验证场景数据
            is_valid, errors = SceneValidator.validate_scene(scene_data)
            if not is_valid:
                print("场景数据无效:")
                for error in errors:
                    print(f"  - {error}")
                return False
            
            # 创建环境管理器
            self.env_manager = EnvironmentManager(self.world_state, sim_config=self.config)
            
            # 直接从场景数据加载环境
            success = self.env_manager.load_scene(scene_data)
            if not success:
                print("从数据加载场景失败")
                return False
            
            # 创建智能体管理器
            self.agent_manager = AgentManager(self.world_state, self.config)
            
            # 如果有任务数据，加载智能体
            if task_data:
                # 验证任务数据
                is_valid, errors = SceneValidator.validate_agent_config(task_data)
                if not is_valid:
                    print("任务数据无效:")
                    for error in errors:
                        print(f"  - {error}")
                    return False
                
                # 保存任务配置
                self.task_config = task_data
                
                # 加载智能体
                if "agents_config" in task_data:
                    success = self.load_agents(task_data["agents_config"])
                    if not success:
                        print("加载智能体失败")
                        return False
            
            # 从场景数据中提取abilities
            scene_abilities = None
            if scene_data and 'abilities' in scene_data:
                self.scene_abilities = scene_data['abilities']
                scene_abilities = self.scene_abilities

            # 创建动作处理器，传递scene_abilities
            self.action_handler = ActionHandler(
                self.world_state,
                self.env_manager,
                self.agent_manager,
                scene_abilities=scene_abilities,
                config=self.config
            )

            # 注册需要工具的动作
            if scene_abilities:
                self._register_scene_specific_actions()

            # 如果有动作配置，处理自定义动作配置
            if action_config:
                self._load_action_config(action_config)

            # 如果有任务数据，设置任务验证器（验证数据现在在task.json中）
            if task_data:
                self.task_verifier = self._create_task_verifier(task_data)

            # 初始化可视化系统
            self._initialize_visualization()

            return True
        except Exception as e:
            print(f"使用数据初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _load_action_config(self, action_config: Dict[str, Any]):
        """
        加载自定义动作配置
        
        Args:
            action_config: 动作配置数据
        """
        try:
            # 处理属性动作配置
            if 'attribute_actions' in action_config:
                from action.actions.attribute_actions import AttributeAction
                from action.actions.corporate_attribute_actions import CorporateAttributeAction
                
                # 可以在这里处理自定义的属性动作配置
                # 例如：动态更新action_configs字典
                custom_actions = action_config['attribute_actions']
                for action_name, config in custom_actions.items():
                    AttributeAction.action_configs[action_name] = config
                    CorporateAttributeAction.action_configs[action_name] = config
                    
                    # 如果不需要工具，添加到全局动作类
                    if not config.get('requires_tool', True):
                        AttributeAction.no_tool_actions.add(action_name)
                        CorporateAttributeAction.no_tool_actions.add(action_name)
                        
                        # 重新注册不需要工具的动作
                        self.action_handler.action_manager.register_action_class(
                            action_name.upper(), AttributeAction
                        )
                        self.action_handler.action_manager.register_action_class(
                            f"CORP_{action_name.upper()}", CorporateAttributeAction
                        )
                
                print(f"已加载 {len(custom_actions)} 个自定义属性动作")
            
        except Exception as e:
            print(f"Failed to load action configuration: {e}")
            import traceback
            traceback.print_exc()

    def _find_scene_file(self, scene_uid: str) -> Optional[str]:
        """
        Find scene file based on scene UID

        Args:
            scene_uid: Scene unique identifier

        Returns:
            str: Scene file path, returns None if not found
        """
        # Search in data/scene/ directory by default
        base_dirs = ["data/default/", "data/scene/"]
        
        for base_dir in base_dirs:
            # Try different file extensions
            for ext in [".json", ".yaml", ".yml"]:
                file_path = f"{base_dir}{scene_uid}{ext}"
                if os.path.exists(file_path):
                    return file_path
        
        return None
    
    def validate_environment(self) -> Tuple[bool, List[str]]:
        """
        验证当前环境是否合法
        
        Returns:
            Tuple[bool, List[str]]: (是否合法, 错误信息列表)
        """
        from environment.scene_validator import SceneValidator
        
        if not self.env_manager:
            return False, ["模拟器未初始化"]
        
        # 构建场景数据结构
        scene_data = {
            "rooms": [],
            "objects": []
        }
        
        # 收集所有房间
        for room_id in self.world_state.graph.room_ids:
            room_data = self.world_state.graph.get_node(room_id)
            if room_data:
                scene_data["rooms"].append(room_data)
        
        # 收集所有物体
        for node_id, node_data in self.world_state.graph.nodes.items():
            if node_id not in self.world_state.graph.room_ids and node_data.get("type", "").upper() not in ["AGENT"]:
                # 补充location_id信息
                if "location_id" not in node_data:
                    edges = self.world_state.graph.get_incoming_edges(node_id)
                    if edges:
                        parent_id, edge_data = next(iter(edges.items()))
                        node_data["location_id"] = f"{edge_data.get('type', 'in')}:{parent_id}"
                
                scene_data["objects"].append(node_data)
        
        # 确保所有物体的位置引用都是有效的
        location_errors = []
        object_ids = set(obj.get("id") for obj in scene_data["objects"])
        room_ids = set(room.get("id") for room in scene_data["rooms"])
        all_valid_ids = object_ids.union(room_ids)

        # 检查每个物体的location_id引用
        for obj in scene_data["objects"]:
            location_id = obj.get("location_id", "")
            if location_id and ":" in location_id:
                _, target_id = SceneValidator._parse_location_id(location_id)
                if target_id not in all_valid_ids:
                    location_errors.append(f"物体 {obj.get('id')} 的位置 {location_id} 不存在")

        # 结合所有验证结果
        _, validator_errors = SceneValidator.validate_scene(scene_data)

        # 合并所有错误
        all_errors = validator_errors + location_errors
        
        # 去重
        unique_errors = []
        for error in all_errors:
            if error not in unique_errors:
                unique_errors.append(error)
        
        return len(unique_errors) == 0, unique_errors
    
    def load_agents(self, agents_config: List[Dict[str, Any]]) -> bool:
        """
        加载智能体配置
        
        Args:
            agents_config: 智能体配置列表
            
        Returns:
            bool: 是否成功加载
        """
        if not self.agent_manager:
            print("智能体管理器未初始化")
            return False
        
        try:
            # 获取所有房间ID
            room_ids = list(self.world_state.graph.room_ids)
            if not room_ids:
                print("环境中没有房间")
                return False
            
            # 默认使用第一个房间
            default_room = sorted(room_ids)[0]
            
            # 清空现有智能体（确保不会有重复）
            self._remove_existing_agents()
            
            # 加载每个智能体
            for i, agent_config in enumerate(agents_config):
                # 确保有名称和位置
                if "name" not in agent_config:
                    agent_config["name"] = f"智能体{i+1}号"
                
                # 智能体ID处理：如果未提供，则根据序号生成
                if "id" not in agent_config:
                    agent_config["id"] = f"agent_{i+1}"
                
                # 确保有位置信息
                if "location_id" not in agent_config:
                    agent_config["location_id"] = default_room
                
                # 添加智能体
                agent_id = self.agent_manager.add_agent(agent_config)
                if not agent_id:
                    print(f"添加智能体失败: {agent_config.get('name')}")
                    continue
            
            return True
        except Exception as e:
            print(f"加载智能体失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _remove_existing_agents(self):
        """
        移除所有现有智能体
        """
        if not self.agent_manager:
            return
        
        # 获取所有智能体ID
        agent_ids = list(self.agent_manager.get_all_agents().keys())
        
        # 移除每个智能体
        for agent_id in agent_ids:
            # 从世界状态中移除
            if agent_id in self.world_state.agents:
                # 先获取位置，移除边关系
                agent = self.agent_manager.get_agent(agent_id)
                if agent and agent.location_id:
                    try:
                        self.world_state.graph.remove_edge(agent.location_id, agent_id)
                    except:
                        pass  # 忽略可能的错误
                
                # 从世界状态中删除
                del self.world_state.agents[agent_id]
                
                # 从图中删除节点
                try:
                    self.world_state.graph.remove_node(agent_id)
                except:
                    pass  # 忽略可能的错误
        
        # 清空智能体管理器中的智能体
        self.agent_manager.agents.clear()
    
    def process_command(self, agent_id: str, command: str):
        """
        处理智能体的命令
        
        Args:
            agent_id: 智能体ID
            command: 命令字符串
            
        Returns:
            Tuple: (执行状态, 反馈消息, 结果数据)
        """
        if not self.action_handler:
            print("模拟器未初始化")
            return None
        
        return self.action_handler.process_command(agent_id, command)
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        获取智能体信息
        
        Args:
            agent_id: 智能体ID
            
        Returns:
            Dict: 智能体信息字典
        """
        if not self.agent_manager:
            return None
        
        agent = self.agent_manager.get_agent(agent_id)
        if not agent:
            return None
        
        return agent.to_dict()

    def get_visualization_status(self) -> Dict[str, Any]:
        """
        获取可视化系统状态

        Returns:
            Dict: 可视化系统状态信息
        """
        if self.visualization_manager:
            return self.visualization_manager.get_status()
        else:
            return {
                'enabled': False,
                'running': False,
                'server_url': None,
                'message': '可视化系统未初始化'
            }

    def get_visualization_url(self) -> Optional[str]:
        """
        获取可视化Web界面URL

        Returns:
            str: 可视化URL，如果未启用则返回None
        """
        if self.visualization_manager:
            return self.visualization_manager.get_server_url()
        return None

    def stop_visualization(self):
        """停止可视化系统"""
        if self.visualization_manager:
            self.visualization_manager.stop()

    def restart_visualization(self) -> bool:
        """
        重启可视化系统

        Returns:
            bool: 是否成功重启
        """
        if self.visualization_manager:
            self.visualization_manager.stop()
            return self.visualization_manager.start()
        return False

    def __del__(self):
        """析构函数 - 确保可视化系统正确关闭"""
        try:
            if self.visualization_manager:
                self.visualization_manager.stop()
        except:
            pass  # 忽略析构时的错误
    
    def get_object_info(self, object_id: str) -> Optional[Dict[str, Any]]:
        """
        获取物体信息
        
        Args:
            object_id: 物体ID
            
        Returns:
            Dict: 物体信息字典
        """
        if not self.env_manager:
            return None
        
        obj = self.env_manager.get_object_by_id(object_id)
        return obj
    
    def get_room_info(self, room_id: str) -> Optional[Dict[str, Any]]:
        """
        获取房间信息
        
        Args:
            room_id: 房间ID
            
        Returns:
            Dict: 房间信息字典
        """
        if not self.env_manager:
            return None
        
        room = self.env_manager.get_room_by_id(room_id)
        return room
    
    def get_task_info(self) -> Optional[Dict[str, Any]]:
        """
        获取当前任务信息

        Returns:
            Dict: 任务信息字典
        """
        return self.task_config

    def _register_scene_specific_actions(self):
        """
        根据场景abilities注册特定的动作
        """
        if not self.action_handler or not self.scene_abilities:
            return

        try:
            from action.actions.attribute_actions import AttributeAction
            from action.actions.corporate_attribute_actions import CorporateAttributeAction

            # 注册场景特定的属性动作
            AttributeAction.register_task_specific_actions(
                self.action_handler.action_manager,
                self.scene_abilities
            )
            CorporateAttributeAction.register_task_specific_actions(
                self.action_handler.action_manager,
                self.scene_abilities
            )

            print(f"已根据场景abilities注册动作: {self.scene_abilities}")

        except Exception as e:
            print(f"注册场景特定动作失败: {e}")
            import traceback
            traceback.print_exc()

    def _create_task_verifier(self, task_data: Dict[str, Any]):
        """
        创建任务验证器

        Args:
            task_data: 任务数据

        Returns:
            TaskVerifier: 任务验证器实例
        """
        try:
            from utils.task_verifier import TaskVerifier

            verifier = TaskVerifier(task_data, self.env_manager, self.config)
            print(f"已创建任务验证器，包含 {len(task_data.get('tasks', []))} 个任务")
            return verifier

        except Exception as e:
            print(f"创建任务验证器失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def update_scene_abilities(self, new_abilities: List[str]):
        """
        更新场景能力并重新注册相关动作

        Args:
            new_abilities: 新的能力列表
        """
        self.scene_abilities = new_abilities
        if self.action_handler:
            self._register_scene_specific_actions()

    def get_task_verification_status(self) -> Optional[Dict[str, Any]]:
        """
        获取任务验证状态

        Returns:
            Optional[Dict[str, Any]]: 验证状态，如果未启用验证则返回None
        """
        if not self.task_verifier:
            return None

        try:
            summary = self.task_verifier.get_completion_summary()
            completion_list = self.task_verifier.get_subtask_completion_list()

            return {
                'summary': summary,
                'completion_list': completion_list,
                'enabled': True
            }
        except Exception as e:
            print(f"获取任务验证状态失败: {e}")
            return None

    def set_task_data(self, task_data: Dict[str, Any]):
        """
        设置任务数据并创建验证器

        Args:
            task_data: 任务数据，来自task.json文件
        """
        self.task_config = task_data
        if self.env_manager:
            self.task_verifier = self._create_task_verifier(task_data)

    def get_agent_supported_actions_description(self, agent_ids: List[str]) -> str:
        """
        获取智能体支持的所有动作的字符串描述

        Args:
            agent_ids: 智能体ID列表，支持单个或多个智能体

        Returns:
            str: 包含所有支持动作的描述字符串（英文）
        """
        if not self.action_handler:
            return "Action handler not initialized"

        return self.action_handler.get_agent_supported_actions_description(agent_ids)