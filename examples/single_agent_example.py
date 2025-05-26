#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单智能体示例 - 展示如何使用基于大模型的智能体与模拟器交互
"""

import os
import sys
import time
import logging
from typing import Dict, Any

# 添加项目根目录到路径，便于直接运行
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from embodied_framework import LLMAgent, ConfigManager, setup_logger, SimulatorBridge

# 设置日志
logger = setup_logger("single_agent_example", logging.INFO)

def main():
    # 步骤1: 加载配置
    config_manager = ConfigManager()
    llm_config = config_manager.get_config("llm_config")
    agent_config = config_manager.get_config("single_agent_config")  # 使用新的配置文件名
    
    # 显示配置信息
    logger.info("LLM配置: %s", llm_config.get("provider", "未指定"))
    logger.info("智能体类型: %s", agent_config.get("agent_type", "未指定"))
    
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
    
    # 步骤3: 创建智能体
    agent_id = "agent_1"  # 使用默认的第一个智能体
    logger.info("创建LLM智能体...")
    agent = LLMAgent(bridge, agent_id, agent_config)
    
    # # 步骤4: 设置任务
    # task = "探索房子，找到厨房，打开冰箱，取出苹果"
    # agent.set_task(task)
    # logger.info("设置任务: %s", task)
    
    # 步骤5: 运行智能体
    logger.info("开始执行任务...")
    max_steps = 15
    for step in range(1, max_steps + 1):
        logger.info("\n==== 步骤 %d ====", step)
        
        # 执行一步
        status, message, _ = agent.step()
        
        # 打印结果
        logger.info("动作结果: %s", message)
        
        # 检查任务是否完成
        state = agent.get_state()
        inventory = [item.get("id") for item in state.get("inventory", [])]
        if "apple_1" in inventory:
            logger.info("\n任务成功完成！智能体已经找到并取出了苹果。")
            break
            
        # 暂停一下，便于观察
        time.sleep(1)
    else:
        logger.info("\n已达到最大步骤数 (%d)，任务未完成。", max_steps)
    
    # 步骤6: 输出执行历史
    logger.info("\n==== 执行历史 ====")
    for i, entry in enumerate(agent.get_history()):
        action = entry.get('action', '')
        result = entry.get('result', {})
        status = result.get('status', '')
        message = result.get('message', '')
        logger.info("%d. 动作: %s, 状态: %s, 消息: %s", i+1, action, status, message)

if __name__ == "__main__":
    main() 