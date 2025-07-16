"""
场景选择器 - 支持all/range/list三种选择模式
"""

import os
import glob
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ScenarioSelector:
    """场景选择器 - 简化实现"""
    
    @staticmethod
    def get_scenario_list(config: Dict[str, Any], scenario_selection: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        获取要评测的场景列表和任务筛选信息

        Args:
            config: 配置文件
            scenario_selection: 场景选择配置
                {
                    'mode': 'all',  # 'all', 'range', 'list'
                    'range': {'start': '00001', 'end': '00010'},
                    'list': ['00001', '00003', '00005'],
                    'task_filter': {
                        'categories': ['direct_command', 'attribute_reasoning']  # 任务类别筛选
                    }
                }

        Returns:
            Dict[str, Any]: 包含场景列表和任务筛选信息
                - 'scenarios': 场景ID列表
                - 'task_indices': 每个场景中需要执行的任务索引
        """
        if scenario_selection is None:
            scenario_selection = {'mode': 'all'}

        mode = scenario_selection.get('mode', 'all')

        # 获取基础场景列表
        if mode == 'all':
            base_scenarios = ScenarioSelector._get_all_scenarios()
        elif mode == 'range':
            range_config = scenario_selection.get('range', {})
            base_scenarios = ScenarioSelector._get_range_scenarios(range_config)
        elif mode == 'list':
            scenario_list = scenario_selection.get('list', ['00001'])
            base_scenarios = ScenarioSelector._validate_scenarios(scenario_list)
        else:
            logger.warning(f"未知的场景选择模式: {mode}, 使用默认场景")
            base_scenarios = ['00001']

        # 应用任务筛选
        task_filter = scenario_selection.get('task_filter')
        if task_filter:
            filter_result = ScenarioSelector._filter_scenarios_by_tasks(base_scenarios, task_filter)
            return filter_result

        return {
            'scenarios': base_scenarios,
            'task_indices': {}  # 空字典表示执行所有任务
        }
    
    @staticmethod
    def _get_all_scenarios() -> List[str]:
        """获取所有可用场景"""
        # 从data/scene目录获取所有场景
        scene_dir = 'data/scene'
        if not os.path.exists(scene_dir):
            logger.warning(f"场景目录不存在: {scene_dir}")
            return ['00001']  # 返回默认场景
        
        # 查找所有场景文件
        scene_files = glob.glob(os.path.join(scene_dir, '*.json'))
        scenario_ids = []
        
        for scene_file in scene_files:
            # 从文件名提取场景ID
            filename = os.path.basename(scene_file)
            if filename.endswith('_scene.json'):
                scenario_id = filename[:-11]  # 移除'_scene.json'后缀
                scenario_ids.append(scenario_id)
        
        if not scenario_ids:
            logger.warning("未找到任何场景文件")
            return ['00001']
        
        # 排序并返回
        scenario_ids.sort()
        logger.info(f"找到 {len(scenario_ids)} 个场景: {scenario_ids[:5]}{'...' if len(scenario_ids) > 5 else ''}")
        return scenario_ids
    
    @staticmethod
    def _get_range_scenarios(range_config: Dict[str, str]) -> List[str]:
        """获取范围内的场景"""
        start = range_config.get('start', '00001')
        end = range_config.get('end', '00001')
        
        try:
            start_num = int(start)
            end_num = int(end)
            
            if start_num > end_num:
                logger.warning(f"起始场景号大于结束场景号: {start} > {end}")
                start_num, end_num = end_num, start_num
            
            # 生成范围内的场景ID
            scenario_ids = []
            for i in range(start_num, end_num + 1):
                scenario_id = f"{i:05d}"  # 格式化为5位数字
                scenario_ids.append(scenario_id)
            
            # 验证场景是否存在
            validated_scenarios = ScenarioSelector._validate_scenarios(scenario_ids)
            
            logger.info(f"范围场景 {start}-{end}: 找到 {len(validated_scenarios)} 个有效场景")
            return validated_scenarios
            
        except ValueError as e:
            logger.error(f"场景范围格式错误: {range_config}, 错误: {e}")
            return ['00001']
    
    @staticmethod
    def _validate_scenarios(scenario_list: List[str]) -> List[str]:
        """验证场景ID的有效性"""
        validated_scenarios = []
        scene_dir = 'data/scene'
        
        for scenario_id in scenario_list:
            scene_file = os.path.join(scene_dir, f'{scenario_id}_scene.json')
            if os.path.exists(scene_file):
                validated_scenarios.append(scenario_id)
            else:
                logger.warning(f"场景文件不存在: {scene_file}")
        
        if not validated_scenarios:
            logger.warning("没有找到有效的场景，使用默认场景")
            return ['00001']
        
        return validated_scenarios

    @staticmethod
    def _filter_scenarios_by_tasks(scenarios: List[str], task_filter: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据任务特征筛选场景和任务

        Args:
            scenarios: 基础场景列表
            task_filter: 任务筛选配置
                {
                    'categories': ['direct_command', 'attribute_reasoning']  # 任务类别筛选
                }

        Returns:
            Dict[str, Any]: 筛选结果，包含：
                - 'scenarios': 筛选后的场景列表
                - 'task_indices': 每个场景中需要执行的任务索引 {scenario_id: [task_index1, task_index2, ...]}
        """
        import json

        if not task_filter:
            return {
                'scenarios': scenarios,
                'task_indices': {}  # 空字典表示执行所有任务
            }

        filtered_scenarios = []
        task_indices = {}
        categories_filter = task_filter.get('categories', [])

        total_tasks_before = 0
        total_tasks_after = 0

        for scenario_id in scenarios:
            try:
                # 加载任务文件
                task_file = f'data/task/{scenario_id}_task.json'
                if not os.path.exists(task_file):
                    logger.warning(f"任务文件不存在: {task_file}")
                    continue

                with open(task_file, 'r', encoding='utf-8') as f:
                    task_data = json.load(f)

                tasks = task_data.get('tasks', [])
                total_tasks_before += len(tasks)

                # 注意：由于当前数据集中所有场景都是双智能体设计，
                # 因此移除了agent_count筛选逻辑

                # 检查任务类别筛选
                if categories_filter:
                    matching_task_indices = []

                    for i, task in enumerate(tasks):
                        task_category = task.get('task_category', 'unknown')
                        if task_category in categories_filter:
                            matching_task_indices.append(i)

                    # 如果没有匹配的任务，跳过此场景
                    if not matching_task_indices:
                        continue

                    # 记录需要执行的任务索引
                    task_indices[scenario_id] = matching_task_indices
                    total_tasks_after += len(matching_task_indices)
                else:
                    # 如果没有类别筛选，执行所有任务
                    task_indices[scenario_id] = []
                    total_tasks_after += len(tasks)

                # 通过所有筛选条件
                filtered_scenarios.append(scenario_id)

            except Exception as e:
                logger.warning(f"处理场景 {scenario_id} 时出错: {e}")
                continue

        logger.info(f"场景筛选结果: {len(scenarios)} -> {len(filtered_scenarios)} 个场景")
        logger.info(f"任务筛选结果: {total_tasks_before} -> {total_tasks_after} 个任务")
        if categories_filter:
            logger.info(f"  类别筛选: {categories_filter}")

        return {
            'scenarios': filtered_scenarios,
            'task_indices': task_indices
        }

    @staticmethod
    def parse_scenario_selection_string(scenarios_str: str) -> Dict[str, Any]:
        """
        解析场景选择字符串
        
        Args:
            scenarios_str: 场景选择字符串
                - 'all': 所有场景
                - '00001-00010': 范围场景
                - '00001,00003,00005': 列表场景
                - '00001': 单个场景
        
        Returns:
            Dict: 场景选择配置
        """
        if scenarios_str == 'all':
            return {'mode': 'all'}
        elif '-' in scenarios_str and ',' not in scenarios_str:
            # 范围模式
            try:
                start, end = scenarios_str.split('-', 1)
                return {
                    'mode': 'range',
                    'range': {'start': start.strip(), 'end': end.strip()}
                }
            except ValueError:
                logger.error(f"范围格式错误: {scenarios_str}")
                return {'mode': 'list', 'list': [scenarios_str]}
        elif ',' in scenarios_str:
            # 列表模式
            scenario_list = [s.strip() for s in scenarios_str.split(',') if s.strip()]
            return {
                'mode': 'list',
                'list': scenario_list
            }
        else:
            # 单个场景
            return {
                'mode': 'list',
                'list': [scenarios_str.strip()]
            }
    
    @staticmethod
    def get_scenario_count(scenario_selection: Dict[str, Any] = None) -> int:
        """获取场景数量"""
        scenario_list = ScenarioSelector.get_scenario_list({}, scenario_selection)
        return len(scenario_list)
    
    @staticmethod
    def validate_scenario_selection(scenario_selection: Dict[str, Any]) -> bool:
        """验证场景选择配置的有效性"""
        if not isinstance(scenario_selection, dict):
            return False
        
        mode = scenario_selection.get('mode')
        if mode not in ['all', 'range', 'list']:
            return False
        
        if mode == 'range':
            range_config = scenario_selection.get('range')
            if not isinstance(range_config, dict):
                return False
            if 'start' not in range_config or 'end' not in range_config:
                return False
        elif mode == 'list':
            scenario_list = scenario_selection.get('list')
            if not isinstance(scenario_list, list) or not scenario_list:
                return False
        
        return True
