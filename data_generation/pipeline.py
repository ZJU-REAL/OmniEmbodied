#!/usr/bin/env python3
"""
End-to-end pipeline for data generation.

This module provides a comprehensive data generation pipeline that processes items
completely from raw text through clue generation, scene generation, and task
generation (combining task and verification) in a single, thread-safe execution.
Each item is processed end-to-end in one thread to ensure consistency and optimal
resource utilization.

Features:
- End-to-end processing of items (clue -> scene -> task)
- Thread-safe concurrent processing with progress tracking
- Resume capability to skip already completed items
- Comprehensive token usage tracking and performance metrics
- Robust error handling with detailed logging
- Task generation with embedded verification criteria
"""

import argparse
import json
import time
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from utils.logger import setup_logging, get_logger, log_success, log_processing, log_completed
from utils.json_utils import load_json, save_json
from generators.clue_generator import ClueGenerator
from generators.scene_generator import SceneGenerator
from generators.task_generator import TaskGenerator
from utils.task_validator import TaskValidator


class Pipeline:
    """
    End-to-end data generation pipeline.
    
    This class orchestrates the complete data generation process, handling items
    from raw text input through clue generation, scene generation, and task
    generation (combining task and verification). Each item is processed completely
    within a single thread to maintain consistency and enable efficient progress tracking.

    Key features:
    - Thread-safe concurrent processing with customizable thread count
    - Automatic resume capability (skips already completed items)
    - Real-time progress tracking with detailed statistics
    - Comprehensive token usage monitoring per generation stage
    - Robust error handling with retry mechanisms
    - Performance metrics and execution summaries
    - Unified task generation with embedded verification criteria
    """
    
    def __init__(self):
        """Initialize the pipeline."""
        self.logger = get_logger("pipeline")
        self.config = self._load_pipeline_config()

        # Output directories - save to project root data/ directory
        self.project_root = Path(__file__).parent.parent  # Go up to project root
        self.data_dir = self.project_root / 'data'
        self.clue_dir = self.data_dir / 'clue'
        self.scene_dir = self.data_dir / 'scene'
        self.task_dir = self.data_dir / 'task'

        # Initialize task validator
        self.task_validator = TaskValidator()

        # Progress tracking
        self.progress_lock = threading.Lock()
        self.progress = {
            'total': 0,
            'completed': 0,
            'failed': 0,
            'skipped': 0,
            'current_items': {},  # thread_id -> current_item_info
            'token_usage': {
                'clue_generation': 0,
                'scene_generation': 0,
                'task_generation': 0,
                'total': 0
            }
        }

    def _load_pipeline_config(self) -> Dict[str, Any]:
        """Load pipeline configuration."""
        try:
            # 直接从配置文件加载
            project_root = Path(__file__).parent.parent  # 项目根目录
            config_path = project_root / "config" / "data_generation" / "pipeline.yaml"

            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}")

            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 应用默认值（只保留实际使用的配置项）
            defaults = {
                'thread_num': 4,
                'start_id': 0,
                'end_id': None,
                'continue_generation': True
            }

            for key, default_value in defaults.items():
                config.setdefault(key, default_value)

            return config

        except Exception as e:
            self.logger.error(f"Failed to load pipeline config: {e}")
            raise
        
    def check_item_completion(self, item_id: int) -> Dict[str, bool]:
        """
        Check if all stages are completed for an item.
        
        Args:
            item_id: Item ID to check
            
        Returns:
            Dict with completion status for each stage
        """
        status = {
            'clue': False,
            'scene': False,
            'task': False
        }

        # Check clue file
        clue_file = self.clue_dir / f"{item_id:05d}_clue.json"
        status['clue'] = clue_file.exists()

        # Check scene file
        scene_file = self.scene_dir / f"{item_id:05d}_scene.json"
        status['scene'] = scene_file.exists()

        # Check task file
        task_file = self.task_dir / f"{item_id:05d}_task.json"
        status['task'] = task_file.exists()
        
        return status
        
    def should_skip_item(self, item_id: int) -> bool:
        """
        Check if item should be skipped (all stages completed).
        
        Args:
            item_id: Item ID to check
            
        Returns:
            True if item should be skipped
        """
        if not self.config.get('continue_generation', True):
            return False
            
        status = self.check_item_completion(item_id)
        return all(status.values())
        
    def process_single_item(self, item: Dict[str, Any], thread_id: int) -> Tuple[bool, Dict[str, Any]]:
        """
        Process a single item through all stages: clue -> scene -> task -> verify.
        
        Args:
            item: Raw data item with 'id' and 'raw_text'
            thread_id: Thread identifier
            
        Returns:
            Tuple of (success, results)
        """
        item_id = item.get('id')
        results = {
            'item_id': item_id,
            'thread_id': thread_id,
            'clue': None,
            'scene': None,
            'task': None,
            'errors': [],
            'skipped': False
        }
        
        # Check if item should be skipped (already completed)
        if item_id and self.should_skip_item(int(item_id)):
            self.logger.info(f"[T{thread_id}] Item {item_id}: Already completed, skipping")
            results['skipped'] = True
            with self.progress_lock:
                self.progress['skipped'] += 1
            return True, results
        
        # Update progress
        with self.progress_lock:
            self.progress['current_items'][thread_id] = f"Item {item_id}: Starting"
        
        try:
            # Stage 1: Generate Clue
            log_processing(self.logger, f"[T{thread_id}] Item {item_id}: Generating clue...")
            with self.progress_lock:
                self.progress['current_items'][thread_id] = f"Item {item_id}: Generating clue"
                
            clue_gen = ClueGenerator()
            clue_result = clue_gen.generate_single(item, thread_id)
            
            if not clue_result:
                raise Exception("Clue generation failed")
                
            results['clue'] = clue_result
            
            # Track token usage for clue generation
            if isinstance(clue_result, dict) and 'token_usage' in clue_result:
                tokens = clue_result['token_usage']
                # Handle both dict and int token usage formats
                if isinstance(tokens, dict):
                    token_count = tokens.get('total_tokens', 0)
                else:
                    token_count = tokens if isinstance(tokens, int) else 0
                    
                with self.progress_lock:
                    self.progress['token_usage']['clue_generation'] += token_count
                    self.progress['token_usage']['total'] += token_count
                    
            log_success(self.logger, f"[T{thread_id}] Item {item_id}: Clue generated")
            
            # Stage 2: Generate Scene
            log_processing(self.logger, f"[T{thread_id}] Item {item_id}: Generating scene...")
            with self.progress_lock:
                self.progress['current_items'][thread_id] = f"Item {item_id}: Generating scene"
                
            # Prepare clue item for scene generation
            clue_item = {
                'id': item_id,
                'response': clue_result.get('response', '')
            }
            
            scene_gen = SceneGenerator()
            scene_result = scene_gen.generate_single(clue_item, thread_id)
            
            if not scene_result:
                raise Exception("Scene generation failed")
                
            results['scene'] = scene_result
            
            # Track token usage for scene generation
            if isinstance(scene_result, dict) and 'token_usage' in scene_result:
                tokens = scene_result['token_usage']
                # Handle both dict and int token usage formats
                if isinstance(tokens, dict):
                    token_count = tokens.get('total_tokens', 0)
                else:
                    token_count = tokens if isinstance(tokens, int) else 0
                    
                with self.progress_lock:
                    self.progress['token_usage']['scene_generation'] += token_count
                    self.progress['token_usage']['total'] += token_count
                    
            log_success(self.logger, f"[T{thread_id}] Item {item_id}: Scene generated")
            
            # Stage 3: Generate Task (with embedded verification)
            log_processing(self.logger, f"[T{thread_id}] Item {item_id}: Generating task...")
            with self.progress_lock:
                self.progress['current_items'][thread_id] = f"Item {item_id}: Generating task"

            # Prepare scene item for task generation
            scene_item = {
                'id': scene_result.get('scene_id', item_id),
                'filename': f"{item_id}_scene.json",
                'scene_data': scene_result.get('scene_data', {})
            }

            task_gen = TaskGenerator()
            task_result = task_gen.generate_single(scene_item, thread_id)

            if not task_result:
                raise Exception("Task generation failed")

            results['task'] = task_result

            # Track token usage for task generation
            if isinstance(task_result, dict) and 'token_usage' in task_result:
                tokens = task_result['token_usage']
                # Handle both dict and int token usage formats
                if isinstance(tokens, dict):
                    token_count = tokens.get('total_tokens', 0)
                else:
                    token_count = tokens if isinstance(tokens, int) else 0

                with self.progress_lock:
                    self.progress['token_usage']['task_generation'] += token_count
                    self.progress['token_usage']['total'] += token_count

            log_success(self.logger, f"[T{thread_id}] Item {item_id}: Task generated")

            # Stage 4: Validate and Fix Task
            log_processing(self.logger, f"[T{thread_id}] Item {item_id}: Validating and fixing task...")
            with self.progress_lock:
                self.progress['current_items'][thread_id] = f"Item {item_id}: Validating task"

            try:
                task_data = task_result.get('task_data', {})
                scene_data = scene_result.get('scene_data', {})

                # Validate and fix task data
                is_valid, error_messages, fixed_task_data, fixes_applied = self.task_validator.validate_and_fix_task_data(
                    task_data, scene_data, auto_fix=True
                )

                # Log validation results
                if error_messages:
                    self.logger.warning(f"[T{thread_id}] Item {item_id}: Found {len(error_messages)} validation issues")
                    for i, error in enumerate(error_messages, 1):
                        self.logger.warning(f"[T{thread_id}] Item {item_id}:   {i}. {error}")
                else:
                    self.logger.info(f"[T{thread_id}] Item {item_id}: Task validation passed ✓")

                # Log fixes applied
                if fixes_applied:
                    self.logger.info(f"[T{thread_id}] Item {item_id}: Applied {len(fixes_applied)} fixes:")
                    for i, fix in enumerate(fixes_applied, 1):
                        self.logger.info(f"[T{thread_id}] Item {item_id}:   {i}. {fix}")
                else:
                    self.logger.info(f"[T{thread_id}] Item {item_id}: No fixes needed")

                # Update task result with fixed data if changes were made
                if fixes_applied and fixed_task_data:
                    task_result['task_data'] = fixed_task_data

                    # Save the fixed task file
                    task_filename = f"{str(item_id).zfill(5)}_task.json"
                    task_path = self.task_dir / task_filename
                    save_json(fixed_task_data, str(task_path))
                    self.logger.info(f"[T{thread_id}] Item {item_id}: Saved fixed task file: {task_path}")

                    # Save fix log
                    self.task_validator._save_fix_log(str(task_path), fixes_applied, error_messages)
                    self.logger.info(f"[T{thread_id}] Item {item_id}: Saved validation fix log")

                log_success(self.logger, f"[T{thread_id}] Item {item_id}: Task validation completed")

            except Exception as validation_error:
                self.logger.error(f"[T{thread_id}] Item {item_id}: Task validation failed: {validation_error}")
                # Continue with original task data if validation fails

            # Update progress
            with self.progress_lock:
                self.progress['completed'] += 1
                del self.progress['current_items'][thread_id]

            log_success(self.logger, f"[T{thread_id}] Item {item_id}: Complete pipeline finished! ✓")
            return True, results
            
        except Exception as e:
            self.logger.error(f"[T{thread_id}] Item {item_id}: Pipeline failed - {str(e)}")
            results['errors'].append(str(e))
            
            with self.progress_lock:
                self.progress['failed'] += 1
                if thread_id in self.progress['current_items']:
                    del self.progress['current_items'][thread_id]
                    
            return False, results
            
    def show_progress(self):
        """Display current progress."""
        with self.progress_lock:
            total = self.progress['total']
            completed = self.progress['completed']
            failed = self.progress['failed']
            skipped = self.progress['skipped']
            in_progress = len(self.progress['current_items'])
            
            self.logger.info("┌──────────────────────────────────────────────────┐")
            self.logger.info("│                   📊 Progress                    │")
            self.logger.info("├──────────────────────────────────────────────────┤")
            self.logger.info(f"│ Done: {completed:>2}/{total:<2} | Skip: {skipped:>2} | Fail: {failed:>2} | Work: {in_progress:>2} │")
            
            # Show what each thread is doing
            if self.progress['current_items']:
                self.logger.info("├──────────────────────────────────────────────────┤")
                for thread_id, status in self.progress['current_items'].items():
                    status_text = f"T{thread_id}: {status}"
                    if len(status_text) > 47:
                        status_text = status_text[:44] + "..."
                    self.logger.info(f"│ {status_text:<48} │")
            self.logger.info("└──────────────────────────────────────────────────┘\n")
            
    def run(self, items: List[Dict[str, Any]], num_threads: int = 4):
        """
        Run the end-to-end pipeline on multiple items.
        
        Args:
            items: List of raw data items
            num_threads: Number of parallel threads
        """
        if not items:
            self.logger.warning("No items to process")
            return
            
        self.logger.info("┌──────────────────────────────────────────────────┐")
        self.logger.info("│               🚀 Pipeline Starting               │")
        self.logger.info("├──────────────────────────────────────────────────┤")
        self.logger.info(f"│ Items: {len(items):<42} │")
        self.logger.info(f"│ Threads: {num_threads:<40} │")
        self.logger.info(f"│ Resume: {str(self.config.get('continue_generation', True)):<41} │")
        self.logger.info("└──────────────────────────────────────────────────┘\n")
        
        # Initialize progress
        with self.progress_lock:
            self.progress['total'] = len(items)
            self.progress['completed'] = 0
            self.progress['failed'] = 0
            self.progress['skipped'] = 0
            self.progress['current_items'] = {}
            
        start_time = time.time()
        all_results = []
        
        # Process items in parallel
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            # Submit all tasks
            future_to_item = {}
            for i, item in enumerate(items):
                future = executor.submit(self.process_single_item, item, i % num_threads + 1)
                future_to_item[future] = item
                
            # Process completed tasks and show progress
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    success, results = future.result()
                    all_results.append(results)
                    
                    # Show progress periodically
                    if len(all_results) % max(1, len(items) // 10) == 0:
                        self.show_progress()
                        
                except Exception as e:
                    self.logger.error(f"Unexpected error processing item {item.get('id')}: {e}")
                    
        # Final statistics
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate time statistics
        avg_time = total_time / max(1, self.progress['completed'])
        time_minutes = total_time / 60
        total_tokens = self.progress['token_usage']['total']
        
        self.logger.info("┌──────────────────────────────────────────────────┐")
        self.logger.info("│                   🎉 Complete!                   │")
        self.logger.info("├──────────────────────────────────────────────────┤")
        self.logger.info(f"│ Time: {time_minutes:>4.1f}min ({total_time:>5.1f}s)                     │")
        self.logger.info(f"│ Done: {self.progress['completed']:>2}/{self.progress['total']:<2}                                       │")
        self.logger.info(f"│ Skip: {self.progress['skipped']:>2}                                         │")
        self.logger.info(f"│ Fail: {self.progress['failed']:>2}                                         │")
        self.logger.info(f"│ Avg: {avg_time:>5.1f}s/item                           │")
        
        if total_tokens > 0:
            self.logger.info("├──────────────────────────────────────────────────┤")
            self.logger.info("│                   💰 Tokens                      │")
            self.logger.info("├──────────────────────────────────────────────────┤")
            self.logger.info(f"│ Total: {total_tokens:>8,}                              │")
            self.logger.info(f"│ Clue:  {self.progress['token_usage']['clue_generation']:>8,}                              │")
            self.logger.info(f"│ Scene: {self.progress['token_usage']['scene_generation']:>8,}                              │")
            self.logger.info(f"│ Task:  {self.progress['token_usage']['task_generation']:>8,}                              │")
            
        self.logger.info("└──────────────────────────────────────────────────┘\n")
        
        # Save summary with ID range
        start_id = min(item['id'] for item in items) if items else 0
        end_id = max(item['id'] for item in items) if items else 0
        self.save_summary(all_results, total_time, start_id, end_id)
        
    def save_summary(self, results: List[Dict[str, Any]], total_time: float, start_id: int, end_id: int):
        """Save execution summary with timestamp and ID range in filename."""
        # 生成时间戳格式：YYYYMMDD_HHMMSS
        timestamp = time.strftime('%Y%m%d_%H%M%S')

        # 生成文件名：时间戳_起始ID-结束ID.json
        filename = f"{timestamp}_data_generation_summary_{start_id}-{end_id}.json"

        # 使用项目根目录的output目录
        output_dir = self.project_root / 'output'
        summary_path = output_dir / filename

        # 确保目录存在
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Count statistics
        successful = sum(1 for r in results if not r.get('errors', []) and not r.get('skipped', False))
        failed = sum(1 for r in results if r.get('errors', []))
        skipped = sum(1 for r in results if r.get('skipped', False))
        
        summary = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'execution_time_seconds': round(total_time, 2),
            'execution_time_minutes': round(total_time / 60, 2),
            'total_items': len(results),
            'successful': successful,
            'failed': failed,
            'skipped': skipped,
            'token_usage': {
                'total_tokens': self.progress['token_usage']['total'],
                'clue_generation': self.progress['token_usage']['clue_generation'],
                'scene_generation': self.progress['token_usage']['scene_generation'],
                'task_generation': self.progress['token_usage']['task_generation']
            },
            'performance': {
                'items_per_minute': round((successful * 60) / max(total_time, 1), 2),
                'average_time_per_item': round(total_time / max(successful, 1), 2),
                'tokens_per_item': round(self.progress['token_usage']['total'] / max(successful, 1), 0) if successful > 0 else 0
            }
        }
        
        save_json(summary, str(summary_path))
        self.logger.info(f"Summary saved to: {summary_path}")


