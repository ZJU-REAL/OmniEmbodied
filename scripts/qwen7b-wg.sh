python examples/single_agent_example.py \
    --model qwen7b \
    --observation-mode global \
    --suffix qwen7b_single_wg \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=20"

python examples/centralized_agent_example.py \
    --model qwen7b \
    --observation-mode global \
    --suffix qwen7b_multi_wg \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=20"
