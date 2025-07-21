#!/bin/bash

# 快速验证脚本功能

echo "🔍 验证实验脚本..."

# 检查脚本文件
if [[ -f "test_qwen3b_experiments.sh" && -x "test_qwen3b_experiments.sh" ]]; then
    echo "✅ Qwen3B脚本存在且可执行"
else
    echo "❌ Qwen3B脚本问题"
    exit 1
fi

if [[ -f "test_deepseek_experiments.sh" && -x "test_deepseek_experiments.sh" ]]; then
    echo "✅ DeepSeek脚本存在且可执行"
else
    echo "❌ DeepSeek脚本问题"
    exit 1
fi

# 检查Python环境
if python -c "import yaml, openai" 2>/dev/null; then
    echo "✅ Python环境正常"
else
    echo "❌ Python环境问题"
    exit 1
fi

# 测试便捷参数
if python examples/single_agent_example.py --help | grep -q "model\|observation-mode"; then
    echo "✅ 便捷参数功能正常"
else
    echo "❌ 便捷参数功能异常"
    exit 1
fi

echo "🎉 所有验证通过！可以开始实验了"
echo ""
echo "使用方法："
echo "  ./test_qwen3b_experiments.sh"
echo "  ./test_deepseek_experiments.sh"
