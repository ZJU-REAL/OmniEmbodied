"""
Scenario Selector - Supports three selection modes: all/range/list
"""

import os
import glob
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ScenarioSelector:
    """Scenario Selector - Simplified implementation"""
    
    @staticmethod
    def get_scenario_list(config: Dict[str, Any], scenario_selection: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get list of scenarios to evaluate and task filtering information

        Args:
            config: Configuration file
            scenario_selection: Scenario selection configuration
                {
                    'mode': 'all',  # 'all', 'range', 'list'
                    'range': {'start': '00001', 'end': '00010'},
                    'list': ['00001', '00003', '00005'],
                    'task_filter': {
                        'categories': ['direct_command', 'attribute_reasoning']  # Task category filtering
                    }
                }

        Returns:
            Dict[str, Any]: Contains scenario list and task filtering information
                - 'scenarios': Scenario ID list
                - 'task_indices': Task indices to execute in each scenario
        """
        if scenario_selection is None:
            scenario_selection = {'mode': 'all'}

        mode = scenario_selection.get('mode', 'all')

        # Get base scenario list
        if mode == 'all':
            base_scenarios = ScenarioSelector._get_all_scenarios(config)
        elif mode == 'range':
            range_config = scenario_selection.get('range', {})
            base_scenarios = ScenarioSelector._get_range_scenarios(range_config)
        elif mode == 'list':
            scenario_list = scenario_selection.get('list', ['00001'])
            base_scenarios = ScenarioSelector._validate_scenarios(scenario_list, config)
        else:
            logger.warning(f"Unknown scenario selection mode: {mode}, using default scenario")
            base_scenarios = ['00001']

        # Apply task filtering
        task_filter = scenario_selection.get('task_filter')
        if task_filter:
            filter_result = ScenarioSelector._filter_scenarios_by_tasks(base_scenarios, task_filter, config)
            return filter_result

        return {
            'scenarios': base_scenarios,
            'task_indices': {}  # Empty dict means execute all tasks
        }
    
    @staticmethod
    def _get_all_scenarios(config: Dict[str, Any]) -> List[str]:
        """
        Get all available scenarios

        Args:
            config: Configuration dictionary, using new dataset configuration

        Raises:
            KeyError: Missing dataset configuration in config
            FileNotFoundError: Scenario directory does not exist
        """
        # Use new dataset configuration system
        from config.config_manager import get_config_manager

        # Get configuration manager
        config_manager = get_config_manager()

        # Get currently used dataset
        dataset_name = config.get('dataset', {}).get('default', 'eval_multi')

        # Get scenario directory
        try:
            # Assume config contains config_file info, use default config if not available
            config_file = getattr(config, 'config_file', 'centralized_config')
            if isinstance(config, dict) and 'config_file' in config:
                config_file = config['config_file']
            elif hasattr(config_manager, 'current_config_name'):
                config_file = config_manager.current_config_name
            else:
                config_file = 'centralized_config'

            scene_dir = config_manager.get_scene_dir(config_file, dataset_name)
        except Exception as e:
            logger.warning(f"Unable to get scenario directory using new config system: {e}")
            # Fall back to old method
            data_dir = config.get('data_dir', 'data')
            if not os.path.isabs(data_dir):
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(current_dir)
                data_dir = os.path.join(project_root, data_dir)
            scene_dir = os.path.join(data_dir, 'scene')

        # Strictly validate scenario directory exists
        if not os.path.exists(scene_dir):
            raise FileNotFoundError(f"Scenario directory does not exist: {scene_dir}")

        # Find all scenario files
        scene_files = glob.glob(os.path.join(scene_dir, '*.json'))
        scenario_ids = []

        for scene_file in scene_files:
            # Extract scenario ID from filename
            filename = os.path.basename(scene_file)
            if filename.endswith('_scene.json'):
                scenario_id = filename[:-11]  # Remove '_scene.json' suffix
                scenario_ids.append(scenario_id)

        if not scenario_ids:
            raise RuntimeError(f"No scenario files found in scenario directory: {scene_dir}")

        # Sort and return
        scenario_ids.sort()
        logger.info(f"Found {len(scenario_ids)} scenarios: {scenario_ids[:5]}{'...' if len(scenario_ids) > 5 else ''}")
        return scenario_ids
    
    @staticmethod
    def _get_range_scenarios(range_config: Dict[str, str]) -> List[str]:
        """Get scenarios within range"""
        start = range_config.get('start', '00001')
        end = range_config.get('end', '00001')
        
        try:
            start_num = int(start)
            end_num = int(end)
            
            if start_num > end_num:
                logger.warning(f"Start scenario number greater than end scenario number: {start} > {end}")
                start_num, end_num = end_num, start_num
            
            # Generate scenario IDs within range
            scenario_ids = []
            for i in range(start_num, end_num + 1):
                scenario_id = f"{i:05d}"  # Format as 5-digit number
                scenario_ids.append(scenario_id)
            
            # Validate if scenarios exist
            # Note: config needs to be passed here, but _get_range_scenarios is static method without config access
            # Temporarily use default data directory, this method needs refactoring
            default_config = {'data_dir': 'data'}
            validated_scenarios = ScenarioSelector._validate_scenarios(scenario_ids, default_config)
            
            logger.info(f"Range scenarios {start}-{end}: found {len(validated_scenarios)} valid scenarios")
            return validated_scenarios
            
        except ValueError as e:
            logger.error(f"Invalid scenario range format: {range_config}, error: {e}")
            return ['00001']
    
    @staticmethod
    def _validate_scenarios(scenario_list: List[str], config: Dict[str, Any]) -> List[str]:
        """Validate the validity of scenario IDs"""
        validated_scenarios = []

        # Use new dataset configuration system
        from config.config_manager import get_config_manager

        try:
            config_manager = get_config_manager()
            dataset_name = config.get('dataset', {}).get('default', 'eval_multi')

            # Get configuration file name
            config_file = getattr(config, 'config_file', 'centralized_config')
            if isinstance(config, dict) and 'config_file' in config:
                config_file = config['config_file']
            else:
                config_file = 'centralized_config'

            scene_dir = config_manager.get_scene_dir(config_file, dataset_name)
        except Exception as e:
            logger.warning(f"Unable to get scenario directory using new config system: {e}")
            # Fall back to old method
            data_dir = config.get('data_dir', 'data')
            if not os.path.isabs(data_dir):
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(current_dir)
                data_dir = os.path.join(project_root, data_dir)
            scene_dir = os.path.join(data_dir, 'scene')

        for scenario_id in scenario_list:
            scene_file = os.path.join(scene_dir, f'{scenario_id}_scene.json')
            if os.path.exists(scene_file):
                validated_scenarios.append(scenario_id)
            else:
                logger.warning(f"Scene file does not exist: {scene_file}")

        if not validated_scenarios:
            logger.warning("No valid scenarios found, using default scenario")
            return ['00001']

        return validated_scenarios

    @staticmethod
    def _filter_scenarios_by_tasks(scenarios: List[str], task_filter: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter scenarios and tasks based on task characteristics

        Args:
            scenarios: Base scenario list
            task_filter: Task filtering configuration
                {
                    'categories': ['direct_command', 'attribute_reasoning']  # Task category filtering
                }

        Returns:
            Dict[str, Any]: Filtering result, containing:
                - 'scenarios': Filtered scenario list
                - 'task_indices': Task indices to execute in each scenario {scenario_id: [task_index1, task_index2, ...]}
        """
        import json

        if not task_filter:
            return {
                'scenarios': scenarios,
                'task_indices': {}  # Empty dict means execute all tasks
            }

        filtered_scenarios = []
        task_indices = {}
        categories_filter = task_filter.get('categories', [])

        total_tasks_before = 0
        total_tasks_after = 0

        # Use new dataset configuration system to get task directory
        from config.config_manager import get_config_manager

        try:
            config_manager = get_config_manager()
            dataset_name = config.get('dataset', {}).get('default', 'eval_multi')

            # Get configuration file name
            config_file = getattr(config, 'config_file', 'centralized_config')
            if isinstance(config, dict) and 'config_file' in config:
                config_file = config['config_file']
            else:
                config_file = 'centralized_config'

            task_dir = config_manager.get_task_dir(config_file, dataset_name)
        except Exception as e:
            logger.warning(f"Unable to get task directory using new config system: {e}")
            # Fall back to old method
            data_dir = config.get('data_dir', 'data')
            if not os.path.isabs(data_dir):
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(current_dir)
                data_dir = os.path.join(project_root, data_dir)
            task_dir = os.path.join(data_dir, 'task')

        for scenario_id in scenarios:
            try:
                # Load task file
                task_file = os.path.join(task_dir, f'{scenario_id}_task.json')
                if not os.path.exists(task_file):
                    logger.warning(f"Task file does not exist: {task_file}")
                    continue

                with open(task_file, 'r', encoding='utf-8') as f:
                    task_data = json.load(f)

                tasks = task_data.get('tasks', [])
                total_tasks_before += len(tasks)

                            # Note: Since all scenarios in the current dataset are designed for dual agents,
            # agent_count filtering logic has been removed

            # Check task category filtering
                if categories_filter:
                    matching_task_indices = []

                    for i, task in enumerate(tasks):
                        task_category = task.get('task_category', 'unknown')
                        if task_category in categories_filter:
                            matching_task_indices.append(i)

                    # Skip this scenario if no matching tasks
                    if not matching_task_indices:
                        continue

                    # Record task indices to execute
                    task_indices[scenario_id] = matching_task_indices
                    total_tasks_after += len(matching_task_indices)
                else:
                    # If no category filtering, execute all tasks
                    task_indices[scenario_id] = []
                    total_tasks_after += len(tasks)

                # Passes all filtering conditions
                filtered_scenarios.append(scenario_id)

            except Exception as e:
                logger.warning(f"Error processing scenario {scenario_id}: {e}")
                continue

        logger.info(f"Scenario filtering result: {len(scenarios)} -> {len(filtered_scenarios)} scenarios")
        logger.info(f"Task filtering result: {total_tasks_before} -> {total_tasks_after} tasks")
        if categories_filter:
            logger.info(f"  Category filtering: {categories_filter}")

        return {
            'scenarios': filtered_scenarios,
            'task_indices': task_indices
        }

    @staticmethod
    def parse_scenario_selection_string(scenarios_str: str) -> Dict[str, Any]:
        """
        Parse scenario selection string
        
        Args:
            scenarios_str: Scenario selection string
                - 'all': All scenarios
                - '00001-00010': Range scenarios
                - '00001,00003,00005': List scenarios
                - '00001': Single scenario
        
        Returns:
            Dict: Scenario selection configuration
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
