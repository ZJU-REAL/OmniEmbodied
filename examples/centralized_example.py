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
from embodied_framework.utils import create_env_description_config
from embodied_simulator.core import ActionStatus

def main():
    # 根据配置设置日志级别
    config_manager = ConfigManager()
    centralized_config = config_manager.get_config("centralized_config")
    
    log_level = logging.INFO
    logging_config = centralized_config.get('logging', {})
    level_str = logging_config.get('level', 'info').lower()
    
    if level_str == 'debug':
        log_level = logging.DEBUG
    elif level_str == 'info':
        log_level = logging.INFO
    elif level_str == 'warning':
        log_level = logging.WARNING
    elif level_str == 'error':
        log_level = logging.ERROR
    
    # 设置日志
    logger = setup_logger("centralized_example", log_level, propagate_to_root=True)
    logger.info("日志级别设置为: %s", level_str.upper())
    
    # 步骤1: 加载配置
    llm_config = config_manager.get_config("llm_config")
    
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
    
    # 使用配置文件中定义的环境描述设置
    coordinator_env_config = centralized_config.get('coordinator', {}).get('env_description', {})
    coordinator_detail_level = coordinator_env_config.get('detail_level', 'full')
    
    # 记录实际使用的环境描述配置
    logger.info("协调器使用环境描述级别: %s", coordinator_detail_level)
    
    # 步骤3: 创建协调器
    coordinator_id = "coordinator"
    logger.info("创建中央协调器...")
    coordinator = Coordinator(bridge, coordinator_id, centralized_config.get("coordinator"))
    
    # 测试环境描述
    test_env_desc = bridge.describe_environment_natural_language(
        sim_config={
            'nlp_show_object_properties': coordinator_env_config.get('show_object_properties', True),
            'nlp_only_show_discovered': coordinator_env_config.get('only_show_discovered', False),
            'nlp_detail_level': coordinator_detail_level
        }
    )
    
    # 根据日志级别显示不同长度的环境描述
    if log_level <= logging.DEBUG:
        logger.info("=== 环境描述示例 ===\n%s\n===============", test_env_desc)
    else:
        logger.info("=== 环境描述示例 ===\n%s\n===============", test_env_desc[:300] + "...")
    
    # 步骤4: 创建工作智能体
    worker_ids = ["worker_1", "worker_2"]
    worker_agents = {}
    
    worker_env_config = centralized_config.get('worker_agents', {}).get('env_description', {})
    worker_detail_level = worker_env_config.get('detail_level', 'room')
    logger.info("工作智能体使用环境描述级别: %s", worker_detail_level)
    
    for worker_id in worker_ids:
        logger.info("创建工作智能体: %s", worker_id)
        worker = WorkerAgent(bridge, worker_id, centralized_config.get("worker_agents"))
        worker_agents[worker_id] = worker
        # 将工作智能体添加到协调器
        coordinator.add_worker(worker)
    
    # 步骤5: 运行协调系统
    logger.info("开始执行任务...")
    max_steps = 20
    for step in range(1, max_steps + 1):
        logger.info("\n==== 步骤 %d ====", step)
        
        if log_level <= logging.DEBUG:
            # 在调试模式下，获取并输出当前协调器状态
            workers_status = coordinator.get_workers_status()
            logger.debug("工作智能体状态: %s", workers_status)
        
        # 执行一步协调
        status, message, results = coordinator.step()
        
        # 打印结果
        logger.info("协调结果: %s", message)
        
        # 在调试模式下显示详细的结果数据
        if log_level <= logging.DEBUG and results:
            import json
            logger.debug("详细结果: %s", json.dumps(results, ensure_ascii=False, indent=2))
        
        # 打印工作智能体的执行结果
        if results and "worker_results" in results:
            for agent_id, result in results["worker_results"].items():
                logger.info("智能体 %s: %s - %s", agent_id, result.get("status"), result.get("message"))
                
                # 处理EXPLORE命令返回PARTIAL的情况
                worker = worker_agents.get(agent_id)
                if worker and worker.history and len(worker.history) > 0:
                    last_action = worker.history[-1].get('action', '')
                    last_status = result.get("status")
                    
                    if last_action.startswith("EXPLORE") and last_status == "PARTIAL":
                        logger.info("智能体 %s 探索未完成，继续探索...", agent_id)
                        
                        # 最多尝试5次探索
                        max_explore_attempts = 5
                        for attempt in range(1, max_explore_attempts + 1):
                            # 继续执行相同的EXPLORE命令
                            explore_status, explore_message, explore_result = bridge.process_command(agent_id, last_action)
                            
                            # 记录到历史
                            worker.record_action(last_action, {"status": explore_status, "message": explore_message, "result": explore_result})
                            
                            logger.info("智能体 %s 额外探索 #%d 结果: %s", agent_id, attempt, explore_message)
                            
                            # 如果不再是PARTIAL状态，就退出循环
                            if explore_status != ActionStatus.PARTIAL:
                                break
                            
                            # 暂停一下，避免请求过快
                            time.sleep(0.5)
                        else:
                            logger.info("智能体 %s 达到最大探索尝试次数，继续下一步操作", agent_id)
        
        # 检查任务是否完成
        task_complete = check_task_completion(worker_agents)
        if task_complete:
            logger.info("\n任务成功完成！")
            break
            
        # 暂停一下，便于观察
        time.sleep(1)
    else:
        logger.info("\n已达到最大步骤数 (%d)，任务未完成。", max_steps)
    
    # 步骤6: 输出执行历史
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

def check_task_completion(worker_agents: Dict[str, WorkerAgent]) -> bool:
    """
    检查任务是否完成的自定义逻辑
    
    Args:
        worker_agents: 工作智能体字典
        
    Returns:
        bool: 任务是否完成
    """
    # 检查任何智能体是否完成了任务
    for worker_id, worker in worker_agents.items():
        state = worker.get_state()
        inventory = [item.get("id") for item in state.get("inventory", [])]
        if "apple_1" in inventory:
            return True
    
    return False

if __name__ == "__main__":
    main() 