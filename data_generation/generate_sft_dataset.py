#!/usr/bin/env python3
"""
SFT数据集生成器
从源数据集中提取指定类型的任务，生成用于监督微调的训练数据集
支持场景范围过滤和智能采样策略，确保数据质量和多样性
"""

import os
import sys
import json
import shutil
import platform
import random
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Set
from collections import defaultdict, Counter
import yaml
from tqdm import tqdm


class SFTDatasetGenerator:
    """SFT数据集生成器"""

    def __init__(self, config_path: str = None):
        """初始化生成器"""
        if config_path is None:
            # 默认配置文件路径
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "data_generation" / "sft_dataset_config.yaml"

        self.config = self.load_config(config_path)
        self.project_root = Path(__file__).parent.parent
        self.validate_config()

        # 任务计数器和场景跟踪
        self.task_counters = Counter()
        self.used_scenes_per_category = defaultdict(set)  # 每个类别已使用的场景
        self.generated_files = 0

        # 操作系统检测
        self.os_type = platform.system().lower()
        self.supports_symlinks = self.os_type in ['linux', 'darwin'] or (
            self.os_type == 'windows' and self._check_windows_symlink_support()
        )
    
    def _check_windows_symlink_support(self) -> bool:
        """检查Windows是否支持符号链接"""
        try:
            # 尝试创建一个测试符号链接
            test_file = Path("test_symlink_check.tmp")
            test_link = Path("test_symlink_check_link.tmp")
            
            test_file.touch()
            os.symlink(test_file, test_link)
            
            # 清理测试文件
            test_link.unlink()
            test_file.unlink()
            return True
        except (OSError, NotImplementedError):
            return False
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件格式错误: {e}")
    
    def validate_config(self):
        """验证配置文件有效性"""
        required_keys = [
            'source.data_dir', 'source.task_subdir', 'source.scene_subdir',
            'output.output_dir', 'output.task_subdir', 'output.scene_subdir',
            'scene_filter.min_scene_id', 'scene_filter.max_scene_id',
            'task_filter.single_agent_tasks', 'task_filter.multi_agent_tasks',
            'agent_selection.single_agent_strategy', 'agent_selection.multi_agent_strategy',
            'scene_processing.create_scene_links',
            'sampling.ensure_scene_diversity', 'sampling.insufficient_scenes_strategy'
        ]

        for key in required_keys:
            keys = key.split('.')
            current = self.config
            try:
                for k in keys:
                    current = current[k]
            except KeyError:
                raise ValueError(f"配置文件缺少必需的键: {key}")

        # 验证任务类型
        valid_single_agent_categories = {'direct_command', 'attribute_reasoning', 'tool_use', 'compound_reasoning'}
        valid_multi_agent_categories = {'explicit_collaboration', 'implicit_collaboration', 'compound_collaboration'}

        single_agent_tasks = set(self.config['task_filter']['single_agent_tasks'].keys())
        multi_agent_tasks = set(self.config['task_filter']['multi_agent_tasks'].keys())

        invalid_single = single_agent_tasks - valid_single_agent_categories
        if invalid_single:
            raise ValueError(f"单智能体任务类型无效: {invalid_single}")

        invalid_multi = multi_agent_tasks - valid_multi_agent_categories
        if invalid_multi:
            raise ValueError(f"多智能体任务类型无效: {invalid_multi}")

        # 验证场景范围
        min_scene = self.config['scene_filter']['min_scene_id']
        max_scene = self.config['scene_filter']['max_scene_id']
        if min_scene >= max_scene:
            raise ValueError(f"场景范围配置错误: min_scene_id ({min_scene}) >= max_scene_id ({max_scene})")
    
    def extract_scene_id_from_filename(self, filename: str) -> Optional[int]:
        """从文件名中提取场景ID"""
        try:
            # 假设文件名格式为 "XXXXX_task.json"
            scene_id_str = filename.split('_')[0]
            return int(scene_id_str)
        except (ValueError, IndexError):
            return None
    
    def is_scene_in_range(self, scene_id: int) -> bool:
        """检查场景ID是否在指定范围内"""
        min_scene = self.config['scene_filter']['min_scene_id']
        max_scene = self.config['scene_filter']['max_scene_id']
        return min_scene <= scene_id <= max_scene
    
    def get_source_paths(self) -> Tuple[Path, Path]:
        """获取源数据路径"""
        source_config = self.config['source']
        task_dir = self.project_root / source_config['data_dir'] / source_config['task_subdir']
        scene_dir = self.project_root / source_config['data_dir'] / source_config['scene_subdir']
        
        if not task_dir.exists():
            raise FileNotFoundError(f"源任务目录不存在: {task_dir}")
        if not scene_dir.exists():
            raise FileNotFoundError(f"源场景目录不存在: {scene_dir}")
        
        return task_dir, scene_dir
    
    def get_output_paths(self) -> Tuple[Path, Path]:
        """获取输出路径"""
        output_config = self.config['output']
        output_root = self.project_root / output_config['output_dir']
        task_output_dir = output_root / output_config['task_subdir']
        scene_output_dir = output_root / output_config['scene_subdir']
        
        # 创建输出目录
        task_output_dir.mkdir(parents=True, exist_ok=True)
        scene_output_dir.mkdir(parents=True, exist_ok=True)
        
        return task_output_dir, scene_output_dir

    def create_output_structure(self, subdir_name: str) -> Tuple[Path, Path]:
        """创建输出目录结构"""
        output_config = self.config['output']
        output_root = self.project_root / output_config['output_dir'] / subdir_name
        task_output_dir = output_root / output_config['task_subdir']
        scene_output_dir = output_root / output_config['scene_subdir']

        # 创建输出目录
        task_output_dir.mkdir(parents=True, exist_ok=True)
        scene_output_dir.mkdir(parents=True, exist_ok=True)

        return task_output_dir, scene_output_dir
    
    def scan_source_files(self, task_dir: Path) -> List[Path]:
        """扫描源数据文件，只包含指定场景范围内的文件"""
        all_task_files = list(task_dir.glob("*_task.json"))
        filtered_files = []
        
        for file_path in all_task_files:
            scene_id = self.extract_scene_id_from_filename(file_path.name)
            if scene_id is not None and self.is_scene_in_range(scene_id):
                filtered_files.append(file_path)
        
        filtered_files.sort()  # 按文件名排序
        return filtered_files
    
    def load_json_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """加载JSON文件，处理错误"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError, UnicodeDecodeError):
            return None

    def extract_tasks_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """从单个文件提取符合条件的任务"""
        data = self.load_json_file(file_path)
        if not data:
            return []

        tasks = data.get('tasks', [])

        # 获取所有目标任务类型
        single_agent_tasks = set(self.config['task_filter']['single_agent_tasks'].keys())
        multi_agent_tasks = set(self.config['task_filter']['multi_agent_tasks'].keys())
        all_target_categories = single_agent_tasks | multi_agent_tasks

        filtered_tasks = []
        for task in tasks:
            task_category = task.get('task_category', '')
            if task_category in all_target_categories:
                filtered_tasks.append(task)

        return filtered_tasks

    def select_agents_for_task(self, agents_config: List[Dict[str, Any]], task_category: str) -> List[Dict[str, Any]]:
        """根据任务类型选择智能体"""
        if not agents_config:
            raise ValueError("智能体配置为空")

        # 判断是单智能体还是多智能体任务
        single_agent_tasks = set(self.config['task_filter']['single_agent_tasks'].keys())
        multi_agent_tasks = set(self.config['task_filter']['multi_agent_tasks'].keys())

        if task_category in single_agent_tasks:
            # 单智能体任务：选择负重最大的智能体
            strategy = self.config['agent_selection']['single_agent_strategy']
            if strategy == 'max_weight':
                selected_agent = max(agents_config, key=lambda x: x.get('max_weight', 0))
                return [selected_agent]
            elif strategy == 'first':
                return [agents_config[0]]
            elif strategy == 'random':
                return [random.choice(agents_config)]
            else:
                raise ValueError(f"不支持的单智能体选择策略: {strategy}")

        elif task_category in multi_agent_tasks:
            # 多智能体任务：保留所有智能体
            return agents_config

        else:
            raise ValueError(f"未知的任务类型: {task_category}")

    def should_use_scene_for_category(self, scene_id: int, category: str) -> bool:
        """判断是否应该为指定类别使用该场景"""
        if not self.config['sampling']['ensure_scene_diversity']:
            return True

        # 如果该类别还没有使用过这个场景，则可以使用
        return scene_id not in self.used_scenes_per_category[category]

    def mark_scene_used_for_category(self, scene_id: int, category: str):
        """标记场景已被某个类别使用"""
        if self.config['sampling']['ensure_scene_diversity']:
            self.used_scenes_per_category[category].add(scene_id)

    def create_single_task_json(self, original_data: Dict[str, Any],
                               task: Dict[str, Any],
                               agents_config: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建单任务JSON数据"""
        return {
            'task_background': original_data.get('task_background', ''),
            'agents_config': agents_config,
            'tasks': [task],
            'scene_id': original_data.get('scene_id', '')
        }

    def create_scene_symlink(self, task_filename: str, source_scene_id: str,
                           scene_dir: Path, scene_output_dir: Path) -> bool:
        """创建场景文件软链接或复制文件"""
        # 构建源场景文件路径
        source_scene_file = scene_dir / f"{source_scene_id}_scene.json"
        if not source_scene_file.exists():
            return False

        # 构建目标场景文件路径
        scene_filename = task_filename.replace('_task.json', '_scene.json')
        target_scene_file = scene_output_dir / scene_filename

        create_links = self.config['scene_processing']['create_scene_links']

        try:
            if create_links and self.supports_symlinks:
                # 创建软链接
                if target_scene_file.exists() or target_scene_file.is_symlink():
                    target_scene_file.unlink()

                # 计算相对路径
                relative_path = os.path.relpath(source_scene_file, scene_output_dir)
                os.symlink(relative_path, target_scene_file)
            else:
                # 复制文件
                shutil.copy2(source_scene_file, target_scene_file)

            return True
        except (OSError, shutil.Error):
            return False

    def generate_dataset(self) -> Dict[str, int]:
        """主生成方法"""
        print("开始生成SFT数据集...")
        print("="*60)

        # 获取路径
        task_dir, scene_dir = self.get_source_paths()

        # 创建输出目录结构
        single_output_dir = self.create_output_structure("single-independent")
        multi_output_dir = self.create_output_structure("multi-independent")

        # 扫描源文件
        source_files = self.scan_source_files(task_dir)
        print(f"在场景范围 {self.config['scene_filter']['min_scene_id']}-{self.config['scene_filter']['max_scene_id']} 中找到 {len(source_files)} 个源任务文件")

        # 获取任务配置
        single_agent_tasks = self.config['task_filter']['single_agent_tasks']
        multi_agent_tasks = self.config['task_filter']['multi_agent_tasks']
        all_target_categories = {**single_agent_tasks, **multi_agent_tasks}

        # 初始化计数器
        for category in all_target_categories:
            self.task_counters[category] = 0

        # 计算总目标数量
        total_target = sum(all_target_categories.values())

        # 处理文件
        single_file_counter = 1
        multi_file_counter = 1

        # 为了确保场景多样性，我们需要多轮扫描
        max_rounds = 3  # 最多扫描3轮
        current_round = 1

        with tqdm(total=total_target, desc="生成SFT数据集") as pbar:

            while current_round <= max_rounds:
                # 检查是否已完成所有类型
                if all(self.task_counters[cat] >= all_target_categories[cat] for cat in all_target_categories):
                    break

                print(f"\n开始第 {current_round} 轮扫描...")
                round_progress = 0

                for source_file in source_files:
                    # 检查是否已完成所有类型
                    if all(self.task_counters[cat] >= all_target_categories[cat] for cat in all_target_categories):
                        break

                    # 提取场景ID
                    scene_id = self.extract_scene_id_from_filename(source_file.name)
                    if scene_id is None:
                        continue

                    # 提取任务
                    tasks = self.extract_tasks_from_file(source_file)
                    if not tasks:
                        continue

                    # 加载原始数据
                    original_data = self.load_json_file(source_file)
                    if not original_data:
                        continue

                    # 获取智能体配置
                    agents_config = original_data.get('agents_config', [])
                    if not agents_config:
                        continue

                    # 按类型分组任务
                    tasks_by_category = defaultdict(list)
                    for task in tasks:
                        category = task.get('task_category', '')
                        if category in all_target_categories:
                            tasks_by_category[category].append(task)

                    # 为每个类型选择一个任务（如果该类型还未达到目标数量且场景可用）
                    for category, category_tasks in tasks_by_category.items():
                        if self.task_counters[category] >= all_target_categories[category]:
                            continue

                        # 检查是否应该使用这个场景
                        if not self.should_use_scene_for_category(scene_id, category):
                            # 如果策略是跳过，则跳过
                            if self.config['sampling']['insufficient_scenes_strategy'] == 'skip':
                                continue
                            # 如果策略是重用，则在后续轮次中允许使用

                        # 选择第一个任务
                        selected_task = category_tasks[0]

                        # 根据任务类型决定使用的智能体配置和输出目录
                        task_agents_config = self.select_agents_for_task(agents_config, category)

                        # 确定输出目录和文件计数器
                        if category in single_agent_tasks:
                            current_task_output_dir, current_scene_output_dir = single_output_dir
                            current_file_counter = single_file_counter
                        else:
                            current_task_output_dir, current_scene_output_dir = multi_output_dir
                            current_file_counter = multi_file_counter

                        # 创建单任务JSON
                        single_task_data = self.create_single_task_json(
                            original_data, selected_task, task_agents_config
                        )

                        # 生成文件名
                        task_filename = f"{current_file_counter:05d}_task.json"
                        task_output_file = current_task_output_dir / task_filename

                        # 保存任务文件
                        with open(task_output_file, 'w', encoding='utf-8') as f:
                            json.dump(single_task_data, f, indent=2, ensure_ascii=False)

                        # 创建场景软链接或复制文件
                        scene_id_str = original_data.get('scene_id', str(scene_id).zfill(5))
                        self.create_scene_symlink(task_filename, scene_id_str, scene_dir, current_scene_output_dir)

                        # 标记场景已使用
                        self.mark_scene_used_for_category(scene_id, category)

                        # 更新计数器
                        self.task_counters[category] += 1
                        self.generated_files += 1

                        # 更新对应的文件计数器
                        if category in single_agent_tasks:
                            single_file_counter += 1
                        else:
                            multi_file_counter += 1

                        round_progress += 1

                        # 更新进度条
                        pbar.update(1)
                        pbar.set_postfix({
                            'round': current_round,
                            'files': self.generated_files,
                            **{cat: f"{self.task_counters[cat]}/{all_target_categories[cat]}"
                               for cat in all_target_categories}
                        })

                print(f"第 {current_round} 轮完成，本轮生成 {round_progress} 个文件")
                current_round += 1

        return dict(self.task_counters)

    def print_statistics(self, stats: Dict[str, int]):
        """打印生成统计信息"""
        print("\n" + "="*60)
        print("SFT数据集生成完成!")
        print("="*60)
        print(f"总共生成文件: {self.generated_files}")
        print(f"场景处理方式: {'软链接' if self.config['scene_processing']['create_scene_links'] and self.supports_symlinks else '文件复制'}")
        print(f"场景范围: {self.config['scene_filter']['min_scene_id']}-{self.config['scene_filter']['max_scene_id']}")
        print(f"场景多样性策略: {'启用' if self.config['sampling']['ensure_scene_diversity'] else '禁用'}")

        # 分别统计单智能体和多智能体任务
        single_agent_tasks = self.config['task_filter']['single_agent_tasks']
        multi_agent_tasks = self.config['task_filter']['multi_agent_tasks']

        print("\n单智能体任务统计:")
        single_total = 0
        for category, target_count in single_agent_tasks.items():
            count = stats.get(category, 0)
            single_total += count
            percentage = (count / target_count) * 100 if target_count > 0 else 0
            status = "✓" if count >= target_count else "✗"
            print(f"  {status} {category}: {count}/{target_count} ({percentage:.1f}%)")

        print(f"\n多智能体任务统计:")
        multi_total = 0
        for category, target_count in multi_agent_tasks.items():
            count = stats.get(category, 0)
            multi_total += count
            percentage = (count / target_count) * 100 if target_count > 0 else 0
            status = "✓" if count >= target_count else "✗"
            print(f"  {status} {category}: {count}/{target_count} ({percentage:.1f}%)")

        print(f"\n总计: 单智能体 {single_total} 个，多智能体 {multi_total} 个")

        # 场景使用统计
        if self.config['sampling']['ensure_scene_diversity']:
            print("\n场景使用统计:")
            for category, used_scenes in self.used_scenes_per_category.items():
                print(f"  {category}: 使用了 {len(used_scenes)} 个不同场景")

        # 输出路径信息
        output_root = self.project_root / self.config['output']['output_dir']
        print(f"\n输出目录: {output_root}")
        print(f"  单智能体: {output_root / 'single-independent'}")
        print(f"  多智能体: {output_root / 'multi-independent'}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='SFT数据集生成器')
    parser.add_argument('--config', '-c', type=str,
                       help='配置文件路径（默认使用 config/data_generation/sft_dataset_config.yaml）')

    args = parser.parse_args()

    try:
        # 创建生成器并生成数据集
        generator = SFTDatasetGenerator(args.config)
        stats = generator.generate_dataset()
        generator.print_statistics(stats)

        print("\n🎉 SFT数据集生成完成！")

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
