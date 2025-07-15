from typing import Dict, List, Optional, Any, Tuple
import logging

from simulator.core.enums import ActionStatus
from simulator.core.engine import SimulationEngine

from core.base_agent import BaseAgent
from llm import BaseLLM, create_llm_from_config
from config import ConfigManager
from utils.prompt_manager import PromptManager
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
            "system_prompt",
            "你是一个协调多个智能体完成任务的中央控制系统。你需要分析当前环境状态，为每个智能体分配适当的任务。"
        )
        
        # 对话历史
        self.chat_history = []
        max_chat_history = self.config.get('max_chat_history', 10)
        # -1 表示不限制历史长度
        self.max_chat_history = None if max_chat_history == -1 else max_chat_history

        # 任务描述
        self.task_description = self.config.get('task_description', "协作完成任务")

        # 循环检测
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
        self.last_assignments = None
    
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
        # 准备智能体输出格式
        agents_format = "\n".join([f"{agent_id}: <行动指令>" for agent_id in self.workers.keys()])
        
        # 获取环境描述
        env_description = ""
        env_config = self.config.get('env_description', {})
        if not isinstance(env_config, dict):
            env_config = {}
            
        # 默认使用完整环境描述
        if self.bridge:
            try:
                detail_level = env_config.get('detail_level', 'full')
                
                # 协调器可以查看完整环境
                env_description = self.bridge.describe_environment_natural_language(
                    sim_config={
                        'nlp_show_object_properties': env_config.get('show_object_properties', False),
                        'nlp_only_show_discovered': env_config.get('only_show_discovered', False)
                    }
                )
            except Exception as e:
                logger.warning(f"获取环境描述时出错: {e}")
        
        # 格式化历史记录
        history_summary = ""
        if self.history:
            # 获取历史记录设置
            history_config = self.config.get('history', {}).get('coordinator', {})
            max_history_in_prompt = history_config.get('max_history_in_prompt', 50)  # 默认显示50条历史记录
            history_summary = self.prompt_manager.format_history(self.mode, self.history, max_entries=max_history_in_prompt)
        
        # 使用提示词管理器格式化完整提示词
        prompt = self.prompt_manager.get_formatted_prompt(
            self.mode,
            "user_prompt",
            task_description=self.task_description,
            agents_status=agents_format,
            environment_description=env_description,
            history_summary=history_summary
        )
        
        return prompt
    
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
        if self.max_chat_history is not None and len(self.chat_history) > self.max_chat_history * 2:
            self.chat_history = self.chat_history[-self.max_chat_history*2:]
        
        try:
            # 调用LLM生成响应
            response = self.llm.generate_chat(self.chat_history, system_message=self.system_prompt)

            # 记录LLM响应到对话历史
            self.chat_history.append({"role": "assistant", "content": response})

            # 解析响应，为各工作智能体分配任务
            assignments = self._parse_assignments(response)

            # 检查是否解析成功
            if not assignments:
                self.consecutive_failures += 1
                logger.warning(f"解析任务分配失败 (连续失败次数: {self.consecutive_failures})")

                if self.consecutive_failures >= self.max_consecutive_failures:
                    logger.error("连续解析失败次数过多，使用默认策略")
                    # 使用默认策略：让所有智能体探索
                    assignments = {agent_id: "EXPLORE" for agent_id in self.workers.keys()}
                    self.consecutive_failures = 0  # 重置计数器
            else:
                self.consecutive_failures = 0  # 重置失败计数器

            # 检查是否与上次分配相同（避免无限循环）
            if assignments == self.last_assignments:
                logger.warning("检测到重复的任务分配，添加随机性")
                # 为其中一个智能体分配不同的动作
                agent_ids = list(assignments.keys())
                if agent_ids:
                    import random
                    random_agent = random.choice(agent_ids)
                    alternative_actions = ["EXPLORE", "LOOK", "DONE"]
                    current_action = assignments[random_agent]
                    alternative_actions = [a for a in alternative_actions if a != current_action]
                    if alternative_actions:
                        assignments[random_agent] = random.choice(alternative_actions)
                        logger.debug(f"为 {random_agent} 分配替代动作: {assignments[random_agent]}")

            self.last_assignments = assignments.copy()
            self._assign_tasks(assignments)

            return "COORDINATION_COMPLETE"

        except Exception as e:
            logger.exception(f"协调器决策时出错: {e}")
            self.consecutive_failures += 1
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

        logger.debug(f"解析LLM响应: {response}")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 尝试解析"agent_X_动作：action"格式（中文格式）
            if '：' in line and ('agent_1_动作' in line or 'agent_2_动作' in line):
                parts = line.split('：', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    action = parts[1].strip()

                    # 映射到实际的智能体ID
                    if 'agent_1' in key:
                        agent_id = 'agent_1'
                    elif 'agent_2' in key:
                        agent_id = 'agent_2'
                    else:
                        continue

                    if agent_id in self.workers:
                        assignments[agent_id] = action
                        logger.debug(f"解析到任务分配: {agent_id} -> {action}")

            # 尝试解析"agent_X_动作: action"格式（英文冒号）
            elif ':' in line and ('agent_1_动作' in line or 'agent_2_动作' in line):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    action = parts[1].strip()

                    # 映射到实际的智能体ID
                    if 'agent_1' in key:
                        agent_id = 'agent_1'
                    elif 'agent_2' in key:
                        agent_id = 'agent_2'
                    else:
                        continue

                    if agent_id in self.workers:
                        assignments[agent_id] = action
                        logger.debug(f"解析到任务分配: {agent_id} -> {action}")

            # 尝试解析"agent_id: action"格式（兼容旧格式）
            elif ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    agent_id = parts[0].strip()
                    action = parts[1].strip()

                    if agent_id in self.workers:
                        assignments[agent_id] = action
                        logger.debug(f"解析到任务分配: {agent_id} -> {action}")

        logger.debug(f"最终解析结果: {assignments}")
        return assignments
    
    def _assign_tasks(self, assignments: Dict[str, str]) -> None:
        """
        将任务分配给工作智能体

        Args:
            assignments: 智能体ID到任务指令的映射
        """
        if not assignments:
            logger.warning("没有解析到任何任务分配，为所有智能体分配默认动作")
            # 如果没有解析到任务，给所有智能体分配探索动作
            for agent_id, worker in self.workers.items():
                worker.set_next_action("EXPLORE")
            return

        for agent_id, action in assignments.items():
            if agent_id in self.workers:
                worker = self.workers[agent_id]
                worker.set_next_action(action)
                logger.debug(f"为智能体 {agent_id} 分配任务: {action}")
            else:
                logger.warning(f"未找到智能体 {agent_id}")

        # 为没有分配任务的智能体分配默认动作
        for agent_id, worker in self.workers.items():
            if agent_id not in assignments:
                worker.set_next_action("EXPLORE")
                logger.debug(f"为智能体 {agent_id} 分配默认任务: EXPLORE")
    
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