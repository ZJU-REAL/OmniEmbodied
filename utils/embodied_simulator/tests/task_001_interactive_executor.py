#!/usr/bin/env python3
"""
001号场景第一个任务逐步执行脚本

通过API方式一步一步操作模拟器执行任务，支持可视化显示
用户可以按回车键进行下一步操作
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent  # 从tests目录向上一级到项目根目录
sys.path.insert(0, str(project_root))

from OmniEmbodied.simulator.core import SimulationEngine, ActionStatus
from OmniEmbodied.simulator.utils.data_loader import default_data_loader


class Task001StepByStepExecutor:
    """001号场景多任务逐步执行器"""

    def __init__(self):
        self.engine = None
        self.scene_data = None
        self.task_data = None
        self.verify_data = None
        self.agent_id = None  # 将在初始化后动态获取
        self.current_step = 0
        self.current_task_index = 0  # 当前任务索引

        # 所有任务的步骤定义
        self.all_tasks = [
            # 任务1：将示波器探头组放到机架式信号分析仪上
            [
                {
                    "command": "goto main_workbench_area",
                    "description": "移动到主工作台区域",
                    "explanation": "智能体需要先到达主工作台区域，这是任务的起始位置"
                },
                {
                    "command": "explore main_workbench_area",
                    "description": "探索主工作台区域",
                    "explanation": "探索区域以发现可用的物品和家具"
                },
                {
                    "command": "goto steel_workbench_1",
                    "description": "移动到钢制工作台",
                    "explanation": "移动到钢制工作台，示波器探头组就在这里"
                },
                {
                    "command": "grab oscilloscope_probe_set_1",
                    "description": "抓取示波器探头组",
                    "explanation": "抓取目标物品：示波器探头组"
                },
                {
                    "command": "goto signal_generation_testing_bay",
                    "description": "移动到信号生成测试区",
                    "explanation": "移动到目标区域，机架式信号分析仪在这里"
                },
                {
                    "command": "explore signal_generation_testing_bay",
                    "description": "探索信号生成测试区",
                    "explanation": "探索目标区域以找到机架式信号分析仪"
                },
                {
                    "command": "goto rack_mounted_signal_analyzer_1",
                    "description": "移动到机架式信号分析仪",
                    "explanation": "靠近目标设备以便放置物品"
                },
                {
                    "command": "place oscilloscope_probe_set_1 on rack_mounted_signal_analyzer_1",
                    "description": "将探头组放到分析仪上",
                    "explanation": "完成任务：将示波器探头组放置到机架式信号分析仪上"
                }
            ],
            # 任务2：打开位于钢制工作台上的双臂放大镜灯
            [
                {
                    "command": "goto main_workbench_area",
                    "description": "移动到主工作台区域",
                    "explanation": "返回主工作台区域执行第二个任务"
                },
                {
                    "command": "goto steel_workbench_1",
                    "description": "移动到钢制工作台",
                    "explanation": "双臂放大镜灯位于钢制工作台上"
                },
                {
                    "command": "goto dual_arm_magnifying_lamp_1",
                    "description": "移动到双臂放大镜灯",
                    "explanation": "靠近双臂放大镜灯以便操作"
                },
                {
                    "command": "turn_on dual_arm_magnifying_lamp_1",
                    "description": "打开双臂放大镜灯",
                    "explanation": "完成任务：打开双臂放大镜灯"
                }
            ],
            # 任务3：找到钢制工作台上最重的金属物体并放到存储组件架
            [
                {
                    "command": "goto main_workbench_area",
                    "description": "移动到主工作台区域",
                    "explanation": "返回主工作台区域执行第三个任务"
                },
                {
                    "command": "goto steel_workbench_1",
                    "description": "移动到钢制工作台",
                    "explanation": "需要在钢制工作台上寻找最重的金属物体"
                },
                {
                    "command": "goto calibration_jig_1",
                    "description": "移动到校准夹具",
                    "explanation": "校准夹具是钢制工作台上最重的金属物体（8.0kg，铝制）"
                },
                {
                    "command": "grab calibration_jig_1",
                    "description": "抓取校准夹具",
                    "explanation": "抓取目标物体：校准夹具"
                },
                {
                    "command": "goto storage_component_shelves",
                    "description": "移动到存储组件架",
                    "explanation": "移动到目标位置：存储组件架"
                },
                {
                    "command": "explore storage_component_shelves",
                    "description": "探索存储组件架",
                    "explanation": "探索存储区域以找到合适的放置位置"
                },
                {
                    "command": "place calibration_jig_1 in storage_component_shelves",
                    "description": "将校准夹具放入存储架",
                    "explanation": "完成任务：将校准夹具放置到存储组件架中"
                }
            ]
        ]

        # 当前任务的步骤（动态设置）
        self.task_steps = self.all_tasks[self.current_task_index] if self.all_tasks else []
    
    def initialize(self) -> bool:
        """初始化模拟器"""
        print("🚀 初始化001号场景任务执行器...")
        print("=" * 70)
        
        try:
            # 加载场景和任务数据
            print("📊 加载数据文件...")
            result = default_data_loader.load_complete_scenario("00001")
            if not result:
                print("❌ 数据加载失败")
                return False

            self.scene_data, self.task_data = result
            self.verify_data = None  # 验证数据暂时设为None
            
            print(f"✅ 场景数据加载成功: {len(self.scene_data.get('objects', []))} 个物体")
            print(f"✅ 任务数据加载成功: {len(self.task_data.get('tasks', []))} 个任务")
            
            # 创建模拟引擎（启用可视化）
            config = {
                'visualization': {
                    'enabled': True,
                    'web_server': {
                        'host': 'localhost',
                        'port': 8080,
                        'auto_open_browser': True
                    }
                },
                'task_verification': {
                    'enabled': True,
                    'mode': 'per_step'
                }
            }
            
            abilities = self.scene_data.get('abilities', [])
            self.engine = SimulationEngine(config=config, scene_abilities=abilities)
            
            # 初始化模拟器
            data = {'scene': self.scene_data, 'task': self.task_data}
            if self.verify_data:
                data['verify'] = self.verify_data
            success = self.engine.initialize_with_data(data)
            
            if not success:
                print("❌ 模拟器初始化失败")
                return False
            
            print("✅ 模拟器初始化成功")

            # 获取第一个智能体ID
            if self.engine.agent_manager:
                agents = self.engine.agent_manager.get_all_agents()
                if agents:
                    self.agent_id = list(agents.keys())[0]
                    print(f"🤖 使用智能体: {self.agent_id}")
                else:
                    print("❌ 没有找到智能体")
                    return False

            # 启动可视化
            if self.engine.visualization_manager:
                viz_url = self.engine.get_visualization_url()
                print(f"🌐 可视化界面: {viz_url}")
                print("💡 可视化界面将自动在浏览器中打开")

            return True
            
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def display_task_info(self):
        """显示当前任务信息"""
        print("\n" + "=" * 70)
        print("📋 任务信息")
        print("=" * 70)

        if self.task_data and 'tasks' in self.task_data:
            total_tasks = len(self.task_data['tasks'])
            current_task = self.task_data['tasks'][self.current_task_index]

            print(f"📊 任务进度: {self.current_task_index + 1}/{total_tasks}")
            print(f"🎯 当前任务: {current_task.get('task_description', '')}")
            print(f"🏷️  任务类型: {current_task.get('task_category', '')}")

            if 'validation_checks' in current_task:
                print("✅ 验证条件:")
                for check in current_task['validation_checks']:
                    if 'location_id' in check:
                        print(f"   - 物品 {check.get('id', '')} 应该位于 {check.get('location_id', '')}")
                    elif 'is_on' in check:
                        print(f"   - 设备 {check.get('id', '')} 应该处于开启状态")
                    else:
                        print(f"   - 物品 {check.get('id', '')} 需要满足特定条件")

        print(f"\n📝 当前任务步骤总数: {len(self.task_steps)}")
        print("💡 按回车键开始执行任务...")
    
    def display_current_status(self):
        """显示当前状态"""
        print("\n" + "-" * 50)
        print("📊 当前状态")
        print("-" * 50)
        
        # 获取智能体信息
        if self.engine and self.engine.agent_manager:
            agents = self.engine.agent_manager.get_all_agents()
            if self.agent_id in agents:
                agent = agents[self.agent_id]
                print(f"🤖 智能体: {agent.name}")
                print(f"📍 位置: {agent.location_id}")
                print(f"🎒 持有物品: {', '.join(agent.inventory) if agent.inventory else '无'}")
                print(f"🔧 当前能力: {', '.join(agent.abilities) if agent.abilities else '无'}")
        
        # 显示任务验证状态
        if self.engine and self.engine.task_verifier:
            try:
                results = self.engine.task_verifier.verify_all_tasks()
                summary = self.engine.task_verifier.get_completion_summary()
                completed = summary.get('completed_tasks', 0)
                total = summary.get('total_tasks', 0)
                print(f"✅ 任务完成情况: {completed}/{total}")
            except Exception as e:
                print(f"⚠️  任务验证状态获取失败: {e}")
    
    def execute_step(self, step_index: int) -> bool:
        """执行指定步骤"""
        if step_index >= len(self.task_steps):
            print("❌ 步骤索引超出范围")
            return False
        
        step = self.task_steps[step_index]
        
        print(f"\n🔄 步骤 {step_index + 1}/{len(self.task_steps)}: {step['description']}")
        print(f"💡 说明: {step['explanation']}")
        print(f"🎮 命令: {step['command']}")
        
        try:
            # 执行命令
            status, message, result = self.engine.process_command(self.agent_id, step['command'])
            
            # 显示执行结果
            if status == ActionStatus.SUCCESS:
                print(f"✅ 执行成功: {message}")
            elif status == ActionStatus.FAILURE:
                print(f"❌ 执行失败: {message}")
                return False
            else:
                print(f"⚠️  执行状态: {status}, 消息: {message}")
            
            # 显示任务验证结果
            if result and 'task_verification' in result:
                verification = result['task_verification']
                if 'completion_summary' in verification:
                    summary = verification['completion_summary']
                    completed = summary.get('completed_tasks', 0)
                    total = summary.get('total_tasks', 0)
                    print(f"📊 任务进度: {completed}/{total}")
            
            return True
            
        except Exception as e:
            print(f"❌ 执行步骤时发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_interactive(self):
        """交互式运行"""
        print("\n🎮 开始交互式执行")
        print("💡 按回车键执行下一步，输入 'q' 退出，输入 's' 查看状态")
        
        while self.current_step < len(self.task_steps):
            self.display_current_status()
            
            print(f"\n⏭️  准备执行步骤 {self.current_step + 1}/{len(self.task_steps)}")
            step = self.task_steps[self.current_step]
            print(f"📝 下一步: {step['description']}")
            
            user_input = input("按回车继续，输入 'q' 退出，输入 's' 查看详细状态: ").strip().lower()
            
            if user_input == 'q':
                print("👋 用户退出")
                break
            elif user_input == 's':
                self.display_detailed_status()
                continue
            
            # 执行步骤
            success = self.execute_step(self.current_step)
            if not success:
                print("❌ 步骤执行失败，是否继续？")
                continue_input = input("输入 'y' 继续，其他键退出: ").strip().lower()
                if continue_input != 'y':
                    break
            
            self.current_step += 1
        
        # 任务完成检查
        if self.current_step >= len(self.task_steps):
            print(f"\n🎉 任务 {self.current_task_index + 1} 的所有步骤执行完成！")

            # 检查是否还有更多任务
            if self.current_task_index + 1 < len(self.all_tasks):
                print(f"\n🔄 准备执行下一个任务...")
                continue_next = input("是否继续执行下一个任务？(y/n): ").strip().lower()

                if continue_next == 'y':
                    self.switch_to_next_task()
                    self.run_interactive()  # 递归调用执行下一个任务
                else:
                    print("👋 用户选择不继续执行下一个任务")
            else:
                print("\n🎊 恭喜！所有任务都已完成！")
                self.final_verification()
    
    def switch_to_next_task(self):
        """切换到下一个任务"""
        if self.current_task_index + 1 < len(self.all_tasks):
            self.current_task_index += 1
            self.task_steps = self.all_tasks[self.current_task_index]
            self.current_step = 0

            print(f"\n🔄 切换到任务 {self.current_task_index + 1}")
            self.display_task_info()
            input("按回车键开始执行新任务...")
        else:
            print("❌ 没有更多任务可执行")

    def display_detailed_status(self):
        """显示详细状态"""
        print("\n" + "=" * 70)
        print("📊 详细状态信息")
        print("=" * 70)

        if self.engine and self.engine.world_state:
            # 显示环境描述
            env_desc = self.engine.world_state.describe_environment_natural_language()
            print("🌍 环境状态:")
            print(env_desc)
    
    def final_verification(self):
        """最终验证"""
        print("\n" + "=" * 70)
        print("🔍 最终任务验证")
        print("=" * 70)
        
        try:
            # 执行done命令进行全局验证
            status, message, result = self.engine.process_command(self.agent_id, "done")
            
            print(f"验证结果: {message}")
            
            if result and 'task_verification' in result:
                verification = result['task_verification']
                if 'completion_summary' in verification:
                    summary = verification['completion_summary']
                    completed = summary.get('completed_tasks', 0)
                    total = summary.get('total_tasks', 0)
                    completion_rate = summary.get('completion_rate', 0)
                    
                    print(f"✅ 最终任务完成情况: {completed}/{total} ({completion_rate:.1%})")
                    
                    if completed == total:
                        print("🎉 恭喜！所有任务都已完成！")
                    else:
                        print("⚠️  还有任务未完成")
        
        except Exception as e:
            print(f"❌ 最终验证失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        if self.engine and self.engine.visualization_manager:
            print("\n🛑 关闭可视化系统...")
            self.engine.stop_visualization()
        print("✅ 清理完成")


def main():
    """主函数"""
    print("🎯 001号场景多任务逐步执行器")
    print("=" * 70)
    print("📋 支持任务:")
    print("   1. 将示波器探头组放到机架式信号分析仪上")
    print("   2. 打开位于钢制工作台上的双臂放大镜灯")
    print("   3. 找到钢制工作台上最重的金属物体并放到存储组件架")
    print("🎯 特色: API方式逐步操作 + 实时可视化 + 多任务支持")
    print("=" * 70)
    
    executor = Task001StepByStepExecutor()
    
    try:
        # 初始化
        if not executor.initialize():
            print("❌ 初始化失败，程序退出")
            return 1
        
        # 显示任务信息
        executor.display_task_info()
        input()  # 等待用户按回车
        
        # 交互式运行
        executor.run_interactive()
        
        # 保持可视化界面开启
        print("\n💡 可视化界面仍在运行，按回车键退出程序...")
        input()
        
    except KeyboardInterrupt:
        print("\n👋 用户中断程序")
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        executor.cleanup()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
