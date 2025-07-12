#!/usr/bin/env python3
"""
Badcase Analysis Script for Data Quality Validation

This script implements the workflow you described:
1. Test a small sample of tasks with R1 (deepseek-reasoner)
2. For R1 successes: likely good quality data
3. For R1 failures: analyze if it's data quality issues or R1 planning errors
4. Generate recommendations for batch generation readiness

Usage:
    python3 badcase_analysis.py --sample-size 10 --output badcase_report.json
"""

import json
import argparse
import time
import random
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import openai

from utils.logger import get_logger


@dataclass
class TaskSample:
    """A single task sample for testing."""
    scene_id: str
    task_index: int
    task_description: str
    task_category: str
    validation_checks: List[Dict]
    scene_data: Dict
    task_data: Dict


@dataclass
class BadcaseResult:
    """Result of badcase analysis for a single task."""
    scene_id: str
    task_index: int
    task_description: str
    task_category: str
    
    # R1 test results
    r1_success: bool
    r1_response: str
    r1_error: str
    
    # Analysis results
    issue_type: str  # 'good_quality', 'data_quality_issue', 'r1_planning_error', 'unclear'
    confidence: float  # 0-1, confidence in classification
    specific_issues: List[str]
    recommendations: List[str]


class BadcaseAnalyzer:
    """Analyzes data quality using R1 validation on a sample."""
    
    def __init__(self, api_key: str = None, endpoint: str = None):
        """Initialize badcase analyzer."""
        self.logger = get_logger(__name__)
        
        # R1 configuration - using your provided API endpoint
        self.api_key = api_key or "sk-68143b8311d24fd08c1bd1d1acd96e99"
        self.endpoint = endpoint or "https://api.deepseek.com"
        
        # Initialize OpenAI client for R1
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.endpoint
        )
        
        self.logger.info(f"Initialized BadcaseAnalyzer with endpoint: {self.endpoint}")
    
    def collect_sample(self, sample_size: int = 10, start_id: int = 1, end_id: int = 50) -> List[TaskSample]:
        """
        Collect a random sample of tasks for testing.
        
        Args:
            sample_size: Number of tasks to sample
            start_id: Starting scene ID
            end_id: Ending scene ID
            
        Returns:
            List of TaskSample objects
        """
        self.logger.info(f"Collecting sample of {sample_size} tasks from scenes {start_id}-{end_id}")
        
        # Find all available task files
        available_tasks = []
        for scene_id in range(start_id, end_id + 1):
            task_file = Path(f"data/task/{scene_id:05d}_task.json")
            scene_file = Path(f"data/scene/{scene_id:05d}_scene.json")
            
            if task_file.exists() and scene_file.exists():
                try:
                    with open(task_file, 'r') as f:
                        task_data = json.load(f)
                    with open(scene_file, 'r') as f:
                        scene_data = json.load(f)
                    
                    # Add each task in the file
                    for task_index, task in enumerate(task_data.get('tasks', [])):
                        available_tasks.append(TaskSample(
                            scene_id=f"{scene_id:05d}",
                            task_index=task_index,
                            task_description=task['task_description'],
                            task_category=task['task_category'],
                            validation_checks=task['validation_checks'],
                            scene_data=scene_data,
                            task_data=task_data
                        ))
                        
                except Exception as e:
                    self.logger.warning(f"Failed to load scene {scene_id}: {e}")
        
        self.logger.info(f"Found {len(available_tasks)} total tasks")
        
        # Random sample
        if len(available_tasks) <= sample_size:
            sample = available_tasks
        else:
            sample = random.sample(available_tasks, sample_size)
        
        self.logger.info(f"Selected {len(sample)} tasks for analysis")
        return sample
    
    def test_task_with_r1(self, task_sample: TaskSample) -> BadcaseResult:
        """
        Test a single task with R1 and analyze the result.
        
        Args:
            task_sample: Task to test
            
        Returns:
            BadcaseResult with analysis
        """
        self.logger.info(f"Testing task {task_sample.scene_id}-{task_sample.task_index} with R1")
        
        # Create R1 test prompt
        prompt = self._create_r1_prompt(task_sample)
        
        try:
            # Call R1
            response = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=4096
            )
            
            response_text = response.choices[0].message.content
            
            # Analyze R1 response
            r1_success, issue_type, confidence, issues, recommendations = self._analyze_r1_response(
                response_text, task_sample
            )
            
            return BadcaseResult(
                scene_id=task_sample.scene_id,
                task_index=task_sample.task_index,
                task_description=task_sample.task_description,
                task_category=task_sample.task_category,
                r1_success=r1_success,
                r1_response=response_text,
                r1_error="",
                issue_type=issue_type,
                confidence=confidence,
                specific_issues=issues,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"R1 test failed for task {task_sample.scene_id}-{task_sample.task_index}: {e}")
            return BadcaseResult(
                scene_id=task_sample.scene_id,
                task_index=task_sample.task_index,
                task_description=task_sample.task_description,
                task_category=task_sample.task_category,
                r1_success=False,
                r1_response="",
                r1_error=str(e),
                issue_type='unclear',
                confidence=0.0,
                specific_issues=[f"R1 API call failed: {e}"],
                recommendations=["Check API configuration", "Retry test"]
            )
    
    def _create_r1_prompt(self, task_sample: TaskSample) -> str:
        """Create prompt for R1 to test task validity."""
        
        prompt = f"""You are an expert AI agent evaluating the quality of generated multi-agent task data.

SCENE DATA:
{json.dumps(task_sample.scene_data, indent=2, ensure_ascii=False)}

AGENT CONFIGURATION:
{json.dumps(task_sample.task_data.get('agents_config', []), indent=2)}

TASK TO EVALUATE:
Description: {task_sample.task_description}
Category: {task_sample.task_category}
Validation Checks: {json.dumps(task_sample.validation_checks, indent=2)}

EVALUATION CRITERIA:
Please carefully analyze this task and determine if it has any quality issues:

1. **Task-Validation Mismatch**: Do the validation checks actually verify completion of the described task?
2. **Infeasible Task**: Can this task be completed given the scene objects and agent capabilities?
3. **Missing Prerequisites**: Are all required objects/tools/conditions present in the scene?
4. **Logical Inconsistencies**: Are there logical contradictions in the task or validation?
5. **Category Mismatch**: Does the task belong to the specified category?

RESPONSE FORMAT:
Provide your analysis in this exact format:

ANALYSIS: [Your detailed reasoning about the task quality]

VERDICT: [VALID/INVALID]

ISSUES: [List specific issues found, or "None" if valid]

CONFIDENCE: [0.0-1.0, your confidence in this assessment]

ISSUE_TYPE: [If invalid: "task_validation_mismatch", "infeasible_task", "missing_prerequisites", "logical_inconsistency", "category_mismatch", or "multiple_issues"]
"""
        return prompt
    
    def _analyze_r1_response(self, response: str, task_sample: TaskSample) -> Tuple[bool, str, float, List[str], List[str]]:
        """
        Analyze R1 response to classify the issue type.
        
        Returns:
            (r1_success, issue_type, confidence, specific_issues, recommendations)
        """
        try:
            # Parse R1 response
            lines = response.strip().split('\n')
            verdict = "INVALID"
            confidence = 0.5
            issue_type_raw = "unclear"
            issues_text = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith("VERDICT:"):
                    verdict = line.split(":", 1)[1].strip()
                elif line.startswith("CONFIDENCE:"):
                    try:
                        confidence = float(line.split(":", 1)[1].strip())
                    except:
                        confidence = 0.5
                elif line.startswith("ISSUE_TYPE:"):
                    issue_type_raw = line.split(":", 1)[1].strip()
                elif line.startswith("ISSUES:"):
                    issues_text = line.split(":", 1)[1].strip()
            
            # Determine R1 success
            r1_success = verdict.upper() == "VALID"
            
            # Classify issue type according to your framework
            if r1_success:
                issue_type = "good_quality"
                specific_issues = []
            else:
                # Distinguish between data quality issues and potential R1 planning errors
                if issue_type_raw in ["task_validation_mismatch", "logical_inconsistency", "category_mismatch"]:
                    issue_type = "data_quality_issue"
                elif issue_type_raw in ["infeasible_task", "missing_prerequisites"]:
                    # These could be data quality OR scene generation issues
                    # For now, classify as data quality issues
                    issue_type = "data_quality_issue"
                elif confidence < 0.6:
                    # Low confidence might indicate R1 planning issues
                    issue_type = "r1_planning_error"
                else:
                    issue_type = "unclear"
                
                specific_issues = [issues_text] if issues_text.lower() != "none" else []
            
            # Generate recommendations
            recommendations = self._generate_recommendations(issue_type, specific_issues, task_sample)
            
            return r1_success, issue_type, confidence, specific_issues, recommendations
            
        except Exception as e:
            self.logger.warning(f"Failed to parse R1 response: {e}")
            return False, "unclear", 0.0, [f"Response parsing failed: {e}"], ["Retry with clearer prompt"]
    
    def _generate_recommendations(self, issue_type: str, issues: List[str], task_sample: TaskSample) -> List[str]:
        """Generate specific recommendations based on issue type."""
        recommendations = []
        
        if issue_type == "good_quality":
            recommendations.append("Task appears valid - good quality data")
        elif issue_type == "data_quality_issue":
            recommendations.extend([
                "Review task generation prompts for this category",
                "Improve validation check generation logic",
                "Add more examples to training data",
                f"Focus on {task_sample.task_category} category improvements"
            ])
        elif issue_type == "r1_planning_error":
            recommendations.extend([
                "R1 may have insufficient context or reasoning capability",
                "Consider manual review of this task",
                "Verify R1 prompt clarity",
                "Test with different reasoning approach"
            ])
        else:
            recommendations.extend([
                "Manual review required",
                "Collect more data for analysis",
                "Consider hybrid validation approach"
            ])
            
        return recommendations


