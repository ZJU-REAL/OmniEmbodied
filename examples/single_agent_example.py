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
from embodied_framework.utils import create_env_description_config
from embodied_simulator.core import ActionStatus

def main():
    # 根据配置设置日志级别
    config_manager = ConfigManager()
    agent_config = config_manager.get_config("single_agent_config")
    
    log_level = logging.INFO
    logging_config = agent_config.get('logging', {})
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
    logger = setup_logger("single_agent_example", log_level, propagate_to_root=True)
    logger.info("日志级别设置为: %s", level_str.upper())
    
    # 步骤1: 加载配置
    llm_config = config_manager.get_config("llm_config")
    
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
    
    # 使用配置文件中定义的环境描述设置，而不是覆盖它
    env_config = agent_config.get('env_description', {})
    detail_level = env_config.get('detail_level', 'room')
    
    # 记录实际使用的环境描述配置
    logger.info("使用环境描述级别: %s", detail_level)
    
    # 步骤3: 创建智能体
    agent_id = "agent_1"  # 使用默认的第一个智能体
    logger.info("创建LLM智能体...")
    agent = LLMAgent(bridge, agent_id, agent_config)
    
    # 测试环境描述 - 添加detail_level参数
    test_env_desc = bridge.describe_environment_natural_language(
        sim_config={
            'nlp_show_object_properties': env_config.get('show_object_properties', True),
            'nlp_only_show_discovered': env_config.get('only_show_discovered', False),
            'nlp_detail_level': detail_level  # 传递detail_level参数
        }
    )
    
    # 根据日志级别显示不同长度的环境描述
    if log_level <= logging.DEBUG:
        logger.info("=== 环境描述示例 ===\n%s\n===============", test_env_desc)
    else:
        logger.info("=== 环境描述示例 ===\n%s\n===============", test_env_desc[:300] + "...")
    
    # 步骤4: 运行智能体
    logger.info("开始执行任务...")
    max_steps = 15
    for step in range(1, max_steps + 1):
        logger.info("==== 步骤 %d ====", step)
        
        if log_level <= logging.DEBUG:
            # 在调试模式下，获取并输出当前智能体状态
            agent_state = agent.get_state()
            location = agent_state.get('location', {}).get('name', '未知位置')
            inventory = [item.get('name', item.get('id', '未知')) for item in agent_state.get('inventory', [])]
            logger.debug("当前位置: %s, 库存: %s", location, inventory)
        
        # 执行一步
        status, message, result = agent.step()
        
        # 获取执行的动作
        last_action = "未知"
        if agent.history and len(agent.history) > 0:
            last_action = agent.history[-1].get('action', '未知')
        
        # 打印结果
        logger.info("动作结果: %s", message)
        
        # 在调试模式下显示详细的结果数据
        if log_level <= logging.DEBUG and result:
            import json
            logger.debug("详细结果: %s", json.dumps(result, ensure_ascii=False, indent=2))
        
        # 检查任务是否完成
        if check_task_completion(agent):
            logger.info("任务成功完成！")
            break
            
        # 暂停一下，便于观察
        time.sleep(1)
    else:
        logger.info("已达到最大步骤数 (%d)，任务未完成。", max_steps)
    
    # 步骤5: 输出执行历史
    logger.info("==== 执行历史 ====")
    for i, entry in enumerate(agent.get_history()):
        action = entry.get('action', '')
        result = entry.get('result', {})
        status = result.get('status', '')
        message = result.get('message', '')
        logger.info("%d. 动作: %s, 状态: %s, 消息: %s", i+1, action, status, message)

def check_task_completion(agent: LLMAgent) -> bool:
    """
    检查任务是否完成的自定义逻辑
    
    Args:
        agent: 智能体实例
        
    Returns:
        bool: 任务是否完成
    """
    # 获取智能体状态
    state = agent.get_state()
    
    # 根据任务目标检查完成情况，这里以抓取苹果为例
    inventory = [item.get("id") for item in state.get("inventory", [])]
    if "apple_1" in inventory:
        return True
    
    return False

if __name__ == "__main__":
    main() 