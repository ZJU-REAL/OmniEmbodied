python examples/single_agent_example.py \
    --model deepseekr1 \
    --observation-mode explore \
    --suffix deepseekr1_single_wo \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=30"

python examples/centralized_agent_example.py \
    --model deepseekr1 \
    --observation-mode explore \
    --suffix deepseekr1_multi_wo \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=30"
