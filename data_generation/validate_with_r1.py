#!/usr/bin/env python3
"""
R1 Validation Script for Generated Tasks

This script tests generated task data using R1 (reasoning model) to validate:
1. Task-validation rule correspondence
2. Task feasibility in given scenes
3. Logical consistency of generated data

Usage:
    python3 validate_with_r1.py --start-id 1 --end-id 10 --output results.json
"""

import json
import argparse
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict

# Import your existing components
from utils.logger import get_logger
import openai


@dataclass
class R1TestResult:
    """Result of R1 testing for a single task."""
    task_id: str
    task_index: int
    task_description: str
    task_category: str
    validation_checks: List[Dict]
    
    # R1 test results
    r1_success: bool
    r1_response: str
    r1_error: str
    
    # Analysis results
    failure_type: str  # 'data_quality', 'r1_planning', 'unclear', 'success'
    confidence: float  # 0-1, confidence in failure_type classification
    issues_found: List[str]
    recommendations: List[str]


class R1TaskValidator:
    """Validates generated tasks using R1 reasoning model."""
    
    def __init__(self, r1_config: Dict[str, Any] = None):
        """Initialize R1 validator."""
        self.logger = get_logger(__name__)
        
        # R1 configuration
        self.r1_config = r1_config or {
            'api_key': 'sk-68143b8311d24fd08c1bd1d1acd96e99',
            'endpoint': 'https://api.deepseek.com',
            'model': 'deepseek-reasoner',
            'temperature': 0.1,
            'max_tokens': 4096
        }
        
        # Initialize OpenAI client for R1
        self.client = openai.OpenAI(
            api_key=self.r1_config['api_key'],
            base_url=self.r1_config['endpoint']
        )
        
    def validate_task_with_r1(self, scene_data: Dict, task_data: Dict, task_index: int) -> R1TestResult:
        """
        Validate a single task using R1.
        
        Args:
            scene_data: Scene JSON data
            task_data: Complete task data
            task_index: Index of specific task to test
            
        Returns:
            R1TestResult with validation results
        """
        task = task_data['tasks'][task_index]
        scene_id = task_data.get('scene_id', 'unknown')
        
        # Create R1 test prompt
        prompt = self._create_r1_test_prompt(scene_data, task_data, task)
        
        try:
            # Call R1
            self.logger.info(f"Testing task {task_index} from scene {scene_id} with R1...")
            response = self.client.chat.completions.create(
                model=self.r1_config['model'],
                messages=[{"role": "user", "content": prompt}],
                temperature=self.r1_config['temperature'],
                max_tokens=self.r1_config['max_tokens']
            )
            response_text = response.choices[0].message.content
            
            # Analyze R1 response
            r1_success, failure_type, confidence, issues, recommendations = self._analyze_r1_response(
                response_text, task, scene_data
            )
            
            return R1TestResult(
                task_id=scene_id,
                task_index=task_index,
                task_description=task['task_description'],
                task_category=task['task_category'],
                validation_checks=task['validation_checks'],
                r1_success=r1_success,
                r1_response=response_text,
                r1_error="",
                failure_type=failure_type,
                confidence=confidence,
                issues_found=issues,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"R1 test failed for task {task_index}: {e}")
            return R1TestResult(
                task_id=scene_id,
                task_index=task_index,
                task_description=task['task_description'],
                task_category=task['task_category'],
                validation_checks=task['validation_checks'],
                r1_success=False,
                r1_response="",
                r1_error=str(e),
                failure_type='unclear',
                confidence=0.0,
                issues_found=[f"R1 call failed: {e}"],
                recommendations=["Retry R1 test", "Check R1 API configuration"]
            )
    
    def _create_r1_test_prompt(self, scene_data: Dict, task_data: Dict, task: Dict) -> str:
        """Create prompt for R1 to test task validity."""
        
        prompt = f"""You are an expert AI agent tasked with validating the quality of generated multi-agent task data.

SCENE DATA:
{json.dumps(scene_data, indent=2, ensure_ascii=False)}

AGENT CONFIGURATION:
{json.dumps(task_data.get('agents_config', []), indent=2)}

TASK TO VALIDATE:
Description: {task['task_description']}
Category: {task['task_category']}
Validation Checks: {json.dumps(task['validation_checks'], indent=2)}

VALIDATION REQUIREMENTS:
Please analyze this task and determine if it has any of these issues:

1. **Task-Validation Mismatch**: Does the validation check actually verify completion of the described task?
2. **Infeasible Task**: Can this task actually be completed given the scene objects and agent capabilities?
3. **Missing Prerequisites**: Are all required objects/tools/conditions present in the scene?
4. **Logical Inconsistencies**: Are there any logical contradictions in the task or validation?
5. **Category Mismatch**: Does the task actually belong to the specified category?

RESPONSE FORMAT:
Provide your analysis in this exact format:

ANALYSIS: [Your detailed reasoning about the task validity]

VERDICT: [VALID/INVALID]

ISSUES: [List specific issues found, or "None" if valid]

CONFIDENCE: [0.0-1.0, your confidence in this assessment]

FAILURE_TYPE: [If invalid: "task_validation_mismatch", "infeasible_task", "missing_prerequisites", "logical_inconsistency", "category_mismatch", or "multiple_issues"]
"""
        return prompt
    
    def _analyze_r1_response(self, response: str, task: Dict, scene_data: Dict) -> Tuple[bool, str, float, List[str], List[str]]:
        """
        Analyze R1 response to determine task validity.
        
        Returns:
            (success, failure_type, confidence, issues, recommendations)
        """
        try:
            # Parse R1 response
            lines = response.strip().split('\n')
            verdict = "INVALID"
            confidence = 0.5
            failure_type = "unclear"
            issues = []
            
            for line in lines:
                line = line.strip()
                if line.startswith("VERDICT:"):
                    verdict = line.split(":", 1)[1].strip()
                elif line.startswith("CONFIDENCE:"):
                    try:
                        confidence = float(line.split(":", 1)[1].strip())
                    except:
                        confidence = 0.5
                elif line.startswith("FAILURE_TYPE:"):
                    failure_type = line.split(":", 1)[1].strip()
                elif line.startswith("ISSUES:"):
                    issues_text = line.split(":", 1)[1].strip()
                    if issues_text.lower() != "none":
                        issues = [issues_text]
            
            # Determine success
            r1_success = verdict.upper() == "VALID"
            
            # Map failure types to our categories
            if r1_success:
                final_failure_type = "success"
            elif failure_type in ["task_validation_mismatch", "logical_inconsistency", "category_mismatch"]:
                final_failure_type = "data_quality"
            elif failure_type in ["infeasible_task", "missing_prerequisites"]:
                final_failure_type = "data_quality"  # Could also be scene generation issue
            else:
                final_failure_type = "unclear"
            
            # Generate recommendations
            recommendations = self._generate_recommendations(final_failure_type, issues, task)
            
            return r1_success, final_failure_type, confidence, issues, recommendations
            
        except Exception as e:
            self.logger.warning(f"Failed to parse R1 response: {e}")
            return False, "unclear", 0.0, [f"Response parsing failed: {e}"], ["Retry with clearer prompt"]
    
    def _generate_recommendations(self, failure_type: str, issues: List[str], task: Dict) -> List[str]:
        """Generate recommendations based on failure analysis."""
        recommendations = []
        
        if failure_type == "data_quality":
            recommendations.extend([
                "Review task generation prompts for clarity",
                "Improve validation check generation logic",
                "Add more examples to training prompts"
            ])
        elif failure_type == "r1_planning":
            recommendations.extend([
                "Check if R1 has sufficient context",
                "Verify R1 reasoning capabilities for this task type",
                "Consider using different reasoning approach"
            ])
        elif failure_type == "success":
            recommendations.append("Task appears valid - good quality data")
        else:
            recommendations.extend([
                "Manual review required",
                "Collect more data for analysis",
                "Consider hybrid validation approach"
            ])
            
        return recommendations


