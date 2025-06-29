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
from embodied_framework.utils import create_env_description_config, load_complete_scenario
from embodied_framework.modes.decentralized.negotiation import NegotiationType
from embodied_simulator.core import ActionStatus

def main():
    # 根据配置设置日志级别
    config_manager = ConfigManager()
    decentralized_config = config_manager.get_config("decentralized_config")
    
    log_level = logging.INFO
    logging_config = decentralized_config.get('logging', {})
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
    logger = setup_logger("decentralized_example", log_level, propagate_to_root=True)
    logger.info("日志级别设置为: %s", level_str.upper())
    
    # 步骤1: 加载配置
    llm_config = config_manager.get_config("llm_config")
    
    # 显示配置信息
    logger.info("LLM配置: %s", llm_config.get("provider", "未指定"))
    logger.info("协作模式: %s", decentralized_config.get("collaboration", {}).get("form_dynamic_teams", "未指定"))
    
    # 步骤2: 初始化模拟器桥接
    logger.info("初始化模拟器桥接...")

    # 创建模拟器配置
    sim_config = {
        'visualization': {'enabled': False},
        'explore_mode': 'thorough'
    }

    bridge = SimulatorBridge(config=sim_config)

    # 尝试使用新的场景ID初始化方式
    success = bridge.initialize_with_scenario("00001")

    if not success:
        # 回退到旧的任务文件初始化方式
        logger.info("尝试使用任务文件初始化...")
        task_file = os.path.join("data", "default", "default_task.json")
        if not os.path.exists(task_file):
            logger.error("任务文件不存在: %s", task_file)
            sys.exit(1)
        success = bridge.initialize_with_task(task_file)

    if not success:
        logger.error("模拟器初始化失败")
        sys.exit(1)
    
    # 输出任务信息
    task_description = bridge.get_task_description()
    logger.info("任务: %s", task_description)
    
    # 获取基本环境描述配置
    base_env_config = decentralized_config.get('autonomous_agent', {}).get('env_description', {})
    base_detail_level = base_env_config.get('detail_level', 'room')
    logger.info("自主智能体基本环境描述级别: %s", base_detail_level)
    
    # 测试环境描述
    test_env_desc = bridge.describe_environment_natural_language(
        sim_config={
            'nlp_show_object_properties': base_env_config.get('show_object_properties', True),
            'nlp_only_show_discovered': base_env_config.get('only_show_discovered', True),
            'nlp_detail_level': base_detail_level
        }
    )
    
    # 根据日志级别显示不同长度的环境描述
    if log_level <= logging.DEBUG:
        logger.info("=== 环境描述示例 ===\n%s\n===============", test_env_desc)
    else:
        logger.info("=== 环境描述示例 ===\n%s\n===============", test_env_desc[:300] + "...")
    
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
        
        # 获取特定智能体的环境描述配置
        agent_env_config = personality_config.get('env_description', base_env_config)
        agent_detail_level = agent_env_config.get('detail_level', base_detail_level)
        logger.info("智能体 %s 环境描述级别: %s", agent_id, agent_detail_level)
        
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
        
        # 在调试模式下显示更多信息
        if log_level <= logging.DEBUG:
            # 获取所有消息队列状态
            message_queues = comm_manager.get_queue_status()
            logger.debug("消息队列状态: %s", message_queues)
        
        # 每个智能体执行一步
        for agent_id, agent_data in agents.items():
            agent = agent_data["agent"]
            logger.info("智能体 %s 执行中...", agent_id)
            
            # 在调试模式下，获取并输出当前智能体状态
            if log_level <= logging.DEBUG:
                agent_state = agent.get_state()
                location = agent_state.get('location', {}).get('name', '未知位置')
                inventory = [item.get('name', item.get('id', '未知')) for item in agent_state.get('inventory', [])]
                logger.debug("智能体 %s 当前位置: %s, 库存: %s", agent_id, location, inventory)
            
            # 执行一步
            status, message, result = agent.step()
            
            # 打印结果
            logger.info("智能体 %s 结果: %s - %s", agent_id, status, message)
            
            # 处理EXPLORE命令返回PARTIAL的情况
            if agent.history and len(agent.history) > 0:
                last_action = agent.history[-1].get('action', '')
                
                if last_action.startswith("EXPLORE") and status == ActionStatus.PARTIAL:
                    logger.info("智能体 %s 探索未完成，继续探索...", agent_id)
                    
                    # 最多尝试5次探索
                    max_explore_attempts = 5
                    for attempt in range(1, max_explore_attempts + 1):
                        # 继续执行相同的EXPLORE命令
                        explore_status, explore_message, explore_result = bridge.process_command(agent_id, last_action)
                        
                        # 记录到历史
                        agent.record_action(last_action, {"status": explore_status, "message": explore_message, "result": explore_result})
                        
                        logger.info("智能体 %s 额外探索 #%d 结果: %s", agent_id, attempt, explore_message)
                        
                        # 如果不再是PARTIAL状态，就退出循环
                        if explore_status != ActionStatus.PARTIAL:
                            break
                        
                        # 暂停一下，避免请求过快
                        time.sleep(0.5)
                    else:
                        logger.info("智能体 %s 达到最大探索尝试次数，继续下一步操作", agent_id)
            
            # 在调试模式下显示详细的结果数据
            if log_level <= logging.DEBUG and result:
                import json
                logger.debug("智能体 %s 详细结果: %s", agent_id, json.dumps(result, ensure_ascii=False, indent=2))
        
        # 检查任务是否完成
        task_complete = check_task_completion(agents)
        if task_complete:
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

def check_task_completion(agents: Dict[str, Dict[str, Any]]) -> bool:
    """
    检查任务是否完成的自定义逻辑
    
    Args:
        agents: 智能体数据字典
        
    Returns:
        bool: 任务是否完成
    """
    # 检查任何智能体是否完成了任务
    for agent_id, agent_data in agents.items():
        agent = agent_data["agent"]
        state = agent.get_state()
        inventory = [item.get("id") for item in state.get("inventory", [])]
        if "apple_1" in inventory:
            return True
    
    return False

if __name__ == "__main__":
    main() 