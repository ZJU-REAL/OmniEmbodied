#!/usr/bin/env python3
"""
分析compound_collaboration任务的失败情况
"""

import pandas as pd
import json
import os
from collections import defaultdict, Counter

def load_csv_data():
    """加载CSV数据"""
    csv_path = "raw_output/20250723_225455_multi_independent_00001_to_00600_qianduoduo_4o_wo_multi/subtask_execution_log.csv"
    
    if not os.path.exists(csv_path):
        print(f"❌ CSV文件不存在: {csv_path}")
        return None
    
    df = pd.read_csv(csv_path)
    print(f"✅ 成功加载CSV文件，共 {len(df)} 条记录")
    return df

def analyze_compound_collaboration_tasks(df):
    """分析compound_collaboration任务"""
    
    # 筛选compound_collaboration任务
    compound_tasks = df[df['task_category'] == 'compound_collaboration'].copy()
    print(f"\n📊 compound_collaboration任务总数: {len(compound_tasks)}")
    
    # 统计成功率
    status_counts = compound_tasks['status'].value_counts()
    print(f"\n📈 任务状态分布:")
    for status, count in status_counts.items():
        percentage = (count / len(compound_tasks)) * 100
        print(f"  {status}: {count} ({percentage:.1f}%)")
    
    # 分析失败任务
    failed_tasks = compound_tasks[compound_tasks['status'].isin(['failed', 'none'])].copy()
    print(f"\n❌ 失败任务数量: {len(failed_tasks)} / {len(compound_tasks)} ({len(failed_tasks)/len(compound_tasks)*100:.1f}%)")
    
    return compound_tasks, failed_tasks

def analyze_failure_patterns(failed_tasks):
    """分析失败模式"""
    print(f"\n🔍 失败模式分析:")
    
    # 按subtask_completed分析
    subtask_completed_counts = failed_tasks['subtask_completed'].value_counts()
    print(f"\n子任务完成情况:")
    for completed, count in subtask_completed_counts.items():
        print(f"  subtask_completed={completed}: {count}")
    
    # 按model_claimed_done分析
    model_claimed_counts = failed_tasks['model_claimed_done'].value_counts()
    print(f"\n模型声称完成情况:")
    for claimed, count in model_claimed_counts.items():
        print(f"  model_claimed_done={claimed}: {count}")
    
    # 分析命令成功率
    print(f"\n命令成功率统计:")
    print(f"  平均命令成功率: {failed_tasks['command_success_rate'].mean():.3f}")
    print(f"  最低命令成功率: {failed_tasks['command_success_rate'].min():.3f}")
    print(f"  最高命令成功率: {failed_tasks['command_success_rate'].max():.3f}")
    
    # 分析LLM交互次数
    print(f"\nLLM交互次数统计:")
    print(f"  平均交互次数: {failed_tasks['llm_interactions'].mean():.1f}")
    print(f"  最少交互次数: {failed_tasks['llm_interactions'].min()}")
    print(f"  最多交互次数: {failed_tasks['llm_interactions'].max()}")

def load_task_and_scene_data(scenario_id):
    """加载任务和场景数据"""
    task_path = f"data/eval/multi-independent/task/{scenario_id:05d}_task.json"
    scene_path = f"data/eval/multi-independent/scene/{scenario_id:05d}_scene.json"
    
    task_data = None
    scene_data = None
    
    if os.path.exists(task_path):
        with open(task_path, 'r', encoding='utf-8') as f:
            task_data = json.load(f)
    
    if os.path.exists(scene_path):
        with open(scene_path, 'r', encoding='utf-8') as f:
            scene_data = json.load(f)
    
    return task_data, scene_data

