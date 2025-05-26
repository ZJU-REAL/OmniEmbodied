from typing import Dict, List, Optional, Any, Tuple
import logging

from embodied_simulator import SimulationEngine
from embodied_simulator.core import ActionStatus

from ...core.base_agent import BaseAgent
from ...llm import BaseLLM, create_llm_from_config
from ...config import ConfigManager
from ...utils.prompt_manager import PromptManager
from .worker_agent import WorkerAgent
from .planner import Planner

logger = logging.getLogger(__name__)

class Coordinator(BaseAgent):
    """
    中心化协调器，使用单个LLM控制多个执行智能体
    """
    
    def __init__(self, simulator: SimulationEngine, agent_id: str, config: Optional[Dict[str, Any]] = None, 
                 llm_config_name: str = 'llm_config'):
        """
        初始化协调器
        
        Args:
            simulator: 模拟引擎实例
            agent_id: 协调器ID
            config: 配置字典，可选
            llm_config_name: LLM配置名称，可选
        """
        super().__init__(simulator, agent_id, config)
        
        # 加载LLM配置
        config_manager = ConfigManager()
        self.llm_config = config_manager.get_config(llm_config_name)
        
        # 创建LLM实例
        self.llm = create_llm_from_config(self.llm_config)
        
        # 创建规划器
        self.planner = Planner(self.llm)
        
        # 工作智能体列表
        self.workers: Dict[str, WorkerAgent] = {}
        
        # 创建提示词管理器
        self.prompt_manager = PromptManager("prompts_config")
        
        # 模式名称
        self.mode = "centralized"
        
        # 系统提示词
        self.system_prompt = self.prompt_manager.get_prompt_template(
            self.mode, 
            "coordinator_system",
            "你是一个协调多个智能体完成任务的中央控制系统。你需要分析当前环境状态，为每个智能体分配适当的任务。"
        )
        
        # 对话历史
        self.chat_history = []
        self.max_chat_history = self.config.get('max_chat_history', 10)
        
        # 任务描述
        self.task_description = self.config.get('task_description', "协作完成任务")
    
    def add_worker(self, worker_agent: WorkerAgent) -> None:
        """
        添加工作智能体
        
        Args:
            worker_agent: 工作智能体实例
        """
        self.workers[worker_agent.agent_id] = worker_agent
    
    def remove_worker(self, agent_id: str) -> bool:
        """
        移除工作智能体
        
        Args:
            agent_id: 智能体ID
            
        Returns:
            bool: 是否成功移除
        """
        if agent_id in self.workers:
            del self.workers[agent_id]
            return True
        return False
    
    def get_workers(self) -> Dict[str, WorkerAgent]:
        """
        获取所有工作智能体
        
        Returns:
            Dict[str, WorkerAgent]: 工作智能体字典
        """
        return self.workers.copy()
    
    def set_task(self, task_description: str) -> None:
        """
        设置任务描述
        
        Args:
            task_description: 任务描述文本
        """
        self.task_description = task_description
        # 重置规划器
        self.planner.reset()
    
    def _parse_prompt(self) -> str:
        """
        解析并构建提示词
        
        Returns:
            str: 格式化后的提示词
        """
        # 获取智能体状态
        agents_status = []
        for agent_id, worker in self.workers.items():
            state = worker.get_state()
            location = state.get('location', {}).get('name', 'unknown')
            inventory = ", ".join([item.get('name', item.get('id', 'unknown')) 
                                 for item in state.get('inventory', [])]) or "空"
            
            # 添加可交互物体信息
            near_objects = ""
            near_objects_list = state.get('near_objects', [])
            if near_objects_list:
                near_objects_str = ", ".join([item.get('name', item.get('id', 'unknown')) 
                                           for item in near_objects_list])
                near_objects = f", 可交互物体={near_objects_str}"
            
            # 格式化智能体状态
            agent_status = self.prompt_manager.get_formatted_prompt(
                self.mode,
                "agent_status_template",
                f"- {agent_id}: 位置={location}, 库存={inventory}{near_objects}",
                agent_id=agent_id,
                location=location,
                inventory=inventory,
                near_objects=near_objects
            )
            agents_status.append(agent_status)
        
        # 获取最近行动
        recent_actions = []
        for agent_id, worker in self.workers.items():
            history = worker.get_history()[-3:] if worker.get_history() else []
            if history:
                action_entries = []
                for entry in history:
                    action = entry.get('action', '')
                    result = entry.get('result', {})
                    status = result.get('status', '')
                    message = result.get('message', '')
                    
                    # 格式化行动条目
                    action_entry = self.prompt_manager.get_formatted_prompt(
                        self.mode,
                        "action_entry_template",
                        f"  * 动作: {action}, 结果: {status}, 消息: {message}",
                        action=action,
                        status=status,
                        message=message
                    )
                    action_entries.append(action_entry)
                
                # 格式化智能体行动
                agent_actions = self.prompt_manager.get_formatted_prompt(
                    self.mode,
                    "agent_actions_template",
                    f"- {agent_id}的最近行动:\n" + "\n".join(action_entries),
                    agent_id=agent_id,
                    action_entries="\n".join(action_entries)
                )
                recent_actions.append(agent_actions)
        
        # 准备智能体输出格式
        agents_format = "\n".join([f"{agent_id}: <行动指令>" for agent_id in self.workers.keys()])
        
        # 使用提示词管理器格式化完整提示词
        return self.prompt_manager.get_formatted_prompt(
            self.mode,
            "coordinator_template",
            default_value="当前任务: {task_description}\n\n请为每个智能体规划下一步行动。",
            task_description=self.task_description,
            agents_status="\n".join(agents_status),
            recent_actions="\n".join(recent_actions),
            agents_format=agents_format
        )
    
    def decide_action(self) -> str:
        """
        协调器不直接执行动作，而是为工作智能体分配任务
        
        Returns:
            str: 协调状态描述
        """
        if not self.workers:
            return "NO_WORKERS"
        
        # 构建提示词
        prompt = self._parse_prompt()
        
        # 记录到对话历史
        self.chat_history.append({"role": "user", "content": prompt})
        
        # 控制对话历史长度
        if len(self.chat_history) > self.max_chat_history * 2:
            self.chat_history = self.chat_history[-self.max_chat_history*2:]
        
        try:
            # 调用LLM生成响应
            response = self.llm.generate_chat(self.chat_history, system_message=self.system_prompt)
            
            # 记录LLM响应到对话历史
            self.chat_history.append({"role": "assistant", "content": response})
            
            # 解析响应，为各工作智能体分配任务
            assignments = self._parse_assignments(response)
            self._assign_tasks(assignments)
            
            return "COORDINATION_COMPLETE"
            
        except Exception as e:
            logger.exception(f"协调器决策时出错: {e}")
            return "COORDINATION_ERROR"
    
    def _parse_assignments(self, response: str) -> Dict[str, str]:
        """
        从LLM响应中解析任务分配
        
        Args:
            response: LLM响应文本
            
        Returns:
            Dict[str, str]: 智能体ID到任务指令的映射
        """
        assignments = {}
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 尝试解析"agent_id: action"格式
            parts = line.split(':', 1)
            if len(parts) == 2:
                agent_id = parts[0].strip()
                action = parts[1].strip()
                
                if agent_id in self.workers:
                    assignments[agent_id] = action
        
        return assignments
    
    def _assign_tasks(self, assignments: Dict[str, str]) -> None:
        """
        将任务分配给工作智能体
        
        Args:
            assignments: 智能体ID到任务指令的映射
        """
        for agent_id, action in assignments.items():
            if agent_id in self.workers:
                worker = self.workers[agent_id]
                worker.set_next_action(action)
    
    def step(self) -> Tuple[ActionStatus, str, Optional[Dict[str, Any]]]:
        """
        执行一步，包括决策和任务分配
        
        Returns:
            Tuple[ActionStatus, str, Optional[Dict[str, Any]]]: (执行状态, 反馈消息, 额外结果数据)
        """
        # 决策并分配任务
        result = self.decide_action()
        
        # 让所有工作智能体执行一步
        worker_results = {}
        for agent_id, worker in self.workers.items():
            status, message, data = worker.step()
            worker_results[agent_id] = {
                "status": status.name if hasattr(status, "name") else str(status),
                "message": message,
                "data": data
            }
        
        # 使用模拟状态枚举
        from enum import Enum
        class CoordinationStatus(Enum):
            SUCCESS = 1
            PARTIAL_SUCCESS = 2
            FAILURE = 3
        
        # 根据工作智能体结果确定总体状态
        success_count = sum(1 for r in worker_results.values() 
                          if r["status"] in ["SUCCESS", "COMPLETE", "OK"])
        
        if success_count == len(self.workers):
            status = CoordinationStatus.SUCCESS
            message = "所有智能体执行成功"
        elif success_count > 0:
            status = CoordinationStatus.PARTIAL_SUCCESS
            message = f"{success_count}/{len(self.workers)}个智能体执行成功"
        else:
            status = CoordinationStatus.FAILURE
            message = "所有智能体执行失败"
        
        # 记录结果
        self.history.append({
            "action": "COORDINATE",
            "result": {
                "status": status.name,
                "message": message,
            }
        })
        
        return status, message, {"worker_results": worker_results} 