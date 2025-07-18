#!/usr/bin/env python3
"""
Task Cleaner Script

This script validates and cleans tasks in the data/data-all directory by:
1. Running validation on all task files
2. Removing tasks that cannot be automatically fixed and fail validation
3. Providing detailed logging of all removed tasks
4. Creating a backup of removed tasks before deletion
"""

import os
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Add the data_generation directory to Python path
import sys
sys.path.append(str(Path(__file__).parent))

from utils.task_validator import TaskValidator
from utils.json_utils import load_json, save_json
from utils.logger import get_logger


class TaskCleaner:
    """Clean and validate tasks in data-all directory."""
    
    def __init__(self, data_dir: str = "data/data-all"):
        """
        Initialize the task cleaner.
        
        Args:
            data_dir: Path to the data-all directory
        """
        self.logger = get_logger("TaskCleaner")
        self.data_dir = Path(data_dir)
        self.task_dir = self.data_dir / "task"
        self.scene_dir = self.data_dir / "scene"
        
        # Initialize validator
        self.validator = TaskValidator()
        
        # Statistics
        self.stats = {
            'total_tasks': 0,
            'valid_tasks': 0,
            'fixed_tasks': 0,
            'removed_tasks': 0,
            'error_tasks': 0,
            'total_fixes_applied': 0,
            'common_fix_types': {},
            'common_error_types': {}
        }
        
        # Track removed tasks for logging
        self.removed_tasks = []
        self.error_tasks = []
        
    def create_backup_dir(self) -> Path:
        """Create backup directory for removed tasks."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.data_dir / f"removed_tasks_backup_{timestamp}"
        backup_dir.mkdir(exist_ok=True)
        self.logger.info(f"Created backup directory: {backup_dir}")
        return backup_dir
        
    def load_scene_data(self, scene_id: str) -> Dict[str, Any]:
        """Load corresponding scene data for a task."""
        scene_file = self.scene_dir / f"{scene_id}_scene.json"
        if scene_file.exists():
            return load_json(str(scene_file))
        else:
            self.logger.warning(f"Scene file not found: {scene_file}")
            return {}
            
    def validate_single_task(self, task_file: Path) -> Tuple[bool, List[str], Dict[str, Any], List[str]]:
        """
        Validate a single task file.
        
        Returns:
            Tuple of (is_valid, errors, fixed_data, fixes_applied)
        """
        try:
            # Load task data
            task_data = load_json(str(task_file))
            if not task_data:
                return False, ["Failed to load task data"], {}, []
                
            # Extract scene ID
            scene_id = task_data.get('scene_id')
            if not scene_id:
                return False, ["Missing scene_id in task data"], {}, []
                
            # Load scene data
            scene_data = self.load_scene_data(str(scene_id).zfill(5))
            if not scene_data:
                return False, [f"Failed to load scene data for scene_id: {scene_id}"], {}, []
                
            # Validate with auto-fix enabled
            is_valid, errors, fixed_data, fixes_applied = self.validator.validate_and_fix_task_data(
                task_data, scene_data, auto_fix=True
            )
            
            return is_valid, errors, fixed_data, fixes_applied
            
        except Exception as e:
            self.logger.error(f"Error validating {task_file}: {e}")
            return False, [f"Validation error: {str(e)}"], {}, []
            
    def process_all_tasks(self, dry_run: bool = False) -> None:
        """
        Process all tasks in the task directory.
        
        Args:
            dry_run: If True, only report what would be done without making changes
        """
        if not self.task_dir.exists():
            self.logger.error(f"Task directory not found: {self.task_dir}")
            return
            
        # Create backup directory if not dry run
        backup_dir = None
        if not dry_run:
            backup_dir = self.create_backup_dir()
            
        # Get all task files
        task_files = list(self.task_dir.glob("*_task.json"))
        task_files.sort()
        
        self.logger.info(f"Found {len(task_files)} task files to process")
        self.stats['total_tasks'] = len(task_files)
        
        for task_file in task_files:
            self.logger.info(f"Processing: {task_file.name}")
            
            try:
                is_valid, errors, fixed_data, fixes_applied = self.validate_single_task(task_file)
                
                if is_valid:
                    if fixes_applied:
                        # Task was fixed
                        self.stats['fixed_tasks'] += 1
                        self.stats['total_fixes_applied'] += len(fixes_applied)

                        # Track common fix types
                        for fix in fixes_applied:
                            fix_type = self._categorize_fix(fix)
                            self.stats['common_fix_types'][fix_type] = self.stats['common_fix_types'].get(fix_type, 0) + 1

                        self.logger.info(f"✅ {task_file.name}: Fixed with {len(fixes_applied)} changes")
                        for fix in fixes_applied[:3]:  # Show first 3 fixes
                            self.logger.info(f"   - {fix}")
                        if len(fixes_applied) > 3:
                            self.logger.info(f"   ... and {len(fixes_applied) - 3} more fixes")

                        if not dry_run:
                            # Save the fixed data
                            save_json(fixed_data, str(task_file))
                            self.logger.info(f"   Saved fixed data to {task_file}")
                    else:
                        # Task was already valid
                        self.stats['valid_tasks'] += 1
                        self.logger.info(f"✅ {task_file.name}: Already valid")
                        
                else:
                    # Task cannot be fixed - mark for removal
                    self.stats['removed_tasks'] += 1

                    # Track common error types
                    for error in errors:
                        error_type = self._categorize_error(error)
                        self.stats['common_error_types'][error_type] = self.stats['common_error_types'].get(error_type, 0) + 1

                    self.removed_tasks.append({
                        'file': task_file.name,
                        'errors': errors,
                        'fixes_attempted': len(fixes_applied),
                        'primary_error': errors[0] if errors else "Unknown error"
                    })

                    self.logger.warning(f"❌ {task_file.name}: Cannot be fixed, will be removed")
                    self.logger.warning(f"   Primary error: {errors[0] if errors else 'Unknown'}")
                    if len(errors) > 1:
                        self.logger.warning(f"   Additional errors: {len(errors) - 1}")

                    if not dry_run:
                        # Backup the task before removal
                        backup_file = backup_dir / task_file.name
                        shutil.copy2(task_file, backup_file)

                        # Remove the task file
                        task_file.unlink()
                        self.logger.info(f"   Removed {task_file.name} (backed up to {backup_file})")
                        
            except Exception as e:
                self.stats['error_tasks'] += 1
                self.error_tasks.append({
                    'file': task_file.name,
                    'error': str(e)
                })
                self.logger.error(f"💥 {task_file.name}: Processing error - {e}")
                
    def generate_report(self) -> None:
        """Generate a detailed report of the cleaning process."""
        self.logger.info("\n" + "="*60)
        self.logger.info("TASK CLEANING REPORT")
        self.logger.info("="*60)
        
        # Statistics
        self.logger.info(f"Total tasks processed: {self.stats['total_tasks']}")
        self.logger.info(f"Valid tasks (no changes): {self.stats['valid_tasks']}")
        self.logger.info(f"Fixed tasks: {self.stats['fixed_tasks']}")
        self.logger.info(f"Removed tasks: {self.stats['removed_tasks']}")
        self.logger.info(f"Error tasks: {self.stats['error_tasks']}")
        self.logger.info(f"Total fixes applied: {self.stats['total_fixes_applied']}")

        # Success rate
        if self.stats['total_tasks'] > 0:
            success_rate = (self.stats['valid_tasks'] + self.stats['fixed_tasks']) / self.stats['total_tasks'] * 100
            self.logger.info(f"Success rate: {success_rate:.1f}%")

        # Common fix types
        if self.stats['common_fix_types']:
            self.logger.info(f"\n🔧 COMMON FIX TYPES:")
            for fix_type, count in sorted(self.stats['common_fix_types'].items(), key=lambda x: x[1], reverse=True):
                self.logger.info(f"  {fix_type}: {count}")

        # Common error types
        if self.stats['common_error_types']:
            self.logger.info(f"\n⚠️  COMMON ERROR TYPES:")
            for error_type, count in sorted(self.stats['common_error_types'].items(), key=lambda x: x[1], reverse=True):
                self.logger.info(f"  {error_type}: {count}")
        
        # Removed tasks details
        if self.removed_tasks:
            self.logger.info(f"\n📋 REMOVED TASKS ({len(self.removed_tasks)}):")
            for i, task in enumerate(self.removed_tasks, 1):
                self.logger.info(f"{i:3d}. {task['file']}")
                self.logger.info(f"     Fixes attempted: {task['fixes_attempted']}")
                self.logger.info(f"     Errors: {task['errors'][:2]}...")  # Show first 2 errors
                
        # Error tasks details
        if self.error_tasks:
            self.logger.info(f"\n💥 ERROR TASKS ({len(self.error_tasks)}):")
            for i, task in enumerate(self.error_tasks, 1):
                self.logger.info(f"{i:3d}. {task['file']}: {task['error']}")
                
        self.logger.info("="*60)
        
    def save_detailed_log(self) -> None:
        """Save detailed log to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.data_dir / f"task_cleaning_log_{timestamp}.json"
        
        log_data = {
            'timestamp': timestamp,
            'statistics': self.stats,
            'removed_tasks': self.removed_tasks,
            'error_tasks': self.error_tasks
        }
        
        save_json(log_data, str(log_file))
        self.logger.info(f"Detailed log saved to: {log_file}")

    def _categorize_fix(self, fix_message: str) -> str:
        """Categorize a fix message into a type."""
        fix_lower = fix_message.lower()

        if 'location_id' in fix_lower:
            return 'location_id_format'
        elif 'attribute' in fix_lower and 'fixed' in fix_lower:
            return 'attribute_correction'
        elif 'removed task' in fix_lower:
            return 'task_removal'
        elif 'added missing' in fix_lower:
            return 'missing_field'
        elif 'nested properties' in fix_lower:
            return 'structure_fix'
        else:
            return 'other'

    def _categorize_error(self, error_message: str) -> str:
        """Categorize an error message into a type."""
        error_lower = error_message.lower()

        if 'does not exist in scene' in error_lower:
            return 'missing_object'
        elif 'task description does not match' in error_lower:
            return 'ability_mismatch'
        elif 'invalid task_category' in error_lower:
            return 'invalid_category'
        elif 'missing' in error_lower and 'field' in error_lower:
            return 'missing_field'
        elif 'validation_check' in error_lower:
            return 'validation_check_error'
        else:
            return 'other'


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Clean and validate tasks in data-all directory')
    parser.add_argument('--data-dir', default='data/data-all', 
                       help='Path to data-all directory (default: data/data-all)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Only report what would be done without making changes')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Set up logging level
    import logging
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create cleaner and run
    cleaner = TaskCleaner(args.data_dir)
    
    if args.dry_run:
        cleaner.logger.info("🔍 DRY RUN MODE - No files will be modified")
    
    cleaner.process_all_tasks(dry_run=args.dry_run)
    cleaner.generate_report()
    
    if not args.dry_run:
        cleaner.save_detailed_log()


if __name__ == "__main__":
    main()
