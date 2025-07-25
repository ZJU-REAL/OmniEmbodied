python examples/single_agent_example.py \
    --model qwen06b \
    --observation-mode explore \
    --suffix qwen06b_single_wo \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=40"

python examples/centralized_agent_example.py \
    --model qwen06b \
    --observation-mode explore \
    --suffix qwen06b_multi_wo \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=40"
