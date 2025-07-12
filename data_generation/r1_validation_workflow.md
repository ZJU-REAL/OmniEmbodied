# R1 Validation Workflow Guide

## 🎯 Overview

This workflow helps you validate generated task data quality using R1 (reasoning model) before batch generation.

## 📋 Step-by-Step Process

### Step 1: Generate Small Sample
```bash
# Generate a small sample (5-10 tasks) with your current configuration
python3 pipeline.py --start-id 12 --end-id 16 --threads 1
```

### Step 2: Run R1 Validation
```bash
# Test the generated tasks with R1
python3 validate_with_r1.py --start-id 12 --end-id 16 --output r1_results_12_16.json
```

### Step 3: Analyze Data Quality
```bash
# Analyze the R1 results to assess data quality
python3 analyze_data_quality.py --input r1_results_12_16.json --report quality_report_12_16.md --print
```

### Step 4: Make Decision
Based on the quality report:
- **Grade A/B + Ready for Batch**: Proceed with large-scale generation
- **Grade C/D/F**: Improve generation before batch processing

## 🔍 Understanding R1 Validation Results

### Success Indicators
- **R1 Success Rate > 80%**: Excellent data quality
- **Data Quality Issues < 20%**: Good task-validation correspondence
- **High Confidence Assessments > 70%**: Reliable R1 evaluations

### Failure Types
1. **data_quality**: Issues with your generated data
   - Task-validation mismatch
   - Logical inconsistencies
   - Category mismatches

2. **r1_planning**: R1 reasoning issues (less concerning)
   - R1 misunderstood the task
   - R1 planning limitations

3. **unclear**: Ambiguous cases requiring manual review

## 🛠️ Improvement Strategies

### For Data Quality Issues

#### Task-Validation Mismatch
```yaml
# Improve task_gen_config.yaml
system_prompt: |
  ...
  **Critical**: For each task, ensure the validation_checks EXACTLY verify 
  the completion of the described action. The validation must be the minimal, 
  necessary change that occurs when the task is completed.
```

#### Category Mismatches
```yaml
# Add explicit category examples
system_prompt: |
  ...
  **Examples by Category:**
  - direct_command: "Place cup_1 on table_1" → location_id change
  - attribute_reasoning: "Find the red mug" → requires attribute matching
  - tool_use: "Repair the broken radio" → requires tool + state change
```

#### Logical Inconsistencies
```yaml
# Add consistency checks
system_prompt: |
  ...
  **Consistency Rules:**
  1. All referenced objects must exist in the scene
  2. All required tools/abilities must be available
  3. Agent capabilities must be sufficient for the task
```

### For R1 Assessment Issues

#### Low Confidence Rates
- Improve R1 prompt clarity
- Add more context about scene and agents
- Consider multiple R1 evaluations per task

#### High R1 Planning Failures
- Verify R1 has sufficient reasoning capability
- Consider using different validation approach
- Manual review of R1 "failures"

## 📊 Quality Thresholds

### Batch Generation Decision Matrix

| Overall Grade | R1 Success Rate | Data Quality Issues | Decision |
|---------------|-----------------|-------------------|----------|
| A (85-100)    | >80%           | <15%              | ✅ Proceed |
| B (75-84)     | >70%           | <25%              | ✅ Proceed |
| C (65-74)     | >60%           | <35%              | ⚠️ Improve first |
| D (50-64)     | >40%           | <50%              | ❌ Significant improvement needed |
| F (<50)       | <40%           | >50%              | ❌ Major revision required |

## 🔄 Iterative Improvement Process

### Iteration 1: Baseline Assessment
1. Generate 5-10 tasks
2. Run R1 validation
3. Identify major issues
4. Get baseline quality score

### Iteration 2: Targeted Improvements
1. Address highest-priority issues from analysis
2. Generate new sample with same IDs (overwrite)
3. Re-run R1 validation
4. Compare improvement

### Iteration 3: Validation
1. Generate fresh sample (new IDs)
2. Confirm improvements are consistent
3. Make final decision on batch generation

## 🚀 Example Workflow

```bash
# Complete workflow example
echo "🎯 Starting R1 validation workflow..."

# Step 1: Generate sample
echo "📝 Generating sample tasks..."
python3 pipeline.py --start-id 20 --end-id 24 --threads 1

# Step 2: R1 validation
echo "🤖 Running R1 validation..."
python3 validate_with_r1.py --start-id 20 --end-id 24 --output r1_validation.json

# Step 3: Quality analysis
echo "📊 Analyzing data quality..."
python3 analyze_data_quality.py --input r1_validation.json --report quality_report.md --print

# Step 4: Decision
echo "🎯 Check quality_report.md for recommendations"
echo "✅ If Grade A/B: proceed with batch generation"
echo "⚠️ If Grade C/D/F: implement recommendations and retry"
```

## 📈 Monitoring Batch Generation

Once you start batch generation, periodically validate quality:

```bash
# Validate every 50 tasks during batch generation
python3 validate_with_r1.py --start-id 100 --end-id 104 --output batch_check.json
python3 analyze_data_quality.py --input batch_check.json --print
```

## 🔧 Troubleshooting

### Common Issues

#### R1 API Errors
- Check API key and endpoint configuration
- Verify model availability (deepseek-reasoner)
- Monitor rate limits

#### Low R1 Success Rates
- Review R1 prompt for clarity
- Check if tasks are genuinely problematic
- Consider manual validation of R1 "failures"

#### Inconsistent Results
- Run multiple R1 evaluations per task
- Check for prompt ambiguity
- Verify scene data quality

### Configuration Tuning

#### R1 Model Settings
```python
r1_config = {
    'model': 'deepseek-reasoner',
    'temperature': 0.1,  # Low for consistent evaluation
    'max_tokens': 4096   # Sufficient for detailed analysis
}
```

#### Validation Thresholds
Adjust based on your quality requirements:
- Research prototype: 60% success rate acceptable
- Production system: 80%+ success rate required
- Critical applications: 90%+ success rate required

## 📝 Best Practices

1. **Start Small**: Always validate with 5-10 tasks first
2. **Iterate Quickly**: Make targeted improvements based on analysis
3. **Document Changes**: Track what improvements work
4. **Monitor Trends**: Watch for quality degradation over time
5. **Manual Review**: Spot-check R1 assessments for accuracy
6. **Backup Strategy**: Keep rule-based validation as fallback

## 🎯 Success Criteria

Your data is ready for batch generation when:
- ✅ Overall quality grade A or B
- ✅ R1 success rate > 70%
- ✅ Data quality issues < 25%
- ✅ High confidence in R1 assessments
- ✅ Consistent results across multiple samples
