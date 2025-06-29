from typing import Dict, List, Optional, Any
import logging

from llm import BaseLLM

logger = logging.getLogger(__name__)

class Planner:
    """
    任务规划组件，负责分解任务和创建执行计划
    """
    
    def __init__(self, llm: BaseLLM):
        """
        初始化规划器
        
        Args:
            llm: LLM实例，用于生成规划
        """
        self.llm = llm
        self.plan = []
        self.current_step = 0
        self.chat_history = []
        
        # 系统提示词
        self.system_prompt = (
            "你是一个高效的任务规划系统。你需要将复杂任务分解为可执行的步骤，"
            "并考虑多个智能体之间的协作。每个步骤应该清晰具体，包括执行者、"
            "动作和预期结果。"
        )
    
    def create_plan(self, task: str, agents: List[str], environment_info: str) -> List[Dict[str, Any]]:
        """
        为给定任务创建执行计划
        
        Args:
            task: 任务描述
            agents: 可用的智能体ID列表
            environment_info: 环境信息描述
            
        Returns:
            List[Dict[str, Any]]: 执行计划，每一步包含执行者、动作等
        """
        prompt = f"""
        任务: {task}
        
        可用智能体: {', '.join(agents)}
        
        环境信息:
        {environment_info}
        
        请为这个任务创建一个详细的执行计划，考虑多个智能体之间的协作。
        对于每一步，指明哪个智能体应该执行什么动作，以及预期的结果。
        
        请使用以下格式:
        步骤1: [智能体ID] [动作] -> [预期结果]
        步骤2: [智能体ID] [动作] -> [预期结果]
        ...
        """
        
        self.chat_history.append({"role": "user", "content": prompt})
        
        try:
            response = self.llm.generate_chat(self.chat_history, system_message=self.system_prompt)
            self.chat_history.append({"role": "assistant", "content": response})
            
            # 解析计划
            plan = self._parse_plan(response, agents)
            self.plan = plan
            self.current_step = 0
            
            return plan
            
        except Exception as e:
            logger.exception(f"创建计划时出错: {e}")
            return []
    
    def _parse_plan(self, response: str, valid_agents: List[str]) -> List[Dict[str, Any]]:
        """
        从LLM响应中解析计划
        
        Args:
            response: LLM响应文本
            valid_agents: 有效的智能体ID列表
            
        Returns:
            List[Dict[str, Any]]: 解析后的计划
        """
        plan = []
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or not any(line.lower().startswith(f"步骤{i}" if i < 10 else f"步骤 {i}") 
                                  for i in range(1, 100)):
                continue
            
            # 移除步骤前缀
            parts = line.split(':', 1)
            if len(parts) < 2:
                continue
                
            step_content = parts[1].strip()
            
            # 尝试解析"[agent_id] [action] -> [expected_result]"格式
            action_parts = step_content.split('->')
            action = action_parts[0].strip() if len(action_parts) > 0 else ""
            expected = action_parts[1].strip() if len(action_parts) > 1 else ""
            
            # 从action中提取agent_id
            agent_id = None
            for valid_id in valid_agents:
                if action.startswith(valid_id):
                    agent_id = valid_id
                    action = action[len(valid_id):].strip()
                    break
            
            if agent_id:
                plan.append({
                    "agent_id": agent_id,
                    "action": action,
                    "expected_result": expected
                })
        
        return plan
    
    def get_next_step(self) -> Optional[Dict[str, Any]]:
        """
        获取计划中的下一步
        
        Returns:
            Optional[Dict[str, Any]]: 下一步，如果计划已完成则返回None
        """
        if not self.plan or self.current_step >= len(self.plan):
            return None
            
        step = self.plan[self.current_step]
        self.current_step += 1
        return step
    
    def reset(self) -> None:
        """
        重置规划器状态
        """
        self.plan = []
        self.current_step = 0
        self.chat_history = []
    
    def get_current_plan(self) -> List[Dict[str, Any]]:
        """
        获取当前计划
        
        Returns:
            List[Dict[str, Any]]: 当前计划
        """
        return self.plan.copy() 