def run_r1_validation_batch(start_id: int, end_id: int, output_file: str = None) -> Dict[str, Any]:
    """
    Run R1 validation on a batch of generated tasks.
    
    Args:
        start_id: Starting task ID
        end_id: Ending task ID  
        output_file: Output file for results
        
    Returns:
        Validation results summary
    """
    logger = get_logger(__name__)
    validator = R1TaskValidator()
    
    results = []
    stats = defaultdict(int)
    
    logger.info(f"🚀 Starting R1 validation for tasks {start_id}-{end_id}")
    
    for task_id in range(start_id, end_id + 1):
        # Load task and scene data
        task_file = Path(f"data/task/{task_id:05d}_task.json")
        scene_file = Path(f"data/scene/{task_id:05d}_scene.json")
        
        if not task_file.exists() or not scene_file.exists():
            logger.warning(f"Skipping task {task_id}: missing files")
            stats['skipped'] += 1
            continue
            
        try:
            with open(task_file, 'r') as f:
                task_data = json.load(f)
            with open(scene_file, 'r') as f:
                scene_data = json.load(f)
                
            # Test each task in the file
            for task_index in range(len(task_data.get('tasks', []))):
                result = validator.validate_task_with_r1(scene_data, task_data, task_index)
                results.append(result)
                
                # Update stats
                stats['total'] += 1
                if result.r1_success:
                    stats['r1_success'] += 1
                else:
                    stats['r1_failed'] += 1
                    
                stats[f'failure_type_{result.failure_type}'] += 1
                
                logger.info(f"Task {task_id}-{task_index}: {result.failure_type} (confidence: {result.confidence:.2f})")
                
        except Exception as e:
            logger.error(f"Failed to process task {task_id}: {e}")
            stats['errors'] += 1
    
    # Generate summary
    summary = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'id_range': f"{start_id}-{end_id}",
        'statistics': dict(stats),
        'results': [
            {
                'task_id': r.task_id,
                'task_index': r.task_index,
                'task_description': r.task_description,
                'task_category': r.task_category,
                'r1_success': r.r1_success,
                'failure_type': r.failure_type,
                'confidence': r.confidence,
                'issues_found': r.issues_found,
                'recommendations': r.recommendations
            }
            for r in results
        ]
    }
    
    # Save results
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {output_file}")
    
    # Print summary
    print_validation_summary(summary)
    
    return summary


