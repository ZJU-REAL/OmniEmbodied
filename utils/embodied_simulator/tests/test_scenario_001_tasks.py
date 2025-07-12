#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
基于001号场景的任务验证测试脚本
包含完整的任务验证系统测试，支持：
- 单智能体任务测试（直接命令、属性推理、工具使用、复合推理）
- 多智能体任务测试（显式协作、隐式协作、复合协作）
- 实时任务进度跟踪和验证
- 可视化界面集成测试
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent  # 从tests目录向上一级到项目根目录
sys.path.insert(0, str(project_root))

# 全局变量控制测试模式
VERBOSE_MODE = False
TEST_RESULTS = []

try:
    from OmniEmbodied.simulator.core.engine import SimulationEngine
    from OmniEmbodied.simulator.utils.data_loader import default_data_loader
    print("✅ 成功导入核心模块")
except ImportError as e:
    try:
        # 尝试直接导入
        from core.engine import SimulationEngine
        from utils.data_loader import default_data_loader
        print("✅ 成功导入核心模块（直接导入）")
    except ImportError as e2:
        print(f"❌ 导入失败: {e}")
        print(f"❌ 直接导入也失败: {e2}")
        sys.exit(1)

def wait_for_enter(test_name: str):
    """在verbose模式下等待用户按回车继续"""
    if VERBOSE_MODE:
        input(f"\n⏸️  {test_name} 完成，按回车继续下一个测试...")

def assert_test(condition: bool, test_name: str, expected: str, actual: str):
    """断言测试结果并记录"""
    result = {
        'name': test_name,
        'passed': condition,
        'expected': expected,
        'actual': actual
    }
    TEST_RESULTS.append(result)

    if condition:
        print(f"✅ {test_name}: PASS")
    else:
        print(f"❌ {test_name}: FAIL")
        print(f"   期望: {expected}")
        print(f"   实际: {actual}")

    return condition

def print_action_result(action_name: str, result):
    """打印动作执行结果"""
    print(f"\n🎯 {action_name}")
    print("─" * 50)
    if isinstance(result, tuple) and len(result) >= 2:
        status, message = result[0], result[1]
        print(f"📋 执行状态: {status.name}")
        print(f"💬 执行消息: {message}")

        # 如果有额外信息，显示关键信息
        if len(result) > 2 and isinstance(result[2], dict):
            extra_info = result[2]
            if 'new_location_id' in extra_info:
                print(f"📍 新位置: {extra_info['new_location_id']}")
            if 'near_object_id' in extra_info:
                print(f"🎯 靠近物体: {extra_info['near_object_id']}")
            if 'object_id' in extra_info and 'attribute' in extra_info:
                print(f"🔧 操作物体: {extra_info['object_id']}")
                print(f"⚙️  属性变化: {extra_info['attribute']} ({extra_info.get('old_value')} → {extra_info.get('new_value')})")
            if 'discovery_count' in extra_info:
                print(f"🔍 发现物体数: {extra_info['discovery_count']}")
    else:
        print(f"📋 执行结果: {result}")

