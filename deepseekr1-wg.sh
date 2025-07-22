python examples/single_agent_example.py \
    --model deepseekr1 \
    --observation-mode global \
    --suffix deepseekr1_single_global_test \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=20"

python examples/centralized_agent_example.py \
    --model deepseekr1 \
    --observation-mode global \
    --suffix deepseekr1_centralized_global_test \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=20"
