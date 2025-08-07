"""
Base generator class for all data generators.
Provides common functionality for LLM-based data generation.
"""

import os
import json
import threading
import yaml
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import time

import openai

from utils.logger import get_logger, log_raw_response
from utils.json_utils import extract_json_from_text, parse_json_safe, save_json, load_json
from utils.thread_pool import ThreadPoolManager, TaskResult, TaskStatus


class BaseGenerator(ABC):
    """
    Abstract base class for all data generators.
    Provides common functionality for configuration, logging, and LLM interaction.
    """
    
    def __init__(self, generator_type: str, config_override: Optional[Dict[str, Any]] = None):
        """
        Initialize the generator.
        
        Args:
            generator_type: Type of generator (e.g., 'clue', 'scene', 'task')
            config_override: Optional configuration overrides
        """
        self.generator_type = generator_type
        self.logger = get_logger(f"{generator_type}_generator")
        
        # Load configuration
        self.config = self._load_config(config_override)
        
        # Initialize OpenAI client
        self.client = self._init_openai_client()
        
        # Thread safety
        self.file_lock = threading.Lock()
        self.stats_lock = threading.Lock()
        
        # Generation statistics
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'total_tokens': 0,
            'total_time': 0.0
        }
        
        # Output paths - always use project root data directory
        self.project_root = Path(__file__).parent.parent.parent  # Project root directory
        self.output_dir = self.project_root / 'data' / generator_type
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_config(self, config_override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Load and merge configuration."""
        try:
            # Load directly from configuration file
            project_root = Path(__file__).parent.parent.parent  # Project root directory
            config_path = project_root / "config" / "data_generation" / f"{self.generator_type}_gen_config.yaml"

            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}")

            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # Apply default values
            defaults = {
                'thread_num': 4,
                'temperature': 0.7,
                'max_tokens': 4096,
                'timeout': 600,
                'start_id': 0,
                'end_id': None
            }

            for key, default_value in defaults.items():
                config.setdefault(key, default_value)

        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            raise

        # Apply overrides if provided
        if config_override:
            config.update(config_override)

        return config
        
    def _init_openai_client(self) -> openai.OpenAI:
        """Initialize OpenAI client."""
        api_key = self.config.get('api_key')
        endpoint = self.config.get('endpoint')
        
        if not api_key:
            raise ValueError("API key not found in configuration")
            
        return openai.OpenAI(api_key=api_key, base_url=endpoint)
        
    @abstractmethod
    def generate_single(self, item: Dict[str, Any], thread_id: int) -> Optional[Dict[str, Any]]:
        """
        Generate data for a single item.
        Must be implemented by subclasses.
        
        Args:
            item: Input item to process
            thread_id: Thread identifier for logging
            
        Returns:
            Generated data or None if failed
        """
        pass
        
    @abstractmethod
    def validate_result(self, result: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate generated result.
        Must be implemented by subclasses.
        
        Args:
            result: Generated result to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        pass
        
    def generate_batch(self, items: List[Dict[str, Any]], 
                      num_threads: Optional[int] = None,
                      start_id: Optional[int] = None,
                      end_id: Optional[int] = None) -> List[TaskResult]:
        """
        Generate data for multiple items in parallel.
        
        Args:
            items: List of items to process
            num_threads: Number of threads (defaults to config value)
            start_id: Starting ID (inclusive)
            end_id: Ending ID (inclusive)
            
        Returns:
            List of TaskResult objects
        """
        # Filter items by ID range if specified
        if start_id is not None or end_id is not None:
            filtered_items = []
            for item in items:
                item_id = item.get('id', 0)
                if start_id is not None and item_id < start_id:
                    continue
                if end_id is not None and item_id > end_id:
                    continue
                filtered_items.append(item)
            items = filtered_items
            
        if not items:
            self.logger.warning("No items to process after filtering")
            return []
            
        # Use configured thread count if not specified
        if num_threads is None:
            num_threads = self.config.get('thread_num', 4)
            
        self.logger.info(f"Starting batch generation for {len(items)} items with {num_threads} threads")
        
        # Create thread pool manager
        pool_manager = ThreadPoolManager(
            num_threads=num_threads,
            max_retries=self.config.get('max_retries', 3),
            retry_delay=self.config.get('retry_delay', 2.0)
        )
        
        # Execute tasks
        results = pool_manager.execute_tasks(
            tasks=items,
            task_func=self._generate_wrapper,
            task_id_func=lambda item: item.get('id', 'unknown'),
            progress_callback=self._progress_callback
        )
        
        # Update statistics
        self._update_final_statistics(results)
        
        return results
        
    def _generate_wrapper(self, item: Dict[str, Any], thread_id: int) -> Dict[str, Any]:
        """Wrapper for generate_single with error handling."""
        start_time = time.time()
        
        try:
            result = self.generate_single(item, thread_id)
            
            if result is None:
                raise ValueError("Generation returned None")
                
            # Validate result
            is_valid, errors = self.validate_result(result)
            if not is_valid:
                raise ValueError(f"Validation failed: {'; '.join(errors)}")
                
            # Update statistics
            with self.stats_lock:
                self.stats['successful'] += 1
                self.stats['total_time'] += time.time() - start_time
                
            return result
            
        except Exception as e:
            with self.stats_lock:
                self.stats['failed'] += 1
                
            self.logger.error(f"Failed to generate for item {item.get('id')}: {e}")
            raise
            
    def _progress_callback(self, progress: float, result: TaskResult):
        """Progress callback for batch generation."""
        if result.status == TaskStatus.COMPLETED:
            self.logger.info(f"Progress: {progress:.1%} - Item {result.task_id} completed")
        elif result.status == TaskStatus.FAILED:
            self.logger.warning(f"Progress: {progress:.1%} - Item {result.task_id} failed")
            
    def _update_final_statistics(self, results: List[TaskResult]):
        """Update and log final statistics."""
        completed = sum(1 for r in results if r.status == TaskStatus.COMPLETED)
        failed = sum(1 for r in results if r.status == TaskStatus.FAILED)
        
        self.logger.info("="*50)
        self.logger.info(f"Generation Complete:")
        self.logger.info(f"  Total items: {len(results)}")
        self.logger.info(f"  Successful: {completed}")
        self.logger.info(f"  Failed: {failed}")
        
        if self.stats['total_tokens'] > 0:
            self.logger.info(f"  Total tokens used: {self.stats['total_tokens']:,}")
            
        self.logger.info("="*50)
        
    def call_llm(self, messages: List[Dict[str, str]], thread_id: int, 
                 temperature: Optional[float] = None,
                 max_tokens: Optional[int] = None) -> Tuple[str, Dict[str, int]]:
        """
        Call the LLM API with the given messages.
        
        Args:
            messages: List of message dictionaries
            thread_id: Thread identifier for logging
            temperature: Override temperature setting
            max_tokens: Override max tokens setting
            
        Returns:
            Tuple of (response_text, token_usage)
        """
        if temperature is None:
            temperature = self.config.get('temperature', 0.7)
        if max_tokens is None:
            max_tokens = self.config.get('max_tokens', 4096)
            
        timeout = self.config.get('timeout', 600)
        model = self.config['model']
        
        try:
            self.logger.debug(f"[Thread {thread_id}] Calling LLM API...")
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout
            )
            
            # Extract response and usage
            response_text = response.choices[0].message.content
            usage = {
                'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                'total_tokens': response.usage.total_tokens if response.usage else 0
            }
            
            # Update token statistics
            with self.stats_lock:
                self.stats['total_tokens'] += usage['total_tokens']
                
            self.logger.debug(f"[Thread {thread_id}] LLM response received, tokens: {usage['total_tokens']}")
            
            return response_text, usage
            
        except Exception as e:
            self.logger.error(f"[Thread {thread_id}] LLM API call failed: {e}")
            raise
            
    def save_result(self, result: Dict[str, Any], filename: str):
        """
        Save a result to file.
        
        Args:
            result: Result data to save
            filename: Output filename
        """
        filepath = self.output_dir / filename
        with self.file_lock:
            save_json(result, str(filepath))
            
    def load_existing_results(self) -> List[Dict[str, Any]]:
        """
        Load existing results from output directory.
        
        Returns:
            List of existing results
        """
        results = []
        
        for file_path in self.output_dir.glob("*.json"):
            try:
                result = load_json(str(file_path))
                results.append(result)
            except Exception as e:
                self.logger.warning(f"Failed to load {file_path}: {e}")
                
        return results 