def print_verification_result(verification_data):
    """打印任务验证结果"""
    if not verification_data:
        return

    print("\n📊 任务验证反馈")
    print("─" * 50)

    completion_summary = verification_data.get('completion_summary', {})
    total_tasks = completion_summary.get('total_tasks', 0)
    completed_tasks = completion_summary.get('completed_tasks', 0)
    completion_rate = completion_summary.get('completion_rate', 0.0)

    print(f"📈 总体进度: {completed_tasks}/{total_tasks} ({completion_rate:.1%})")

    # 显示各类别进度
    categories = completion_summary.get('categories', {})
    if categories:
        print("📂 分类进度:")
        category_names = {
            'direct_command': '  🤖 直接命令',
            'attribute_reasoning': '  🤖 属性推理',
            'tool_use': '  🤖 工具使用',
            'compound_reasoning': '  🤖 复合推理',
            'explicit_collaboration': '  👥 显式协作',
            'implicit_collaboration': '  👥 隐式协作',
            'compound_collaboration': '  👥 复合协作'
        }

        for category, info in categories.items():
            display_name = category_names.get(category, f"  📋 {category}")
            completed = info.get('completed', 0)
            total = info.get('total', 0)
            rate = info.get('completion_rate', 0.0)
            status_icon = "✅" if rate >= 1.0 else "⏳" if completed > 0 else "⭕"
            print(f"{display_name}: {status_icon} {completed}/{total} ({rate:.1%})")

    # 显示接下来的未完成任务
    next_tasks = verification_data.get('next_incomplete_tasks', [])
    if next_tasks:
        print(f"\n🎯 接下来的任务 (显示前3个):")
        for i, task in enumerate(next_tasks[:3], 1):
            print(f"  {i}. {task.get('task_description', 'N/A')}")

