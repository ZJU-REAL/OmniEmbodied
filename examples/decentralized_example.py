#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
去中心化多智能体示例 - 展示如何使用自主智能体协作完成任务
"""

import os
import sys
import time
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modes.decentralized import AutonomousAgent, CommunicationManager, Negotiator
from utils.embodied_simulator import ActionStatus
from common_utils import setup_example_environment, get_task_description, check_apple_task_completion

def main():
    try:
        # 使用公共函数设置环境
        logger, config_manager, bridge, decentralized_config = setup_example_environment(
            "去中心化多智能体", "decentralized_config"
        )

        # 加载LLM配置
        llm_config = config_manager.get_config("llm_config")
        logger.info("LLM配置: %s", llm_config.get("api", {}).get("provider", "未指定"))

        # 获取任务描述
        task_description = get_task_description(bridge, logger)

    except RuntimeError as e:
        print(f"❌ 初始化失败: {e}")
        sys.exit(1)
    
    # 步骤3: 创建通信管理器
    logger.info("创建通信管理器...")
    comm_manager = CommunicationManager()
    comm_manager.start_processing()
    
    # 步骤4: 创建自主智能体
    agent_configs = {
        "explorer": decentralized_config["agent_personalities"]["explorer"],
        "operator": decentralized_config["agent_personalities"]["operator"]
    }

    agents = {}
    for agent_id, personality_config in agent_configs.items():
        # 合并基础配置和个性化配置
        agent_config = {**decentralized_config["autonomous_agent"], **personality_config}

        logger.info("创建自主智能体: %s (%s)", agent_id, personality_config.get("personality", ""))
        agent = AutonomousAgent(bridge, agent_id, agent_config,
                              llm_config_name="llm_config", comm_manager=comm_manager)

        # 注册到通信管理器
        comm_manager.register_agent(agent_id, agent, agent.receive_message)

        # 创建协商器
        negotiator = Negotiator(agent_id, comm_manager)

        # 保存引用
        agents[agent_id] = {
            "agent": agent,
            "negotiator": negotiator
        }
    
    # 步骤5: 设置任务 (根据角色设置不同任务)
    for agent_id, agent_data in agents.items():
        if agent_id == "explorer":
            agent_data["agent"].set_task("探索房子，找到厨房，并告知操作者")
        elif agent_id == "operator":
            agent_data["agent"].set_task("等待探索者找到厨房，然后打开冰箱，取出苹果")
    
    logger.info("设置多智能体任务")
    
    # 步骤6: 创建智能体组
    comm_manager.create_group("task_force", list(agents.keys()))
    
    # 步骤7: 运行智能体系统
    logger.info("开始执行任务...")
    max_steps = 25
    for step in range(1, max_steps + 1):
        logger.info("\n==== 步骤 %d ====", step)
        
        # 每个智能体执行一步
        for agent_id, agent_data in agents.items():
            agent = agent_data["agent"]
            logger.info("智能体 %s 执行中...", agent_id)

            # 执行一步
            status, message, result = agent.step()

            # 打印结果
            logger.info("智能体 %s 结果: %s - %s", agent_id, status, message)

        # 检查任务是否完成
        agent_ids = list(agents.keys())
        if check_apple_task_completion(bridge, agent_ids):
            logger.info("\n任务成功完成！")
            break
            
        # 暂停一下，便于观察
        time.sleep(1)
    else:
        logger.info("\n已达到最大步骤数 (%d)，任务未完成。", max_steps)
    
    # 步骤8: 输出每个智能体的执行历史
    for agent_id, agent_data in agents.items():
        agent = agent_data["agent"]
        logger.info("\n==== 智能体 %s 执行历史 ====", agent_id)
        for i, entry in enumerate(agent.get_history()):
            action = entry.get('action', '')
            result = entry.get('result', {})
            status = result.get('status', '')
            message = result.get('message', '')
            logger.info("%d. 动作: %s, 状态: %s, 消息: %s", i+1, action, status, message)
    
    # 步骤9: 停止通信管理器
    comm_manager.stop_processing()



if __name__ == "__main__":
    main() 