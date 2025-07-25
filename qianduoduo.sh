python examples/single_agent_example.py \
    --model volcengine \
    --observation-mode explore \
    --suffix qianduoduo_4o_wo_single \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=20"

python examples/centralized_agent_example.py \
    --model volcengine \
    --observation-mode explore \
    --suffix qianduoduo_2.5-flash_wo_multi \
    --parallel \
    --config-override "parallel_evaluation.scenario_parallelism.max_parallel_scenarios=40"