def print_test_summary():
    """打印测试总结"""
    total = len(TEST_RESULTS)
    passed = sum(1 for r in TEST_RESULTS if r['passed'])
    failed = total - passed

    print("\n" + "="*60)
    print("📊 测试结果总结")
    print("="*60)
    print(f"总测试数: {total}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"成功率: {passed/total*100:.1f}%" if total > 0 else "成功率: 0%")

    if failed > 0:
        print("\n❌ 失败的测试:")
        for result in TEST_RESULTS:
            if not result['passed']:
                print(f"  - {result['name']}")
                print(f"    期望: {result['expected']}")
                print(f"    实际: {result['actual']}")

    print("="*60)

def test_single_agent_tasks():
    """测试单智能体任务"""
    global engine
    print("\n🤖 测试单智能体任务...")

    # 加载00001场景
    print("📥 加载场景00001...")
    result = default_data_loader.load_complete_scenario("00001")
    if not result:
        print("❌ 场景加载失败")
        return False

    scene_data, task_data = result

    # 初始化引擎 - abilities现在从scene_data获取
    abilities = scene_data.get("abilities", [])

    # 检查是否启用可视化（通过命令行参数-v控制）
    enable_visualization = len(sys.argv) > 1 and '-v' in sys.argv
    config = {
        'visualization': {'enabled': enable_visualization}
    }

    if enable_visualization:
        print("🌐 可视化已启用，测试过程中可在浏览器访问: http://localhost:8082")
    
    engine = SimulationEngine(config=config, scene_abilities=abilities)

    data = {'scene': scene_data, 'task': task_data}
    success = engine.initialize_with_data(data)

    if not success:
        print("❌ 引擎初始化失败")
        return False

    print("✅ 引擎初始化成功")
    
    # 获取智能体
    agents = engine.agent_manager.get_all_agents()
    if not agents:
        print("❌ 没有找到智能体")
        return False
    
    agent_id = list(agents.keys())[0]
    agent = agents[agent_id]
    
    print(f"🤖 使用智能体: {agent.name} (ID: {agent_id})")
    print(f"📍 初始位置: {agent.location_id}")

    # 获取初始任务状态
    print("\n📊 初始任务状态:")
    initial_status = engine.get_task_verification_status()
    if initial_status:
        summary = initial_status.get("completion_summary", {})
        print(f"   总任务数: {summary.get('total_tasks', 0)}")
        print(f"   已完成: {summary.get('completed_tasks', 0)}")
        print(f"   完成率: {summary.get('completion_rate', 0):.2%}")

    action_handler = engine.action_handler

    # 测试1: 移动到主工作台区域
    print("\n" + "="*60)
    print("🧪 测试1: 移动到主工作台区域")
    print("="*60)

    result = action_handler.process_command(agent_id, "GOTO main_workbench_area")

    # 分离显示执行结果和验证结果
    print_action_result("移动到主工作台区域", result)

    # 提取验证数据
    verification_data = None
    if len(result) > 2 and isinstance(result[2], dict):
        verification_data = result[2].get('task_verification')

    if verification_data:
        print_verification_result(verification_data)

    agent = engine.agent_manager.get_agent(agent_id)
    assert_test(
        result[0].name == "SUCCESS",
        "移动到主工作台区域",
        "SUCCESS",
        result[0].name
    )
    wait_for_enter("测试1: 移动到主工作台区域")

    # 测试2: 探索主工作台区域
    print("\n" + "="*60)
    print("🧪 测试2: 探索主工作台区域")
    print("="*60)

    result = action_handler.process_command(agent_id, "EXPLORE main_workbench_area")

    # 分离显示执行结果和验证结果
    print_action_result("探索主工作台区域", result)

    # 提取验证数据
    verification_data = None
    if len(result) > 2 and isinstance(result[2], dict):
        verification_data = result[2].get('task_verification')

    if verification_data:
        print_verification_result(verification_data)

    wait_for_enter("测试2: 探索主工作台区域")

    # 测试3: 移动到示波器
    print("\n" + "="*60)
    print("🧪 测试3: 移动到示波器")
    print("="*60)

    result = action_handler.process_command(agent_id, "GOTO oscilloscope_1")

    # 分离显示执行结果和验证结果
    print_action_result("移动到示波器", result)

    # 提取验证数据
    verification_data = None
    if len(result) > 2 and isinstance(result[2], dict):
        verification_data = result[2].get('task_verification')

    if verification_data:
        print_verification_result(verification_data)

    wait_for_enter("测试3: 移动到示波器")

    # 测试4: 打开示波器（直接命令任务）
    print("\n" + "="*60)
    print("🧪 测试4: 打开示波器 (直接命令任务)")
    print("="*60)

    result = action_handler.process_command(agent_id, "TURN_ON oscilloscope_1")

    # 分离显示执行结果和验证结果
    print_action_result("打开示波器", result)

    # 提取验证数据
    verification_data = None
    if len(result) > 2 and isinstance(result[2], dict):
        verification_data = result[2].get('task_verification')

    if verification_data:
        print_verification_result(verification_data)

    assert_test(
        result[0].name == "SUCCESS",
        "打开示波器",
        "SUCCESS",
        result[0].name
    )
    wait_for_enter("测试4: 打开示波器")

    # 测试5: 移动到系数编程器
    print("\n" + "="*60)
    print("🧪 测试5: 移动到系数编程器")
    print("="*60)

    result = action_handler.process_command(agent_id, "GOTO coefficient_programmer_1")

    # 分离显示执行结果和验证结果
    print_action_result("移动到系数编程器", result)

    # 提取验证数据
    verification_data = None
    if len(result) > 2 and isinstance(result[2], dict):
        verification_data = result[2].get('task_verification')

    if verification_data:
        print_verification_result(verification_data)

    wait_for_enter("测试5: 移动到系数编程器")

    # 测试6: 插入系数编程器（直接命令任务）
    print("\n" + "="*60)
    print("🧪 测试6: 插入系数编程器 (直接命令任务)")
    print("="*60)

    result = action_handler.process_command(agent_id, "PLUG_IN coefficient_programmer_1")

    # 分离显示执行结果和验证结果
    print_action_result("插入系数编程器", result)

    # 提取验证数据
    verification_data = None
    if len(result) > 2 and isinstance(result[2], dict):
        verification_data = result[2].get('task_verification')

    if verification_data:
        print_verification_result(verification_data)

    assert_test(
        result[0].name == "SUCCESS",
        "插入系数编程器",
        "SUCCESS",
        result[0].name
    )
    wait_for_enter("测试6: 插入系数编程器")

    return True

def test_multi_agent_tasks():
    """测试多智能体任务"""
    print("\n👥 测试多智能体任务...")
    
    # 获取所有智能体
    agents = engine.agent_manager.get_all_agents()
    agent_ids = list(agents.keys())

    if len(agent_ids) < 2:
        print("❌ 需要至少2个智能体进行多智能体测试")
        return False

    agent1_id = agent_ids[0]
    agent2_id = agent_ids[1]
    agent1 = agents[agent1_id]
    agent2 = agents[agent2_id]

    print(f"🤖 智能体1: {agent1.name} (ID: {agent1_id})")
    print(f"🤖 智能体2: {agent2.name} (ID: {agent2_id})")

    action_handler = engine.action_handler

    # 测试7: 两个智能体都移动到原型制作区
    print("\n" + "="*60)
    print("🧪 测试7: 两个智能体都移动到原型制作区")
    print("="*60)

    result1 = action_handler.process_command(agent1_id, "GOTO prototyping_bay")
    result2 = action_handler.process_command(agent2_id, "GOTO prototyping_bay")

    print_action_result(f"智能体1 ({agent1.name}) 移动", result1)
    print_action_result(f"智能体2 ({agent2.name}) 移动", result2)

    # 显示最后一个结果的验证信息
    verification_data = None
    if len(result2) > 2 and isinstance(result2[2], dict):
        verification_data = result2[2].get('task_verification')

    if verification_data:
        print_verification_result(verification_data)

    wait_for_enter("测试7: 两个智能体都移动到原型制作区")

    # 测试8: 两个智能体都探索原型制作区
    print("\n" + "="*60)
    print("🧪 测试8: 两个智能体都探索原型制作区")
    print("="*60)

    result1 = action_handler.process_command(agent1_id, "EXPLORE prototyping_bay")
    result2 = action_handler.process_command(agent2_id, "EXPLORE prototyping_bay")

    print_action_result(f"智能体1 ({agent1.name}) 探索", result1)
    print_action_result(f"智能体2 ({agent2.name}) 探索", result2)

    # 显示最后一个结果的验证信息
    verification_data = None
    if len(result2) > 2 and isinstance(result2[2], dict):
        verification_data = result2[2].get('task_verification')

    if verification_data:
        print_verification_result(verification_data)

    wait_for_enter("测试8: 两个智能体都探索原型制作区")

    # 测试9: 简单的合作搬运任务（显式协作任务）
    print("\n" + "="*60)
    print("🧪 测试9: 简单的合作搬运任务 (显式协作任务)")
    print("="*60)

    # 查找一个重物进行合作搬运测试
    print("🔍 查找重物进行合作搬运测试...")

    # 首先确保两个智能体都移动到有重物的地方
    print("🎯 准备阶段: 两个智能体移动到FIR滤波器测试单元")
    print("─" * 30)
    result1 = action_handler.process_command(agent1_id, "GOTO fir_filter_testing_unit_1")
    result2 = action_handler.process_command(agent2_id, "GOTO fir_filter_testing_unit_1")

    print_action_result(f"智能体1 ({agent1.name}) 靠近FIR滤波器", result1)
    print_action_result(f"智能体2 ({agent2.name}) 靠近FIR滤波器", result2)

    # 尝试合作抓取重物
    print("\n🤝 协作阶段1: 合作抓取重物")
    print("─" * 30)
    corp_grab_command = f"CORP_GRAB {agent1_id},{agent2_id} fir_filter_testing_unit_1"
    result = action_handler.process_command(agent1_id, corp_grab_command)

    print_action_result("合作抓取FIR滤波器测试单元", result)

    # 提取验证数据
    verification_data = None
    if len(result) > 2 and isinstance(result[2], dict):
        verification_data = result[2].get('task_verification')

    if verification_data:
        print_verification_result(verification_data)

    # 如果抓取成功，尝试合作移动
    if result[0].name == "SUCCESS":
        print("\n🚚 协作阶段2: 合作移动到组件存储区")
        print("─" * 30)
        corp_goto_command = f"CORP_GOTO {agent1_id},{agent2_id} component_storage"
        result = action_handler.process_command(agent1_id, corp_goto_command)

        print_action_result("合作移动到组件存储区", result)

        # 提取验证数据
        verification_data = None
        if len(result) > 2 and isinstance(result[2], dict):
            verification_data = result[2].get('task_verification')

        if verification_data:
            print_verification_result(verification_data)

        # 如果移动成功，尝试合作放置
        if result[0].name == "SUCCESS":
            print("\n📦 协作阶段3: 合作放置重物")
            print("─" * 30)
            corp_place_command = f"CORP_PLACE {agent1_id},{agent2_id} fir_filter_testing_unit_1 component_storage"
            result = action_handler.process_command(agent1_id, corp_place_command)

            print_action_result("合作放置FIR滤波器测试单元", result)

            # 提取验证数据
            verification_data = None
            if len(result) > 2 and isinstance(result[2], dict):
                verification_data = result[2].get('task_verification')

            if verification_data:
                print_verification_result(verification_data)

            # 检查任务完成状态
            assert_test(
                result[0].name == "SUCCESS",
                "合作放置重物",
                "SUCCESS",
                result[0].name
            )

    wait_for_enter("测试9: 简单的合作搬运任务")

    return True

def main():
    """主函数"""
    global VERBOSE_MODE

    # 解析命令行参数
    parser = argparse.ArgumentParser(description='测试001号场景的任务')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='详细模式：每个测试后等待用户按回车继续，并启用可视化')

    args = parser.parse_args()
    VERBOSE_MODE = args.verbose

    if VERBOSE_MODE:
        print("🔍 详细模式已启用：每个测试后将等待您按回车继续")
        print("🌐 可视化已启用，可在浏览器访问: http://localhost:8082")

    print("🚀 开始测试001号场景的任务...")

    try:
        # 测试单智能体任务
        success1 = test_single_agent_tasks()
        
        # 测试多智能体任务
        success2 = test_multi_agent_tasks()

        # 打印测试总结
        print_test_summary()

        # 显示最终任务完成状态
        if 'engine' in globals():
            print("\n📊 最终任务完成状态:")
            final_status = engine.get_task_verification_status()
            if final_status:
                summary = final_status.get("completion_summary", {})
                print(f"   总任务数: {summary.get('total_tasks', 0)}")
                print(f"   已完成: {summary.get('completed_tasks', 0)}")
                print(f"   完成率: {summary.get('completion_rate', 0):.2%}")
                
                # 显示各类别完成情况
                categories = summary.get('categories', {})
                if categories:
                    print("   各类别完成情况:")
                    for category, info in categories.items():
                        category_name = {
                            'direct_command': '直接命令',
                            'attribute_reasoning': '属性推理',
                            'tool_use': '工具使用',
                            'compound_reasoning': '复合推理',
                            'explicit_collaboration': '显式协作',
                            'implicit_collaboration': '隐式协作',
                            'compound_collaboration': '复合协作'
                        }.get(category, category)
                        completed = info.get('completed', 0)
                        total = info.get('total', 0)
                        rate = info.get('completion_rate', 0.0)
                        print(f"     {category_name}: {completed}/{total} ({rate:.1%})")

        if success1 and success2:
            print("\n✅ 所有测试完成")
        else:
            print("\n❌ 部分测试失败")

        # 如果启用了可视化，提供查看选项
        if VERBOSE_MODE and 'engine' in globals():
            viz_status = engine.get_visualization_status()
            if viz_status.get('enabled') and viz_status.get('running'):
                print(f"\n🌐 可视化界面正在运行: {engine.get_visualization_url()}")
                print("📱 您可以在浏览器中查看当前状态和任务完成情况")
                print("⏳ 按回车键继续并停止可视化服务器...")
                try:
                    input()
                except KeyboardInterrupt:
                    pass
                print("🛑 正在停止可视化服务器...")
                engine.stop_visualization()

        # 返回适当的退出码
        failed_count = sum(1 for r in TEST_RESULTS if not r['passed'])
        sys.exit(failed_count)

    except Exception as e:
        print(f"\n💥 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
