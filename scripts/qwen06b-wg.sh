python examples/single_agent_example.py \
    --model qwen06b \
    --observation-mode global \
    --suffix qwen06b_single_wg \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=25"

python examples/centralized_agent_example.py \
    --model qwen06b \
    --observation-mode global \
    --suffix qwen06b_multi_wg \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=25"
