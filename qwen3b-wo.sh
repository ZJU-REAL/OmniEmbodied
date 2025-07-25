python examples/single_agent_example.py \
    --model qwen3b \
    --observation-mode explore \
    --suffix qwen3b_single_wo \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=25"

python examples/centralized_agent_example.py \
    --model qwen3b \
    --observation-mode explore \
    --suffix qwen3b_multi_wo \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=25"
