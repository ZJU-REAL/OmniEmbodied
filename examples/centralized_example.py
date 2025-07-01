#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中心化双智能体示例 - 展示如何使用中心化协调器控制两个智能体协作完成任务
"""

import os
import sys
import time
from typing import Dict, List, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_manager import ConfigManager
from utils.prompt_manager import PromptManager
from utils.simulator_bridge import SimulatorBridge
from llm.llm_factory import create_llm_from_config
from common_utils import setup_example_environment, get_task_description, check_apple_task_completion, log_agent_status

class DualAgentCoordinator:
    """双智能体协调器"""

    def __init__(self, bridge: SimulatorBridge, config: Dict[str, Any]):
        self.bridge = bridge
        self.config = config

        # 创建LLM实例
        config_manager = ConfigManager()
        llm_config_name = config.get('llm_config', 'llm_config')
        self.llm_config = config_manager.get_config(llm_config_name)
        self.llm = create_llm_from_config(self.llm_config)

        # 创建提示词管理器
        self.prompt_manager = PromptManager("prompts_config")

        # 智能体管理
        self.task_description = ""
        self.chat_history = []
        max_chat_history = config.get('max_chat_history', 10)
        # -1 表示不限制历史长度
        self.max_chat_history = None if max_chat_history == -1 else max_chat_history

        # 系统提示词
        self.system_prompt = self.prompt_manager.get_prompt_template(
            "centralized",
            "system_prompt",
            "你是一个协调两个智能体完成任务的中央控制器。"
        )

    def set_task(self, task_description: str):
        """设置任务描述"""
        self.task_description = task_description

    def get_agents_status(self, agent_ids: List[str]) -> str:
        """获取智能体状态描述"""
        status_lines = []
        for agent_id in agent_ids:
            agent_info = self.bridge.get_agent_info(agent_id)
            if agent_info:
                location = agent_info.get('location_id', '未知')
                inventory = agent_info.get('inventory', [])
                inventory_str = ', '.join(inventory) if inventory else '无'
                status_lines.append(f"- {agent_id}: 位置={location}, 库存={inventory_str}")
            else:
                status_lines.append(f"- {agent_id}: 状态未知")
        return '\n'.join(status_lines)

    def build_prompt(self, agent_ids: List[str]) -> str:
        """构建协调提示词"""
        # 获取环境描述
        env_description = self.bridge.describe_environment_natural_language()

        # 获取智能体状态
        agents_status = self.get_agents_status(agent_ids)

        # 使用配置文件中的提示词模板
        template = self.prompt_manager.get_prompt_template(
            "centralized",
            "user_prompt"
        )

        # 格式化提示词
        prompt = template.format(
            task_description=self.task_description,
            environment_description=env_description,
            agents_status=agents_status,
            history_summary="无历史记录"
        )

        return prompt

    def parse_assignments(self, response: str, agent_ids: List[str]) -> Dict[str, str]:
        """解析LLM响应中的任务分配"""
        assignments = {}
        lines = response.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 寻找智能体ID和动作的模式
            for agent_id in agent_ids:
                if agent_id in line and ':' in line:
                    action_part = line.split(':', 1)[1].strip()
                    action = action_part.replace('动作：', '').replace('动作:', '').strip()
                    if action:
                        assignments[agent_id] = action
                        break

        # 如果解析失败，尝试备用解析方法
        if not assignments and len(agent_ids) == 2:
            action_lines = [line.strip() for line in lines if line.strip() and not line.startswith('思考')]
            if len(action_lines) >= 2:
                assignments[agent_ids[0]] = action_lines[0]
                assignments[agent_ids[1]] = action_lines[1]

        return assignments

    def coordinate_step(self, agent_ids: List[str]) -> Dict[str, Any]:
        """执行一步协调"""
        # 构建提示词
        prompt = self.build_prompt(agent_ids)

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

            # 解析响应
            assignments = self.parse_assignments(response, agent_ids)

            # 执行分配的动作
            results = {}
            for agent_id, action in assignments.items():
                status, message, _ = self.bridge.process_command(agent_id, action)
                results[agent_id] = {
                    "action": action,
                    "status": status.name if hasattr(status, "name") else str(status),
                    "message": message
                }

            return {"assignments": assignments, "results": results, "llm_response": response}

        except Exception as e:
            return {"error": f"协调失败: {e}"}

def main():
    """主函数"""
    try:
        # 使用公共函数设置环境
        logger, _, bridge, centralized_config = setup_example_environment(
            "中心化双智能体", "centralized_config"
        )

        # 创建协调器
        coordinator_config = centralized_config.get('coordinator', {})
        coordinator = DualAgentCoordinator(bridge, coordinator_config)

        # 设置任务
        task_description = get_task_description(bridge, logger)
        coordinator.set_task(task_description)

        # 智能体ID列表
        agent_ids = ['agent_1', 'agent_2']

    except RuntimeError as e:
        print(f"❌ 初始化失败: {e}")
        return

    # 执行协调循环
    max_steps = 10
    for step in range(1, max_steps + 1):
        logger.info(f"\n==== 步骤 {step} ====")

        # 显示当前状态
        log_agent_status(bridge, agent_ids, logger)

        # 执行协调步骤
        coord_result = coordinator.coordinate_step(agent_ids)

        if "error" in coord_result:
            logger.error(f"协调失败: {coord_result['error']}")
            continue

        # 显示分配结果
        assignments = coord_result.get("assignments", {})
        for agent_id, action in assignments.items():
            logger.info(f"分配给 {agent_id}: {action}")

        # 显示执行结果
        results = coord_result.get("results", {})
        for agent_id, result in results.items():
            logger.info(f"{agent_id}: {result['status']} - {result['message']}")

        # 检查任务完成
        if check_apple_task_completion(bridge, agent_ids):
            logger.info("🎉 任务完成! (找到苹果)")
            break

        time.sleep(1)

    logger.info("中心化双智能体示例执行完成")

if __name__ == "__main__":
    main() 