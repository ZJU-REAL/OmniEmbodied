python examples/single_agent_example.py \
    --model deepseekv3 \
    --observation-mode explore \
    --suffix deepseekv3_single_explore_test \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=20"

python examples/centralized_agent_example.py \
    --model deepseekv3 \
    --observation-mode explore \
    --suffix deepseekv3_centralized_explore_test \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=20"