def load_trajectory_data(scenario_id):
    """加载轨迹数据"""
    trajectory_path = f"raw_output/20250723_225455_multi_independent_00001_to_00600_qianduoduo_4o_wo_multi/trajectories/{scenario_id:05d}_trajectory.json"
    
    if os.path.exists(trajectory_path):
        with open(trajectory_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def categorize_failure_reasons(failed_tasks):
    """分类失败原因"""
    print(f"\n🔍 失败原因分类:")

    failure_categories = {
        'low_command_success': [],  # 命令成功率低
        'model_false_positive': [],  # 模型误报完成
        'timeout_failure': [],  # 超时失败
        'complex_task_failure': []  # 复杂任务失败
    }

    for _, task in failed_tasks.iterrows():
        scenario_id = int(task['scenario_id'])

        # 命令成功率低于50%
        if task['command_success_rate'] < 0.5:
            failure_categories['low_command_success'].append(scenario_id)

        # 模型声称完成但实际未完成
        if task['model_claimed_done'] and not task['subtask_completed']:
            failure_categories['model_false_positive'].append(scenario_id)

        # LLM交互次数达到上限(35次)
        if task['llm_interactions'] >= 35:
            failure_categories['timeout_failure'].append(scenario_id)

        # 任务描述包含多个动作的复杂任务
        if 'and use' in task['task_description'] or 'then' in task['task_description']:
            failure_categories['complex_task_failure'].append(scenario_id)

    for category, scenarios in failure_categories.items():
        print(f"\n{category}: {len(scenarios)} 个任务")
        if scenarios:
            print(f"  场景ID: {scenarios[:10]}{'...' if len(scenarios) > 10 else ''}")

    return failure_categories

def analyze_failed_task_details(failed_tasks):
    """详细分析失败任务"""
    print(f"\n🔍 失败任务详细分析:")
    print("=" * 80)

    # 按失败严重程度排序（命令成功率低的优先）
    failed_tasks_sorted = failed_tasks.sort_values('command_success_rate').reset_index(drop=True)

    for idx in range(min(15, len(failed_tasks_sorted))):  # 分析前15个最严重的失败任务
        task = failed_tasks_sorted.iloc[idx]
        scenario_id = int(task['scenario_id'])

        print(f"\n📋 失败任务 #{idx+1} (按严重程度排序)")
        print(f"场景ID: {scenario_id:05d}")
        print(f"任务描述: {task['task_description']}")
        print(f"状态: {task['status']}")
        print(f"子任务完成: {task['subtask_completed']}")
        print(f"模型声称完成: {task['model_claimed_done']}")
        print(f"命令成功率: {task['command_success_rate']:.3f}")
        print(f"LLM交互次数: {task['llm_interactions']}")
        print(f"执行时长: {task['duration_seconds']:.1f}秒")

        # 加载任务和场景数据
        task_data, scene_data = load_task_and_scene_data(scenario_id)

        if task_data:
            print(f"\n📝 任务详情:")
            if 'tasks' in task_data and len(task_data['tasks']) > 0:
                task_info = task_data['tasks'][0]  # 通常第一个任务
                print(f"  验证检查: {task_info.get('validation_checks', [])}")

        if scene_data:
            print(f"\n🏠 场景信息:")
            print(f"  场景名称: {scene_data.get('scene_name', 'N/A')}")
            print(f"  智能体数量: {len(scene_data.get('agents_config', []))}")

        # 加载轨迹数据
        trajectory_data = load_trajectory_data(scenario_id)
        if trajectory_data:
            print(f"\n🛤️ 轨迹信息:")
            if 'tasks' in trajectory_data and len(trajectory_data['tasks']) > 0:
                task_trajectory = trajectory_data['tasks'][0]
                print(f"  最终状态: {task_trajectory.get('final_status', 'N/A')}")
                if 'error_message' in task_trajectory:
                    print(f"  错误信息: {task_trajectory['error_message']}")

        print("-" * 60)

    if len(failed_tasks_sorted) > 15:
        print(f"\n... 还有 {len(failed_tasks_sorted) - 15} 个失败任务未显示")

def main():
    """主函数"""
    print("🔍 开始分析compound_collaboration任务失败情况...")
    
    # 加载数据
    df = load_csv_data()
    if df is None:
        return
    
    # 分析compound_collaboration任务
    compound_tasks, failed_tasks = analyze_compound_collaboration_tasks(df)
    
    # 分析失败模式
    analyze_failure_patterns(failed_tasks)
    
    # 详细分析失败任务
    analyze_failed_task_details(failed_tasks)
    
    print(f"\n✅ 分析完成！")

if __name__ == "__main__":
    main()
