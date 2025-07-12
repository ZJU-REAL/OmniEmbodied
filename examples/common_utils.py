#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例代码公共工具函数
提供示例代码中常用的初始化和配置加载功能
"""

import os
import sys
import logging
from typing import Dict, Any, Optional, Tuple

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ConfigManager
from utils.logger import setup_logger
from utils.simulator_bridge import SimulatorBridge


def setup_example_environment(example_name: str, config_name: str,
                            scenario_id: str = "00001",
                            log_level: int = logging.INFO) -> Tuple[logging.Logger, ConfigManager, SimulatorBridge, Dict[str, Any]]:
    """
    设置示例运行环境的公共函数
    
    Args:
        example_name: 示例名称，用于日志标识
        config_name: 配置文件名称
        scenario_id: 场景ID
        log_level: 日志级别
        
    Returns:
        tuple: (logger, config_manager, bridge, config)
        
    Raises:
        RuntimeError: 如果初始化失败
    """
    # 设置日志
    logger = setup_logger(example_name, log_level, propagate_to_root=True)
    logger.info(f"🚀 启动{example_name}示例...")
    
    # 加载配置
    config_manager = ConfigManager()
    config = config_manager.get_config(config_name)
    if not config:
        raise RuntimeError(f"无法加载配置文件: {config_name}")
    
    logger.info(f"✅ 配置加载成功: {config_name}")
    
    # 初始化模拟器桥接
    logger.info("🔧 初始化模拟器桥接...")
    bridge = SimulatorBridge()
    success = bridge.initialize_with_scenario(scenario_id)
    if not success:
        raise RuntimeError(f"模拟器初始化失败，场景ID: {scenario_id}")
    
    logger.info(f"✅ 模拟器初始化成功，场景: {scenario_id}")
    
    return logger, config_manager, bridge, config


def get_task_description(bridge: SimulatorBridge, logger: logging.Logger) -> str:
    """
    获取任务描述的公共函数
    
    Args:
        bridge: 模拟器桥接实例
        logger: 日志记录器
        
    Returns:
        str: 任务描述
        
    Raises:
        RuntimeError: 如果无法获取任务描述
    """
    # 尝试直接获取任务描述
    task_description = bridge.get_task_description()
    if task_description:
        logger.info(f"📋 任务描述: {task_description}")
        return task_description
    
    # 如果直接获取失败，尝试从任务信息中获取
    task_info = bridge.get_task_info()
    if task_info and 'task_background' in task_info:
        task_description = task_info['task_background']
        logger.info(f"📋 任务描述 (从任务信息获取): {task_description}")
        return task_description
    
    raise RuntimeError("无法获取任务描述")


def check_apple_task_completion(bridge: SimulatorBridge, agent_ids: list) -> bool:
    """
    检查苹果任务是否完成的公共函数
    
    Args:
        bridge: 模拟器桥接实例
        agent_ids: 智能体ID列表
        
    Returns:
        bool: 任务是否完成
    """
    for agent_id in agent_ids:
        agent_info = bridge.get_agent_info(agent_id)
        if agent_info:
            inventory = agent_info.get('inventory', [])
            # 检查库存中是否有苹果
            if any('apple' in str(item).lower() for item in inventory):
                return True
    return False


def log_agent_status(bridge: SimulatorBridge, agent_ids: list, logger: logging.Logger) -> None:
    """
    记录智能体状态的公共函数
    
    Args:
        bridge: 模拟器桥接实例
        agent_ids: 智能体ID列表
        logger: 日志记录器
    """
    logger.info("📊 智能体状态:")
    for agent_id in agent_ids:
        agent_info = bridge.get_agent_info(agent_id)
        if agent_info:
            location = agent_info.get('location_id', '未知')
            inventory = agent_info.get('inventory', [])
            inventory_str = ', '.join(str(item) for item in inventory) if inventory else '无'
            logger.info(f"  - {agent_id}: 位置={location}, 库存={inventory_str}")
        else:
            logger.info(f"  - {agent_id}: 状态未知")
