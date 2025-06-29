#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化后的单智能体示例 - 使用框架中的LLMAgent
- 数据通过data文件夹导入
- 提示词完全从config目录的配置文件导入
- 支持动态动作描述插入
"""

import os
import sys
import time
import logging

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ConfigManager
from utils.logger import setup_logger
from utils.simulator_bridge import SimulatorBridge
from utils.data_loader import DataLoader
from embodied_simulator.core import ActionStatus
from modes.single_agent.llm_agent import LLMAgent


def main():
    """主函数"""
    # 设置日志
    setup_logger(log_level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("🚀 启动单智能体示例")

    try:
        # 创建模拟器桥接
        bridge = SimulatorBridge()
        logger.info("✅ 模拟器桥接创建成功")

        # 初始化场景
        scenario_id = "00001"
        logger.info(f"🔄 正在初始化场景: {scenario_id}")

        if not bridge.initialize_with_scenario(scenario_id):
            logger.error("❌ 模拟器初始化失败")
            return 1

        # 验证智能体是否存在
        if not hasattr(bridge.simulator, 'agent_manager') or not bridge.simulator.agent_manager:
            logger.error("❌ 智能体管理器不存在")
            return 1

        agents = bridge.simulator.agent_manager.get_all_agents()
        if not agents:
            logger.error("❌ 没有找到任何智能体")
            return 1

        agent_id = list(agents.keys())[0]
        logger.info(f"🤖 找到智能体: {agent_id}")

        # 加载配置
        config_manager = ConfigManager()
        config = config_manager.get_config("single_agent_config")

        # 获取任务描述
        data_loader = DataLoader()
        result = data_loader.load_complete_scenario(scenario_id)
        if not result:
            logger.error("❌ 无法加载场景数据")
            return 1
        _, task_data = result

        task_background = task_data.get('task_background', '执行实验室任务')
        first_task = task_data.get('tasks', [{}])[0]
        task_description = first_task.get('task_description', task_background)

        logger.info(f"🎯 任务描述: {task_description}")

        # 创建LLM智能体
        simulator = bridge.simulator
        agent = LLMAgent(simulator, agent_id, config)
        agent.set_task(task_description)

        # 执行配置
        exec_config = config.get('execution', {})
        max_steps = exec_config.get('max_steps', 50)

        # 执行统计
        stats = {
            'total_actions': 0,
            'successful_actions': 0,
            'start_time': time.time()
        }

        # 执行任务
        logger.info(f"🎬 开始执行任务，最大步数: {max_steps}")
        for step in range(1, max_steps + 1):
            logger.info(f"\n📍 步骤 {step}/{max_steps}")

            try:
                # 执行一步
                status, message, _ = agent.step()

                # 更新统计
                stats['total_actions'] += 1
                if status == ActionStatus.SUCCESS:
                    stats['successful_actions'] += 1
                    logger.info(f"✅ 动作成功: {message}")
                else:
                    logger.warning(f"⚠️ 动作失败: {message}")

                # 检查是否完成任务（简单检查）
                if "完成" in message or "成功" in message:
                    logger.info("🎉 任务可能已完成")
                    break

            except Exception as e:
                logger.error(f"❌ 执行动作时出错: {e}")
                break

        # 计算最终统计
        runtime = time.time() - stats['start_time']
        success_rate = (stats['successful_actions'] / stats['total_actions']
                       if stats['total_actions'] > 0 else 0)

        # 输出统计信息
        logger.info("\n📊 执行统计:")
        logger.info(f"总动作数: {stats['total_actions']}")
        logger.info(f"成功动作数: {stats['successful_actions']}")
        logger.info(f"成功率: {success_rate:.2%}")
        logger.info(f"运行时间: {runtime:.2f}秒")

        logger.info("🎉 程序执行完成")
        return 0

    except Exception as e:
        logger.exception(f"❌ 程序执行失败: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
