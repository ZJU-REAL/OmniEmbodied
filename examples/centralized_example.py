#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中心化多智能体示例 - 展示如何使用中心化控制器协调多个智能体完成任务
"""

import os
import sys
import time
import logging
from typing import Dict, List, Any

# 添加项目根目录到路径，便于直接运行
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from embodied_framework import Coordinator, WorkerAgent, ConfigManager, setup_logger, SimulatorBridge

# 设置日志
logger = setup_logger("centralized_example", logging.INFO)

def main():
    # 步骤1: 加载配置
    config_manager = ConfigManager()
    llm_config = config_manager.get_config("llm_config")
    centralized_config = config_manager.get_config("centralized_config")
    
    # 显示配置信息
    logger.info("LLM配置: %s", llm_config.get("provider", "未指定"))
    logger.info("协调模式: %s", centralized_config.get("collaboration", {}).get("mode", "未指定"))
    
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
    
    # 步骤3: 创建协调器
    coordinator_id = "coordinator"
    logger.info("创建中央协调器...")
    coordinator = Coordinator(bridge, coordinator_id, centralized_config.get("coordinator"))
    
    # 步骤4: 创建工作智能体
    worker_ids = ["worker_1", "worker_2"]
    worker_agents = {}
    
    for worker_id in worker_ids:
        logger.info("创建工作智能体: %s", worker_id)
        worker = WorkerAgent(bridge, worker_id, centralized_config.get("worker_agents"))
        worker_agents[worker_id] = worker
        # 将工作智能体添加到协调器
        coordinator.add_worker(worker)
    
    # 步骤5: 设置任务 (如果任务文件中已包含任务描述，此步可选)
    # task = "探索房子，找到厨房，一个智能体打开冰箱，另一个智能体取出苹果"
    # coordinator.set_task(task)
    # logger.info("设置任务: %s", task)
    
    # 步骤6: 运行协调系统
    logger.info("开始执行任务...")
    max_steps = 20
    for step in range(1, max_steps + 1):
        logger.info("\n==== 步骤 %d ====", step)
        
        # 执行一步协调
        status, message, results = coordinator.step()
        
        # 打印结果
        logger.info("协调结果: %s", message)
        if results and "worker_results" in results:
            for agent_id, result in results["worker_results"].items():
                logger.info("智能体 %s: %s - %s", agent_id, result.get("status"), result.get("message"))
        
        # 检查任务是否完成
        task_complete = False
        for worker_id, worker in worker_agents.items():
            state = worker.get_state()
            inventory = [item.get("id") for item in state.get("inventory", [])]
            if "apple_1" in inventory:
                logger.info("\n任务成功完成！智能体 %s 已经找到并取出了苹果。", worker_id)
                task_complete = True
                break
                
        if task_complete:
            break
            
        # 暂停一下，便于观察
        time.sleep(1)
    else:
        logger.info("\n已达到最大步骤数 (%d)，任务未完成。", max_steps)
    
    # 步骤7: 输出执行历史
    logger.info("\n==== 协调器执行历史 ====")
    for i, entry in enumerate(coordinator.get_history()):
        action = entry.get('action', '')
        result = entry.get('result', {})
        status = result.get('status', '')
        message = result.get('message', '')
        logger.info("%d. 动作: %s, 状态: %s, 消息: %s", i+1, action, status, message)
    
    # 输出每个工作智能体的历史
    for worker_id, worker in worker_agents.items():
        logger.info("\n==== 智能体 %s 执行历史 ====", worker_id)
        for i, entry in enumerate(worker.get_history()):
            action = entry.get('action', '')
            result = entry.get('result', {})
            status = result.get('status', '')
            message = result.get('message', '')
            logger.info("%d. 动作: %s, 状态: %s, 消息: %s", i+1, action, status, message)

if __name__ == "__main__":
    main() 