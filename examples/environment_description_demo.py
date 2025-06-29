#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境描述配置演示 - 展示不同配置对提示词中房间信息的影响
"""

import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embodied_framework.utils import SimulatorBridge, create_env_description_config


def demo_environment_descriptions():
    """演示不同环境描述配置的效果"""
    
    print("🚀 环境描述配置演示")
    print("=" * 60)
    
    # 初始化模拟器
    bridge = SimulatorBridge()
    success = bridge.initialize_with_scenario("00001")
    
    if not success:
        print("❌ 模拟器初始化失败")
        return
    
    print("✅ 模拟器初始化成功")
    
    # 获取智能体信息
    all_agents = bridge.get_all_agents()
    if not all_agents:
        print("❌ 没有找到智能体")
        return
    
    agent_id = list(all_agents.keys())[0]
    agent_info = all_agents[agent_id]
    room_id = agent_info.get('location_id')
    
    print(f"🤖 智能体: {agent_id}")
    print(f"📍 当前位置: {room_id}")
    print()
    
    # 配置1: 只显示当前房间（默认配置）
    print("📋 配置1: detail_level='room' - 只显示当前房间")
    print("-" * 50)
    
    room_desc = bridge.describe_room_natural_language(room_id)
    print(room_desc)
    print()
    
    # 配置2: 显示所有房间，但只显示已发现物体
    print("📋 配置2: detail_level='full', only_show_discovered=True")
    print("-" * 50)
    
    env_desc_discovered = bridge.describe_environment_natural_language(
        sim_config={
            'nlp_show_object_properties': False,  # 简化输出
            'nlp_only_show_discovered': True
        }
    )
    
    # 只显示前1000字符
    print(env_desc_discovered[:1000] + "..." if len(env_desc_discovered) > 1000 else env_desc_discovered)
    print()
    
    # 配置3: 显示所有房间和所有物体（全知模式）
    print("📋 配置3: detail_level='full', only_show_discovered=False")
    print("-" * 50)
    
    env_desc_full = bridge.describe_environment_natural_language(
        sim_config={
            'nlp_show_object_properties': False,  # 简化输出
            'nlp_only_show_discovered': False
        }
    )
    
    # 只显示前1000字符
    print(env_desc_full[:1000] + "..." if len(env_desc_full) > 1000 else env_desc_full)
    print()
    
    # 配置4: 显示详细物体属性
    print("📋 配置4: 包含详细物体属性")
    print("-" * 50)
    
    room_desc_detailed = bridge.describe_room_natural_language(
        room_id,
        sim_config={
            'nlp_show_object_properties': True,
            'nlp_only_show_discovered': False
        }
    )
    
    # 只显示前800字符
    print(room_desc_detailed[:800] + "..." if len(room_desc_detailed) > 800 else room_desc_detailed)
    print()
    
    # 配置5: 简要描述
    print("📋 配置5: detail_level='brief' - 只显示智能体状态")
    print("-" * 50)
    
    agent_desc = bridge.describe_agent_natural_language(agent_id)
    print(agent_desc)
    print()
    
    # 统计信息
    print("📊 配置对比统计")
    print("-" * 50)
    print(f"当前房间描述长度: {len(room_desc)} 字符")
    print(f"完整环境描述长度: {len(env_desc_full)} 字符")
    print(f"智能体描述长度: {len(agent_desc)} 字符")
    print()
    
    # 配置建议
    print("💡 配置建议")
    print("-" * 50)
    print("🎯 全局规划任务: detail_level='full', only_show_discovered=False")
    print("🔍 探索任务: detail_level='room', only_show_discovered=True")
    print("⚡ 简单任务: detail_level='brief' 或 detail_level='room'")
    print("🔧 调试模式: detail_level='full', show_object_properties=True")


def demo_config_creation():
    """演示如何创建和使用环境描述配置"""
    
    print("\n🛠️ 环境描述配置创建演示")
    print("=" * 60)
    
    # 创建不同的配置
    configs = {
        "全局规划": create_env_description_config(
            detail_level='full',
            show_properties=True,
            only_discovered=False
        ),
        "探索模式": create_env_description_config(
            detail_level='room',
            show_properties=True,
            only_discovered=True
        ),
        "轻量模式": create_env_description_config(
            detail_level='brief',
            show_properties=False,
            only_discovered=True
        )
    }
    
    for name, config in configs.items():
        print(f"📋 {name}配置:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        print()


if __name__ == "__main__":
    try:
        demo_environment_descriptions()
        demo_config_creation()
        
        print("✅ 演示完成！")
        print("\n📖 更多信息请参考:")
        print("   - docs/environment_description.md")
        print("   - config/defaults/single_agent_config.yaml")
        
    except KeyboardInterrupt:
        print("\n⏹️ 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()
