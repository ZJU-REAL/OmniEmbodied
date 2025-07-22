python examples/single_agent_example.py \
    --model deepseekr1 \
    --observation-mode explore \
    --suffix deepseekr1_single_explore_test \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=20"

python examples/centralized_agent_example.py \
    --model deepseekr1 \
    --observation-mode explore \
    --suffix deepseekr1_centralized_explore_test \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=20"
