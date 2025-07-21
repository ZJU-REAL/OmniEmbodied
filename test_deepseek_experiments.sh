#!/bin/bash

# DeepSeek模型实验脚本 - 4个实验：单智能体(全局/部分) + Centralized(全局/部分)
# 并发数：1 (API限制)

set -e

echo "🚀 开始DeepSeek实验..."

# 实验配置
MODEL="deepseek"
PARALLEL=10

# 运行实验
run_exp() {
    local name="$1"
    local script="$2"
    local mode="$3"
    local suffix="$4"

    echo "📋 实验: $name"
    python $script --model $MODEL --observation-mode $mode --suffix $suffix --parallel \
        --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=$PARALLEL"
    echo "✅ 完成: $name"
    echo ""
}

# 4个实验
run_exp "单智能体-全局观察" "examples/single_agent_example.py" "global" "${MODEL}_single_global"
# run_exp "单智能体-部分观察" "examples/single_agent_example.py" "explore" "${MODEL}_single_explore"
# run_exp "Centralized-全局观察" "examples/centralized_agent_example.py" "global" "${MODEL}_centralized_global"
# run_exp "Centralized-部分观察" "examples/centralized_agent_example.py" "explore" "${MODEL}_centralized_explore"

echo "🎉 所有DeepSeek实验完成！"
echo "📁 结果保存在 output/ 目录中"
