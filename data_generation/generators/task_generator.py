#!/usr/bin/env python3
"""
Task Generator with embedded verification.

This module provides a unified approach to task generation that combines
task creation and verification in a single step, producing thematically
coherent task sequences with embedded validation criteria.
"""

import json
import csv
import threading
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from utils.logger import get_logger, log_processing, log_success, log_raw_response
from utils.json_utils import extract_json_from_text, parse_json_safe, save_json
from generators.base_generator import BaseGenerator


class TaskGenerator(BaseGenerator):
    """
    Unified task generator that creates thematically coherent task sequences
    with embedded verification criteria in a single generation step.
    
    This generator replaces the separate TaskGenerator and VerifyGenerator,
    producing a more cohesive and narrative-driven task structure.
    """
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        """Initialize the task generator."""
        super().__init__('task', config_override)

        # Set specific paths - use project root data directory
        self.project_root = Path(__file__).parent.parent.parent  # 项目根目录
        self.data_dir = self.project_root / 'data'
        self.scene_dir = self.data_dir / 'scene'
        self.task_dir = self.data_dir / 'task'
        self.task_dir.mkdir(parents=True, exist_ok=True)

        # Load CSV data for action details
        self.actions_csv_path = self.data_dir / 'attribute_actions.csv'
        self.actions_data = self._load_actions_csv()

        self.logger.info("TaskGenerator initialized")

    def _load_actions_csv(self) -> List[Dict[str, Any]]:
        """Load actions from CSV file."""
        actions = []

        if not self.actions_csv_path.exists():
            self.logger.warning(f"Actions CSV not found: {self.actions_csv_path}")
            return actions

        try:
            with open(self.actions_csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                actions = list(reader)
            self.logger.info(f"Loaded {len(actions)} actions from CSV")
        except Exception as e:
            self.logger.error(f"Failed to load actions CSV: {e}")

        return actions

    def generate_single(self, scene_item: Dict[str, Any], thread_id: int = 0) -> Optional[Dict[str, Any]]:
        """
        Generate a unified task sequence with embedded verification for a single scene.
        
        Args:
            scene_item: Scene data containing 'id', 'filename', and 'scene_data'
            thread_id: Thread identifier for logging
            
        Returns:
            Dict containing generation results or None if failed
        """
        scene_id = scene_item.get('id', 'unknown')
        scene_data = scene_item.get('scene_data', {})
        
        self.logger.info(f"[Thread {thread_id}] Starting unified task generation for scene {scene_id}")
        
        try:
            # Step 1: Extract abilities from scene data
            self.logger.info(f"[Thread {thread_id}] Step 1: Extracting abilities from scene...")
            available_abilities = scene_data.get('abilities', [])
            self.logger.info(f"[Thread {thread_id}] Step 1 complete: Found {len(available_abilities)} available abilities")

            # Step 2: Prepare messages for LLM
            self.logger.info(f"[Thread {thread_id}] Step 2: Preparing LLM messages...")
            messages = self.prepare_messages(scene_data, available_abilities)
            self.logger.info(f"[Thread {thread_id}] Step 2 complete: Messages prepared")
            
            # Step 3: Call LLM
            self.logger.info(f"[Thread {thread_id}] Step 3: Calling LLM for task generation...")
            response_text, usage = self.call_llm(messages, thread_id)

            # Log raw response
            log_raw_response('task', scene_id, thread_id, response_text)

            # Step 4: Extract and parse JSON
            self.logger.info(f"[Thread {thread_id}] Step 4: Extracting JSON from response...")
            json_str = extract_json_from_text(response_text)

            if not json_str:
                self.logger.warning(f"[Thread {thread_id}] Failed to extract JSON for scene {scene_id}")
                return None

            # Parse JSON
            task_data, parse_error = parse_json_safe(json_str)

            if task_data is None:
                self.logger.error(f"[Thread {thread_id}] Failed to parse JSON for scene {scene_id}: {parse_error}")
                return None

            # Step 5: Add metadata
            self.logger.info(f"[Thread {thread_id}] Step 5: Adding metadata...")
            # Add metadata (abilities now stored in scene, not task)
            task_data['scene_id'] = scene_id

            # Note: Task validation is disabled
            # To enable validation, uncomment the following lines:
            # is_valid, errors, fixed_task_data, fixes_applied = self.task_validator.validate_and_fix_task_data(
            #     task_data, scene_data, auto_fix=True
            # )
            # if fixes_applied:
            #     self.logger.info(f"[Thread {thread_id}] Applied {len(fixes_applied)} automatic fixes:")
            #     for fix in fixes_applied:
            #         self.logger.info(f"[Thread {thread_id}]   - {fix}")
            #     task_data = fixed_task_data
            # if not is_valid:
            #     self.logger.error(f"[Thread {thread_id}] Validation failed for scene {scene_id} with {len(errors)} errors:")
            #     for error in errors:
            #         self.logger.error(f"[Thread {thread_id}]   - {error}")
            #     return None

            # Step 6: Save task file
            task_filename = f"{str(scene_id).zfill(5)}_task.json"
            task_path = self.task_dir / task_filename
            save_json(task_data, str(task_path))

            self.logger.info(f"[Thread {thread_id}] Task saved for scene {scene_id}: {task_path}")
            self.logger.info(f"[Thread {thread_id}]   - Scene ID: {scene_id}")
            self.logger.info(f"[Thread {thread_id}]   - Task Background: {task_data.get('task_background', 'N/A')}")
            self.logger.info(f"[Thread {thread_id}]   - Number of tasks: {len(task_data.get('tasks', []))}")

            return {
                'scene_id': scene_id,
                'task_file': task_filename,
                'task_data': task_data,
                'token_usage': usage.get('total_tokens', 0) if isinstance(usage, dict) else usage
            }
            
        except Exception as e:
            self.logger.error(f"[Thread {thread_id}] Failed to generate unified tasks for scene {scene_id}: {e}")
            return None
            
    def prepare_messages(self, scene_data: Dict[str, Any], available_abilities: List[str]) -> List[Dict[str, str]]:
        """
        Prepare messages for LLM call.

        Args:
            scene_data: Scene data dictionary
            available_abilities: List of available ability names

        Returns:
            List of message dictionaries for LLM
        """
        system_prompt = self.config['system_prompt']
        user_prompt = self.config['user_prompt']

        # Format abilities with detailed information from CSV
        if available_abilities:
            formatted_abilities = self._format_abilities_with_details(available_abilities)
        else:
            formatted_abilities = "No specific abilities available in this scene."

        # Format the prompts with scene data and abilities
        formatted_user_prompt = user_prompt.format(
            scene_json=json.dumps(scene_data, indent=2, ensure_ascii=False),
            action_schema=formatted_abilities
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": formatted_user_prompt}
        ]

    def _format_abilities_with_details(self, available_abilities: List[str]) -> str:
        """
        Format abilities with detailed information from CSV.

        Args:
            available_abilities: List of available ability names

        Returns:
            Formatted string with ability details
        """
        if not self.actions_data:
            # Fallback to simple list if CSV data not available
            return '\n'.join([f"- {ability}" for ability in available_abilities])

        formatted_lines = []

        for ability in available_abilities:
            # Find matching action in CSV data
            action_info = None
            for action in self.actions_data:
                if action.get('action_name', '').strip() == ability:
                    action_info = action
                    break

            if action_info:
                # Format with detailed information
                attribute = action_info.get('attribute', '').strip()
                value = action_info.get('value', '').strip()
                requires_tool = action_info.get('requires_tool', '').strip().lower() == 'true'
                description = action_info.get('description', '').strip().strip('"')

                # Build formatted line
                line = f"- {ability}: {attribute}={value}"
                if requires_tool:
                    line += ", requires_tool=true"
                else:
                    line += ", requires_tool=false"
                if description:
                    line += f", {description}"

                formatted_lines.append(line)
            else:
                # Fallback for abilities not found in CSV
                formatted_lines.append(f"- {ability}: (details not available)")

        return '\n'.join(formatted_lines)

    def validate_task_data(self, task_data: Dict[str, Any], scene_data: Dict[str, Any]) -> bool:
        """
        Validate the generated task data.

        Args:
            task_data: Generated task data
            scene_data: Original scene data

        Returns:
            True if validation passes, False otherwise
        """
        try:
            # Check required top-level fields
            required_fields = ['scene_id', 'task_background', 'agents_config', 'tasks']
            for field in required_fields:
                if field not in task_data:
                    self.logger.error(f"Missing required field: {field}")
                    return False

            # Validate task_background
            if not isinstance(task_data['task_background'], str) or not task_data['task_background'].strip():
                self.logger.error("task_background must be a non-empty string")
                return False

            # Validate agents_config
            agents_config = task_data['agents_config']
            if not isinstance(agents_config, list) or len(agents_config) != 2:
                self.logger.error("agents_config must be a list with exactly 2 agents")
                return False

            for i, agent in enumerate(agents_config):
                if not isinstance(agent, dict):
                    self.logger.error(f"Agent {i} must be a dictionary")
                    return False

                required_agent_fields = ['name', 'max_grasp_limit', 'max_weight', 'max_size']
                for field in required_agent_fields:
                    if field not in agent:
                        self.logger.error(f"Agent {i} missing required field: {field}")
                        return False

            # Validate tasks
            tasks = task_data['tasks']
            if not isinstance(tasks, list) or len(tasks) == 0:
                self.logger.error("tasks must be a non-empty list")
                return False

            for i, task in enumerate(tasks):
                if not isinstance(task, dict):
                    self.logger.error(f"Task {i} must be a dictionary")
                    return False

                required_task_fields = ['task_description', 'task_category', 'validation_checks']
                for field in required_task_fields:
                    if field not in task:
                        self.logger.error(f"Task {i} missing required field: {field}")
                        return False

                # Validate validation_checks
                validation_checks = task['validation_checks']
                if not isinstance(validation_checks, list) or len(validation_checks) == 0:
                    self.logger.error(f"Task {i} validation_checks must be a non-empty list")
                    return False

                for j, check in enumerate(validation_checks):
                    if not isinstance(check, dict) or 'id' not in check:
                        self.logger.error(f"Task {i} validation_check {j} must be a dict with 'id' field")
                        return False

            self.logger.info("Task data validation passed")
            return True

        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return False


    def validate_result(self, result: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a generated unified task result.

        Args:
            result: Unified task result to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check required fields
        required_fields = ['scene_id', 'task_file', 'unified_task_data']
        for field in required_fields:
            if field not in result:
                errors.append(f"Missing required field: {field}")

        # Check unified task data structure
        if 'unified_task_data' in result:
            unified_task_data = result['unified_task_data']

            # Check required top-level fields
            required_top_fields = ['scene_id', 'task_background', 'agents_config', 'tasks']
            for field in required_top_fields:
                if field not in unified_task_data:
                    errors.append(f"unified_task_data missing required field: {field}")

            # Validate agents_config
            if 'agents_config' in unified_task_data:
                agents_config = unified_task_data['agents_config']
                if not isinstance(agents_config, list) or len(agents_config) != 2:
                    errors.append("agents_config must be a list with exactly 2 agents")

            # Validate tasks
            if 'tasks' in unified_task_data:
                tasks = unified_task_data['tasks']
                if not isinstance(tasks, list) or len(tasks) != 6:
                    errors.append("tasks must be a list with exactly 6 tasks")

        return len(errors) == 0, errors

    def load_scenes(self) -> List[Dict[str, Any]]:
        """
        Load all scene files for batch processing.

        Returns:
            List of scene items with id, filename, and scene_data
        """
        scene_dir = self.scene_dir
        scenes = []

        if not scene_dir.exists():
            self.logger.warning(f"Scene directory not found: {scene_dir}")
            return scenes

        for scene_file in sorted(scene_dir.glob("*_scene.json")):
            try:
                with open(scene_file, 'r', encoding='utf-8') as f:
                    scene_data = json.load(f)

                # Extract scene ID from filename
                scene_id = scene_file.stem.replace('_scene', '')

                scenes.append({
                    'id': scene_id,
                    'filename': scene_file.name,
                    'scene_data': scene_data.get('scene_data', scene_data)
                })

            except Exception as e:
                self.logger.error(f"Failed to load scene file {scene_file}: {e}")
                continue

        self.logger.info(f"Loaded {len(scenes)} scene files")
        return scenes

    def run_batch_generation(self, start_id: Optional[int] = None,
                           end_id: Optional[int] = None,
                           num_threads: Optional[int] = None,
                           scene_ids: Optional[List[str]] = None):
        """
        Run batch generation for tasks.

        Args:
            start_id: Starting ID (inclusive)
            end_id: Ending ID (inclusive)
            num_threads: Number of threads
            scene_ids: Specific scene IDs to process
        """
        # Load scenes
        all_scenes = self.load_scenes()

        # Filter by specific scene IDs if provided
        if scene_ids:
            scenes = [s for s in all_scenes if s['id'] in scene_ids]
            self.logger.info(f"Processing {len(scenes)} specific scenes")
        else:
            scenes = all_scenes

        # Generate batch
        results = self.generate_batch(
            items=scenes,
            num_threads=num_threads,
            start_id=start_id,
            end_id=end_id
        )

        # Log summary
        successful = sum(1 for r in results if r is not None)
        total = len(results)
        self.logger.info(f"Batch generation complete: {successful}/{total} successful")

        return results
