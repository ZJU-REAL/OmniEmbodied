#!/bin/bash

echo "==================================="
echo "    数据集矫正工具启动脚本"
echo "==================================="

# 检查Node.js是否安装
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到Node.js，请先安装Node.js"
    echo "   下载地址: https://nodejs.org/"
    exit 1
fi

# 检查npm是否安装
if ! command -v npm &> /dev/null; then
    echo "❌ 错误: 未找到npm，请先安装npm"
    exit 1
fi

echo "✅ Node.js版本: $(node --version)"
echo "✅ npm版本: $(npm --version)"
echo ""

# 检查是否存在node_modules
if [ ! -d "node_modules" ]; then
    echo "📦 正在安装依赖..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
    echo "✅ 依赖安装完成"
    echo ""
fi

# 检查数据文件是否存在
echo "🔍 检查数据文件..."

SINGLE_CSV="../raw_output/20250723_220044_single_independent_00001_to_00800_qianduoduo_4o_wo_single/subtask_execution_log.csv"
MULTI_CSV="../raw_output/20250723_225455_multi_independent_00001_to_00600_qianduoduo_4o_wo_multi/subtask_execution_log.csv"

if [ ! -f "$SINGLE_CSV" ]; then
    echo "⚠️  警告: 未找到single数据集CSV文件"
    echo "   路径: $SINGLE_CSV"
fi

if [ ! -f "$MULTI_CSV" ]; then
    echo "⚠️  警告: 未找到multi数据集CSV文件"
    echo "   路径: $MULTI_CSV"
fi

if [ -f "$SINGLE_CSV" ] || [ -f "$MULTI_CSV" ]; then
    echo "✅ 找到数据文件"
else
    echo "❌ 未找到任何数据文件，请检查路径配置"
fi

echo ""
echo "🚀 启动服务器..."
echo "   访问地址: http://localhost:3000"
echo "   按 Ctrl+C 停止服务"
echo ""

# 启动服务器
npm start
