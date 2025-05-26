#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
去中心化多智能体示例 - 展示如何使用自主智能体协作完成任务
"""

import os
import sys
import time
import logging
from typing import Dict, List, Any

# 添加项目根目录到路径，便于直接运行
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from embodied_framework import (
    AutonomousAgent, CommunicationManager, Negotiator, 
    ConfigManager, setup_logger, SimulatorBridge
)
from embodied_framework.modes.decentralized.negotiation import NegotiationType

# 设置日志
logger = setup_logger("decentralized_example", logging.INFO)

def main():
    # 步骤1: 加载配置
    config_manager = ConfigManager()
    llm_config = config_manager.get_config("llm_config")
    decentralized_config = config_manager.get_config("decentralized_config")
    
    # 显示配置信息
    logger.info("LLM配置: %s", llm_config.get("provider", "未指定"))
    logger.info("协作模式: %s", decentralized_config.get("collaboration", {}).get("form_dynamic_teams", "未指定"))
    
    # 步骤2: 初始化模拟器桥接
    task_file = os.path.join("data", "default", "default_task.json")
    if not os.path.exists(task_file):
        logger.error("任务文件不存在: %s", task_file)
        sys.exit(1)
        
    logger.info("初始化模拟器桥接...")
    bridge = SimulatorBridge()
    success = bridge.initialize_with_task(task_file)
    if not success:
        logger.error("模拟器初始化失败")
        sys.exit(1)
    
    # 输出任务信息
    task_description = bridge.get_task_description()
    logger.info("任务: %s", task_description)
    
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
    
    # 步骤5: 设置任务 (如果任务文件中已包含任务描述，此步可选)
    # 为每个智能体设置任务，但可能有不同的解释
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
            status, message, _ = agent.step()
            
            # 打印结果
            logger.info("智能体 %s 结果: %s - %s", agent_id, status, message)
        
        # 检查任务是否完成
        task_complete = False
        for agent_id, agent_data in agents.items():
            agent = agent_data["agent"]
            state = agent.get_state()
            inventory = [item.get("id") for item in state.get("inventory", [])]
            if "apple_1" in inventory:
                logger.info("\n任务成功完成！智能体 %s 已经找到并取出了苹果。", agent_id)
                task_complete = True
                break
                
        if task_complete:
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