def run_badcase_analysis(sample_size: int = 10, output_file: str = None) -> Dict[str, Any]:
    """
    Run badcase analysis on a sample of generated tasks.
    
    Args:
        sample_size: Number of tasks to sample and test
        output_file: Output file for results
        
    Returns:
        Analysis results summary
    """
    logger = get_logger(__name__)
    analyzer = BadcaseAnalyzer()
    
    logger.info(f"🚀 Starting badcase analysis with sample size {sample_size}")
    
    # Collect sample
    sample = analyzer.collect_sample(sample_size)
    if not sample:
        logger.error("No tasks found for analysis")
        return {}
    
    # Test each task
    results = []
    stats = defaultdict(int)
    
    for task_sample in sample:
        result = analyzer.test_task_with_r1(task_sample)
        results.append(result)
        
        # Update stats
        stats['total'] += 1
        stats[f'issue_type_{result.issue_type}'] += 1
        if result.r1_success:
            stats['r1_success'] += 1
        else:
            stats['r1_failed'] += 1
        
        logger.info(f"Task {result.scene_id}-{result.task_index}: {result.issue_type} (confidence: {result.confidence:.2f})")
    
    # Generate summary
    summary = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'sample_size': len(results),
        'statistics': dict(stats),
        'results': [asdict(r) for r in results],
        'quality_assessment': _assess_batch_readiness(stats),
        'recommendations': _generate_batch_recommendations(stats, results)
    }
    
    # Save results
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {output_file}")
    
    # Print summary
    print_badcase_summary(summary)
    
    return summary


