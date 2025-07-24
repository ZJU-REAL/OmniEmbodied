#!/usr/bin/env python3
"""
检查task json文件中的scene_id是与文件名对应还是与json中的id对应

分析规律：
- 文件名格式：00XXX_task.json
- scene_id格式：00YYY

检查是否 XXX == YYY (文件名对应) 还是存在其他映射关系
"""

import json
import os
import glob
from collections import defaultdict

def analyze_scene_id_pattern():
    """分析scene_id的对应模式"""
    
    data_dir = "/home/wzx/workspace/OmniEmbodied/data/eval/multi-independent"
    task_dir = os.path.join(data_dir, "task")
    
    # 获取所有任务文件
    task_files = glob.glob(os.path.join(task_dir, "*_task.json"))
    # 排除备份文件
    task_files = [f for f in task_files if not f.endswith('.backup_types') and 'backup_' not in f]
    task_files.sort()
    
    print(f"找到 {len(task_files)} 个任务文件")
    
    # 统计数据
    filename_matches = 0  # 文件名与scene_id匹配的数量
    filename_mismatches = 0  # 文件名与scene_id不匹配的数量
    scene_id_mapping = defaultdict(list)  # scene_id -> [task_files]
    mismatch_examples = []
    
    for task_file in task_files:
        # 提取文件名中的数字
        filename = os.path.basename(task_file)
        file_number = filename.split('_')[0]  # 00XXX
        
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                task_data = json.load(f)
            
            scene_id = task_data.get("scene_id", "")
            scene_id_mapping[scene_id].append(filename)
            
            if file_number == scene_id:
                filename_matches += 1
            else:
                filename_mismatches += 1
                mismatch_examples.append({
                    "file": filename,
                    "file_number": file_number,
                    "scene_id": scene_id
                })
                
        except Exception as e:
            print(f"Error processing {task_file}: {e}")
    
    print("\n=== 分析结果 ===")
    print(f"文件名与scene_id匹配: {filename_matches}")
    print(f"文件名与scene_id不匹配: {filename_mismatches}")
    print(f"匹配率: {filename_matches/(filename_matches+filename_mismatches)*100:.1f}%")
    
    print(f"\n=== Scene ID使用统计 ===")
    print(f"总共使用了 {len(scene_id_mapping)} 个不同的scene_id")
    
    # 显示每个scene_id被多少个任务使用
    scene_usage = [(scene_id, len(files)) for scene_id, files in scene_id_mapping.items()]
    scene_usage.sort(key=lambda x: x[1], reverse=True)
    
    print("\nScene ID使用频率 (前20个):")
    for scene_id, count in scene_usage[:20]:
        print(f"  {scene_id}: {count} 个任务")
    
    print(f"\n=== 不匹配示例 (前10个) ===")
    for example in mismatch_examples[:10]:
        print(f"文件: {example['file']} -> scene_id: {example['scene_id']}")
    
    # 分析模式
    print(f"\n=== 模式分析 ===")
    if filename_matches > filename_mismatches:
        print("结论: 主要模式是文件名与scene_id对应")
        print("但存在一些例外情况，可能是多个任务共享同一个场景")
    else:
        print("结论: 文件名与scene_id不是一一对应关系")
        print("任务文件中的scene_id指向的是实际要使用的场景文件")
    
    return {
        "filename_matches": filename_matches,
        "filename_mismatches": filename_mismatches,
        "scene_id_mapping": dict(scene_id_mapping),
        "mismatch_examples": mismatch_examples
    }

