# OmniEmbodied Project Cost Analysis Report

## Executive Summary

Based on the codebase analysis and DeepSeek pricing structure, this report provides detailed cost estimates for data generation and baseline evaluation in the OmniEmbodied project.

## DeepSeek Pricing (Optimized Hours: 00:30-08:30 Beijing Time)

### Model Pricing
- **deepseek-chat**: 
  - Input (cache miss): ¥1/M tokens (50% off)
  - Input (cache hit): ¥0.25/M tokens (50% off)
  - Output: ¥4/M tokens (50% off)

- **deepseek-reasoner**:
  - Input (cache miss): ¥1/M tokens (75% off)
  - Input (cache hit): ¥0.25/M tokens (75% off)  
  - Output: ¥4/M tokens (75% off)

## Data Generation Pipeline Cost Analysis

### 1. Scene Generation (Per Scene)

**Prompt Structure Analysis:**
- System prompt: ~8,000 tokens (detailed scene architecture instructions)
- User prompt template: ~1,000 tokens
- Clue input: ~500 tokens
- Agent abilities list: ~2,000 tokens
- **Total input per scene: ~11,500 tokens**

**Output Analysis:**
- Scene JSON output: ~6,000-8,000 tokens (detailed scene with objects, rooms, abilities)
- **Average output per scene: ~7,000 tokens**

**Two-round generation process:**
- Round 1: 11,500 input + 7,000 output = 18,500 tokens
- Round 2 (refinement): 11,500 + 7,000 (previous) + 7,000 (new) = 25,500 tokens
- **Total per scene: ~44,000 tokens**

**Cost per scene (optimized hours):**
- Input: 23,000 tokens × ¥1/M = ¥0.023
- Output: 14,000 tokens × ¥4/M = ¥0.056
- **Total per scene: ¥0.079 (~8 cents)**

### 2. Task Generation (Per Scene)

**Prompt Structure:**
- System prompt: ~6,000 tokens (task generation instructions)
- Scene JSON input: ~7,000 tokens
- Agent abilities: ~2,000 tokens
- **Total input: ~15,000 tokens**

**Output:**
- Task suite with 14 tasks (7 categories × 2): ~4,000 tokens
- **Total output: ~4,000 tokens**

**Cost per scene (optimized hours):**
- Input: 15,000 tokens × ¥1/M = ¥0.015
- Output: 4,000 tokens × ¥4/M = ¥0.016
- **Total per scene: ¥0.031 (~3 cents)**

### 3. Clue Generation (Per Scene)

**Prompt Structure:**
- System prompt: ~3,000 tokens
- Raw text input: ~1,000 tokens
- **Total input: ~4,000 tokens**

**Output:**
- Conceptual clue: ~800 tokens
- **Total output: ~800 tokens**

**Cost per scene (optimized hours):**
- Input: 4,000 tokens × ¥1/M = ¥0.004
- Output: 800 tokens × ¥4/M = ¥0.0032
- **Total per scene: ¥0.0072 (~0.7 cents)**

### Total Data Generation Cost Per Scene
- Clue generation: ¥0.007
- Scene generation: ¥0.079
- Task generation: ¥0.031
- **Total per scene: ¥0.117 (~12 cents)**

## Baseline Evaluation Cost Analysis

### Single Agent Trajectory Analysis

Based on execution logs analysis:
- Average steps per task: 10-15 steps
- Average LLM interactions per task: 10-15 calls
- Max steps limit: 20-30 steps

### Prompt Structure for Each LLM Call

**System Prompt:**
- Agent role and capabilities: ~2,000 tokens
- Available actions description: ~3,564 tokens (from code)
- Behavior guidelines: ~1,000 tokens
- **System prompt total: ~6,564 tokens**

**User Prompt per step:**
- Current task description: ~100 tokens
- Environment description: ~2,000-4,000 tokens (varies by detail level)
- Agent status (location, inventory): ~300 tokens
- History summary: ~500-1,500 tokens (grows with steps)
- **User prompt average: ~3,000 tokens**

**Total input per LLM call: ~9,564 tokens**

**Output per call:**
- JSON response (thought, action, reason): ~200 tokens
- **Output per call: ~200 tokens**

### Cost Per Trajectory

**Average trajectory (12 LLM calls):**
- Input: 12 × 9,564 = 114,768 tokens
- Output: 12 × 200 = 2,400 tokens
- **Total: ~117,168 tokens per trajectory**

**Cost per trajectory (optimized hours):**
- Input: 114,768 tokens × ¥1/M = ¥0.115
- Output: 2,400 tokens × ¥4/M = ¥0.0096
- **Total per trajectory: ¥0.125 (~13 cents)**

### Multi-Agent Trajectory Cost

**Centralized mode:**
- Coordinator calls: Similar to single agent
- **Cost per trajectory: ~¥0.125**

**Decentralized mode:**
- 2 agents × single agent cost = 2 × ¥0.125 = ¥0.25
- Communication overhead: +20%
- **Cost per trajectory: ~¥0.30**

## Batch Processing Cost Estimates

### Data Generation (1000 scenes)
- 1000 scenes × ¥0.117 = **¥117 (~$16)**

### Baseline Evaluation
**Single Agent (1000 trajectories):**
- 1000 trajectories × ¥0.125 = **¥125 (~$17)**

**Multi-Agent Centralized (1000 trajectories):**
- 1000 trajectories × ¥0.125 = **¥125 (~$17)**

**Multi-Agent Decentralized (1000 trajectories):**
- 1000 trajectories × ¥0.30 = **¥300 (~$41)**

## Cost Optimization Strategies

### 1. Time-based Optimization
- **Use optimized hours (00:30-08:30 Beijing)** for 50-75% cost reduction
- Schedule batch processing during off-peak hours

### 2. Caching Optimization
- Enable context caching for repeated prompts
- Cache hit rate can reduce input costs by 75%

### 3. Prompt Engineering
- Optimize prompt length while maintaining quality
- Use more concise environment descriptions for simple tasks

### 4. Batch Processing
- Process multiple items in parallel during optimized hours
- Use pipeline mode for efficient resource utilization

## Summary

**Per Unit Costs (Optimized Hours):**
- Data generation per scene: ¥0.117 (~12 cents)
- Single agent trajectory: ¥0.125 (~13 cents)
- Multi-agent trajectory: ¥0.125-0.30 (~13-30 cents)

**Recommended Budget for 1000 scenes + evaluation:**
- Data generation: ¥117 (~$16)
- Single agent evaluation: ¥125 (~$17)
- Multi-agent evaluation: ¥125-300 (~$17-41)
- **Total project budget: ¥367-542 (~$50-75)**

The project is highly cost-effective when using DeepSeek during optimized hours, making it feasible for large-scale experimentation and evaluation.