def _assess_batch_readiness(stats: Dict[str, int]) -> Dict[str, Any]:
    """Assess readiness for batch generation based on stats."""
    total = stats.get('total', 0)
    if total == 0:
        return {'ready': False, 'confidence': 0.0, 'reason': 'No data'}
    
    good_quality_rate = stats.get('issue_type_good_quality', 0) / total
    data_issue_rate = stats.get('issue_type_data_quality_issue', 0) / total
    r1_error_rate = stats.get('issue_type_r1_planning_error', 0) / total
    
    # Decision logic based on your requirements
    if good_quality_rate >= 0.7:
        ready = True
        confidence = 0.9
        reason = f"High quality rate ({good_quality_rate*100:.1f}%)"
    elif good_quality_rate >= 0.5 and data_issue_rate <= 0.3:
        ready = True
        confidence = 0.7
        reason = f"Acceptable quality with manageable issues"
    elif data_issue_rate >= 0.5:
        ready = False
        confidence = 0.8
        reason = f"High data quality issue rate ({data_issue_rate*100:.1f}%)"
    else:
        ready = False
        confidence = 0.6
        reason = "Mixed results require further investigation"
    
    return {
        'ready': ready,
        'confidence': confidence,
        'reason': reason,
        'good_quality_rate': round(good_quality_rate * 100, 1),
        'data_issue_rate': round(data_issue_rate * 100, 1),
        'r1_error_rate': round(r1_error_rate * 100, 1)
    }


