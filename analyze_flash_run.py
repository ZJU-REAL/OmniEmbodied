#!/usr/bin/env python3
"""
分析 Gemini 2.5 Flash 模型在多智能体任务上的表现
特别关注 compound_collaboration 任务的失败情况
"""

import pandas as pd
import json
import os
from collections import defaultdict, Counter

def load_csv_data():
    """加载CSV数据"""
    csv_path = "output/20250724_183034_multi_independent_00001_to_00600_qianduoduo_2.5-flash_wo_multi/subtask_execution_log.csv"
    
    if not os.path.exists(csv_path):
        print(f"❌ CSV文件不存在: {csv_path}")
        return None
    
    df = pd.read_csv(csv_path)
    print(f"✅ 成功加载CSV文件，共 {len(df)} 条记录")
    return df

def analyze_overall_performance(df):
    """分析整体性能"""
    print(f"\n📊 整体性能分析:")
    print(f"总任务数: {len(df)}")
    
    # 按任务类别统计
    category_stats = df.groupby('task_category').agg({
        'subtask_completed': ['count', 'sum'],
        'model_claimed_done': 'sum',
        'command_success_rate': 'mean',
        'llm_interactions': 'mean',
        'duration_seconds': 'mean'
    }).round(3)
    
    print(f"\n📈 各任务类别表现:")
    for category in df['task_category'].unique():
        category_data = df[df['task_category'] == category]
        total = len(category_data)
        completed = category_data['subtask_completed'].sum()
        model_claimed = category_data['model_claimed_done'].sum()
        completion_rate = completed / total
        avg_cmd_success = category_data['command_success_rate'].mean()
        avg_interactions = category_data['llm_interactions'].mean()
        avg_duration = category_data['duration_seconds'].mean()
        
        print(f"\n{category}:")
        print(f"  总数: {total}")
        print(f"  实际完成: {completed} ({completion_rate:.1%})")
        print(f"  模型声称完成: {model_claimed}")
        print(f"  平均命令成功率: {avg_cmd_success:.3f}")
        print(f"  平均LLM交互次数: {avg_interactions:.1f}")
        print(f"  平均执行时长: {avg_duration:.1f}秒")

def analyze_compound_collaboration_failures(df):
    """深入分析compound_collaboration任务的失败情况"""
    compound_tasks = df[df['task_category'] == 'compound_collaboration'].copy()
    failed_tasks = compound_tasks[compound_tasks['subtask_completed'] == False].copy()
    
    print(f"\n🔍 compound_collaboration 任务失败分析:")
    print(f"总数: {len(compound_tasks)}")
    print(f"失败数: {len(failed_tasks)} ({len(failed_tasks)/len(compound_tasks):.1%})")
    
    # 分析失败原因
    print(f"\n失败任务状态分布:")
    status_counts = failed_tasks['status'].value_counts()
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    
    # 分析模型误判情况
    false_positives = failed_tasks[failed_tasks['model_claimed_done'] == True]
    print(f"\n模型误判完成的失败任务: {len(false_positives)} / {len(failed_tasks)} ({len(false_positives)/len(failed_tasks):.1%})")
    
    # 分析命令成功率分布
    print(f"\n失败任务命令成功率统计:")
    print(f"  平均: {failed_tasks['command_success_rate'].mean():.3f}")
    print(f"  中位数: {failed_tasks['command_success_rate'].median():.3f}")
    print(f"  最低: {failed_tasks['command_success_rate'].min():.3f}")
    print(f"  最高: {failed_tasks['command_success_rate'].max():.3f}")
    
    # 按命令成功率分组
    low_success = failed_tasks[failed_tasks['command_success_rate'] < 0.3]
    medium_success = failed_tasks[(failed_tasks['command_success_rate'] >= 0.3) & (failed_tasks['command_success_rate'] < 0.7)]
    high_success = failed_tasks[failed_tasks['command_success_rate'] >= 0.7]
    
    print(f"\n按命令成功率分组:")
    print(f"  低成功率 (<30%): {len(low_success)} 个任务")
    print(f"  中等成功率 (30%-70%): {len(medium_success)} 个任务")
    print(f"  高成功率 (>=70%): {len(high_success)} 个任务")
    
    return compound_tasks, failed_tasks

