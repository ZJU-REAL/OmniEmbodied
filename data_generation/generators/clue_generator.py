"""
Clue generator implementation.
Generates clues from raw text using LLM.
"""

import os
import json
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import threading

from generators.base_generator import BaseGenerator
from utils.logger import log_raw_response
from utils.json_utils import save_json, load_json


class ClueGenerator(BaseGenerator):
    """
    Generator for creating clues from raw text.
    """
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        """Initialize clue generator."""
        super().__init__('clue', config_override)
        
        # Set specific paths - use project root data directory
        self.project_root = Path(__file__).parent.parent.parent  # Project root directory
        self.data_dir = self.project_root / 'data'
        self.output_dir = self.data_dir / 'clue'
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # File paths
        self.raw_clue_path = self.data_dir / 'news.json'
        
        # Thread-safe access to file operations
        self.file_lock = threading.Lock()
        
    def load_raw_clues(self) -> List[Dict[str, Any]]:
        """
        Load raw clues from file.
        
        Returns:
            List of raw clue items
        """
        if not self.raw_clue_path.exists():
            raise FileNotFoundError(f"Raw clue file not found: {self.raw_clue_path}")
            
        data = load_json(str(self.raw_clue_path))
        
        # Ensure we return a list
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'data' in data:
            return data['data']
        else:
            raise ValueError(f"Invalid raw clue file format: expected list or dict with 'data' key")
        
    def generate_single(self, item: Dict[str, Any], thread_id: int) -> Optional[Dict[str, Any]]:
        """
        Generate a single clue from raw text.
        
        Args:
            item: Raw clue item with 'id' and 'raw_text'
            thread_id: Thread identifier
            
        Returns:
            Generated clue data or None if failed
        """
        clue_id = item.get('id')
        raw_text = item.get('raw_text', '')
        
        if not raw_text:
            self.logger.warning(f"[Thread {thread_id}] Item {clue_id} has no raw_text, skipping")
            return None
            
        self.logger.info(f"[Thread {thread_id}] Generating clue for item {clue_id}")
        
        # Prepare prompt
        user_prompt_filled = self.config['user_prompt'].replace('{raw_text}', raw_text)
        
        messages = [
            {"role": "system", "content": self.config['system_prompt']},
            {"role": "user", "content": user_prompt_filled}
        ]
        
        try:
            # Call LLM with temperature from config
            response_text, usage = self.call_llm(
                messages, 
                thread_id,
                temperature=self.config.get('temperature', 0.7)
            )
            
            # Log raw response
            log_raw_response('clue', str(clue_id), thread_id, response_text)
            
            # Create result with token_usage
            result = {
                "id": clue_id,
                "raw": raw_text,
                "response": response_text,
                "token_usage": usage
            }
            
            # Save to individual file
            self._save_individual_clue(result)
            
            self.logger.info(f"[Thread {thread_id}] Successfully generated clue for item {clue_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"[Thread {thread_id}] Failed to generate clue for item {clue_id}: {e}")
            return None
            
    def _save_individual_clue(self, clue_record: Dict[str, Any]):
        """
        Save a clue record to individual JSON file in thread-safe manner.
        Excludes token_usage from the saved file.
        
        Args:
            clue_record: Clue record to save
        """
        clue_id = clue_record.get('id')
        if clue_id is None:
            self.logger.error("Cannot save clue without ID")
            return
            
        # Create a copy without token_usage for saving
        save_record = {
            "id": clue_record.get("id"),
            "raw": clue_record.get("raw"),
            "response": clue_record.get("response")
        }
            
        # Create filename with ID in unified format
        filename = f"{str(clue_id).zfill(5)}_clue.json"
        file_path = self.output_dir / filename
        
        with self.file_lock:
            try:
                save_json(save_record, str(file_path))
                self.logger.debug(f"Saved clue {clue_id} to {file_path}")
            except Exception as e:
                self.logger.error(f"Failed to save clue {clue_id}: {e}")
            
    def validate_result(self, result: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a generated clue result.
        
        Args:
            result: Clue result to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        required_fields = ['id', 'raw', 'response']
        for field in required_fields:
            if field not in result:
                errors.append(f"Missing required field: {field}")
                
        # Check response is not empty
        if 'response' in result and not result['response'].strip():
            errors.append("Response is empty")
            
        return len(errors) == 0, errors
        
    def run_batch_generation(self, start_id: Optional[int] = None, 
                           end_id: Optional[int] = None,
                           num_threads: Optional[int] = None):
        """
        Run batch generation for clues.
        
        Args:
            start_id: Starting ID (inclusive)
            end_id: Ending ID (inclusive)
            num_threads: Number of threads
        """
        # Load raw clues
        raw_clues = self.load_raw_clues()
        self.logger.info(f"Loaded {len(raw_clues)} raw clues from {self.raw_clue_path}")
        
        # Use config values if not specified
        if start_id is None:
            start_id = self.config.get('start_id', 0)
        if end_id is None:
            end_id = self.config.get('end_id')
            
        # Generate batch
        results = self.generate_batch(
            items=raw_clues,
            num_threads=num_threads,
            start_id=start_id,
            end_id=end_id
        )
        
        self.logger.info(f"Batch generation complete. All clues saved to individual files in: {self.output_dir}")
        
        return results


# Standalone execution
if __name__ == "__main__":
    from utils.logger import setup_logging
    
    # Setup logging
    setup_logging()
    
    # Create generator and run
    generator = ClueGenerator()
    generator.run_batch_generation()
