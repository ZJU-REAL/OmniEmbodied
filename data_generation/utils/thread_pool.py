"""
Thread pool management utilities for the data generation project.
Provides thread-safe task execution with proper error handling.
"""

import threading
import time
from typing import Callable, Any, List, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum

from logger import get_logger


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class TaskResult:
    """Result of a task execution."""
    task_id: Any
    status: TaskStatus
    result: Any = None
    error: Optional[Exception] = None
    attempts: int = 0
    execution_time: float = 0.0


class ThreadPoolManager:
    """
    Thread pool manager with task queue and error handling.
    """
    
    def __init__(self, num_threads: int = 4, max_retries: int = 3, retry_delay: float = 2.0):
        """
        Initialize thread pool manager.
        
        Args:
            num_threads: Number of worker threads
            max_retries: Maximum retry attempts for failed tasks
            retry_delay: Base delay between retries (exponential backoff)
        """
        self.num_threads = num_threads
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = get_logger(self.__class__.__name__)
        
        # Task tracking
        self.task_results: Dict[Any, TaskResult] = {}
        self.results_lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'retried_tasks': 0,
            'total_execution_time': 0.0
        }
        self.stats_lock = threading.Lock()
        
    def execute_tasks(self, tasks: List[Any], task_func: Callable, 
                     task_id_func: Optional[Callable] = None,
                     progress_callback: Optional[Callable] = None) -> List[TaskResult]:
        """
        Execute tasks in parallel with thread pool.
        
        Args:
            tasks: List of task items to process
            task_func: Function to execute for each task (should accept task item and thread_id)
            task_id_func: Optional function to extract task ID from task item
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of TaskResult objects
        """
        if not tasks:
            self.logger.warning("No tasks to execute")
            return []
            
        self.logger.info(f"Starting execution of {len(tasks)} tasks with {self.num_threads} threads")
        
        # Reset statistics
        with self.stats_lock:
            self.stats = {
                'total_tasks': len(tasks),
                'completed_tasks': 0,
                'failed_tasks': 0,
                'retried_tasks': 0,
                'total_execution_time': 0.0
            }
            
        results = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            # Submit all tasks
            future_to_task = {}
            for i, task in enumerate(tasks):
                task_id = task_id_func(task) if task_id_func else i
                future = executor.submit(self._execute_single_task, task, task_func, task_id, i % self.num_threads + 1)
                future_to_task[future] = (task, task_id)
                
            # Process completed tasks
            for future in as_completed(future_to_task):
                task, task_id = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Update progress
                    if progress_callback:
                        with self.stats_lock:
                            progress = self.stats['completed_tasks'] / self.stats['total_tasks']
                        progress_callback(progress, result)
                        
                except Exception as e:
                    self.logger.error(f"Unexpected error processing task {task_id}: {e}")
                    result = TaskResult(
                        task_id=task_id,
                        status=TaskStatus.FAILED,
                        error=e,
                        attempts=1
                    )
                    results.append(result)
                    
        # Final statistics
        total_time = time.time() - start_time
        self._log_statistics(total_time)
        
        return results
        
    def _execute_single_task(self, task: Any, task_func: Callable, task_id: Any, thread_id: int) -> TaskResult:
        """
        Execute a single task with retry logic.
        
        Args:
            task: Task item to process
            task_func: Function to execute
            task_id: Task identifier
            thread_id: Thread identifier for logging
            
        Returns:
            TaskResult object
        """
        result = TaskResult(task_id=task_id, status=TaskStatus.PENDING)
        
        for attempt in range(1, self.max_retries + 1):
            result.attempts = attempt
            
            try:
                # Update status
                result.status = TaskStatus.RUNNING
                self._update_task_result(task_id, result)
                
                # Execute task
                start_time = time.time()
                task_result = task_func(task, thread_id)
                execution_time = time.time() - start_time
                
                # Success
                result.status = TaskStatus.COMPLETED
                result.result = task_result
                result.execution_time = execution_time
                
                # Update statistics
                with self.stats_lock:
                    self.stats['completed_tasks'] += 1
                    self.stats['total_execution_time'] += execution_time
                    
                self.logger.debug(f"Task {task_id} completed successfully (attempt {attempt}, time: {execution_time:.2f}s)")
                break
                
            except Exception as e:
                self.logger.warning(f"Task {task_id} failed on attempt {attempt}: {e}")
                result.error = e
                
                if attempt < self.max_retries:
                    # Retry with exponential backoff
                    result.status = TaskStatus.RETRYING
                    retry_delay = self.retry_delay * (2 ** (attempt - 1))
                    self.logger.info(f"🔄 RETRY: Task {task_id} will retry in {retry_delay:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                    
                    with self.stats_lock:
                        self.stats['retried_tasks'] += 1
                        
                    time.sleep(retry_delay)
                else:
                    # Final failure
                    result.status = TaskStatus.FAILED
                    with self.stats_lock:
                        self.stats['failed_tasks'] += 1
                        
                    self.logger.error(f"❌ FINAL FAILURE: Task {task_id} failed permanently after {attempt} attempts")
                    self.logger.error(f"❌ Last error: {str(e)}")
                    
        self._update_task_result(task_id, result)
        return result
        
    def _update_task_result(self, task_id: Any, result: TaskResult):
        """Update task result in thread-safe manner."""
        with self.results_lock:
            self.task_results[task_id] = result
            
    def _log_statistics(self, total_time: float):
        """Log execution statistics."""
        with self.stats_lock:
            stats = self.stats.copy()
            
        self.logger.info("="*50)
        self.logger.info("Execution Statistics:")
        self.logger.info(f"  Total tasks: {stats['total_tasks']}")
        self.logger.info(f"  Completed: {stats['completed_tasks']}")
        self.logger.info(f"  Failed: {stats['failed_tasks']}")
        self.logger.info(f"  Retried: {stats['retried_tasks']}")
        self.logger.info(f"  Total execution time: {total_time:.2f}s")
        self.logger.info(f"  Average time per task: {stats['total_execution_time'] / max(stats['completed_tasks'], 1):.2f}s")
        self.logger.info(f"  Throughput: {stats['completed_tasks'] / max(total_time, 1):.2f} tasks/s")
        self.logger.info("="*50)
        
    def get_failed_tasks(self) -> List[TaskResult]:
        """Get all failed task results."""
        with self.results_lock:
            return [r for r in self.task_results.values() if r.status == TaskStatus.FAILED]
            
    def get_statistics(self) -> Dict[str, Any]:
        """Get current execution statistics."""
        with self.stats_lock:
            return self.stats.copy() 