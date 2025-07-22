python examples/single_agent_example.py \
    --model qwen3b \
    --observation-mode global \
    --suffix qwen3b_single_test \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=76"

python examples/centralized_agent_example.py \
    --model qwen7b \
    --observation-mode global \
    --suffix qwen3b_centralized_test \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=76"
