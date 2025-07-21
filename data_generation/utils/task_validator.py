#!/usr/bin/env python3
"""
Task Validator and Auto-Fixer

This module provides comprehensive validation and automatic fixing for generated task JSON data.
It checks task structure, validates task categories, fixes validation_checks format,
verifies location_id values, and ensures object existence in scenes.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

import pandas as pd

import logging


class TaskValidator:
    """Validator for task JSON data with automatic fixing capabilities."""

    def __init__(self, attribute_actions_csv_path: str = None, scene_dir: Optional[Path] = None):
        """
        Initialize the task validator.

        Args:
            attribute_actions_csv_path: Path to the attribute actions CSV file
            scene_dir: Directory containing scene files for persistent modifications
        """
        self.logger = logging.getLogger(__name__)

        # 设置默认CSV路径
        if attribute_actions_csv_path is None:
            project_root = Path(__file__).parent.parent.parent  # 项目根目录
            attribute_actions_csv_path = str(project_root / 'data' / 'attribute_actions.csv')

        self.attribute_actions_csv_path = attribute_actions_csv_path
        self.attribute_actions_df = None
        self.valid_task_categories = {
            'direct_command', 'attribute_reasoning', 'tool_use', 'compound_reasoning',
            'explicit_collaboration', 'implicit_collaboration', 'compound_collaboration'
        }

        # Scene directory for saving modified scene files
        self.scene_dir = Path(scene_dir) if scene_dir else None

        # Track modified scenes to avoid duplicate saves
        self._modified_scenes = set()

        # Scene data management for intelligent caching and saving
        self._scene_data_cache = {}  # Cache loaded scene data
        self._scene_modifications = {}  # Track scene modification status
        self._pending_saves = set()  # Track scenes that need to be saved
        self._scene_task_counts = {}  # Track how many tasks per scene are being processed

        # Task data management for intelligent caching
        self._task_data_cache = {}  # Cache task data by task file ID

        # Load attribute actions CSV
        self._load_attribute_actions()

    def _get_cached_scene_data(self, scene_data: Dict[str, Any], scene_id: str) -> Dict[str, Any]:
        """
        Get scene data from cache or add to cache if not present.
        Always returns the most up-to-date version of scene data.

        Args:
            scene_data: Scene data passed from external caller
            scene_id: Scene ID

        Returns:
            The cached (and potentially modified) scene data
        """
        if scene_id in self._scene_data_cache:
            # Use cached version which may have modifications
            self.logger.debug(f"Using cached scene data for scene {scene_id}")
            return self._scene_data_cache[scene_id]
        else:
            # First time processing this scene, add to cache
            self._scene_data_cache[scene_id] = scene_data.copy()
            self.logger.debug(f"Added scene {scene_id} to cache")
            return self._scene_data_cache[scene_id]

    def _get_cached_task_data(self, task_data: Dict[str, Any], task_file_id: str) -> Dict[str, Any]:
        """
        Get task data from cache or add to cache if not present.
        Always returns the most up-to-date version of task data.

        Args:
            task_data: Task data passed from external caller
            task_file_id: Task file identifier (e.g., "00001")

        Returns:
            The cached (and potentially modified) task data
        """
        if task_file_id in self._task_data_cache:
            # Use cached version which may have modifications
            self.logger.debug(f"Using cached task data for task file {task_file_id}")
            return self._task_data_cache[task_file_id]
        else:
            # First time processing this task file, add to cache
            self._task_data_cache[task_file_id] = task_data.copy()
            self.logger.debug(f"Added task file {task_file_id} to cache")
            return self._task_data_cache[task_file_id]

    def _register_scene_task(self, scene_id: str):
        """Register that a task for this scene is being processed."""
        if scene_id not in self._scene_task_counts:
            self._scene_task_counts[scene_id] = 0
        self._scene_task_counts[scene_id] += 1
        self.logger.debug(f"Scene {scene_id} task count: {self._scene_task_counts[scene_id]}")

    def _unregister_scene_task(self, scene_id: str) -> bool:
        """
        Unregister a task for this scene and return whether this was the last task.

        Returns:
            True if this was the last task for this scene, False otherwise
        """
        if scene_id in self._scene_task_counts:
            self._scene_task_counts[scene_id] -= 1
            is_last_task = self._scene_task_counts[scene_id] <= 0
            if is_last_task:
                # Clean up the counter
                del self._scene_task_counts[scene_id]
            self.logger.debug(f"Scene {scene_id} remaining tasks: {self._scene_task_counts.get(scene_id, 0)}")
            return is_last_task
        return True  # If not tracked, assume it's the last task

    def _mark_scene_for_save(self, scene_id: str):
        """Mark a scene as needing to be saved."""
        self._pending_saves.add(scene_id)
        self.logger.debug(f"Marked scene {scene_id} for saving")

    def _update_task_data_cache(self, task_file_id: str, updated_task_data: Dict[str, Any]):
        """Update the cached task data with modifications."""
        if task_file_id:
            self._task_data_cache[task_file_id] = updated_task_data.copy()
            self.logger.debug(f"Updated cached task data for task file {task_file_id}")

    def _flush_scene_modifications(self):
        """Save all pending scene modifications to files."""
        if not self._pending_saves:
            return

        self.logger.debug(f"Flushing {len(self._pending_saves)} pending scene saves")

        for scene_id in list(self._pending_saves):
            if scene_id in self._scene_data_cache:
                success = self._save_scene_file(self._scene_data_cache[scene_id], scene_id)
                if success:
                    self._pending_saves.remove(scene_id)
                    self.logger.debug(f"Successfully saved scene {scene_id}")
                else:
                    self.logger.error(f"Failed to save scene {scene_id}")

    def _save_scene_file(self, scene_data: Dict[str, Any], scene_id: str) -> bool:
        """
        Save modified scene data to file.

        Args:
            scene_data: Modified scene data
            scene_id: Scene ID (e.g., "00001")

        Returns:
            bool: True if saved successfully, False otherwise
        """
        if not self.scene_dir:
            self.logger.warning(f"Scene directory not set, cannot save scene {scene_id}")
            return False

        # Avoid duplicate saves for the same scene
        if scene_id in self._modified_scenes:
            self.logger.debug(f"Scene {scene_id} already saved in this session")
            return True

        try:
            scene_file = self.scene_dir / f"{scene_id}_scene.json"

            # Ensure directory exists
            self.scene_dir.mkdir(parents=True, exist_ok=True)

            # Save scene data
            with open(scene_file, 'w', encoding='utf-8') as f:
                json.dump(scene_data, f, indent=2, ensure_ascii=False)

            # Mark as saved
            self._modified_scenes.add(scene_id)

            self.logger.info(f"💾 Saved modified scene data to {scene_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save scene {scene_id}: {e}")
            return False

    def _load_attribute_actions(self):
        """Load the attribute actions CSV file."""
        try:
            if Path(self.attribute_actions_csv_path).exists():
                self.attribute_actions_df = pd.read_csv(self.attribute_actions_csv_path)
                self.logger.info(f"Loaded {len(self.attribute_actions_df)} attribute actions from CSV")
            else:
                self.logger.warning(f"Attribute actions CSV not found: {self.attribute_actions_csv_path}")
        except Exception as e:
            self.logger.error(f"Failed to load attribute actions CSV: {e}")

    def validate_and_fix_task_data(self, task_data: Dict[str, Any], scene_data: Dict[str, Any],
                                   auto_fix: bool = True) -> Tuple[bool, List[str], Dict[str, Any], List[str]]:
        """
        Validate and optionally fix task data with proper check-then-fix workflow.

        Args:
            task_data: Generated task data to validate
            scene_data: Original scene data for reference
            auto_fix: Whether to automatically fix issues

        Returns:
            Tuple of (is_valid, error_messages, fixed_task_data, fixes_applied)
        """
        self.logger.info("🔍 Starting task validation process...")

        # Get scene ID and task file ID for caching
        scene_id = task_data.get('scene_id')
        task_file_id = str(scene_id).zfill(5) if scene_id else None

        # Manage scene data caching
        if scene_id:
            scene_id_str = str(scene_id).zfill(5)
            # Register this task for the scene
            self._register_scene_task(scene_id_str)
            # Use cached scene data if available, otherwise cache the provided data
            actual_scene_data = self._get_cached_scene_data(scene_data, scene_id_str)
        else:
            actual_scene_data = scene_data
            scene_id_str = None

        # Manage task data caching
        if task_file_id:
            actual_task_data = self._get_cached_task_data(task_data, task_file_id)
        else:
            actual_task_data = task_data

        # Step 1: Initial validation (check only)
        self.logger.info("📋 Step 1: Performing initial validation check...")
        initial_errors, has_removable_tasks = self._validate_task_data_check_only(actual_task_data, actual_scene_data)

        if initial_errors:
            self.logger.warning(f"❌ Found {len(initial_errors)} validation issues:")
            for i, error in enumerate(initial_errors, 1):
                self.logger.warning(f"   {i}. {error}")
        elif not has_removable_tasks:
            self.logger.info("✅ No validation issues found!")
            return True, [], actual_task_data, []
        else:
            self.logger.info("ℹ️  No errors found, but some tasks may need to be removed")

        # Step 2: Apply fixes if requested
        fixes_applied = []
        fixed_data = actual_task_data.copy() if actual_task_data else {}

        if auto_fix:
            self.logger.info("🔧 Step 2: Applying automatic fixes...")

            try:
                # Apply structure fixes
                structure_fixes = self._apply_structure_fixes(fixed_data)
                fixes_applied.extend(structure_fixes)

                # Apply task-level fixes using cached scene data
                if 'tasks' in fixed_data:
                    task_fixes = self._apply_task_fixes(fixed_data['tasks'], actual_scene_data, fixed_data)
                    fixes_applied.extend(task_fixes)

                if fixes_applied:
                    self.logger.info(f"✅ Applied {len(fixes_applied)} fixes:")
                    for i, fix in enumerate(fixes_applied, 1):
                        self.logger.info(f"   {i}. {fix}")
                    # Update task data cache with the fixed data
                    if task_file_id:
                        self._update_task_data_cache(task_file_id, fixed_data)
                else:
                    self.logger.info("ℹ️  No fixes could be applied automatically")

            except Exception as e:
                self.logger.error(f"💥 Error during fix application: {e}")
                # Unregister task before returning
                if scene_id_str:
                    self._unregister_scene_task(scene_id_str)
                return False, initial_errors + [f"Fix application error: {str(e)}"], actual_task_data, []
        else:
            self.logger.info("⏭️  Step 2: Skipping fixes (auto_fix=False)")

        # Step 3: Final validation using cached scene data
        self.logger.info("🔍 Step 3: Performing final validation...")
        final_errors, _ = self._validate_task_data_check_only(fixed_data, actual_scene_data)

        if final_errors:
            self.logger.warning(f"❌ {len(final_errors)} issues remain after fixes:")
            for i, error in enumerate(final_errors, 1):
                self.logger.warning(f"   {i}. {error}")
        else:
            self.logger.info("✅ All issues resolved!")

        # Step 4: Handle scene data saving
        if scene_id_str:
            is_last_task = self._unregister_scene_task(scene_id_str)
            if is_last_task and scene_id_str in self._pending_saves:
                self.logger.info(f"🔄 Last task for scene {scene_id_str}, triggering save...")
                self._flush_scene_modifications()

        is_valid = len(final_errors) == 0
        return is_valid, final_errors, fixed_data, fixes_applied

    def _validate_task_data_check_only(self, task_data: Dict[str, Any], scene_data: Dict[str, Any]) -> Tuple[List[str], bool]:
        """
        Validate task data without making any changes (check-only mode).

        Args:
            task_data: Task data to validate
            scene_data: Scene data for reference

        Returns:
            Tuple of (error_messages, has_removable_tasks)
        """
        errors = []

        try:
            # Check basic structure
            structure_errors = self._check_structure(task_data)
            errors.extend(structure_errors)

            # Check tasks
            if 'tasks' in task_data and isinstance(task_data['tasks'], list):
                scene_objects = self._extract_scene_objects(scene_data)
                scene_rooms = self._extract_scene_rooms(scene_data)
                scene_abilities = self._extract_scene_abilities(scene_data)

                # Set current agents_config for physical constraint checking
                self._current_agents_config = task_data.get('agents_config', [])

                # Count valid tasks (not marked for removal)
                valid_tasks_count = 0
                removable_tasks_count = 0
                total_tasks = len(task_data['tasks'])

                for i, task in enumerate(task_data['tasks']):
                    task_errors, should_remove = self._check_single_task(
                        task, i, scene_objects, scene_rooms, scene_abilities
                    )

                    # Add real errors (not removal flags)
                    errors.extend(task_errors)

                    # Count tasks that are not marked for removal
                    if not should_remove:
                        valid_tasks_count += 1
                    else:
                        removable_tasks_count += 1

                # If all tasks should be removed, add a special error to indicate file should be deleted
                if valid_tasks_count == 0 and total_tasks > 0:
                    errors.append("All tasks in this file should be removed - file will be deleted")

                has_removable_tasks = removable_tasks_count > 0
            else:
                has_removable_tasks = False

        except Exception as e:
            errors.append(f"Validation check error: {str(e)}")
            has_removable_tasks = False

        return errors, has_removable_tasks

    def _check_structure(self, task_data: Dict[str, Any]) -> List[str]:
        """Check basic task data structure without fixing."""
        errors = []

        # Check required top-level fields
        required_fields = ['task_background', 'agents_config', 'tasks']
        for field in required_fields:
            if field not in task_data:
                errors.append(f"Missing required field: {field}")

        # Check task_background
        if 'task_background' in task_data:
            if not isinstance(task_data['task_background'], str) or not task_data['task_background'].strip():
                errors.append("task_background must be a non-empty string")

        # Check agents_config
        if 'agents_config' in task_data:
            agents_config = task_data['agents_config']
            if not isinstance(agents_config, list) or len(agents_config) != 2:
                errors.append("agents_config must be a list with exactly 2 agents")

        # Check tasks is a list
        if 'tasks' in task_data:
            if not isinstance(task_data['tasks'], list):
                errors.append("tasks must be a list")
            elif len(task_data['tasks']) == 0:
                errors.append("tasks list cannot be empty")

        return errors

    def _check_single_task(self, task: Dict[str, Any], task_index: int,
                          scene_objects: Dict[str, Any], scene_rooms: Dict[str, Any],
                          scene_abilities: List[str]) -> Tuple[List[str], bool]:
        """
        Check a single task without fixing.

        Returns:
            Tuple of (errors, should_remove)
        """
        errors = []

        if not isinstance(task, dict):
            errors.append(f"Task {task_index} must be a dictionary")
            return errors, False

        # Check if task should be removed due to unfixable issues
        should_remove, remove_reason = self._should_remove_task(
            task, task_index, scene_objects, scene_rooms, scene_abilities
        )

        if should_remove:
            # Don't add this as an error, just return the removal flag
            return [], True

        # Check required fields
        required_fields = ['task_description', 'task_category', 'validation_checks']
        for field in required_fields:
            if field not in task:
                errors.append(f"Task {task_index} missing required field: {field}")



        # Check validation_checks
        if 'validation_checks' in task:
            validation_checks = task['validation_checks']
            if not isinstance(validation_checks, list):
                errors.append(f"Task {task_index} validation_checks must be a list")
            elif len(validation_checks) == 0:
                errors.append(f"Task {task_index} validation_checks must not be empty")
            else:
                for j, check in enumerate(validation_checks):
                    check_errors = self._check_validation_check(
                        check, task_index, j, task.get('task_description', ''),
                        scene_objects, scene_rooms, scene_abilities
                    )
                    errors.extend(check_errors)

        # Check physical constraints (新增) - 只对搬运任务进行检查
        if self._is_move_task(task):
            task_objects = self._extract_task_objects(task, scene_objects)
            # 从task_data中获取agents_config，如果没有则使用None
            agents_config = getattr(self, '_current_agents_config', None)
            constraint_violations = self._check_physical_constraints(task_objects, scene_objects, agents_config, task)
            if constraint_violations:
                for violation in constraint_violations:
                    errors.append(f"Task {task_index} physical constraint violation: {violation}")

        return errors, False

    def _check_validation_check(self, check: Dict[str, Any], task_index: int, check_index: int,
                               task_description: str, scene_objects: Dict[str, Any],
                               scene_rooms: Dict[str, Any], scene_abilities: List[str]) -> List[str]:
        """Check a single validation check without fixing."""
        errors = []

        if not isinstance(check, dict):
            errors.append(f"Task {task_index} validation_check {check_index} must be a dictionary")
            return errors

        # Check for nested properties
        if 'properties' in check:
            errors.append(f"Task {task_index} validation_check {check_index} should not have nested 'properties'")

        # Check required 'id' field
        if 'id' not in check:
            errors.append(f"Task {task_index} validation_check {check_index} missing required 'id' field")
            return errors

        object_id = check['id']

        # Check if object exists in scene
        if object_id not in scene_objects and object_id not in scene_rooms:
            errors.append(f"Task {task_index} validation_check {check_index}: Object '{object_id}' does not exist in scene")

        # Check location_id if present
        if 'location_id' in check:
            location_errors = self._check_location_id(
                check['location_id'], task_index, check_index, task_description,
                scene_objects, scene_rooms
            )
            errors.extend(location_errors)

        # Check other attributes using CSV
        for attr_name, attr_value in check.items():
            if attr_name not in ['id', 'location_id']:
                attr_errors = self._check_attribute_value(
                    attr_name, attr_value, task_index, check_index, task_description, scene_abilities
                )
                errors.extend(attr_errors)

        return errors

    def _check_location_id(self, location_id: str, task_index: int, check_index: int,
                          task_description: str, scene_objects: Dict[str, Any],
                          scene_rooms: Dict[str, Any]) -> List[str]:
        """Check location_id format and correctness."""
        errors = []

        if not location_id:
            return errors

        # Analyze task description for spatial prepositions
        description_lower = task_description.lower()
        has_in = ' in ' in description_lower or description_lower.startswith('in ')
        has_on = ' on ' in description_lower or description_lower.startswith('on ')

        # Determine correct prefix based on task description
        if has_in and has_on:
            correct_prefix = ":"  # Both present, use empty prefix
        elif has_in:
            correct_prefix = "in:"
        elif has_on:
            correct_prefix = "on:"
        else:
            correct_prefix = ":"  # Neither present, use empty prefix

        # Extract base location (remove existing prefix if any)
        if location_id.startswith(('in:', 'on:', ':')):
            base_location = location_id.split(':', 1)[1] if ':' in location_id else location_id
        else:
            base_location = location_id

        # Construct correct location_id
        correct_location_id = f"{correct_prefix}{base_location}"

        # Check if current location_id matches the expected format
        if location_id != correct_location_id:
            if correct_prefix == ":":
                errors.append(f"Task {task_index} validation_check {check_index}: "
                             f"location_id '{location_id}' should be '{correct_location_id}' (empty prefix - no spatial preposition found)")
            elif correct_prefix == "in:":
                errors.append(f"Task {task_index} validation_check {check_index}: "
                             f"location_id '{location_id}' should be '{correct_location_id}' (in: prefix expected)")
            elif correct_prefix == "on:":
                errors.append(f"Task {task_index} validation_check {check_index}: "
                             f"location_id '{location_id}' should be '{correct_location_id}' (on: prefix expected)")

        # Check if target location exists
        if base_location and base_location not in scene_objects and base_location not in scene_rooms:
            errors.append(f"Task {task_index} validation_check {check_index}: "
                         f"location_id target '{base_location}' does not exist in scene")

        return errors

    def _check_attribute_value(self, attr_name: str, attr_value: Any, task_index: int,
                              check_index: int, task_description: str, scene_abilities: List[str]) -> List[str]:
        """Check attribute value against scene abilities and CSV lookup."""
        errors = []

        # Find the best matching action in scene abilities
        best_action = self._find_best_matching_action(attr_name, task_description, scene_abilities)

        if best_action and self.attribute_actions_df is not None:
            # Look up the action in CSV to get expected value
            matching_rows = self.attribute_actions_df[
                (self.attribute_actions_df['attribute'] == attr_name) &
                (self.attribute_actions_df['action_name'] == best_action)
            ]

            if not matching_rows.empty:
                action_row = matching_rows.iloc[0]
                expected_value = not action_row['value']  # Take inverse as per requirement
                if attr_value != expected_value:
                    errors.append(f"Task {task_index} validation_check {check_index}: "
                                 f"Attribute '{attr_name}' should be {expected_value} "
                                 f"(inverse of CSV value {action_row['value']}, matched action: {best_action})")
        # Note: No error reported if no matching action found - attributes will be handled in repair phase

        return errors

    def _apply_structure_fixes(self, task_data: Dict[str, Any]) -> List[str]:
        """Apply fixes to basic structure."""
        fixes = []

        # Fix missing required fields
        required_fields = ['task_background', 'agents_config', 'tasks']
        for field in required_fields:
            if field not in task_data:
                if field == 'task_background':
                    task_data[field] = "Generated task background"
                    fixes.append(f"Added missing '{field}' field")
                elif field == 'agents_config':
                    task_data[field] = [
                        {"name": "robot_1", "max_grasp_limit": 1, "max_weight": 40.0, "max_size": [1.5, 1.5, 1.5]},
                        {"name": "robot_2", "max_grasp_limit": 1, "max_weight": 40.0, "max_size": [1.5, 1.5, 1.5]}
                    ]
                    fixes.append(f"Added default '{field}' configuration")
                elif field == 'tasks':
                    task_data[field] = []
                    fixes.append(f"Added empty '{field}' array")

        # Fix task_background
        if 'task_background' in task_data:
            if not isinstance(task_data['task_background'], str) or not task_data['task_background'].strip():
                task_data['task_background'] = "Generated task background"
                fixes.append("Fixed empty task_background")

        # Fix agents_config
        if 'agents_config' in task_data:
            agents_config = task_data['agents_config']
            if not isinstance(agents_config, list) or len(agents_config) != 2:
                task_data['agents_config'] = [
                    {"name": "robot_1", "max_grasp_limit": 1, "max_weight": 40.0},
                    {"name": "robot_2", "max_grasp_limit": 1, "max_weight": 40.0}
                ]
                fixes.append("Fixed agents_config structure")

        return fixes

    def _apply_task_fixes(self, tasks: List[Dict[str, Any]], scene_data: Dict[str, Any], task_data: Dict[str, Any]) -> List[str]:
        """Apply fixes to individual tasks."""
        fixes = []

        if not isinstance(tasks, list):
            return fixes

        # Set current agents_config for physical constraint checking
        self._current_agents_config = task_data.get('agents_config', [])

        # Get scene ID for saving modified scene files
        scene_id = task_data.get('scene_id')

        # Get scene data for validation
        scene_objects = self._extract_scene_objects(scene_data)
        scene_rooms = self._extract_scene_rooms(scene_data)
        scene_abilities = self._extract_scene_abilities(scene_data)

        # Track tasks to remove
        tasks_to_remove = []

        for i, task in enumerate(tasks):
            if not isinstance(task, dict):
                continue

            # Check if task should be removed due to unfixable issues
            should_remove, remove_reason = self._should_remove_task(
                task, i, scene_objects, scene_rooms, scene_abilities
            )

            if should_remove:
                tasks_to_remove.append((i, remove_reason))
                continue

            task_fixes = self._apply_single_task_fixes(
                task, i, scene_objects, scene_rooms, scene_abilities, scene_data, scene_id
            )
            fixes.extend(task_fixes)

            # Physical constraint fixes are now handled in _apply_task_fixes
            # by modifying object weights instead of agent capabilities

        # Remove tasks in reverse order to maintain indices
        for task_index, reason in reversed(tasks_to_remove):
            tasks.pop(task_index)
            fixes.append(f"Removed Task {task_index}: {reason}")

        return fixes

    def _should_remove_task(self, task: Dict[str, Any], task_index: int,
                           scene_objects: Dict[str, Any], scene_rooms: Dict[str, Any],
                           scene_abilities: List[str]) -> Tuple[bool, str]:
        """
        严格按照五步验证顺序确定任务是否应该被删除

        第一步：任务类别验证
        第二步：对象ID存在性验证
        第三步：属性验证（仅针对非location_id属性）
        第四步：物理约束验证
        第五步：初始状态与目标状态比较验证（新增）

        Returns:
            Tuple of (should_remove, reason)
        """
        if not isinstance(task, dict):
            self.logger.warning(f"Task {task_index}: Not a dictionary, will be removed")
            return True, "Task is not a dictionary"

        # 第一步：任务类别验证
        self.logger.debug(f"Task {task_index}: Step 1 - Validating task_category")
        if 'task_category' in task:
            category = task.get('task_category', '')
            if category not in self.valid_task_categories:
                self.logger.warning(f"Task {task_index}: Invalid task_category '{category}', will be removed")
                return True, f"Invalid task_category: '{category}'"
        else:
            self.logger.warning(f"Task {task_index}: Missing task_category field, will be removed")
            return True, "Missing task_category field"

        # 检查validation_checks结构
        if 'validation_checks' not in task or not isinstance(task['validation_checks'], list):
            self.logger.warning(f"Task {task_index}: Missing or invalid validation_checks, will be removed")
            return True, "Missing or invalid validation_checks"

        validation_checks = task['validation_checks']
        if len(validation_checks) == 0:
            self.logger.warning(f"Task {task_index}: Empty validation_checks, will be removed")
            return True, "Empty validation_checks"

        # 第二步：对象ID存在性验证
        self.logger.debug(f"Task {task_index}: Step 2 - Validating object ID existence")
        for j, check in enumerate(validation_checks):
            if not isinstance(check, dict):
                self.logger.warning(f"Task {task_index}: validation_check {j} is not a dictionary, will be removed")
                return True, f"validation_check {j} is not a dictionary"

            # 验证id字段及其对应的值
            object_id = check.get('id')
            if not object_id:
                self.logger.warning(f"Task {task_index}: validation_check {j} missing 'id' field, will be removed")
                return True, f"validation_check {j} missing 'id' field"

            # 检查该id对应的物体是否存在于对应场景的JSON文件中
            if object_id not in scene_objects and object_id not in scene_rooms:
                self.logger.warning(f"Task {task_index}: Object '{object_id}' does not exist in scene, will be removed")
                return True, f"Object '{object_id}' does not exist in scene"

        # 第三步：属性验证（仅针对非location_id属性）
        task_description = task.get('task_description', '')
        self.logger.debug(f"Task {task_index}: Step 3 - Validating attributes")

        # 检查是否有非location_id属性需要验证
        if self._task_has_non_location_attributes(task):
            # 确定任务对应的动作：检查每个ability是否出现在任务描述中
            if not self._task_matches_any_scene_ability(task_description, scene_abilities):
                self.logger.warning(f"Task {task_index}: Task description does not match any supported scene abilities, will be removed")
                return True, f"Task description does not match any supported scene abilities"

        # 第四步：物理约束验证
        self.logger.debug(f"Task {task_index}: Step 4 - Validating physical constraints")

        # 检查是否是搬运任务且存在物理约束违反
        if self._is_move_task(task):
            # 获取任务中涉及的对象
            task_objects = self._extract_task_objects(task, scene_objects)

            # 检查物理约束违反（但不删除任务，而是标记需要修复）
            agents_config = getattr(self, '_current_agents_config', None)
            constraint_violations = self._check_physical_constraints(task_objects, scene_objects, agents_config, task)
            if constraint_violations:
                self.logger.info(f"Task {task_index}: Found physical constraint violations that can be auto-fixed: {constraint_violations}")
                # 不删除任务，让修复逻辑处理

        # 第五步：初始状态与目标状态比较验证（新增）
        self.logger.debug(f"Task {task_index}: Step 5 - Validating initial vs target state")
        should_remove_redundant, redundant_reason = self._check_initial_vs_target_state(
            task, task_index, scene_objects, scene_rooms
        )
        if should_remove_redundant:
            self.logger.warning(f"Task {task_index}: {redundant_reason}, will be removed")
            return True, redundant_reason

        self.logger.debug(f"Task {task_index}: All validation steps passed, task will be kept")
        return False, ""

    def _task_has_non_location_attributes(self, task: Dict[str, Any]) -> bool:
        """
        Check if task has attributes other than 'id' and 'location_id'.

        Returns True if the task has attributes that require action validation.
        Returns False if the task only has location_id (no action validation needed).
        """
        validation_checks = task.get('validation_checks', [])

        for check in validation_checks:
            if not isinstance(check, dict):
                continue

            # Check if this validation_check has any attributes other than 'id' and 'location_id'
            for key in check.keys():
                if key not in ['id', 'location_id']:
                    return True  # Found a non-location attribute

        return False  # Only has 'id' and 'location_id'

    def _task_matches_any_scene_ability(self, task_description: str, scene_abilities: List[str]) -> bool:
        """
        Check if task description matches any scene ability.

        Returns True if at least one scene ability can be found in the task description.
        Returns False if no scene abilities match, indicating the task cannot be executed in this scene.
        """
        description_lower = task_description.lower()

        for ability in scene_abilities:
            score = self._score_action_match(ability, description_lower)
            if score > 0:
                return True  # Found at least one matching ability

        return False  # No abilities match this task description

    def _is_collaboration_task(self, task: Dict[str, Any]) -> bool:
        """检查是否是合作任务 - 基于任务类型判断"""
        task_category = task.get('task_category', '')
        task_description = task.get('task_description', 'Unknown task')

        # 合作任务的固定类型
        collaboration_categories = {
            'explicit_collaboration',
            'implicit_collaboration',
            'compound_collaboration'
        }

        is_collaboration = task_category in collaboration_categories

        if is_collaboration:
            self.logger.debug(f"🤝 Collaboration task detected: '{task_description}' (category: {task_category})")
        else:
            self.logger.debug(f"👤 Single-agent task: '{task_description}' (category: {task_category})")

        return is_collaboration

    def _is_move_task(self, task: Dict[str, Any]) -> bool:
        """检查是否是搬运任务 - 基于validation_checks中的location_id判断"""
        validation_checks = task.get('validation_checks', [])

        for check in validation_checks:
            if isinstance(check, dict) and 'location_id' in check:
                return True

        return False

    def _extract_task_objects(self, task: Dict[str, Any], scene_objects: Dict[str, Any]) -> List[str]:
        """从任务中提取需要移动的对象ID（只包含location_id发生改变的物体）"""
        moving_objects = []

        # 只从validation_checks中提取需要移动的对象ID
        validation_checks = task.get('validation_checks', [])
        for check in validation_checks:
            if isinstance(check, dict) and 'id' in check:
                obj_id = check['id']
                # 只有当检查包含location_id时，才认为该物体需要移动
                if 'location_id' in check and obj_id in scene_objects:
                    moving_objects.append(obj_id)

        # 不再从任务描述中提取对象ID，避免包含目标位置等不相关物体
        return moving_objects

    def _check_physical_constraints(self, task_objects: List[str], scene_objects: Dict[str, Any],
                                  agents_config: List[Dict[str, Any]] = None, task: Dict[str, Any] = None) -> List[str]:
        """检查物理约束违反 - 只检查重量，忽略尺寸"""
        violations = []

        # 获取智能体配置（从上下文获取或使用默认值）
        if not agents_config:
            agents_config = self._get_agents_config_from_context()

        # 判断任务类型并计算承重能力（与修复阶段保持一致）
        if task:
            is_collaboration = self._is_collaboration_task(task)
            task_desc = task.get('task_description', 'Unknown task')
        else:
            is_collaboration = False
            task_desc = 'Unknown task'

        if is_collaboration:
            # 多智能体协作：使用最强的两个智能体承重之和
            max_capacity = self._calculate_max_combined_weight(agents_config)
            task_type = "collaboration"
        else:
            # 单智能体：使用单个智能体的承重能力
            max_capacity = max(agent.get('max_weight', 50.0) for agent in agents_config) if agents_config else 50.0
            task_type = "single-agent"

        self.logger.debug(f"🔍 Physical constraint check for task: '{task_desc}'")
        self.logger.debug(f"   Task type: {task_type}")
        self.logger.debug(f"   Max capacity: {max_capacity}kg")
        self.logger.debug(f"   Objects to check: {task_objects}")

        for obj_id in task_objects:
            if obj_id in scene_objects:
                obj = scene_objects[obj_id]
                properties = obj.get('properties', {})

                # 检查重量约束 - 使用动态计算的承重能力
                weight = properties.get('weight', 0)
                self.logger.debug(f"   Object {obj_id}: weight={weight}kg, limit={max_capacity}kg")

                if weight > max_capacity:
                    violation_msg = f"Object {obj_id} weight {weight}kg exceeds max capacity"
                    violations.append(violation_msg)
                    self.logger.warning(f"   ❌ {violation_msg}")
                else:
                    self.logger.debug(f"   ✅ Object {obj_id} weight within limits")
            else:
                self.logger.warning(f"   ⚠️  Object {obj_id} not found in scene")

                # 删除尺寸约束检查 - 完全忽略size相关验证

        return violations




    def _find_best_matching_action(self, attr_name: str, task_description: str,
                                  scene_abilities: List[str]) -> Optional[str]:
        """
        Find the best matching action for an attribute in the task description.

        验证逻辑：
        1. 遍历场景中的所有支持的能力，在任务描述中查看是否能匹配成功
        2. 对于匹配到的动作，已知动作名字，在csv中找到对应的属性和属性值
        3. 修复属性值或保持不变
        4. 如果以上任何步骤失败 → 删除任务
        """
        description_lower = task_description.lower()
        action_scores = []

        # Step 1: 遍历场景中的所有支持的能力，在任务描述中查看是否能匹配成功
        for ability in scene_abilities:
            score = self._score_action_match(ability, description_lower)
            if score > 0:
                # 找到匹配的动作，检查是否与属性相关
                if self._could_action_relate_to_attribute(ability, attr_name):
                    action_scores.append((ability, score))

        # 返回得分最高的动作
        if action_scores:
            action_scores.sort(key=lambda x: x[1], reverse=True)
            return action_scores[0][0]

        return None

    def _score_action_match(self, action_name: str, description_lower: str) -> int:
        """
        Score how well an action matches the description.

        For actions with underscores (e.g., 'turn_on', 'stop_playback'):
        - Split by underscore and check if ALL parts are present in description
        - Only match if every part is found
        """
        action_lower = action_name.lower()
        score = 0

        # Direct match (highest score)
        if action_lower in description_lower:
            score = 100

        # Handle underscore to space conversion
        elif action_lower.replace('_', ' ') in description_lower:
            score = 90

        # Handle compound actions with underscores - ALL parts must be present
        elif '_' in action_lower:
            action_parts = action_lower.split('_')
            if all(part in description_lower for part in action_parts):
                score = 80 + len(action_parts) * 5  # Bonus for more specific compound actions

        return score

    def _could_action_relate_to_attribute(self, action_name: str, attr_name: str) -> bool:
        """
        Check if an action could reasonably relate to an attribute by looking up CSV.

        Since CSV contains action_name and attribute pairs, we use CSV as the source of truth
        for attribute-action relationships instead of hardcoded mappings.
        """
        if self.attribute_actions_df is None:
            return False

        # Check if this action-attribute pair exists in CSV
        matching_rows = self.attribute_actions_df[
            (self.attribute_actions_df['action_name'] == action_name) &
            (self.attribute_actions_df['attribute'] == attr_name)
        ]

        return not matching_rows.empty



    def _apply_single_task_fixes(self, task: Dict[str, Any], task_index: int,
                                scene_objects: Dict[str, Any], scene_rooms: Dict[str, Any],
                                scene_abilities: List[str], scene_data: Dict[str, Any] = None,
                                scene_id: str = None) -> List[str]:
        """Apply fixes to a single task."""
        fixes = []

        # Fix missing required fields
        required_fields = ['task_description', 'task_category', 'validation_checks']
        for field in required_fields:
            if field not in task:
                if field == 'validation_checks':
                    task[field] = []
                    fixes.append(f"Task {task_index}: Added empty validation_checks")

        # Note: Invalid task_category is handled in _should_remove_task - no fixing attempted

        # Fix validation_checks
        if 'validation_checks' in task and isinstance(task['validation_checks'], list):
            for j, check in enumerate(task['validation_checks']):
                if isinstance(check, dict):
                    check_fixes = self._apply_validation_check_fixes(
                        check, task_index, j, task.get('task_description', ''),
                        scene_objects, scene_rooms, scene_abilities
                    )
                    fixes.extend(check_fixes)

        # Fix physical constraints (新增) - 只对搬运任务进行修复
        if self._is_move_task(task):
            physical_fixes = self._apply_physical_constraint_fixes(
                task, task_index, scene_objects, scene_data, scene_id
            )
            fixes.extend(physical_fixes)

        return fixes

    def _apply_validation_check_fixes(self, check: Dict[str, Any], task_index: int, check_index: int,
                                     task_description: str, scene_objects: Dict[str, Any],
                                     scene_rooms: Dict[str, Any], scene_abilities: List[str]) -> List[str]:
        """Apply fixes to a single validation check."""
        fixes = []

        # Fix nested properties
        if 'properties' in check:
            properties = check.pop('properties')
            if isinstance(properties, dict):
                check.update(properties)
                fixes.append(f"Task {task_index} check {check_index}: Removed nested 'properties' and moved contents up")

        # Fix location_id if present
        if 'location_id' in check:
            location_fixes = self._apply_location_id_fixes(
                check, task_index, check_index, task_description, scene_objects, scene_rooms
            )
            fixes.extend(location_fixes)

        # Fix other attributes using CSV
        for attr_name, attr_value in list(check.items()):
            if attr_name not in ['id', 'location_id']:
                attr_fixes = self._apply_attribute_fixes(
                    attr_name, attr_value, task_index, check_index, task_description,
                    scene_abilities, check
                )
                fixes.extend(attr_fixes)

        return fixes

    def _apply_location_id_fixes(self, check: Dict[str, Any], task_index: int, check_index: int,
                                task_description: str, scene_objects: Dict[str, Any],
                                scene_rooms: Dict[str, Any]) -> List[str]:
        """Apply fixes to location_id - checks both missing and incorrect prefixes."""
        fixes = []
        location_id = check.get('location_id', '')

        if not location_id:
            return fixes

        # Analyze task description for spatial prepositions
        description_lower = task_description.lower()
        has_in = ' in ' in description_lower or description_lower.startswith('in ')
        has_on = ' on ' in description_lower or description_lower.startswith('on ')

        # Determine correct prefix based on task description
        if has_in and has_on:
            correct_prefix = ":"  # Both present, use empty prefix
        elif has_in:
            correct_prefix = "in:"
        elif has_on:
            correct_prefix = "on:"
        else:
            correct_prefix = ":"  # Neither present, use empty prefix

        # Extract base location (remove existing prefix if any)
        if location_id.startswith(('in:', 'on:', ':')):
            base_location = location_id.split(':', 1)[1] if ':' in location_id else location_id
        else:
            base_location = location_id

        # Construct correct location_id
        correct_location_id = f"{correct_prefix}{base_location}"

        # Apply fix if current location_id is incorrect
        if location_id != correct_location_id:
            check['location_id'] = correct_location_id
            if correct_prefix == ":":
                fixes.append(f"Task {task_index} check {check_index}: Fixed location_id from '{location_id}' to '{correct_location_id}' (empty prefix - no spatial preposition found)")
            elif correct_prefix == "in:":
                fixes.append(f"Task {task_index} check {check_index}: Fixed location_id from '{location_id}' to '{correct_location_id}' (in: prefix)")
            elif correct_prefix == "on:":
                fixes.append(f"Task {task_index} check {check_index}: Fixed location_id from '{location_id}' to '{correct_location_id}' (on: prefix)")

        return fixes

    def _apply_attribute_fixes(self, attr_name: str, attr_value: Any, task_index: int,
                              check_index: int, task_description: str, scene_abilities: List[str],
                              check: Dict[str, Any]) -> List[str]:
        """
        严格按照第三步属性验证和修复逻辑：

        情况B：如果是其他属性字段
        - 首先确定任务对应的动作：
          - 读取任务对应场景JSON文件中的abilities字段
          - 逐个检查每个ability是否出现在任务描述(task_description)中
          - 对于包含下划线的ability（如"turn_on"），需要将其分割后检查所有部分是否都在任务描述中出现
          - 如果所有abilities都无法匹配任务描述，删除整个任务
        - 找到匹配的动作后：
          - 在CSV文件中查询该动作名对应的标准属性名和属性值
          - 对比原始键值对与CSV中的标准格式
          - 修正属性名为CSV中对应的标准属性名
          - 修正属性值为CSV中取值的逻辑取反值
          - 记录所有修改详情
        """
        fixes = []

        self.logger.debug(f"Task {task_index} check {check_index}: Processing attribute '{attr_name}' with value '{attr_value}'")

        # 首先确定任务对应的动作：逐个检查每个ability是否出现在任务描述中
        matched_action = None
        for ability in scene_abilities:
            if self._ability_matches_task_description(ability, task_description):
                self.logger.debug(f"Task {task_index} check {check_index}: Found matching ability '{ability}' in task description")
                matched_action = ability
                break

        if not matched_action:
            # 如果所有abilities都无法匹配任务描述，这个任务应该在_should_remove_task中被删除
            # 这里不应该到达，但为了安全起见记录警告
            self.logger.warning(f"Task {task_index} check {check_index}: No matching ability found for attribute '{attr_name}'")
            return fixes

        # 找到匹配的动作后：在CSV文件中查询该动作名对应的标准属性名和属性值
        if self.attribute_actions_df is not None:
            # 查找CSV中该动作对应的所有属性
            action_rows = self.attribute_actions_df[
                self.attribute_actions_df['action_name'] == matched_action
            ]

            if not action_rows.empty:
                # 尝试找到与当前属性名匹配的行
                matching_attr_row = action_rows[action_rows['attribute'] == attr_name]

                if not matching_attr_row.empty:
                    # 找到完全匹配的属性名
                    csv_row = matching_attr_row.iloc[0]
                    expected_value = not csv_row['value']  # 修正属性值为CSV中取值的逻辑取反值

                    if attr_value != expected_value:
                        check[attr_name] = expected_value
                        fixes.append(f"Task {task_index} check {check_index}: "
                                   f"Fixed attribute '{attr_name}' value from {attr_value} to {expected_value} "
                                   f"(matched action: {matched_action}, CSV value inverted)")
                        self.logger.info(f"Task {task_index} check {check_index}: Fixed attribute value")
                else:
                    # 属性名不匹配，尝试修正属性名
                    # 查找该动作的第一个属性作为标准属性名
                    if len(action_rows) > 0:
                        csv_row = action_rows.iloc[0]
                        correct_attr_name = csv_row['attribute']
                        expected_value = not csv_row['value']  # 修正属性值为CSV中取值的逻辑取反值

                        # 修正属性名为CSV中对应的标准属性名
                        del check[attr_name]  # 删除原有的错误属性名
                        check[correct_attr_name] = expected_value
                        fixes.append(f"Task {task_index} check {check_index}: "
                                   f"Fixed attribute name from '{attr_name}' to '{correct_attr_name}' "
                                   f"and set value to {expected_value} "
                                   f"(matched action: {matched_action}, CSV value inverted)")
                        self.logger.info(f"Task {task_index} check {check_index}: Fixed attribute name and value")
            else:
                self.logger.warning(f"Task {task_index} check {check_index}: No CSV data found for action '{matched_action}'")

        return fixes
    def _ability_matches_task_description(self, ability: str, task_description: str) -> bool:
        """
        检查ability是否出现在任务描述中
        对于包含下划线的ability（如"turn_on"），需要将其分割后检查所有部分是否都在任务描述中出现
        """
        description_lower = task_description.lower()
        ability_lower = ability.lower()

        # 直接匹配
        if ability_lower in description_lower:
            return True

        # 处理下划线转空格的情况
        if ability_lower.replace('_', ' ') in description_lower:
            return True

        # 对于包含下划线的ability，分割后检查所有部分是否都在任务描述中出现
        if '_' in ability_lower:
            ability_parts = ability_lower.split('_')
            if all(part in description_lower for part in ability_parts):
                return True

        return False






    def _extract_scene_objects(self, scene_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract objects from scene data."""
        objects = {}
        if 'objects' in scene_data:
            for obj in scene_data['objects']:
                if isinstance(obj, dict) and 'id' in obj:
                    objects[obj['id']] = obj
        return objects

    def _extract_scene_rooms(self, scene_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract rooms from scene data."""
        rooms = {}
        if 'rooms' in scene_data:
            for room in scene_data['rooms']:
                if isinstance(room, dict) and 'id' in room:
                    rooms[room['id']] = room
        return rooms

    def _extract_scene_abilities(self, scene_data: Dict[str, Any]) -> List[str]:
        """Extract abilities from scene data."""
        abilities = []
        if 'abilities' in scene_data:
            for ability in scene_data['abilities']:
                if isinstance(ability, dict) and 'name' in ability:
                    abilities.append(ability['name'])  # Keep original case
                elif isinstance(ability, str):
                    abilities.append(ability)  # Direct string ability
        return abilities

    def validate_task_file(self, task_file_path: str, scene_file_path: str,
                          auto_fix: bool = True, save_changes: bool = True) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a task file against its corresponding scene file.

        Args:
            task_file_path: Path to the task JSON file
            scene_file_path: Path to the scene JSON file
            auto_fix: Whether to automatically fix issues
            save_changes: Whether to save changes to the file (False for testing)

        Returns:
            Tuple of (is_valid, error_messages, fixes_applied)
        """
        try:
            # Load task data
            with open(task_file_path, 'r', encoding='utf-8') as f:
                task_data = json.load(f)

            # Load scene data
            with open(scene_file_path, 'r', encoding='utf-8') as f:
                scene_data = json.load(f)

            # Validate and fix
            is_valid, errors, fixed_task_data, fixes_applied = self.validate_and_fix_task_data(
                task_data, scene_data, auto_fix
            )

            # Save fixed data if fixes were applied and save_changes is True
            if auto_fix and fixes_applied and save_changes:
                with open(task_file_path, 'w', encoding='utf-8') as f:
                    json.dump(fixed_task_data, f, ensure_ascii=False, indent=2)
                self.logger.info(f"Applied {len(fixes_applied)} fixes to {task_file_path}")

                # Save fix log
                self._save_fix_log(task_file_path, fixes_applied, errors)
            elif auto_fix and fixes_applied and not save_changes:
                self.logger.info(f"Would apply {len(fixes_applied)} fixes to {task_file_path} (test mode)")

            return is_valid, errors, fixes_applied

        except Exception as e:
            self.logger.error(f"Error validating task file {task_file_path}: {e}")
            return False, [f"File validation error: {str(e)}"], []

    def _save_fix_log(self, task_file_path: str, fixes_applied: List[str], remaining_errors: List[str]):
        """Save fix log to a log file."""
        import datetime

        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Create log filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        task_filename = Path(task_file_path).stem
        log_filename = f"{task_filename}_fixes_{timestamp}.log"
        log_path = log_dir / log_filename

        # Write log
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"Task Validation and Fix Log\n")
            f.write(f"=" * 50 + "\n")
            f.write(f"File: {task_file_path}\n")
            f.write(f"Timestamp: {datetime.datetime.now().isoformat()}\n")
            f.write(f"Fixes Applied: {len(fixes_applied)}\n")
            f.write(f"Remaining Errors: {len(remaining_errors)}\n\n")

            if fixes_applied:
                f.write("FIXES APPLIED:\n")
                f.write("-" * 20 + "\n")
                for i, fix in enumerate(fixes_applied, 1):
                    f.write(f"{i}. {fix}\n")
                f.write("\n")

            if remaining_errors:
                f.write("REMAINING ERRORS:\n")
                f.write("-" * 20 + "\n")
                for i, error in enumerate(remaining_errors, 1):
                    f.write(f"{i}. {error}\n")
                f.write("\n")

        self.logger.info(f"Fix log saved to: {log_path}")

    def _apply_physical_constraint_fixes(self, task: Dict[str, Any], task_index: int,
                                       scene_objects: Dict[str, Any], scene_data: Dict[str, Any] = None,
                                       scene_id: str = None) -> List[str]:
        """应用物理约束修复 - 修改物体重量而不是智能体能力"""
        fixes = []
        scene_modified = False

        # 获取任务中涉及的对象
        task_objects = self._extract_task_objects(task, scene_objects)

        # 判断任务类型并计算承重能力
        is_collaboration = self._is_collaboration_task(task)
        task_desc = task.get('task_description', 'Unknown task')

        # 获取智能体配置（从上下文获取或使用默认值）
        agents_config = self._get_agents_config_from_context()

        if is_collaboration:
            # 多智能体协作：使用最强的两个智能体承重之和
            max_capacity = self._calculate_max_combined_weight(agents_config)
            task_type = "collaboration"
        else:
            # 单智能体：使用单个智能体的承重能力
            max_capacity = max(agent.get('max_weight', 50.0) for agent in agents_config) if agents_config else 50.0
            task_type = "single-agent"

        self.logger.info(f"🔧 Physical constraint fix for Task {task_index}: '{task_desc}'")
        self.logger.info(f"   Task type: {task_type}")
        self.logger.info(f"   Max capacity: {max_capacity}kg")
        self.logger.info(f"   Objects to fix: {task_objects}")

        for obj_id in task_objects:
            if obj_id in scene_objects:
                obj = scene_objects[obj_id]
                properties = obj.get('properties', {})

                # 检查并修复重量约束
                current_weight = properties.get('weight', 0)
                self.logger.debug(f"   Checking object {obj_id}: current_weight={current_weight}kg, limit={max_capacity}kg")

                if current_weight > max_capacity:
                    self.logger.info(f"   ❌ Object {obj_id} exceeds weight limit: {current_weight}kg > {max_capacity}kg")

                    # 修改物体重量为智能体承重能力
                    old_weight = current_weight
                    properties['weight'] = max_capacity
                    scene_modified = True

                    # 同步更新 scene_objects 中的数据
                    if obj_id in scene_objects:
                        scene_objects[obj_id]['properties']['weight'] = max_capacity
                        self.logger.debug(f"   🔄 Updated scene_objects for {obj_id}: {old_weight}kg -> {max_capacity}kg")

                    fixes.append(f"Task {task_index}: Reduced object {obj_id} weight from {old_weight}kg to {max_capacity}kg ({task_type} task)")
                    self.logger.info(f"   ✅ Fixed weight constraint for {obj_id}: {old_weight}kg -> {max_capacity}kg ({task_type})")
                else:
                    self.logger.debug(f"   ✅ Object {obj_id} weight within limits")
            else:
                self.logger.warning(f"   ⚠️  Object {obj_id} not found in scene_objects")

        # 如果场景被修改且提供了场景数据和ID，标记为待保存
        if scene_modified and scene_data and scene_id:
            self.logger.info(f"💾 Scene modified, marking scene {scene_id} for saving")
            self._mark_scene_for_save(scene_id)
        elif scene_modified:
            self.logger.warning(f"⚠️  Scene was modified but cannot save (scene_data={bool(scene_data)}, scene_id={scene_id})")

        return fixes

    def _get_agents_config_from_context(self) -> List[Dict[str, Any]]:
        """从上下文获取智能体配置，如果没有则返回默认配置"""
        agents_config = getattr(self, '_current_agents_config', None)
        if not agents_config:
            # 返回默认的双智能体配置
            return [
                {"name": "robot_1", "max_grasp_limit": 1, "max_weight": 50.0},
                {"name": "robot_2", "max_grasp_limit": 1, "max_weight": 50.0}
            ]
        return agents_config

    def _calculate_max_combined_weight(self, agents_config: List[Dict[str, Any]]) -> float:
        """计算智能体组合的最大承重能力"""
        if not agents_config:
            return 100.0  # 默认值

        # 找到承重能力最高的两个智能体
        weights = [agent.get('max_weight', 50.0) for agent in agents_config]
        weights.sort(reverse=True)

        # 返回最高的两个智能体的承重和
        return weights[0] + (weights[1] if len(weights) > 1 else 0)

    # 删除 _calculate_max_combined_size 方法，不再需要尺寸计算

    # 删除 _apply_agents_config_fixes_for_task 方法
    # 新的修复策略是修改物体重量而不是智能体能力

    def _check_initial_vs_target_state(self, task: Dict[str, Any], task_index: int,
                                      scene_objects: Dict[str, Any], scene_rooms: Dict[str, Any]) -> Tuple[bool, str]:
        """
        检查任务的目标状态是否与场景的初始状态相同

        如果目标状态与初始状态相同，说明任务已经完成或无意义，应该被删除

        Args:
            task: 任务数据
            task_index: 任务索引
            scene_objects: 场景对象字典
            scene_rooms: 场景房间字典

        Returns:
            Tuple of (should_remove, reason)
        """
        validation_checks = task.get('validation_checks', [])

        for check_index, check in enumerate(validation_checks):
            if not isinstance(check, dict):
                continue

            object_id = check.get('id')
            if not object_id:
                continue

            # 获取场景中的对象或房间
            scene_entity = None
            if object_id in scene_objects:
                scene_entity = scene_objects[object_id]
            elif object_id in scene_rooms:
                scene_entity = scene_rooms[object_id]
            else:
                # 对象不存在，这个问题会在第二步验证中被捕获
                continue

            # 检查位置是否相同
            if 'location_id' in check:
                current_location = scene_entity.get('location_id', '')
                target_location = check['location_id']

                # 标准化位置ID进行比较
                normalized_current = self._normalize_location_id(current_location)
                normalized_target = self._normalize_location_id(target_location)

                if normalized_current == normalized_target:
                    self.logger.debug(f"Task {task_index}: Object {object_id} already at target location '{target_location}'")
                    return True, f"Object {object_id} already at target location (current: '{current_location}', target: '{target_location}')"

            # 检查状态属性是否相同
            scene_states = scene_entity.get('states', {})
            for attr_name, target_value in check.items():
                if attr_name in ['id', 'location_id']:
                    continue

                if attr_name.startswith('is_'):
                    current_value = scene_states.get(attr_name)
                    if current_value == target_value:
                        self.logger.debug(f"Task {task_index}: Object {object_id} already has target state {attr_name}={target_value}")
                        return True, f"Object {object_id} already has target state {attr_name}={target_value}"

        return False, ""

    def _normalize_location_id(self, location_id: str) -> str:
        """
        标准化location_id以便比较

        移除前缀并返回基础位置ID

        Args:
            location_id: 原始位置ID

        Returns:
            标准化的位置ID
        """
        if not location_id:
            return ""

        # 移除前缀 (in:, on:, :)
        if location_id.startswith(('in:', 'on:', ':')):
            if ':' in location_id:
                return location_id.split(':', 1)[1]

        return location_id
