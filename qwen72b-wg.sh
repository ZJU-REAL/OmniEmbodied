python examples/single_agent_example.py \
    --model qwen72b \
    --observation-mode global \
    --suffix qwen72b_single_wo \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=4"

python examples/centralized_agent_example.py \
    --model bailian \
    --observation-mode global \
    --suffix qwen72b_multi_wo \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=4"
