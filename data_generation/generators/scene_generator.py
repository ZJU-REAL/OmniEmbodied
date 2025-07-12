"""
Scene generator implementation.
Generates scenes from clues using LLM with validation and auto-fixing.
"""

import os
import json
import random
import csv
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import threading
from datetime import datetime

from generators.base_generator import BaseGenerator
from utils.logger import log_raw_response
from utils.json_utils import extract_json_from_text, parse_json_safe, save_json, load_json
from utils.scene_validator import SceneValidator
from utils.action_manager import ActionManager


class SceneGenerator(BaseGenerator):
    """
    Generator for creating scenes from clues.
    """
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        """Initialize scene generator."""
        super().__init__('scene', config_override)

        # Set specific paths - use project data directory
        self.base_dir = Path(__file__).parent.parent  # data_generation/
        self.clue_dir = self.base_dir / 'data' / 'clue'
        self.scene_dir = self.base_dir / 'data' / 'scene'
        self.scene_dir.mkdir(parents=True, exist_ok=True)

        # Actions CSV path
        self.actions_csv_path = self.base_dir / 'data' / 'attribute_actions.csv'

        # Load validator
        self.validator = SceneValidator(str(self.actions_csv_path))

        # Initialize action manager for abilities analysis
        self.action_manager = ActionManager(str(self.actions_csv_path))

        # No longer needed - using clue_id directly

        # Actions data
        self.actions_lock = threading.Lock()
        self.actions_data = self._load_actions_csv()

        # Token statistics
        self.token_stats = {
            'total_prompt_tokens': 0,
            'total_completion_tokens': 0,
            'total_tokens': 0,
            'round1_calls': 0,
            'round2_calls': 0
        }
        
    # Removed _initialize_scene_counter and _get_next_scene_id - using clue_id directly
            
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
        
    def _get_random_actions(self, count: int = 20) -> str:
        """Get random actions formatted as string with detailed CSV information, always including open and close."""
        if not self.actions_data:
            return ""

        # Always include open and close actions with detailed information
        required_actions = ['open', 'close']
        formatted_actions = []

        # First, add required actions (open and close) with detailed CSV information
        for required_action in required_actions:
            action_info = self._find_action_in_csv(required_action)
            if action_info:
                formatted_line = self._format_action_with_details(action_info)
                formatted_actions.append(formatted_line)
            else:
                # Fallback if not found in CSV
                formatted_actions.append(f"- {required_action}: (details not available)")

        # Then, randomly select additional actions (excluding open and close)
        with self.actions_lock:
            # Filter out open and close from random selection
            available_actions = [action for action in self.actions_data
                               if action.get('action_name', '') not in required_actions]

            # Calculate how many more actions we need (subtract the 2 required actions)
            remaining_count = max(0, count - len(required_actions))
            selected_count = min(remaining_count, len(available_actions))

            if selected_count > 0:
                selected_actions = random.sample(available_actions, selected_count)

                for action in selected_actions:
                    formatted_line = self._format_action_with_details(action)
                    formatted_actions.append(formatted_line)

        return '\n'.join(formatted_actions)

    def _find_action_in_csv(self, action_name: str) -> Optional[Dict[str, Any]]:
        """Find action information in CSV data by action name."""
        for action in self.actions_data:
            if action.get('action_name', '').strip() == action_name:
                return action
        return None

    def _format_action_with_details(self, action: Dict[str, Any]) -> str:
        """Format action with detailed information from CSV."""
        action_name = action.get('action_name', '')
        attribute = action.get('attribute', '')
        value = action.get('value', '')
        requires_tool = action.get('requires_tool', '')
        description = action.get('description', '').strip('"')

        return f"- {action_name}: {attribute}={value}, requires_tool={requires_tool}, {description}"
        
    def load_clues(self) -> List[Dict[str, Any]]:
        """Load clues from individual JSON files (in reverse order)."""
        if not self.clue_dir.exists():
            raise FileNotFoundError(f"Clue directory not found: {self.clue_dir}")
            
        clues = []
        
        # Find all JSON files in the clue directory
        json_files = list(self.clue_dir.glob("*.json"))
        
        if not json_files:
            self.logger.warning(f"No clue JSON files found in: {self.clue_dir}")
            return clues
            
        # Load each clue file
        for json_file in json_files:
            try:
                # Check if this is a clue file (ends with _clue.json)
                if not json_file.stem.endswith('_clue'):
                    continue
                    
                clue_data = load_json(str(json_file))
                if clue_data:
                    clues.append(clue_data)
            except Exception as e:
                self.logger.warning(f"Failed to load clue file {json_file}: {e}")
                
        # Sort by ID and reverse for processing from last to first
        clues.sort(key=lambda x: x.get('id', 0), reverse=True)
        self.logger.info(f"Loaded {len(clues)} clues from individual files (reversed)")
        
        return clues
        
    def generate_single(self, item: Dict[str, Any], thread_id: int) -> Optional[Dict[str, Any]]:
        """
        Generate a single scene from a clue.
        
        Args:
            item: Clue item with response text
            thread_id: Thread identifier
            
        Returns:
            Generated scene data or None if failed
        """
        clue_id = item.get('id')
        clue_text = item.get('response', '')
        
        if not clue_text:
            self.logger.warning(f"[Thread {thread_id}] Clue {clue_id} has no response text, skipping")
            return None
            
        self.logger.info(f"[Thread {thread_id}] Generating scene for clue {clue_id}")
        
        # Get random abilities
        random_abilities = self._get_random_actions(20)
        
        # Prepare prompt
        user_prompt_filled = self.config['user_prompt'].replace('{clue}', clue_text)
        user_prompt_filled = user_prompt_filled.replace('{abilities}', random_abilities)
        
        # First round messages
        messages_round1 = [
            {"role": "system", "content": self.config['system_prompt']},
            {"role": "user", "content": user_prompt_filled}
        ]
        
        try:
            # First round LLM call
            self.logger.info(f"[Thread {thread_id}] [Clue {clue_id}] Round 1: Calling LLM...")
            self.logger.info(f"[Thread {thread_id}] [Clue {clue_id}] Estimated wait time: 2-5 minutes")
            
            response_text_round1, usage_round1 = self.call_llm(
                messages_round1, 
                thread_id,
                temperature=self.config.get('temperature', 0.7),
                max_tokens=self.config.get('max_tokens', 4096)
            )
            
            # Update token stats
            with self.stats_lock:
                self.token_stats['total_prompt_tokens'] += usage_round1['prompt_tokens']
                self.token_stats['total_completion_tokens'] += usage_round1['completion_tokens']
                self.token_stats['total_tokens'] += usage_round1['total_tokens']
                self.token_stats['round1_calls'] += 1
                
            # Log raw response
            log_raw_response('scene', str(clue_id), thread_id, response_text_round1)
            
            # Extract and process JSON
            json_str = extract_json_from_text(response_text_round1)
            
            if not json_str or len(json_str.strip()) < 50:
                self.logger.warning(f"[Thread {thread_id}] [Clue {clue_id}] Extracted JSON too short")
                return None
                
            # Process JSON with auto-fix
            final_scene_obj, success = self._process_json_with_auto_fix(
                json_str, response_text_round1, user_prompt_filled,
                clue_id, thread_id
            )
            
            if success and final_scene_obj:
                # Step 3: Analyze scene abilities and add to scene data
                self.logger.info(f"[Thread {thread_id}] [Clue {clue_id}] Step 3: Analyzing scene abilities...")
                available_abilities, abilities_details = self.action_manager.analyze_scene_abilities(final_scene_obj, thread_id)
                self.logger.info(f"[Thread {thread_id}] [Clue {clue_id}] Step 3 complete: Found {len(available_abilities)} available abilities")

                # Ensure open and close are always included in abilities
                required_abilities = ['open', 'close']
                for required_ability in required_abilities:
                    if required_ability not in available_abilities:
                        available_abilities.append(required_ability)
                        self.logger.info(f"[Thread {thread_id}] [Clue {clue_id}] Added required ability: {required_ability}")

                # Add abilities to scene data
                final_scene_obj['abilities'] = available_abilities

                # Save as JSON using clue_id in unified format
                scene_filename = f"{int(clue_id or 0):05d}_scene.json"
                scene_path = self.scene_dir / scene_filename
                save_json(final_scene_obj, str(scene_path))
                self.logger.info(f"[Thread {thread_id}] [Clue {clue_id}] Scene saved with {len(available_abilities)} abilities: {scene_path}")

                return {
                    'scene_id': f"{str(clue_id).zfill(5)}",
                    'clue_id': clue_id,
                    'scene_data': final_scene_obj,
                    'token_usage': usage_round1.get('total_tokens', 0) if isinstance(usage_round1, dict) else usage_round1
                }
            else:
                # Save as TXT if failed
                self._save_failed_generation(f"{str(clue_id).zfill(5)}", item, response_text_round1, json_str, thread_id)
                return None
                
        except Exception as e:
            self.logger.error(f"[Thread {thread_id}] [Clue {clue_id}] Failed to generate scene: {e}")
            return None

    def _process_json_with_auto_fix(self, json_str: str, response_text_round1: str,
                                   user_prompt_filled: str, clue_id: Any, 
                                   thread_id: int) -> Tuple[Optional[Dict[str, Any]], bool]:
        """Process JSON with automatic fixing and multi-round correction."""
        # Try to parse JSON
        scene_obj, parse_error = parse_json_safe(json_str)
        
        # If parsing successful, validate and auto-fix
        if scene_obj is not None:
            if not scene_obj:  # Empty JSON
                self.logger.warning(f"[Thread {thread_id}] [Clue {clue_id}] Empty JSON detected")
                return self._handle_multi_round_correction(
                    json_str, scene_obj, "Empty JSON object", response_text_round1,
                    user_prompt_filled, clue_id, thread_id
                )
                
            # Validate and auto-fix
            is_valid, validation_errors, fixed_scene_obj, fixes_applied = \
                self.validator.validate_and_fix_json_data(scene_obj, auto_fix=True)
                
            if fixes_applied:
                self.logger.info(f"[Thread {thread_id}] [Clue {clue_id}] Applied {len(fixes_applied)} auto-fixes")
                
            if is_valid:
                return fixed_scene_obj, True
            else:
                self.logger.warning(f"[Thread {thread_id}] [Clue {clue_id}] {len(validation_errors)} errors remain after auto-fix")
                scene_obj = fixed_scene_obj
                
        # Multi-round correction if needed
        return self._handle_multi_round_correction(
            json_str, scene_obj, parse_error, response_text_round1,
            user_prompt_filled, clue_id, thread_id
        )
        
    def _handle_multi_round_correction(self, json_str: str, scene_obj: Optional[Dict[str, Any]],
                                     parse_error: Optional[str], response_text_round1: str,
                                     user_prompt_filled: str, clue_id: Any,
                                     thread_id: int) -> Tuple[Optional[Dict[str, Any]], bool]:
        """Handle multi-round correction for failed JSON generation."""
        # Generate error report
        if scene_obj:
            validation_errors = self.validator.validate_scene_json_detailed(scene_obj)
        else:
            validation_errors = []
            
        if not parse_error and not validation_errors:
            return scene_obj, True
            
        self.logger.info(f"[Thread {thread_id}] [Clue {clue_id}] Starting round 2 correction...")
        
        # Generate error report
        try:
            error_report = self.validator.generate_error_report(json_str, parse_error, validation_errors)
        except Exception as e:
            self.logger.error(f"[Thread {thread_id}] [Clue {clue_id}] Failed to generate error report: {e}")
            return None, False
            
        # Prepare debug correction prompt
        debug_prompt = self.config.get('debug_correction_prompt', '').format(error_report=error_report)
        
        # Second round messages
        messages_round2 = [
            {"role": "system", "content": self.config['system_prompt']},
            {"role": "user", "content": user_prompt_filled},
            {"role": "assistant", "content": json_str},
            {"role": "user", "content": debug_prompt}
        ]
        
        try:
            # Second round LLM call
            self.logger.info(f"[Thread {thread_id}] [Clue {clue_id}] Round 2: Calling LLM for correction...")
            response_text_round2, usage_round2 = self.call_llm(messages_round2, thread_id)
            
            # Update token stats
            with self.stats_lock:
                self.token_stats['total_prompt_tokens'] += usage_round2['prompt_tokens']
                self.token_stats['total_completion_tokens'] += usage_round2['completion_tokens']
                self.token_stats['total_tokens'] += usage_round2['total_tokens']
                self.token_stats['round2_calls'] += 1
                
            # Extract fixed JSON
            json_str_fixed = extract_json_from_text(response_text_round2)
            
            if not json_str_fixed or len(json_str_fixed.strip()) < 50:
                self.logger.warning(f"[Thread {thread_id}] [Clue {clue_id}] Round 2 extracted JSON too short")
                return None, False
                
            # Parse fixed JSON
            scene_obj_round2, parse_error2 = parse_json_safe(json_str_fixed)
            
            if scene_obj_round2 is None:
                self.logger.error(f"[Thread {thread_id}] [Clue {clue_id}] Round 2 JSON parsing failed: {parse_error2}")
                return None, False
                
            # Validate and auto-fix again
            is_valid_final, final_errors, final_scene_obj, fixes_applied = \
                self.validator.validate_and_fix_json_data(scene_obj_round2, auto_fix=True)
                
            if is_valid_final:
                self.logger.info(f"[Thread {thread_id}] [Clue {clue_id}] Round 2 correction successful")
                return final_scene_obj, True
            else:
                self.logger.error(f"[Thread {thread_id}] [Clue {clue_id}] Round 2 still has {len(final_errors)} errors")
                return None, False
                
        except Exception as e:
            self.logger.error(f"[Thread {thread_id}] [Clue {clue_id}] Round 2 correction failed: {e}")
            return None, False
            
    def _save_failed_generation(self, scene_id: str, clue_item: Dict[str, Any],
                              response_text: str, json_str: str, thread_id: int):
        """Save failed generation as TXT file."""
        txt_path = self.scene_dir / f"{scene_id}_scene_failed.txt"
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"# Scene Generation Failed\n")
            f.write(f"# Clue ID: {clue_item.get('id')}\n")
            f.write(f"# Generated at: {datetime.now()}\n")
            f.write(f"# Scene ID: {scene_id}\n\n")
            f.write("# First Round Response:\n")
            f.write(response_text)
            f.write("\n\n# Extracted JSON:\n")
            f.write(json_str)
            f.write("\n\n# Note: Failed after auto-fix and multi-round correction attempts")
            
        self.logger.info(f"[Thread {thread_id}] Failed scene saved as TXT: {txt_path}")
        
    def validate_result(self, result: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate a generated scene result."""
        errors = []
        
        required_fields = ['scene_id', 'clue_id', 'scene_data']
        for field in required_fields:
            if field not in result:
                errors.append(f"Missing required field: {field}")
                
        if 'scene_data' in result:
            scene_errors = self.validator.validate_scene_json_detailed(result['scene_data'])
            errors.extend(scene_errors)
            
        return len(errors) == 0, errors
        
    def run_batch_generation(self, start_id: Optional[int] = None,
                           end_id: Optional[int] = None,
                           num_threads: Optional[int] = None):
        """Run batch generation for scenes."""
        # Load clues
        clues = self.load_clues()
        self.logger.info(f"Loaded {len(clues)} clues for scene generation")
        
        # Generate batch
        results = self.generate_batch(
            items=clues,
            num_threads=num_threads,
            start_id=start_id,
            end_id=end_id
        )
        
        # Log token statistics
        self._log_token_statistics()
        
        return results
        
    def _log_token_statistics(self):
        """Log token usage statistics."""
        with self.stats_lock:
            stats = self.token_stats.copy()
            
        self.logger.info("="*50)
        self.logger.info("Token Usage Statistics:")
        self.logger.info(f"  Round 1 calls: {stats['round1_calls']}")
        self.logger.info(f"  Round 2 calls: {stats['round2_calls']}")
        self.logger.info(f"  Total prompt tokens: {stats['total_prompt_tokens']:,}")
        self.logger.info(f"  Total completion tokens: {stats['total_completion_tokens']:,}")
        self.logger.info(f"  Total tokens: {stats['total_tokens']:,}")
        self.logger.info("="*50)


# Standalone execution
if __name__ == "__main__":
    from utils.logger import setup_logging
    
    # Setup logging
    setup_logging()
    
    # Create generator and run
    generator = SceneGenerator()
    generator.run_batch_generation()