def _generate_batch_recommendations(stats: Dict[str, int], results: List[BadcaseResult]) -> List[str]:
    """Generate recommendations for batch generation."""
    recommendations = []
    assessment = _assess_batch_readiness(stats)
    
    if assessment['ready']:
        recommendations.append("✅ Ready for batch generation!")
        recommendations.append("Consider addressing any specific issues found in failed cases")
    else:
        recommendations.append("❌ Not ready for batch generation")
        recommendations.append("Address data quality issues before scaling up")
        
        # Specific recommendations based on failure patterns
        data_issues = [r for r in results if r.issue_type == 'data_quality_issue']
        if data_issues:
            categories = set(r.task_category for r in data_issues)
            recommendations.append(f"Focus on improving these categories: {', '.join(categories)}")
    
    return recommendations


def print_badcase_summary(summary: Dict[str, Any]):
    """Print a formatted summary of badcase analysis."""
    stats = summary['statistics']
    assessment = summary['quality_assessment']
    
    print("\n" + "="*60)
    print("🔍 BADCASE ANALYSIS RESULTS")
    print("="*60)
    
    print(f"📊 SAMPLE ANALYSIS")
    print(f"   Sample Size: {summary['sample_size']}")
    print(f"   R1 Success: {stats.get('r1_success', 0)} ({stats.get('r1_success', 0)/max(summary['sample_size'], 1)*100:.1f}%)")
    print(f"   R1 Failed: {stats.get('r1_failed', 0)} ({stats.get('r1_failed', 0)/max(summary['sample_size'], 1)*100:.1f}%)")
    print()
    
    print(f"🎯 ISSUE TYPE BREAKDOWN")
    issue_types = ['good_quality', 'data_quality_issue', 'r1_planning_error', 'unclear']
    for it in issue_types:
        count = stats.get(f'issue_type_{it}', 0)
        if count > 0:
            percentage = count / max(summary['sample_size'], 1) * 100
            print(f"   {it}: {count} ({percentage:.1f}%)")
    print()
    
    print(f"🚀 BATCH GENERATION READINESS")
    print(f"   Ready: {'✅ YES' if assessment['ready'] else '❌ NO'}")
    print(f"   Confidence: {assessment['confidence']:.1f}")
    print(f"   Reason: {assessment['reason']}")
    print()
    
    print(f"💡 RECOMMENDATIONS")
    for rec in summary['recommendations']:
        print(f"   • {rec}")


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="Run badcase analysis on generated tasks")
    parser.add_argument("--sample-size", type=int, default=10, help="Number of tasks to sample")
    parser.add_argument("--output", type=str, default="badcase_analysis_results.json", help="Output file")
    
    args = parser.parse_args()
    
    run_badcase_analysis(args.sample_size, args.output)


if __name__ == "__main__":
    main()
