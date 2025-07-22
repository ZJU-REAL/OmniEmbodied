python examples/single_agent_example.py \
    --model llama8b \
    --observation-mode explore \
    --suffix qwen3b_single_test \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=40"

python examples/centralized_agent_example.py \
    --model llama8b \
    --observation-mode explore \
    --suffix qwen3b_centralized_test \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=40"