def print_validation_summary(summary: Dict[str, Any]):
    """Print a formatted summary of validation results."""
    stats = summary['statistics']
    
    print("\n" + "="*60)
    print("🎯 R1 VALIDATION RESULTS SUMMARY")
    print("="*60)
    
    print(f"📊 BASIC STATISTICS")
    print(f"   Total Tasks Tested: {stats.get('total', 0)}")
    print(f"   R1 Success: {stats.get('r1_success', 0)} ({stats.get('r1_success', 0)/max(stats.get('total', 1), 1)*100:.1f}%)")
    print(f"   R1 Failed: {stats.get('r1_failed', 0)} ({stats.get('r1_failed', 0)/max(stats.get('total', 1), 1)*100:.1f}%)")
    print(f"   Errors: {stats.get('errors', 0)}")
    print(f"   Skipped: {stats.get('skipped', 0)}")
    print()
    
    print(f"🔍 FAILURE TYPE BREAKDOWN")
    failure_types = ['success', 'data_quality', 'r1_planning', 'unclear']
    for ft in failure_types:
        count = stats.get(f'failure_type_{ft}', 0)
        if count > 0:
            percentage = count / max(stats.get('total', 1), 1) * 100
            print(f"   {ft}: {count} ({percentage:.1f}%)")
    print()
    
    # Quality assessment
    success_rate = stats.get('r1_success', 0) / max(stats.get('total', 1), 1)
    data_quality_rate = stats.get('failure_type_success', 0) / max(stats.get('total', 1), 1)
    
    print(f"🏆 QUALITY ASSESSMENT")
    if success_rate >= 0.8:
        print(f"   ✅ EXCELLENT: {success_rate*100:.1f}% R1 success rate - Ready for batch generation!")
    elif success_rate >= 0.6:
        print(f"   👍 GOOD: {success_rate*100:.1f}% R1 success rate - Consider minor improvements")
    elif success_rate >= 0.4:
        print(f"   ⚠️  FAIR: {success_rate*100:.1f}% R1 success rate - Needs improvement before batch generation")
    else:
        print(f"   ❌ POOR: {success_rate*100:.1f}% R1 success rate - Significant improvements needed")


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="Validate generated tasks using R1")
    parser.add_argument("--start-id", type=int, default=1, help="Starting task ID")
    parser.add_argument("--end-id", type=int, default=5, help="Ending task ID")
    parser.add_argument("--output", type=str, default="r1_validation_results.json", help="Output file")
    
    args = parser.parse_args()
    
    run_r1_validation_batch(args.start_id, args.end_id, args.output)


if __name__ == "__main__":
    main()
