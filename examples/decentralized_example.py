#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
去中心化多智能体示例 - 展示如何使用自主智能体协作完成任务

这个示例展示了去中心化多智能体系统的核心特性：
1. 每个智能体都有自己的LLM，可以独立决策
2. 智能体之间可以通过消息传递进行通信
3. 支持协商机制进行任务分配和资源共享
4. 每个智能体有不同的个性和技能特长
5. 去中心化决策，无需中央控制器

主要功能：
- 自主智能体创建和管理
- 智能体间通信和协商
- 任务分配和协作执行
- 个性化智能体配置
- 完整的执行轨迹记录

使用方法：
python examples/decentralized_example.py
"""

import sys
import os
import time
import json
import logging
import argparse
from typing import Dict, Any, List, Tuple
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 使用标准导入方式
from modes.decentralized.autonomous_agent import AutonomousAgent
from modes.decentralized.communication import CommunicationManager
from modes.decentralized.negotiation import Negotiator, NegotiationType, NegotiationStatus
# OmniSimulator作为第三方库
from OmniSimulator import ActionStatus
from utils.logger import setup_logger
from utils.task_evaluator import TaskEvaluator
from utils.run_naming import RunNamingManager
from config.config_manager import ConfigManager
from common_utils import setup_example_environment, get_task_description, check_apple_task_completion


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='去中心化多智能体任务执行示例')
    parser.add_argument('--mode', type=str,
                       choices=['sequential', 'combined', 'independent'],
                       default='sequential',
                       help='评测模式: sequential(逐个), combined(混合), independent(独立)')
    parser.add_argument('--scenario', type=str, default='00001',
                       help='场景ID (默认: 00001)')
    parser.add_argument('--suffix', type=str, default='demo',
                       help='运行后缀 (默认: demo)')
    parser.add_argument('--config', type=str, default='decentralized_config',
                       help='配置文件名 (默认: decentralized_config)')
    parser.add_argument('--log-level', type=str,
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO',
                       help='日志级别 (默认: INFO)')
    parser.add_argument('--max-steps', type=int, default=50,
                       help='最大执行步数 (默认: 50)')
    parser.add_argument('--enable-negotiation', action='store_true',
                       help='启用智能体协商机制')

    return parser.parse_args()


def setup_negotiation_handlers(negotiator: Negotiator, agent_id: str, logger: logging.Logger):
    """
    设置协商处理函数

    Args:
        negotiator: 协商器实例
        agent_id: 智能体ID
        logger: 日志记录器
    """
    def handle_task_allocation(content: Any, sender_id: str) -> Dict[str, Any]:
        """处理任务分配协商"""
        logger.info(f"智能体 {agent_id} 收到来自 {sender_id} 的任务分配请求: {content}")

        # 简单的任务分配逻辑
        task_type = content.get('task_type', '')

        if agent_id == 'explorer' and 'explore' in task_type.lower():
            return {
                "status": NegotiationStatus.ACCEPTED.value,
                "content": {"message": "接受探索任务", "estimated_time": 10}
            }
        elif agent_id == 'operator' and 'operate' in task_type.lower():
            return {
                "status": NegotiationStatus.ACCEPTED.value,
                "content": {"message": "接受操作任务", "estimated_time": 15}
            }
        else:
            return {
                "status": NegotiationStatus.REJECTED.value,
                "content": {"reason": "任务类型不匹配我的技能"}
            }

    def handle_information_request(content: Any, sender_id: str) -> Dict[str, Any]:
        """处理信息请求协商"""
        logger.info(f"智能体 {agent_id} 收到来自 {sender_id} 的信息请求: {content}")

        info_type = content.get('info_type', '')

        if info_type == 'location':
            return {
                "status": NegotiationStatus.ACCEPTED.value,
                "content": {"location": "当前位置信息", "room": "unknown"}
            }
        elif info_type == 'status':
            return {
                "status": NegotiationStatus.ACCEPTED.value,
                "content": {"status": "正常工作中", "task_progress": "50%"}
            }
        else:
            return {
                "status": NegotiationStatus.REJECTED.value,
                "content": {"reason": "不支持的信息类型"}
            }

    # 注册处理函数
    negotiator.register_handler(NegotiationType.TASK_ALLOCATION, handle_task_allocation)
    negotiator.register_handler(NegotiationType.INFORMATION_REQUEST, handle_information_request)
def setup_multi_agent_environment(bridge, agent_configs: Dict[str, Dict], logger: logging.Logger) -> bool:
    """
    设置多智能体环境，确保智能体在模拟器中正确初始化

    Args:
        bridge: 模拟器桥接
        agent_configs: 智能体配置字典
        logger: 日志记录器

    Returns:
        bool: 是否成功设置
    """
    try:
        # 获取所有房间信息
        rooms = bridge.get_rooms()
        if not rooms:
            logger.error("环境中没有可用房间")
            return False

        # 为每个智能体分配不同的起始位置
        room_ids = [room['id'] for room in rooms]
        logger.info(f"可用房间: {room_ids}")

        # 构建智能体初始化配置
        agents_init_config = []
        for i, (agent_id, config) in enumerate(agent_configs.items()):
            # 分配房间：如果房间数量足够，分配不同房间；否则使用第一个房间
            room_id = room_ids[i % len(room_ids)] if len(room_ids) > 1 else room_ids[0]

            agent_init_config = {
                "id": agent_id,
                "name": config.get('name', f"智能体_{agent_id}"),
                "location_id": room_id,
                "personality": config.get('personality', ''),
                "skills": config.get('skills', [])
            }
            agents_init_config.append(agent_init_config)
            logger.info(f"智能体 {agent_id} 将在房间 {room_id} 初始化")

        # 在模拟器中初始化智能体
        success = bridge.simulator.load_agents(agents_init_config)
        if not success:
            logger.error("在模拟器中初始化智能体失败")
            return False

        logger.info("✅ 多智能体环境设置成功")
        return True

    except Exception as e:
        logger.exception(f"设置多智能体环境时出错: {e}")
        return False


def create_decentralized_agents(config: Dict[str, Any], bridge, comm_manager,
                              enable_negotiation: bool, logger: logging.Logger) -> Dict[str, Dict[str, Any]]:
    """
    创建去中心化智能体

    Args:
        config: 配置字典
        bridge: 模拟器桥接
        comm_manager: 通信管理器
        enable_negotiation: 是否启用协商
        logger: 日志记录器

    Returns:
        Dict[str, Dict[str, Any]]: 智能体字典
    """
    # 智能体配置 - 参考CoELA的Alice和Bob设计
    agent_configs = {
        "alice": {
            **config["agent_personalities"]["explorer"],
            "name": "Alice",
            "role": "探索者",
            "communication_style": "主动、详细"
        },
        "bob": {
            **config["agent_personalities"]["operator"],
            "name": "Bob",
            "role": "操作者",
            "communication_style": "简洁、高效"
        }
    }

    # 设置多智能体环境
    env_setup_success = setup_multi_agent_environment(bridge, agent_configs, logger)
    if not env_setup_success:
        logger.error("多智能体环境设置失败")
        return {}

    agents = {}
    for agent_id, personality_config in agent_configs.items():
        # 合并基础配置和个性化配置
        agent_config = {**config["autonomous_agent"], **personality_config}

        logger.info(f"创建自主智能体: {agent_id} (角色: {personality_config.get('role', '')}, 个性: {personality_config.get('personality', '')})")
        agent = AutonomousAgent(bridge, agent_id, agent_config,
                              llm_config_name="llm_config", comm_manager=comm_manager)

        # 注册到通信管理器
        comm_manager.register_agent(agent_id, agent, agent.receive_message)

        # 创建协商器
        negotiator = Negotiator(agent_id, comm_manager)

        # 如果启用协商，设置协商处理函数
        if enable_negotiation:
            setup_negotiation_handlers(negotiator, agent_id, logger)

        # 保存引用
        agents[agent_id] = {
            "agent": agent,
            "negotiator": negotiator,
            "role": personality_config.get('role', ''),
            "communication_style": personality_config.get('communication_style', '')
        }

    return agents


def assign_collaborative_tasks(agents: Dict[str, Dict[str, Any]], task_description: str, logger: logging.Logger):
    """
    为智能体分配协作任务，参考CoELA的任务分配策略

    Args:
        agents: 智能体字典
        task_description: 主任务描述
        logger: 日志记录器
    """
    logger.info("为智能体分配协作任务...")

    # 根据角色和主任务分配具体任务，参考CoELA的Alice/Bob协作模式
    for agent_id, agent_data in agents.items():
        agent = agent_data["agent"]
        role = agent_data.get("role", "")
        comm_style = agent_data.get("communication_style", "")

        if agent_id == "alice":
            # Alice作为探索者，负责探索和信息收集
            specific_task = f"""主任务: {task_description}

