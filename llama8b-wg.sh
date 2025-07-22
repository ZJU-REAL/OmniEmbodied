python examples/single_agent_example.py \
    --model llama8b \
    --observation-mode global \
    --suffix llama8b_single_global_test \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=40"

python examples/centralized_agent_example.py \
    --model llama8b \
    --observation-mode global \
    --suffix llama8b_centralized_global_test \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=40"