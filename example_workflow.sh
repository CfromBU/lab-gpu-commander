#!/bin/bash
# Lab-GPU 完整工作流示例
# 使用方法: bash example_workflow.sh

set -e  # 遇到错误立即退出

echo "======================================"
echo "   Lab-GPU 完整工作流演示"
echo "======================================"

# 激活环境
source ~/miniconda3/etc/profile.d/conda.sh
conda activate graphAR

echo -e "\n✅ 步骤 1: 启动 Master 服务"
lab-gpu server start --role master --host 127.0.0.1
echo "   服务已启动在 127.0.0.1"

echo -e "\n✅ 步骤 2: 添加 GPU 节点"
lab-gpu server add-node --name node-1 --gpus 2 --vram 24 --gpu-type "RTX 3090"
echo "   已添加节点: node-1 (2x RTX 3090, 24GB)"

echo -e "\n✅ 步骤 3: 查看当前状态"
lab-gpu status
echo ""

echo -e "\n✅ 步骤 4: 测试任务配置 (dry-run)"
echo "   正在检查 tasks.json 中的任务..."
lab-gpu submit-batch --file tasks.json --dry-run | python -m json.tool
echo ""

echo -e "\n✅ 步骤 5: 提交单个测试任务"
TASK_ID=$(lab-gpu submit --mem 2G --priority high "python examples/gpu_alloc.py --mock --gb 0.5" | grep -oP 'task \K\d+')
echo "   已提交任务 ID: $TASK_ID"

echo -e "\n✅ 步骤 6: 批量提交 tasks.json 中的任务"
lab-gpu submit-batch --file tasks.json
echo "   批量任务已提交"

echo -e "\n✅ 步骤 7: 执行调度"
lab-gpu server tick
echo "   调度完成"

echo -e "\n✅ 步骤 8: 查看详细状态"
lab-gpu status --json | python -m json.tool
echo ""

echo -e "\n======================================"
echo "   演示完成！"
echo "======================================"
echo ""
echo "💡 接下来你可以："
echo "   1. 查看任务日志: lab-gpu logs <task_id>"
echo "   2. 启动 TUI 界面: lab-gpu tui"
echo "   3. 查看状态: lab-gpu status"
echo "   4. 提交更多任务: lab-gpu submit --mem 10G \"your command\""
echo ""
