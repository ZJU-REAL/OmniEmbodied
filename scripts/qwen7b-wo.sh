python examples/single_agent_example.py \
    --model qwen7b \
    --observation-mode explore \
    --suffix qwen7b_single_wo \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=20"

python examples/centralized_agent_example.py \
    --model qwen7b \
    --observation-mode explore \
    --suffix qwen7b_centralized_wo \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=20"
