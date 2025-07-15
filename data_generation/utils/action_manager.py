"""
Action manager for analyzing scene abilities based on action definitions.
"""

import os
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

from utils.logger import get_logger


class ActionManager:
    """
    Manages action definitions and analyzes scene abilities.
    """
    
    def __init__(self, csv_path: Optional[str] = None):
        """
        Initialize action manager.
        
        Args:
            csv_path: Path to attribute_actions.csv file
        """
        self.logger = get_logger("ActionManager")
        
        # Default CSV path - use project root data directory
        if csv_path is None:
            project_root = Path(__file__).parent.parent.parent  # 项目根目录
            csv_path = project_root / 'data' / 'attribute_actions.csv'
            
        self.csv_path = csv_path
        self.actions_df = None
        self._load_actions_csv()
        
    def _load_actions_csv(self) -> bool:
        """
        Load actions from CSV file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.actions_df = pd.read_csv(self.csv_path)
            self.logger.info(f"Loaded {len(self.actions_df)} action definitions from {self.csv_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load CSV file: {e}")
            return False
            
    def analyze_scene_abilities(self, scene_json: Dict[str, Any], thread_id: Optional[int] = None) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Analyze what abilities are available in a scene based on object states and provided abilities.
        
        Args:
            scene_json: Scene data in JSON format
            thread_id: Thread identifier for logging
            
        Returns:
            Tuple of (available_abilities, abilities_details)
        """
        prefix = f"[Thread {thread_id}] " if thread_id is not None else ""
        
        self.logger.debug(f"{prefix}Starting scene ability analysis...")
        available_abilities = []
        abilities_details = []
        
        if self.actions_df is None:
            self.logger.warning(f"{prefix}CSV data not loaded, cannot analyze abilities")
            return [], []
            
        # Step 1: Collect all object states and provided abilities
        scene_states = {}  # {state_key: [(object_id, state_value), ...]}
        provides_abilities = {}  # {ability_name: [object_ids]}
        total_objects = 0
        
        # Handle both list and dict formats for objects
        objects = scene_json.get('objects', [])
        if isinstance(objects, list):
            total_objects = len(objects)
            for obj_data in objects:
                obj_id = obj_data.get('id', '')
                # Collect object states
                states = obj_data.get('states', {})
                for state_key, state_value in states.items():
                    if state_key not in scene_states:
                        scene_states[state_key] = []
                    scene_states[state_key].append((obj_id, state_value))
                
                # Collect provided abilities
                properties = obj_data.get('properties', {})
                if 'provides_abilities' in properties:
                    for ability in properties['provides_abilities']:
                        if ability not in provides_abilities:
                            provides_abilities[ability] = []
                        provides_abilities[ability].append(obj_id)
        elif isinstance(objects, dict):
            total_objects = len(objects)
            for obj_id, obj_data in objects.items():
                # Collect object states
                states = obj_data.get('states', {})
                for state_key, state_value in states.items():
                    if state_key not in scene_states:
                        scene_states[state_key] = []
                    scene_states[state_key].append((obj_id, state_value))
                
                # Collect provided abilities
                properties = obj_data.get('properties', {})
                if 'provides_abilities' in properties:
                    for ability in properties['provides_abilities']:
                        if ability not in provides_abilities:
                            provides_abilities[ability] = []
                        provides_abilities[ability].append(obj_id)
                        
        self.logger.debug(f"{prefix}Scene stats: {total_objects} objects, {len(scene_states)} states, {len(provides_abilities)} provided abilities")
        
        # Step 2: Check each action in CSV against scene
        self.logger.debug(f"{prefix}Checking {len(self.actions_df)} actions against scene...")

        for _, action_row in self.actions_df.iterrows():
            action_name = action_row['action_name']
            attribute = action_row['attribute']
            value = action_row['value']
            requires_tool = action_row['requires_tool']
            description = action_row['description']

            # Check if scene has objects with required state
            state_available = False
            target_objects = []

            if attribute in scene_states:
                for obj_id, obj_state_value in scene_states[attribute]:
                    # Convert CSV value to appropriate type for comparison
                    csv_value = value
                    if isinstance(obj_state_value, bool):
                        csv_value = str(value).lower() == 'true'
                    elif isinstance(obj_state_value, (int, float)):
                        try:
                            csv_value = float(value)
                        except:
                            csv_value = value

                    if obj_state_value == csv_value:
                        state_available = True
                        target_objects.append(obj_id)

            # Check if this action is provided by scene objects (regardless of state availability)
            action_provided_by_scene = action_name in provides_abilities

            # Include action if either:
            # 1. Required state is available in scene, OR
            # 2. Action is explicitly provided by scene objects through provides_abilities
            if not state_available and not action_provided_by_scene:
                continue

            # Handle based on whether tool is required
            if pd.isna(requires_tool) or not requires_tool:
                # Case 1: Action doesn't require tools
                available_abilities.append(action_name)
                abilities_details.append({
                    'action_name': action_name,
                    'attribute': attribute,
                    'value': value,
                    'requires_tool': False,
                    'description': description,
                    'target_objects': target_objects,
                    'tool_objects': []
                })
                self.logger.debug(f"{prefix}Added no-tool ability: {action_name} (targets: {target_objects})")
            else:
                # Case 2: Action requires tools, check if ability is provided
                if action_name in provides_abilities:
                    available_abilities.append(action_name)
                    tool_objects = provides_abilities[action_name]
                    abilities_details.append({
                        'action_name': action_name,
                        'attribute': attribute,
                        'value': value,
                        'requires_tool': True,
                        'description': description,
                        'target_objects': target_objects,
                        'tool_objects': tool_objects
                    })
                    self.logger.debug(f"{prefix}Added tool ability: {action_name} (targets: {target_objects}, tools: {tool_objects})")
                    
        self.logger.info(f"{prefix}Scene ability analysis complete: {len(available_abilities)} abilities found")
        return available_abilities, abilities_details
        
    def format_abilities_for_prompt(self, abilities_details: List[Dict[str, Any]]) -> str:
        """
        Format ability details into a string suitable for prompt insertion.
        
        Args:
            abilities_details: List of ability details
            
        Returns:
            Formatted string
        """
        if not abilities_details:
            return "No specific abilities available in this scene."
            
        formatted_lines = []
        for ability in abilities_details:
            line = f"- {ability['action_name']}: {ability['description']}"
            if ability['requires_tool']:
                line += f" (requires tool: {', '.join(ability['tool_objects'])})"
            line += f" [targets: {', '.join(ability['target_objects'])}]"
            formatted_lines.append(line)
            
        return "\n".join(formatted_lines)


# Singleton instance
_action_manager = None


def get_action_manager(csv_path: Optional[str] = None) -> ActionManager:
    """
    Get singleton action manager instance.
    
    Args:
        csv_path: Path to CSV file (only used on first call)
        
    Returns:
        ActionManager instance
    """
    global _action_manager
    if _action_manager is None:
        _action_manager = ActionManager(csv_path)
    return _action_manager 