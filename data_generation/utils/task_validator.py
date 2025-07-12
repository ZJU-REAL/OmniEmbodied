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

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

from utils.logger import get_logger


class TaskValidator:
    """Validator for task JSON data with automatic fixing capabilities."""

    def __init__(self, attribute_actions_csv_path: str = "data/attribute_actions.csv"):
        """
        Initialize the task validator.

        Args:
            attribute_actions_csv_path: Path to the attribute actions CSV file
        """
        self.logger = get_logger(__name__)
        self.attribute_actions_csv_path = attribute_actions_csv_path
        self.attribute_actions_df = None
        self.valid_task_categories = {
            'direct_command', 'attribute_reasoning', 'tool_use', 'compound_reasoning',
            'explicit_collaboration', 'implicit_collaboration', 'compound_collaboration'
        }

        # Load attribute actions CSV
        self._load_attribute_actions()

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

        # Step 1: Initial validation (check only)
        self.logger.info("📋 Step 1: Performing initial validation check...")
        initial_errors = self._validate_task_data_check_only(task_data, scene_data)

        if initial_errors:
            self.logger.warning(f"❌ Found {len(initial_errors)} validation issues:")
            for i, error in enumerate(initial_errors, 1):
                self.logger.warning(f"   {i}. {error}")
        else:
            self.logger.info("✅ No validation issues found!")
            return True, [], task_data, []

        # Step 2: Apply fixes if requested
        fixes_applied = []
        fixed_data = task_data.copy() if task_data else {}

        if auto_fix:
            self.logger.info("🔧 Step 2: Applying automatic fixes...")

            try:
                # Apply structure fixes
                structure_fixes = self._apply_structure_fixes(fixed_data)
                fixes_applied.extend(structure_fixes)

                # Apply task-level fixes
                if 'tasks' in fixed_data:
                    task_fixes = self._apply_task_fixes(fixed_data['tasks'], scene_data)
                    fixes_applied.extend(task_fixes)

                if fixes_applied:
                    self.logger.info(f"✅ Applied {len(fixes_applied)} fixes:")
                    for i, fix in enumerate(fixes_applied, 1):
                        self.logger.info(f"   {i}. {fix}")
                else:
                    self.logger.info("ℹ️  No fixes could be applied automatically")

            except Exception as e:
                self.logger.error(f"💥 Error during fix application: {e}")
                return False, initial_errors + [f"Fix application error: {str(e)}"], task_data, []
        else:
            self.logger.info("⏭️  Step 2: Skipping fixes (auto_fix=False)")

        # Step 3: Final validation
        self.logger.info("🔍 Step 3: Performing final validation...")
        final_errors = self._validate_task_data_check_only(fixed_data, scene_data)

        if final_errors:
            self.logger.warning(f"❌ {len(final_errors)} issues remain after fixes:")
            for i, error in enumerate(final_errors, 1):
                self.logger.warning(f"   {i}. {error}")
        else:
            self.logger.info("✅ All issues resolved!")

        is_valid = len(final_errors) == 0
        return is_valid, final_errors, fixed_data, fixes_applied

    def _validate_task_data_check_only(self, task_data: Dict[str, Any], scene_data: Dict[str, Any]) -> List[str]:
        """
        Validate task data without making any changes (check-only mode).

        Args:
            task_data: Task data to validate
            scene_data: Scene data for reference

        Returns:
            List of error messages
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

                for i, task in enumerate(task_data['tasks']):
                    task_errors = self._check_single_task(
                        task, i, scene_objects, scene_rooms, scene_abilities
                    )
                    errors.extend(task_errors)

        except Exception as e:
            errors.append(f"Validation check error: {str(e)}")

        return errors

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
                          scene_abilities: List[str]) -> List[str]:
        """Check a single task without fixing."""
        errors = []

        if not isinstance(task, dict):
            errors.append(f"Task {task_index} must be a dictionary")
            return errors

        # Check if task should be removed due to unfixable issues
        should_remove, remove_reason = self._should_remove_task(
            task, task_index, scene_objects, scene_rooms, scene_abilities
        )

        if should_remove:
            errors.append(f"Task {task_index} should be removed: {remove_reason}")
            return errors

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

        # Check physical constraints (新增)
        task_description = task.get('task_description', '')
        if self._is_collaboration_move_task(task_description):
            task_objects = self._extract_task_objects(task, scene_objects)
            constraint_violations = self._check_physical_constraints(task_objects, scene_objects)
            if constraint_violations:
                for violation in constraint_violations:
                    errors.append(f"Task {task_index} physical constraint violation: {violation}")

        return errors

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
        """Check location_id without fixing."""
        errors = []

        # Check if location_id has proper format (in:, on:, or :)
        if not location_id.startswith(('in:', 'on:', ':')):
            description_lower = task_description.lower()
            has_in = ' in ' in description_lower or description_lower.startswith('in ')
            has_on = ' on ' in description_lower or description_lower.startswith('on ')

            if has_in and has_on:
                errors.append(f"Task {task_index} validation_check {check_index}: "
                             f"location_id '{location_id}' should use format ':object_id' when both in/on are present")
            elif has_in or has_on:
                errors.append(f"Task {task_index} validation_check {check_index}: "
                             f"location_id '{location_id}' should have 'in:' or 'on:' prefix based on task description")
            else:
                errors.append(f"Task {task_index} validation_check {check_index}: "
                             f"location_id '{location_id}' should use format ':object_id' when no spatial relationship is specified")

        # Check if target location exists
        if ':' in location_id:
            prefix, target = location_id.split(':', 1)
            if target and target not in scene_objects and target not in scene_rooms:
                errors.append(f"Task {task_index} validation_check {check_index}: "
                             f"location_id target '{target}' does not exist in scene")

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
                    {"name": "robot_1", "max_grasp_limit": 1, "max_weight": 40.0, "max_size": [1.5, 1.5, 1.5]},
                    {"name": "robot_2", "max_grasp_limit": 1, "max_weight": 40.0, "max_size": [1.5, 1.5, 1.5]}
                ]
                fixes.append("Fixed agents_config structure")

        return fixes

    def _apply_task_fixes(self, tasks: List[Dict[str, Any]], scene_data: Dict[str, Any]) -> List[str]:
        """Apply fixes to individual tasks."""
        fixes = []

        if not isinstance(tasks, list):
            return fixes

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
                task, i, scene_objects, scene_rooms, scene_abilities
            )
            fixes.extend(task_fixes)

        # Remove tasks in reverse order to maintain indices
        for task_index, reason in reversed(tasks_to_remove):
            tasks.pop(task_index)
            fixes.append(f"Removed Task {task_index}: {reason}")

        return fixes

    def _should_remove_task(self, task: Dict[str, Any], task_index: int,
                           scene_objects: Dict[str, Any], scene_rooms: Dict[str, Any],
                           scene_abilities: List[str]) -> Tuple[bool, str]:
        """
        严格按照三步验证顺序确定任务是否应该被删除

        第一步：任务类别验证
        第二步：对象ID存在性验证
        第三步：属性验证（仅针对非location_id属性）

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

        # 第四步：物理约束验证（新增）
        self.logger.debug(f"Task {task_index}: Step 4 - Validating physical constraints")

        # 检查是否是协作搬运任务且存在物理约束违反
        if self._is_collaboration_move_task(task_description):
            # 获取任务中涉及的对象
            task_objects = self._extract_task_objects(task, scene_objects)

            # 检查物理约束违反（但不删除任务，而是标记需要修复）
            constraint_violations = self._check_physical_constraints(task_objects, scene_objects)
            if constraint_violations:
                self.logger.info(f"Task {task_index}: Found physical constraint violations that can be auto-fixed: {constraint_violations}")
                # 不删除任务，让修复逻辑处理

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

    def _is_collaboration_move_task(self, task_description: str) -> bool:
        """检查是否是协作搬运任务"""
        description_lower = task_description.lower()

        # 协作关键词
        collaboration_keywords = ['cooperat', 'together', 'both', 'robot_1 and robot_2']

        # 搬运关键词
        move_keywords = ['move', 'transport', 'carry', 'bring', 'take']

        has_collaboration = any(keyword in description_lower for keyword in collaboration_keywords)
        has_movement = any(keyword in description_lower for keyword in move_keywords)

        return has_collaboration and has_movement

    def _extract_task_objects(self, task: Dict[str, Any], scene_objects: Dict[str, Any]) -> List[str]:
        """从任务中提取涉及的对象ID"""
        task_objects = []

        # 从validation_checks中提取对象ID
        validation_checks = task.get('validation_checks', [])
        for check in validation_checks:
            if isinstance(check, dict) and 'id' in check:
                obj_id = check['id']
                if obj_id in scene_objects:
                    task_objects.append(obj_id)

        # 从任务描述中提取对象ID（简单的正则匹配）
        import re
        task_description = task.get('task_description', '')

        # 查找形如 object_name_1 的模式
        object_pattern = r'\b([a-zA-Z_]+_\d+)\b'
        matches = re.findall(object_pattern, task_description)

        for match in matches:
            if match in scene_objects and match not in task_objects:
                task_objects.append(match)

        return task_objects

    def _check_physical_constraints(self, task_objects: List[str], scene_objects: Dict[str, Any]) -> List[str]:
        """检查物理约束违反"""
        violations = []

        for obj_id in task_objects:
            if obj_id in scene_objects:
                obj = scene_objects[obj_id]
                properties = obj.get('properties', {})

                # 检查重量约束
                weight = properties.get('weight', 0)
                if weight > 100:  # 假设两个机器人最大承重100kg
                    violations.append(f"Object {obj_id} weight {weight}kg exceeds max capacity")

                # 检查尺寸约束
                size = properties.get('size', [0, 0, 0])
                if isinstance(size, list) and len(size) >= 3:
                    if any(dim > 1.5 for dim in size):  # 假设最大尺寸限制1.5
                        violations.append(f"Object {obj_id} size {size} exceeds max dimensions")

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
                                scene_abilities: List[str]) -> List[str]:
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

        # Fix physical constraints (新增)
        task_description = task.get('task_description', '')
        if self._is_collaboration_move_task(task_description):
            # 需要传递完整的任务数据以获取agents_config
            # 这里我们需要从上层获取完整的task_data
            # 暂时使用默认配置，后续可以优化
            physical_fixes = self._apply_physical_constraint_fixes(
                task, task_index, scene_objects
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
        """Apply fixes to location_id."""
        fixes = []

        location_id = check.get('location_id', '')

        # Fix location_id format
        if not location_id.startswith(('in:', 'on:')):
            description_lower = task_description.lower()
            has_in = ' in ' in description_lower or description_lower.startswith('in ')
            has_on = ' on ' in description_lower or description_lower.startswith('on ')

            if has_in and has_on:
                # Both present, keep original format (no prefix change)
                check['location_id'] = f":{location_id}"
                fixes.append(f"Task {task_index} check {check_index}: Fixed location_id to use empty prefix (both in/on found, keeping original)")
            elif has_in:
                check['location_id'] = f"in:{location_id}"
                fixes.append(f"Task {task_index} check {check_index}: Fixed location_id to use 'in:' prefix")
            elif has_on:
                check['location_id'] = f"on:{location_id}"
                fixes.append(f"Task {task_index} check {check_index}: Fixed location_id to use 'on:' prefix")
            else:
                object_id = check.get('id', '')
                check['location_id'] = f":{object_id}"
                fixes.append(f"Task {task_index} check {check_index}: Set location_id to empty format")

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
        from pathlib import Path

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
                                       scene_objects: Dict[str, Any]) -> List[str]:
        """应用物理约束修复"""
        fixes = []

        # 获取任务中涉及的对象
        task_objects = self._extract_task_objects(task, scene_objects)

        # 获取智能体配置，计算最大承重能力
        agents_config = self._get_agents_config_from_context()
        max_combined_weight = self._calculate_max_combined_weight(agents_config)
        max_combined_size = self._calculate_max_combined_size(agents_config)

        for obj_id in task_objects:
            if obj_id in scene_objects:
                obj = scene_objects[obj_id]
                properties = obj.get('properties', {})

                # 修复重量约束违反
                weight = properties.get('weight', 0)
                if weight > max_combined_weight:
                    # 将重量调整为略低于最大承重
                    new_weight = max_combined_weight * 0.9  # 留10%安全余量
                    properties['weight'] = new_weight
                    fixes.append(f"Task {task_index}: Reduced object {obj_id} weight from {weight}kg to {new_weight}kg for collaboration feasibility")
                    self.logger.info(f"Fixed weight constraint for {obj_id}: {weight} -> {new_weight}")

                # 修复尺寸约束违反
                size = properties.get('size', [0, 0, 0])
                if isinstance(size, list) and len(size) >= 3:
                    size_fixed = False
                    new_size = size.copy()

                    for i, (dim, max_dim) in enumerate(zip(size, max_combined_size)):
                        if dim > max_dim:
                            new_size[i] = max_dim * 0.9  # 留10%安全余量
                            size_fixed = True

                    if size_fixed:
                        properties['size'] = new_size
                        fixes.append(f"Task {task_index}: Adjusted object {obj_id} size from {size} to {new_size} for collaboration feasibility")
                        self.logger.info(f"Fixed size constraint for {obj_id}: {size} -> {new_size}")

        return fixes

    def _get_agents_config_from_context(self) -> List[Dict[str, Any]]:
        """获取智能体配置（从上下文或使用默认值）"""
        # 这里可以从当前处理的任务数据中获取agents_config
        # 为了简化，先使用默认配置
        return [
            {"name": "robot_1", "max_weight": 50.0, "max_size": [1.5, 1.5, 1.5]},
            {"name": "robot_2", "max_weight": 50.0, "max_size": [1.5, 1.5, 1.5]}
        ]

    def _calculate_max_combined_weight(self, agents_config: List[Dict[str, Any]]) -> float:
        """计算智能体组合的最大承重能力"""
        if not agents_config:
            return 100.0  # 默认值

        # 找到承重能力最高的两个智能体
        weights = [agent.get('max_weight', 50.0) for agent in agents_config]
        weights.sort(reverse=True)

        # 返回最高的两个智能体的承重和
        return weights[0] + (weights[1] if len(weights) > 1 else 0)

    def _calculate_max_combined_size(self, agents_config: List[Dict[str, Any]]) -> List[float]:
        """计算智能体组合的最大尺寸能力"""
        if not agents_config:
            return [1.5, 1.5, 1.5]  # 默认值

        # 找到尺寸能力最大的智能体
        max_sizes = []
        for agent in agents_config:
            agent_size = agent.get('max_size', [1.5, 1.5, 1.5])
            if not max_sizes:
                max_sizes = agent_size.copy()
            else:
                for i in range(min(len(max_sizes), len(agent_size))):
                    max_sizes[i] = max(max_sizes[i], agent_size[i])

        return max_sizes if max_sizes else [1.5, 1.5, 1.5]
