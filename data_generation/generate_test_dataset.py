#!/usr/bin/env python3
"""
测试数据集生成器
从源数据集中提取指定类型的任务，生成独立的测试集
"""

import os
import sys
import json
import shutil
import platform
import random
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict, Counter
import yaml
from tqdm import tqdm


class TestDatasetGenerator:
    """测试数据集生成器"""
    
    def __init__(self, config_path: str = None):
        """初始化生成器"""
        if config_path is None:
            # 默认配置文件路径
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "data_generation" / "test_dataset_config.yaml"
        
        self.config = self.load_config(config_path)
        self.project_root = Path(__file__).parent.parent
        self.validate_config()
        
        # 任务计数器
        self.task_counters = Counter()
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
            'task_filter.agent_mode', 'task_filter.task_categories', 'task_filter.count_per_category',
            'agent_selection.strategy', 'scene_processing.create_scene_links'
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
        valid_all_categories = valid_single_agent_categories | valid_multi_agent_categories
        
        agent_mode = self.config['task_filter']['agent_mode']
        task_categories = set(self.config['task_filter']['task_categories'])
        
        if agent_mode == 'single':
            invalid_categories = task_categories - valid_single_agent_categories
            if invalid_categories:
                raise ValueError(f"单智能体模式下不支持的任务类型: {invalid_categories}")
        elif agent_mode == 'multi':
            invalid_categories = task_categories - valid_multi_agent_categories
            if invalid_categories:
                raise ValueError(f"多智能体模式下不支持的任务类型: {invalid_categories}")
        elif agent_mode == 'all':
            invalid_categories = task_categories - valid_all_categories
            if invalid_categories:
                raise ValueError(f"不支持的任务类型: {invalid_categories}")
        else:
            raise ValueError(f"不支持的智能体模式: {agent_mode}")
    
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
    
    def scan_source_files(self, task_dir: Path) -> List[Path]:
        """扫描源数据文件"""
        task_files = list(task_dir.glob("*_task.json"))
        task_files.sort()  # 按文件名排序
        return task_files
    
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
        agent_mode = self.config['task_filter']['agent_mode']
        target_categories = set(self.config['task_filter']['task_categories'])

        # 根据智能体模式筛选任务
        single_agent_categories = {'direct_command', 'attribute_reasoning', 'tool_use', 'compound_reasoning'}
        multi_agent_categories = {'explicit_collaboration', 'implicit_collaboration', 'compound_collaboration'}

        filtered_tasks = []
        for task in tasks:
            task_category = task.get('task_category', '')

            # 检查任务类型是否在目标列表中
            if task_category not in target_categories:
                continue

            # 根据智能体模式进一步筛选
            if agent_mode == 'single' and task_category in single_agent_categories:
                filtered_tasks.append(task)
            elif agent_mode == 'multi' and task_category in multi_agent_categories:
                filtered_tasks.append(task)
            elif agent_mode == 'all':
                filtered_tasks.append(task)

        return filtered_tasks

    def select_best_agent(self, agents_config: List[Dict[str, Any]]) -> Dict[str, Any]:
        """根据策略选择最佳智能体"""
        if not agents_config:
            raise ValueError("智能体配置为空")

        strategy = self.config['agent_selection']['strategy']

        if strategy == 'max_weight':
            # 选择max_weight最大的智能体
            return max(agents_config, key=lambda x: x.get('max_weight', 0))
        elif strategy == 'first':
            # 选择第一个智能体
            return agents_config[0]
        elif strategy == 'random':
            # 随机选择智能体
            return random.choice(agents_config)
        else:
            raise ValueError(f"不支持的智能体选择策略: {strategy}")

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
        # 获取路径
        task_dir, scene_dir = self.get_source_paths()
        task_output_dir, scene_output_dir = self.get_output_paths()

        # 扫描源文件
        source_files = self.scan_source_files(task_dir)
        print(f"找到 {len(source_files)} 个源任务文件")

        # 初始化计数器
        target_categories = self.config['task_filter']['task_categories']
        count_per_category = self.config['task_filter']['count_per_category']

        for category in target_categories:
            self.task_counters[category] = 0

        # 处理文件
        file_counter = 1

        with tqdm(total=len(target_categories) * count_per_category,
                 desc="生成测试数据集") as pbar:

            for source_file in source_files:
                # 检查是否已完成所有类型
                if all(self.task_counters[cat] >= count_per_category for cat in target_categories):
                    break

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
                    if category in target_categories:
                        tasks_by_category[category].append(task)

                # 为每个类型选择一个任务（如果该类型还未达到目标数量）
                for category, category_tasks in tasks_by_category.items():
                    if self.task_counters[category] >= count_per_category:
                        continue

                    # 选择第一个任务
                    selected_task = category_tasks[0]

                    # 根据任务类型决定使用的智能体配置
                    multi_agent_categories = {'explicit_collaboration', 'implicit_collaboration', 'compound_collaboration'}

                    if category in multi_agent_categories:
                        # 多智能体任务：保留所有智能体配置
                        task_agents_config = agents_config
                    else:
                        # 单智能体任务：选择最佳智能体
                        selected_agent = self.select_best_agent(agents_config)
                        task_agents_config = [selected_agent]

                    # 创建单任务JSON
                    single_task_data = self.create_single_task_json(
                        original_data, selected_task, task_agents_config
                    )

                    # 生成文件名
                    task_filename = f"{file_counter:05d}_task.json"
                    task_output_file = task_output_dir / task_filename

                    # 保存任务文件
                    with open(task_output_file, 'w', encoding='utf-8') as f:
                        json.dump(single_task_data, f, indent=2, ensure_ascii=False)

                    # 创建场景软链接或复制文件
                    scene_id = original_data.get('scene_id', '')
                    self.create_scene_symlink(task_filename, scene_id, scene_dir, scene_output_dir)

                    # 更新计数器
                    self.task_counters[category] += 1
                    self.generated_files += 1
                    file_counter += 1

                    # 更新进度条
                    pbar.update(1)
                    pbar.set_postfix({
                        'files': self.generated_files,
                        **{cat: self.task_counters[cat] for cat in target_categories}
                    })

        return dict(self.task_counters)

    def print_statistics(self, stats: Dict[str, int]):
        """打印生成统计信息"""
        print("\n" + "="*50)
        print("测试数据集生成完成!")
        print("="*50)
        print(f"总共生成文件: {self.generated_files}")
        print(f"场景处理方式: {'软链接' if self.config['scene_processing']['create_scene_links'] and self.supports_symlinks else '文件复制'}")
        print("\n各任务类型统计:")

        for category, count in stats.items():
            target_count = self.config['task_filter']['count_per_category']
            percentage = (count / target_count) * 100 if target_count > 0 else 0
            print(f"  {category}: {count}/{target_count} ({percentage:.1f}%)")

        # 输出路径信息
        output_root = self.project_root / self.config['output']['output_dir']
        print(f"\n输出目录: {output_root}")
        print(f"  任务文件: {output_root / self.config['output']['task_subdir']}")
        print(f"  场景文件: {output_root / self.config['output']['scene_subdir']}")


def main():
    """主函数"""
    try:
        # 创建生成器
        generator = TestDatasetGenerator()

        # 生成数据集
        stats = generator.generate_dataset()

        # 打印统计信息
        generator.print_statistics(stats)

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