def check_scene_files_exist():
    """检查scene_id对应的场景文件是否存在"""
    
    data_dir = "/home/wzx/workspace/OmniEmbodied/data/eval/multi-independent"
    task_dir = os.path.join(data_dir, "task")
    scene_dir = os.path.join(data_dir, "scene")
    
    task_files = glob.glob(os.path.join(task_dir, "*_task.json"))
    task_files = [f for f in task_files if not f.endswith('.backup_types') and 'backup_' not in f]
    
    missing_scenes = []
    existing_scenes = set()
    
    for task_file in task_files:
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                task_data = json.load(f)
            
            scene_id = task_data.get("scene_id", "")
            scene_file = os.path.join(scene_dir, f"{scene_id}_scene.json")
            
            if os.path.exists(scene_file):
                existing_scenes.add(scene_id)
            else:
                missing_scenes.append({
                    "task_file": os.path.basename(task_file),
                    "scene_id": scene_id,
                    "expected_scene_file": f"{scene_id}_scene.json"
                })
                
        except Exception as e:
            print(f"Error processing {task_file}: {e}")
    
    print(f"\n=== 场景文件存在性检查 ===")
    print(f"存在的场景文件: {len(existing_scenes)} 个")
    print(f"缺失的场景文件: {len(missing_scenes)} 个")
    
    if missing_scenes:
        print("\n缺失的场景文件:")
        for missing in missing_scenes[:10]:  # 只显示前10个
            print(f"  任务: {missing['task_file']} -> 缺失场景: {missing['expected_scene_file']}")
    
    return missing_scenes

def verify_object_existence():
    """验证任务中引用的物品是否真的存在于对应的场景中"""

    data_dir = "/home/wzx/workspace/OmniEmbodied/data/eval/multi-independent"
    task_dir = os.path.join(data_dir, "task")
    scene_dir = os.path.join(data_dir, "scene")

    # 检查几个具体例子
    test_cases = [
        ("00009_task.json", "white_noise_generator_1"),
        ("00010_task.json", "war_table_1"),
        ("00011_task.json", "press_1")
    ]

    print(f"\n=== 验证物品存在性 ===")

    for task_file, object_id in test_cases:
        task_path = os.path.join(task_dir, task_file)

        try:
            with open(task_path, 'r', encoding='utf-8') as f:
                task_data = json.load(f)

            scene_id = task_data.get("scene_id", "")
            scene_path = os.path.join(scene_dir, f"{scene_id}_scene.json")

            # 检查场景文件是否存在
            if not os.path.exists(scene_path):
                print(f"❌ {task_file}: 场景文件 {scene_id}_scene.json 不存在")
                continue

            # 检查物品是否存在于场景中
            with open(scene_path, 'r', encoding='utf-8') as f:
                scene_data = json.load(f)

            objects = scene_data.get("objects", [])
            object_found = any(obj.get("id") == object_id for obj in objects)

            if object_found:
                print(f"✅ {task_file}: 物品 {object_id} 存在于场景 {scene_id}")
            else:
                print(f"❌ {task_file}: 物品 {object_id} 不存在于场景 {scene_id}")

                # 检查是否存在于对应编号的场景中
                correct_scene_id = task_file.split('_')[0]  # 00009 -> 00009
                correct_scene_path = os.path.join(scene_dir, f"{correct_scene_id}_scene.json")

                if os.path.exists(correct_scene_path):
                    with open(correct_scene_path, 'r', encoding='utf-8') as f:
                        correct_scene_data = json.load(f)

                    correct_objects = correct_scene_data.get("objects", [])
                    object_in_correct_scene = any(obj.get("id") == object_id for obj in correct_objects)

                    if object_in_correct_scene:
                        print(f"   💡 但物品 {object_id} 存在于对应编号的场景 {correct_scene_id}")
                    else:
                        print(f"   ❌ 物品 {object_id} 也不存在于对应编号的场景 {correct_scene_id}")

        except Exception as e:
            print(f"Error processing {task_file}: {e}")

if __name__ == "__main__":
    print("开始分析scene_id对应模式...")

    # 分析scene_id模式
    result = analyze_scene_id_pattern()

    # 检查场景文件存在性
    missing_scenes = check_scene_files_exist()

    # 验证物品存在性
    verify_object_existence()

    print(f"\n=== 最终结论 ===")
    if result["filename_matches"] > result["filename_mismatches"]:
        print("✅ 主要模式：文件名与scene_id对应")
        print("   例如：00010_task.json 中的 scene_id 应该是 '00010'")
        print("   但存在例外情况，多个任务可能共享同一个场景")
    else:
        print("❌ 文件名与scene_id不是直接对应关系")
        print("   任务文件中的scene_id指向实际要使用的场景文件")
        print("   系统应该根据json中的scene_id来加载对应的场景文件")
        print("   但这可能存在数据不一致的问题！")

    if missing_scenes:
        print(f"\n⚠️  发现 {len(missing_scenes)} 个任务引用了不存在的场景文件")
        print("   这可能导致任务执行失败")