你的身份: Alice (探索者)
你的特长: {agent_data['agent'].skills}
沟通风格: {comm_style}

协作策略:
1. 主动探索环境，发现目标物品和容器
2. 及时与Bob分享发现的信息
3. 协调任务分工，避免重复工作
4. 在需要帮助时主动请求Bob的协助

通信格式:
- 发送消息给Bob: MSGbob: <消息内容>
- 广播消息: BROADCAST: <消息内容>

记住: 你们是合作伙伴，共同完成任务比单独行动更高效！"""

        elif agent_id == "bob":
            # Bob作为操作者，负责具体操作和执行
            specific_task = f"""主任务: {task_description}

你的身份: Bob (操作者)
你的特长: {agent_data['agent'].skills}
沟通风格: {comm_style}

协作策略:
1. 等待Alice的探索信息，根据信息制定行动计划
2. 执行精确的操作任务，如抓取、放置物品
3. 及时反馈任务进度给Alice
4. 在发现重要信息时主动分享给Alice

通信格式:
- 发送消息给Alice: MSGalice: <消息内容>
- 广播消息: BROADCAST: <消息内容>

记住: 与Alice密切配合，你们的目标是共同成功！"""

        else:
            specific_task = task_description

        agent.set_task(specific_task)
        logger.info(f"智能体 {agent_id} ({role}) 任务已分配")
        logger.debug(f"详细任务: {specific_task[:100]}...")


def demonstrate_communication_and_negotiation(agents: Dict[str, Dict[str, Any]], logger: logging.Logger):
    """
    演示智能体间通信和协商机制，参考CoELA的通信模式

    Args:
        agents: 智能体字典
        logger: 日志记录器
    """
    logger.info("\n=== 演示智能体通信和协商机制 ===")

    alice_agent = agents["alice"]["agent"]
    bob_agent = agents["bob"]["agent"]
    alice_negotiator = agents["alice"]["negotiator"]
    bob_negotiator = agents["bob"]["negotiator"]

    # 1. 演示基础通信
    logger.info("1. 演示基础通信...")

    # Alice向Bob发送初始问候消息
    alice_agent.send_message("bob", "Hi Bob! 我是Alice，让我们开始协作完成任务吧！我会负责探索环境。")
    time.sleep(1)

    # Bob回复Alice
    bob_agent.send_message("alice", "Hi Alice! 我是Bob，我会等待你的探索信息，然后执行具体操作。")
    time.sleep(1)

    # 演示广播消息
    alice_agent.broadcast_message("大家好！我们开始协作任务，有任何发现我会及时分享！")
    time.sleep(1)

    # 2. 演示任务分配协商
    logger.info("2. 演示任务分配协商...")
    negotiation_id = alice_negotiator.start_negotiation(
        "bob",
        NegotiationType.TASK_ALLOCATION,
        {
            "task_type": "kitchen_operation",
            "description": "需要你去厨房操作设备，我发现了一些目标物品",
            "priority": "high",
            "estimated_time": 15
        }
    )

    # 等待协商结果
    time.sleep(2)
    status, result = alice_negotiator.get_negotiation_status(negotiation_id)
    logger.info(f"任务分配协商结果: {status}")
    if result:
        logger.info(f"协商详情: {result}")

    # 3. 演示信息请求协商
    logger.info("3. 演示信息请求协商...")
    negotiation_id = bob_negotiator.start_negotiation(
        "alice",
        NegotiationType.INFORMATION_REQUEST,
        {
            "info_type": "location",
            "description": "请告诉我目标物品的具体位置",
            "urgency": "medium"
        }
    )

    # 等待协商结果
    time.sleep(2)
    status, result = bob_negotiator.get_negotiation_status(negotiation_id)
    logger.info(f"信息请求协商结果: {status}")
    if result:
        logger.info(f"信息详情: {result}")

    # 4. 演示协作策略讨论
    logger.info("4. 演示协作策略讨论...")
    alice_agent.send_message("bob", "我建议我们分工合作：我负责探索和发现，你负责精确操作。你觉得怎么样？")
    time.sleep(1)
    bob_agent.send_message("alice", "好主意！我会等待你的信息，然后执行操作任务。请及时告诉我你的发现。")

    logger.info("✅ 通信和协商演示完成")


def demonstrate_collaboration_scenario(agents: Dict[str, Dict[str, Any]], bridge, logger: logging.Logger):
    """
    演示具体的协作场景 - 参考CoELA的协作模式

    Args:
        agents: 智能体字典
        bridge: 模拟器桥接
        logger: 日志记录器
    """
    logger.info("\n=== 演示协作场景：寻找和操作物品 ===")

    alice_agent = agents["alice"]["agent"]
    bob_agent = agents["bob"]["agent"]

    # 场景1: Alice探索并分享发现
    logger.info("场景1: Alice探索环境...")
    alice_agent.send_message("bob", "[INFO] 我开始探索环境，寻找目标物品和有用的容器")

    # 模拟Alice的探索发现
    time.sleep(1)
    alice_agent.send_message("bob", "[INFO] 我在厨房发现了一个苹果和一个篮子，位置是kitchen_counter")

    # 场景2: Bob响应并协调任务
    logger.info("场景2: Bob响应Alice的发现...")
    bob_agent.send_message("alice", "[TASK] 太好了！我去厨房帮你操作，你继续探索其他房间")

    # 场景3: 协作执行
    logger.info("场景3: 协作执行任务...")
    alice_agent.send_message("bob", "[STATUS] 我现在去客厅继续探索，厨房交给你了")
    bob_agent.send_message("alice", "[STATUS] 收到！我正在前往厨房")

    # 场景4: 遇到问题求助
    logger.info("场景4: 遇到困难时的协作...")
    time.sleep(1)
    bob_agent.send_message("alice", "[HELP] 我在厨房找不到篮子，你能再确认一下位置吗？")
    alice_agent.send_message("bob", "[INFO] 篮子在厨房的柜台上，可能被其他物品挡住了，试试LOOK命令")

    # 场景5: 成功协作
    logger.info("场景5: 成功协作完成...")
    bob_agent.send_message("alice", "[STATUS] 找到了！我已经把苹果放进篮子里")
    alice_agent.broadcast_message("[INFO] 太好了！我们成功协作完成了第一个目标")

    logger.info("✅ 协作场景演示完成 - 展示了信息分享、任务协调、问题求助等协作模式")


def run_decentralized_execution(agents: Dict[str, Dict[str, Any]], bridge,
                               max_steps: int, enable_negotiation: bool,
                               logger: logging.Logger) -> Tuple[bool, Dict[str, int]]:
    """
    运行去中心化执行

    Args:
        agents: 智能体字典
        bridge: 模拟器桥接
        max_steps: 最大步数
        enable_negotiation: 是否启用协商
        logger: 日志记录器

    Returns:
        Tuple[bool, Dict[str, int]]: (是否成功完成任务, 协作统计信息)
    """
    logger.info("开始去中心化多智能体执行...")

    # 如果启用协商，先演示协商机制
    if enable_negotiation:
        demonstrate_communication_and_negotiation(agents, logger)

    # 演示协作场景
    demonstrate_collaboration_scenario(agents, bridge, logger)

    # 创建智能体组
    comm_manager = list(agents.values())[0]["agent"].comm_manager
    comm_manager.create_group("task_force", list(agents.keys()))

    # 执行主循环 - 参考CoELA的多智能体协作模式
    collaboration_metrics = {
        "messages_sent": 0,
        "negotiations_started": 0,
        "successful_collaborations": 0
    }

    for step in range(1, max_steps + 1):
        logger.info(f"\n==== 步骤 {step} ====")

        # 每个智能体执行一步
        step_results = {}
        step_messages = []

        for agent_id, agent_data in agents.items():
            agent = agent_data["agent"]
            negotiator = agent_data["negotiator"]
            role = agent_data.get("role", "")

            logger.info(f"智能体 {agent_id} ({role}) 执行中...")

            # 检查协商超时
            if enable_negotiation:
                timed_out = negotiator.check_timeout()
                if timed_out:
                    logger.info(f"智能体 {agent_id} 有 {len(timed_out)} 个协商超时")
                    collaboration_metrics["negotiations_started"] += len(timed_out)

            # 记录执行前的消息队列长度
            pre_msg_count = len(agent.message_queue)

            # 执行一步
            try:
                status, message, result = agent.step()
                step_results[agent_id] = (status, message, result)

                # 检查是否发送了消息
                if "MESSAGE_SENT" in str(status) or "BROADCAST" in str(status):
                    collaboration_metrics["messages_sent"] += 1
                    step_messages.append(f"{agent_id} 发送了消息")

                # 记录执行后的消息队列变化
                post_msg_count = len(agent.message_queue)
                if post_msg_count > pre_msg_count:
                    step_messages.append(f"{agent_id} 收到了 {post_msg_count - pre_msg_count} 条新消息")

                logger.info(f"智能体 {agent_id} 结果: {status} - {message}")

            except Exception as e:
                logger.error(f"智能体 {agent_id} 执行出错: {e}")
                step_results[agent_id] = ("ERROR", str(e), None)

        # 显示本步骤的协作信息
        if step_messages:
            logger.info(f"本步骤协作活动: {', '.join(step_messages)}")

        # 每5步显示一次协作统计
        if step % 5 == 0:
            logger.info(f"协作统计 - 消息: {collaboration_metrics['messages_sent']}, "
                       f"协商: {collaboration_metrics['negotiations_started']}")

        # 检查任务是否完成
        agent_ids = list(agents.keys())
        if check_apple_task_completion(bridge, agent_ids):
            logger.info("\n🎉 任务成功完成！")
            collaboration_metrics["successful_collaborations"] += 1
            logger.info(f"最终协作统计: {collaboration_metrics}")
            return True, collaboration_metrics

        # 暂停一下，便于观察
        time.sleep(1)

    logger.info(f"\n⏰ 已达到最大步骤数 ({max_steps})，任务未完成。")
    return False, collaboration_metrics


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()

    try:
        # 设置日志级别
        log_level = getattr(logging, args.log_level.upper())

        # 使用公共函数设置环境
        logger, config_manager, bridge, config = setup_example_environment(
            "去中心化多智能体", args.config, args.scenario, log_level
        )

        # 加载LLM配置
        llm_config = config_manager.get_config("llm_config")
        logger.info(f"LLM配置: {llm_config.get('api', {}).get('provider', '未指定')}")

        # 获取任务描述
        task_description = get_task_description(bridge, logger)

    except RuntimeError as e:
        print(f"❌ 初始化失败: {e}")
        sys.exit(1)

    # 创建通信管理器
    logger.info("创建通信管理器...")
    comm_manager = CommunicationManager()
    comm_manager.start_processing()

    try:
        # 创建自主智能体
        agents = create_decentralized_agents(
            config, bridge, comm_manager, args.enable_negotiation, logger
        )

        # 分配任务
        assign_collaborative_tasks(agents, task_description, logger)

        # 运行去中心化执行
        success, collaboration_metrics = run_decentralized_execution(
            agents, bridge, args.max_steps, args.enable_negotiation, logger
        )

        # 输出详细的执行分析
        logger.info("\n=== 多智能体协作分析 ===")

        # 通信统计
        if hasattr(comm_manager, 'get_message_statistics'):
            comm_stats = comm_manager.get_message_statistics()
            logger.info(f"通信统计: {comm_stats}")

        # 智能体执行历史
        logger.info("\n=== 智能体执行历史 ===")
        for agent_id, agent_data in agents.items():
            agent = agent_data["agent"]
            role = agent_data.get("role", "")
            logger.info(f"\n智能体 {agent_id} ({role}) 执行历史:")
            history = agent.get_history()

            # 统计不同类型的动作
            action_stats = {}
            message_count = 0

            for entry in history:
                action = entry.get('action', '')
                if 'MESSAGE' in action or 'BROADCAST' in action:
                    message_count += 1
                action_type = action.split('_')[0] if '_' in action else action
                action_stats[action_type] = action_stats.get(action_type, 0) + 1

            logger.info(f"  动作统计: {action_stats}")
            logger.info(f"  通信次数: {message_count}")

            # 显示最后10条历史记录
            logger.info("  最近动作:")
            for i, entry in enumerate(history[-10:]):
                action = entry.get('action', '')
                result = entry.get('result', {})
                status = result.get('status', '')
                message = result.get('message', '')
                logger.info(f"    {i+1}. {action} -> {status}: {message}")

        # 协作效果评估
        logger.info("\n=== 协作效果评估 ===")
        total_messages = collaboration_metrics["messages_sent"]
        total_negotiations = collaboration_metrics["negotiations_started"]

        if total_messages > 0:
            logger.info(f"✅ 智能体间进行了 {total_messages} 次通信交流")
        else:
            logger.info("⚠️  智能体间缺乏通信交流")

        if total_negotiations > 0:
            logger.info(f"✅ 进行了 {total_negotiations} 次协商")
        else:
            logger.info("ℹ️  未进行正式协商")

        # 输出最终结果
        if success:
            logger.info("\n🎉 去中心化多智能体任务执行成功！")
            logger.info("✅ 智能体成功协作完成了任务")
        else:
            logger.info("\n❌ 去中心化多智能体任务执行未完成")
            if total_messages == 0:
                logger.info("💡 建议: 增加智能体间的通信交流可能有助于任务完成")

        logger.info(f"\n📊 最终协作统计: {collaboration_metrics}")

    finally:
        # 停止通信管理器
        logger.info("停止通信管理器...")
        comm_manager.stop_processing()


if __name__ == "__main__":
    main()