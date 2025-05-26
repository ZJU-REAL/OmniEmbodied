#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟器桥接示例 - 展示如何使用SimulatorBridge直接与模拟器交互，替代复杂的场景和任务管理
"""

import os
import sys
import logging

# 添加项目根目录到路径，便于直接运行
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from embodied_framework.utils.logger import setup_logger
from embodied_framework.utils.simulator_bridge import SimulatorBridge

# 设置日志
logger = setup_logger("simulator_bridge_demo", logging.INFO)

def main():
    # 步骤1: 初始化模拟器桥接
    logger.info("初始化模拟器桥接...")
    bridge = SimulatorBridge()
    
    # 步骤2: 使用任务文件初始化模拟器
    task_file = os.path.join("data", "default", "default_task.json")
    if not os.path.exists(task_file):
        logger.error(f"任务文件不存在: {task_file}")
        sys.exit(1)
        
    logger.info(f"使用任务初始化模拟器: {task_file}")
    success = bridge.initialize_with_task(task_file)
    if not success:
        logger.error("模拟器初始化失败")
        sys.exit(1)
    
    # 步骤3: 获取任务信息
    task_description = bridge.get_task_description()
    logger.info(f"任务描述: {task_description}")
    
    # 步骤4: 获取智能体配置
    agents_config = bridge.get_agents_config()
    logger.info(f"\n任务配置了 {len(agents_config)} 个智能体:")
    for agent_config in agents_config:
        agent_name = agent_config.get('name', '')
        max_weight = agent_config.get('max_weight', 0)
        max_grasp = agent_config.get('max_grasp_limit', 0)
        logger.info(f"- {agent_name}: 最大承重 {max_weight}kg, 可同时抓取 {max_grasp} 个物体")
    
    # 步骤5: 获取场景信息
    rooms = bridge.get_rooms()
    logger.info(f"\n场景包含 {len(rooms)} 个房间:")
    for room in rooms:
        room_id = room.get('id')
        room_name = room.get('name', room_id)
        logger.info(f"- {room_id}: {room_name}")
        
        # 获取房间内物体
        objects_in_room = bridge.get_objects_in_room(room_id)
        logger.info(f"  房间内有 {len(objects_in_room)} 个物体:")
        for obj in objects_in_room[:3]:  # 只显示前三个
            obj_id = obj.get('id', '')
            obj_name = obj.get('name', '')
            obj_type = obj.get('type', '')
            logger.info(f"  - {obj_id}: {obj_name} ({obj_type})")
        
        if len(objects_in_room) > 3:
            logger.info(f"  - ... 等 {len(objects_in_room) - 3} 个物体")
    
    # 步骤6: 查找特定物体
    target_object = "红色滤波器套件"
    logger.info(f"\n查找物体: {target_object}")
    objects = bridge.find_objects_by_name_keyword(target_object)
    
    if objects:
        for obj in objects:
            obj_id = obj.get('id')
            obj_name = obj.get('name')
            location_id = obj.get('location_id', '')
            
            logger.info(f"找到物体: {obj_name} (ID: {obj_id})")
            logger.info(f"位置: {location_id}")
            
            # 显示物体属性
            properties = obj.get('properties', {})
            logger.info(f"物体属性:")
            for key, value in properties.items():
                logger.info(f"  - {key}: {value}")
    else:
        logger.info(f"未找到物体: {target_object}")
    
    # 步骤7: 分析任务相关物体
    logger.info("\n===== 任务物体分析 =====")
    
    # 1. 查找货架
    shelves = bridge.find_objects_by_name_keyword("货架")
    logger.info(f"找到 {len(shelves)} 个货架:")
    for shelf in shelves:
        shelf_id = shelf.get('id')
        shelf_name = shelf.get('name')
        weight = shelf.get('properties', {}).get('weight', '未知')
        location = shelf.get('location_id', '未知')
        logger.info(f"- {shelf_name} (ID: {shelf_id}): 重量 {weight}kg, 位置 {location}")
    
    # 2. 查找防静电工作台
    benches = bridge.find_objects_by_name_keyword("防静电工作台")
    logger.info(f"\n找到 {len(benches)} 个防静电工作台:")
    for bench in benches:
        bench_id = bench.get('id')
        bench_name = bench.get('name')
        location = bench.get('location_id', '未知')
        
        # 检查工作台上有什么物体
        objects_on_bench = bridge.get_objects_on_furniture(bench_id)
        logger.info(f"- {bench_name} (ID: {bench_id}): 位置 {location}")
        logger.info(f"  工作台上有 {len(objects_on_bench)} 个物体:")
        for obj in objects_on_bench:
            logger.info(f"  - {obj.get('name')} (ID: {obj.get('id')})")
    
    # 步骤8: 智能体配置分析
    logger.info("\n===== 智能体分析 =====")
    
    # 获取所有智能体
    agents = bridge.get_all_agents()
    logger.info(f"模拟器中有 {len(agents)} 个智能体:")
    for agent_id, agent in agents.items():
        agent_name = agent.get('name')
        location_id = agent.get('location_id')
        inventory = agent.get('inventory', [])
        
        logger.info(f"- {agent_id}: {agent_name}")
        logger.info(f"  位置: {location_id}")
        logger.info(f"  库存: {', '.join(inventory) if inventory else '空'}")


if __name__ == "__main__":
    main() 