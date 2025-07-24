#!/usr/bin/env python3
"""
验证任务文件更新结果的脚本
"""

import json
import os
from pathlib import Path
from collections import defaultdict

def verify_updates():
    """
    验证更新结果
    """
    task_dir = Path("/home/wzx/workspace/OmniEmbodied/data/eval/multi-independent/task")
    
    stats = {
        'total_files': 0,
        'weight_ranges': defaultdict(int),
        'compound_collaboration_tasks': 0,
        'compound_collaboration_updated': 0,
        'move_tasks': 0,
        'non_move_tasks': 0
    }
    
    for task_file in sorted(task_dir.glob("*_task.json")):
        stats['total_files'] += 1
        
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                task_data = json.load(f)
            
            # 检查智能体重量
            for agent in task_data.get('agents_config', []):
                weight = agent.get('max_weight', 0)
                if 1 <= weight <= 4:
                    stats['weight_ranges']['1-4'] += 1
                elif 5 <= weight <= 30:
                    stats['weight_ranges']['5-30'] += 1
                else:
                    stats['weight_ranges']['other'] += 1
            
            # 检查任务类型
            for task in task_data.get('tasks', []):
                if task.get('task_category') == 'compound_collaboration':
                    stats['compound_collaboration_tasks'] += 1
                    
                    # 检查是否正确更新了描述
                    description = task.get('task_description', '')
                    if not description.startswith('Cooperatively ') and ' and cooperatively ' in description:
                        stats['compound_collaboration_updated'] += 1
                
                # 检查是否为move任务
                validation_checks = task.get('validation_checks', [])
                is_move_task = any('location_id' in check for check in validation_checks)
                if is_move_task:
                    stats['move_tasks'] += 1
                else:
                    stats['non_move_tasks'] += 1
                    
        except Exception as e:
            print(f"错误: 无法处理文件 {task_file}: {e}")
    
    # 打印统计结果
    print("=== 更新结果验证 ===")
    print(f"总文件数: {stats['total_files']}")
    print(f"Move任务数: {stats['move_tasks']}")
    print(f"非Move任务数: {stats['non_move_tasks']}")
    print(f"Compound collaboration任务数: {stats['compound_collaboration_tasks']}")
    print(f"Compound collaboration任务更新数: {stats['compound_collaboration_updated']}")
    print("\n智能体重量分布:")
    for range_name, count in stats['weight_ranges'].items():
        print(f"  {range_name}: {count}")
    
    print(f"\n更新成功率:")
    if stats['compound_collaboration_tasks'] > 0:
        success_rate = stats['compound_collaboration_updated'] / stats['compound_collaboration_tasks'] * 100
        print(f"  Compound collaboration任务描述更新: {success_rate:.1f}%")

if __name__ == "__main__":
    verify_updates()
