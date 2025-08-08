#!/usr/bin/env python3
"""
Verify Expert Trajectory Data for OmniEAR
Validates the quality, format, and consistency of expert trajectory data
"""

import os
import json
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrajectoryValidator:
    """Validates expert trajectory data quality and consistency"""
    
    def __init__(self, data_path: str = ".", config_path: str = "hf_config.yaml"):
        """Initialize validator
        
        Args:
            data_path: Path to trajectory data directory
            config_path: Path to configuration file
        """
        self.data_path = Path(data_path)
        self.config = self._load_config(config_path)
        self.stats = defaultdict(int)
        self.errors = []
        self.warnings = []
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load config: {e}")
            return {}
            
    def validate_file_structure(self) -> bool:
        """Validate directory and file structure"""
        logger.info("Validating file structure...")
        
        # Check for expected directories
        single_agent_dir = self.data_path / "single_agent"
        centralized_agent_dir = self.data_path / "centralized_agent"
        
        structure_valid = True
        
        if not single_agent_dir.exists():
            self.errors.append("Missing single_agent directory")
            structure_valid = False
        else:
            single_agent_files = list(single_agent_dir.glob("*.json"))
            self.stats['single_agent_files'] = len(single_agent_files)
            logger.info(f"Found {len(single_agent_files)} single-agent files")
            
        if not centralized_agent_dir.exists():
            self.errors.append("Missing centralized_agent directory")
            structure_valid = False
        else:
            centralized_files = list(centralized_agent_dir.glob("*.json"))
            self.stats['centralized_agent_files'] = len(centralized_files)
            logger.info(f"Found {len(centralized_files)} centralized-agent files")
            
        return structure_valid
        
    def validate_json_format(self) -> bool:
        """Validate JSON format and required fields"""
        logger.info("Validating JSON format...")
        
        required_fields = self.config.get('validation', {}).get('required_fields', 
                                                               ['instruction', 'output', 'system'])
        
        all_files = []
        if (self.data_path / "single_agent").exists():
            all_files.extend((self.data_path / "single_agent").glob("*.json"))
        if (self.data_path / "centralized_agent").exists():
            all_files.extend((self.data_path / "centralized_agent").glob("*.json"))
            
        valid_files = 0
        invalid_files = 0
        
        for file_path in all_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Check required fields
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    self.errors.append(f"Missing fields {missing_fields} in {file_path.name}")
                    invalid_files += 1
                    continue
                    
                # Validate field types and content
                if not isinstance(data.get('instruction', ''), str) or not data['instruction'].strip():
                    self.errors.append(f"Invalid instruction in {file_path.name}")
                    invalid_files += 1
                    continue
                    
                if not isinstance(data.get('output', ''), str) or not data['output'].strip():
                    self.errors.append(f"Invalid output in {file_path.name}")
                    invalid_files += 1
                    continue
                    
                if not isinstance(data.get('system', ''), str) or not data['system'].strip():
                    self.errors.append(f"Invalid system prompt in {file_path.name}")
                    invalid_files += 1
                    continue
                    
                valid_files += 1
                
            except json.JSONDecodeError as e:
                self.errors.append(f"Invalid JSON in {file_path.name}: {e}")
                invalid_files += 1
            except Exception as e:
                self.errors.append(f"Error processing {file_path.name}: {e}")
                invalid_files += 1
                
        self.stats['valid_json_files'] = valid_files
        self.stats['invalid_json_files'] = invalid_files
        
        logger.info(f"Valid JSON files: {valid_files}")
        logger.info(f"Invalid JSON files: {invalid_files}")
        
        return invalid_files == 0
        
    def analyze_task_distribution(self) -> None:
        """Analyze distribution of task types"""
        logger.info("Analyzing task distribution...")
        
        task_counts = defaultdict(int)
        
        # Analyze single-agent tasks
        single_agent_dir = self.data_path / "single_agent"
        if single_agent_dir.exists():
            for file_path in single_agent_dir.glob("*.json"):
                # Extract task type from filename
                filename = file_path.name
                if '_' in filename:
                    task_type = '_'.join(filename.split('_')[:-1])  # Remove file number
                    task_counts[task_type] += 1
                    
        # Analyze centralized-agent tasks  
        centralized_dir = self.data_path / "centralized_agent" 
        if centralized_dir.exists():
            for file_path in centralized_dir.glob("*.json"):
                filename = file_path.name
                if '_' in filename:
                    task_type = '_'.join(filename.split('_')[:-1])
                    task_counts[task_type] += 1
                    
        self.stats['task_distribution'] = dict(task_counts)
        
        logger.info("Task distribution:")
        for task_type, count in task_counts.items():
            logger.info(f"  {task_type}: {count} samples")
            
    def analyze_content_quality(self) -> None:
        """Analyze content quality metrics"""
        logger.info("Analyzing content quality...")
        
        instruction_lengths = []
        output_lengths = []
        system_lengths = []
        
        all_files = []
        if (self.data_path / "single_agent").exists():
            all_files.extend((self.data_path / "single_agent").glob("*.json"))
        if (self.data_path / "centralized_agent").exists():
            all_files.extend((self.data_path / "centralized_agent").glob("*.json"))
            
        for file_path in all_files[:100]:  # Sample first 100 files for efficiency
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                instruction_lengths.append(len(data.get('instruction', '')))
                output_lengths.append(len(data.get('output', '')))
                system_lengths.append(len(data.get('system', '')))
                
            except Exception as e:
                self.warnings.append(f"Could not analyze {file_path.name}: {e}")
                
        if instruction_lengths:
            self.stats['avg_instruction_length'] = sum(instruction_lengths) // len(instruction_lengths)
            self.stats['avg_output_length'] = sum(output_lengths) // len(output_lengths)
            self.stats['avg_system_length'] = sum(system_lengths) // len(system_lengths)
            
            logger.info(f"Average instruction length: {self.stats['avg_instruction_length']} chars")
            logger.info(f"Average output length: {self.stats['avg_output_length']} chars")
            logger.info(f"Average system length: {self.stats['avg_system_length']} chars")
            
    def validate_action_format(self) -> None:
        """Validate action format in outputs"""
        logger.info("Validating action format...")
        
        valid_actions = 0
        invalid_actions = 0
        
        # Common action patterns in OmniEAR
        action_patterns = [
            r'GOTO\s+\w+',
            r'GRAB\s+\w+', 
            r'PLACE\s+\w+\s+(in|on)\s+\w+',
            r'EXPLORE',
            r'DONE',
            r'OPEN\s+\w+',
            r'CLOSE\s+\w+',
            r'TURN_ON\s+\w+',
        ]
        
        all_files = []
        if (self.data_path / "single_agent").exists():
            all_files.extend(list((self.data_path / "single_agent").glob("*.json"))[:50])
        if (self.data_path / "centralized_agent").exists():
            all_files.extend(list((self.data_path / "centralized_agent").glob("*.json"))[:50])
            
        for file_path in all_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                output = data.get('output', '')
                
                # Check if output contains valid action
                has_valid_action = False
                for pattern in action_patterns:
                    if re.search(pattern, output):
                        has_valid_action = True
                        break
                        
                if has_valid_action:
                    valid_actions += 1
                else:
                    invalid_actions += 1
                    self.warnings.append(f"No recognized actions in {file_path.name}")
                    
            except Exception as e:
                self.warnings.append(f"Could not validate actions in {file_path.name}: {e}")
                
        self.stats['valid_action_format'] = valid_actions
        self.stats['invalid_action_format'] = invalid_actions
        
        logger.info(f"Files with valid actions: {valid_actions}")
        logger.info(f"Files with questionable actions: {invalid_actions}")
        
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        logger.info("Generating validation report...")
        
        total_files = self.stats.get('single_agent_files', 0) + self.stats.get('centralized_agent_files', 0)
        
        report = {
            'summary': {
                'total_files': total_files,
                'valid_files': self.stats.get('valid_json_files', 0),
                'invalid_files': self.stats.get('invalid_json_files', 0),
                'error_count': len(self.errors),
                'warning_count': len(self.warnings)
            },
            'file_distribution': {
                'single_agent_files': self.stats.get('single_agent_files', 0),
                'centralized_agent_files': self.stats.get('centralized_agent_files', 0)
            },
            'task_distribution': self.stats.get('task_distribution', {}),
            'content_metrics': {
                'avg_instruction_length': self.stats.get('avg_instruction_length', 0),
                'avg_output_length': self.stats.get('avg_output_length', 0),
                'avg_system_length': self.stats.get('avg_system_length', 0)
            },
            'validation_results': {
                'valid_action_format': self.stats.get('valid_action_format', 0),
                'invalid_action_format': self.stats.get('invalid_action_format', 0)
            },
            'errors': self.errors,
            'warnings': self.warnings
        }
        
        return report
        
    def run_full_validation(self) -> bool:
        """Run complete validation pipeline"""
        logger.info("Starting comprehensive validation...")
        
        # Run all validation steps
        structure_ok = self.validate_file_structure()
        format_ok = self.validate_json_format()
        
        # Analysis steps (non-blocking)
        self.analyze_task_distribution()
        self.analyze_content_quality()
        self.validate_action_format()
        
        # Generate and save report
        report = self.generate_report()
        
        # Save report to file
        report_path = self.data_path / "validation_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Validation report saved to: {report_path}")
        
        # Print summary
        self.print_summary(report)
        
        return structure_ok and format_ok
        
    def print_summary(self, report: Dict[str, Any]) -> None:
        """Print validation summary"""
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        
        summary = report['summary']
        print(f"Total files: {summary['total_files']}")
        print(f"Valid files: {summary['valid_files']}")
        print(f"Invalid files: {summary['invalid_files']}")
        print(f"Errors: {summary['error_count']}")
        print(f"Warnings: {summary['warning_count']}")
        
        print("\nTask Distribution:")
        for task_type, count in report['task_distribution'].items():
            print(f"  {task_type}: {count}")
            
        if self.errors:
            print("\nErrors:")
            for error in self.errors[:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more errors")
                
        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings[:5]:  # Show first 5 warnings
                print(f"  - {warning}")
            if len(self.warnings) > 5:
                print(f"  ... and {len(self.warnings) - 5} more warnings")
                
        print("\n" + "="*60)


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate OmniEAR expert trajectory data")
    parser.add_argument("--data-path", default=".", help="Path to data directory")
    parser.add_argument("--config", default="hf_config.yaml", help="Path to configuration file") 
    parser.add_argument("--save-report", action="store_true", help="Save detailed report to file")
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = TrajectoryValidator(args.data_path, args.config)
    
    # Run validation
    success = validator.run_full_validation()
    
    if success:
        logger.info("Validation completed successfully")
        exit(0)
    else:
        logger.error("Validation failed")
        exit(1)


if __name__ == "__main__":
    main()
