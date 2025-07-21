# 实验脚本使用说明

## 脚本文件

- `test_qwen3b_experiments.sh` - Qwen3B模型实验 (并发70)
- `test_deepseek_experiments.sh` - DeepSeek模型实验 (并发1)

## 实验内容

每个脚本运行4个实验：

| 实验 | 智能体类型 | 观察模式 | 后缀 |
|------|------------|----------|------|
| 1 | Single Agent | 全局观察 | `{model}_single_global` |
| 2 | Single Agent | 部分观察 | `{model}_single_explore` |
| 3 | Centralized | 全局观察 | `{model}_centralized_global` |
| 4 | Centralized | 部分观察 | `{model}_centralized_explore` |

## 使用方法

```bash
# 运行Qwen3B实验
./test_qwen3b_experiments.sh

# 运行DeepSeek实验
./test_deepseek_experiments.sh

# 并行运行
./test_qwen3b_experiments.sh &
./test_deepseek_experiments.sh &
wait
```

## 输出结果

结果保存在 `output/` 目录中，每个实验有独立的时间戳目录：

```
output/
├── {timestamp}_single_independent_{scenarios}_{model}_single_global/
├── {timestamp}_single_independent_{scenarios}_{model}_single_explore/
├── {timestamp}_centralized_independent_{scenarios}_{model}_centralized_global/
└── {timestamp}_centralized_independent_{scenarios}_{model}_centralized_explore/
```

关键文件：
- `run_summary.json` - 运行摘要
- `experiment_config.yaml` - 实验配置
- `trajectories/` - 执行轨迹
- `llm_qa/` - LLM交互记录

## 注意事项

- **Qwen3B**: 本地部署，高并发，资源消耗大
- **DeepSeek**: 云端API，低并发，需要稳定网络
- **存储**: 确保有足够磁盘空间存储结果
- **权限**: 确保脚本有执行权限 `chmod +x test_*.sh`