def main():
    """
    Main entry point for the end-to-end data generation pipeline.
    
    This function sets up command-line argument parsing, loads configuration,
    processes input data, and executes the complete pipeline. It supports
    flexible input sources, ID range filtering, and various execution options.
    """
    parser = argparse.ArgumentParser(description='Run end-to-end data generation pipeline')
    
    parser.add_argument('--input', default='data/news.json',
                       help='Input file with raw data')
    parser.add_argument('--start-id', type=int, default=None,
                       help='Starting ID (inclusive)')
    parser.add_argument('--end-id', type=int, default=None,
                       help='Ending ID (inclusive)')
    parser.add_argument('--threads', type=int, default=4,
                       help='Number of parallel threads')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(console_level=args.log_level)

    # Load configuration for default values
    try:
        project_root = Path(__file__).parent.parent  # 项目根目录
        config_path = project_root / "config" / "data_generation" / "pipeline.yaml"

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 应用默认值（只保留实际使用的配置项）
        defaults = {
            'thread_num': 4,
            'start_id': 0,
            'end_id': None,
        }

        for key, default_value in defaults.items():
            config.setdefault(key, default_value)

    except Exception as e:
        print(f"Error loading pipeline config: {e}")
        config = {'thread_num': 4, 'start_id': 0, 'end_id': None}
    
    # Use config values if not provided via command line
    if args.start_id is None:
        args.start_id = config.get('start_id')
    if args.end_id is None:
        args.end_id = config.get('end_id')
    if args.threads == 4:  # Only override if default value
        args.threads = config.get('thread_num', 4)
    
    # Load input data
    try:
        input_path = Path(args.input)
        if not input_path.exists():
            # Try relative to project root
            input_path = Path(__file__).parent.parent / args.input
            
        data = load_json(str(input_path))
        
        # Handle both list and dict formats
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and 'data' in data:
            items = data['data']
        else:
            items = data if isinstance(data, list) else []
        
        # Filter by ID range if specified
        if args.start_id is not None or args.end_id is not None:
            filtered_items = []
            for item in items:
                if isinstance(item, dict):
                    item_id = item.get('id', 0)
                    if args.start_id is not None and item_id < args.start_id:
                        continue
                    if args.end_id is not None and item_id > args.end_id:
                        continue
                    filtered_items.append(item)
            items = filtered_items
            
    except Exception as e:
        print(f"Error loading input file: {e}")
        return
        
    # Run pipeline
    pipeline = Pipeline()
    pipeline.run(items, args.threads)


if __name__ == "__main__":
    main() 