def analyze_task_patterns(failed_tasks):
    """分析失败任务的模式"""
    print(f"\n🔍 失败任务模式分析:")
    
    # 分析任务描述中的关键词
    task_keywords = defaultdict(int)
    for desc in failed_tasks['task_description']:
        desc_lower = desc.lower()
        if 'printer' in desc_lower:
            task_keywords['printer'] += 1
        if 'heavy' in desc_lower:
            task_keywords['heavy'] += 1
        if 'repair' in desc_lower:
            task_keywords['repair'] += 1
        if 'use' in desc_lower or 'using' in desc_lower:
            task_keywords['use_tool'] += 1
        if 'move' in desc_lower:
            task_keywords['move'] += 1
        if 'open' in desc_lower:
            task_keywords['open'] += 1
        if 'turn on' in desc_lower:
            task_keywords['turn_on'] += 1
    
    print(f"\n失败任务关键词统计:")
    for keyword, count in sorted(task_keywords.items(), key=lambda x: x[1], reverse=True):
        print(f"  {keyword}: {count}")
    
    # 分析LLM交互次数
    print(f"\nLLM交互次数分析:")
    print(f"  平均: {failed_tasks['llm_interactions'].mean():.1f}")
    print(f"  中位数: {failed_tasks['llm_interactions'].median():.1f}")
    print(f"  最多: {failed_tasks['llm_interactions'].max()}")
    print(f"  最少: {failed_tasks['llm_interactions'].min()}")
    
    # 达到最大交互次数的任务
    max_interactions = failed_tasks[failed_tasks['llm_interactions'] == 35]
    print(f"  达到最大交互次数(35)的任务: {len(max_interactions)}")

def analyze_specific_failures(failed_tasks):
    """分析具体的失败案例"""
    print(f"\n🔍 具体失败案例分析:")
    print("=" * 80)
    
    # 按命令成功率排序，分析最严重的失败
    failed_sorted = failed_tasks.sort_values('command_success_rate').reset_index(drop=True)
    
    for idx in range(min(10, len(failed_sorted))):
        task = failed_sorted.iloc[idx]
        scenario_id = int(task['scenario_id'])
        
        print(f"\n📋 失败案例 #{idx+1}")
        print(f"场景ID: {scenario_id:05d}")
        print(f"任务描述: {task['task_description']}")
        print(f"状态: {task['status']}")
        print(f"模型声称完成: {task['model_claimed_done']}")
        print(f"命令成功率: {task['command_success_rate']:.3f}")
        print(f"LLM交互次数: {task['llm_interactions']}")
        print(f"执行时长: {task['duration_seconds']:.1f}秒")
        
        # 尝试加载轨迹数据
        trajectory_path = f"output/20250724_183034_multi_independent_00001_to_00600_qianduoduo_2.5-flash_wo_multi/trajectories/{scenario_id:05d}_task_00001_trajectory.json"
        if os.path.exists(trajectory_path):
            try:
                with open(trajectory_path, 'r', encoding='utf-8') as f:
                    trajectory_data = json.load(f)
                    if 'error_message' in trajectory_data:
                        print(f"错误信息: {trajectory_data['error_message']}")
                    if 'final_status' in trajectory_data:
                        print(f"最终状态: {trajectory_data['final_status']}")
            except:
                pass
        
        print("-" * 60)

def compare_with_gpt4_results():
    """与GPT-4结果对比"""
    print(f"\n📊 与GPT-4结果对比:")
    
    # 加载GPT-4的结果
    gpt4_path = "raw_output/20250723_225455_multi_independent_00001_to_00600_qianduoduo_4o_wo_multi/subtask_execution_log.csv"
    if os.path.exists(gpt4_path):
        gpt4_df = pd.read_csv(gpt4_path)
        gpt4_compound = gpt4_df[gpt4_df['task_category'] == 'compound_collaboration']
        gpt4_completion_rate = gpt4_compound['subtask_completed'].mean()
        
        # 加载Flash结果
        flash_path = "output/20250724_183034_multi_independent_00001_to_00600_qianduoduo_2.5-flash_wo_multi/subtask_execution_log.csv"
        flash_df = pd.read_csv(flash_path)
        flash_compound = flash_df[flash_df['task_category'] == 'compound_collaboration']
        flash_completion_rate = flash_compound['subtask_completed'].mean()
        
        print(f"GPT-4 compound_collaboration 完成率: {gpt4_completion_rate:.1%}")
        print(f"Gemini 2.5 Flash compound_collaboration 完成率: {flash_completion_rate:.1%}")
        print(f"性能差距: {(gpt4_completion_rate - flash_completion_rate):.1%}")
        
        # 详细对比
        print(f"\n详细对比:")
        print(f"GPT-4: 总数 {len(gpt4_compound)}, 完成 {gpt4_compound['subtask_completed'].sum()}")
        print(f"Flash: 总数 {len(flash_compound)}, 完成 {flash_compound['subtask_completed'].sum()}")
    else:
        print("未找到GPT-4结果文件，无法对比")

def main():
    """主函数"""
    print("🔍 开始分析 Gemini 2.5 Flash 模型表现...")
    
    # 加载数据
    df = load_csv_data()
    if df is None:
        return
    
    # 整体性能分析
    analyze_overall_performance(df)
    
    # compound_collaboration失败分析
    compound_tasks, failed_tasks = analyze_compound_collaboration_failures(df)
    
    # 任务模式分析
    analyze_task_patterns(failed_tasks)
    
    # 具体失败案例分析
    analyze_specific_failures(failed_tasks)
    
    # 与GPT-4对比
    compare_with_gpt4_results()
    
    print(f"\n✅ 分析完成！")

if __name__ == "__main__":
    main()
