#!/bin/bash
# 使用 Lab-GPU 运行示例任务的完整脚本
# 无需预设 tasks.json，直接使用 examples 中的示例程序

set -e  # 遇到错误立即退出

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     Lab-GPU 示例任务运行脚本                                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 激活环境
source ~/miniconda3/etc/profile.d/conda.sh
conda activate graphAR

# 进入项目目录
cd /home/cwx/workspace/gpudirector

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 步骤 1: 启动 Lab-GPU Master 服务"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
lab-gpu server start --role master --host 127.0.0.1
echo "✅ Master 服务已启动"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 步骤 2: 注册 GPU 节点"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
lab-gpu server add-node --name node-1 --gpus 2 --vram 24 --gpu-type "RTX 3090"
lab-gpu server add-node --name node-2 --gpus 2 --vram 48 --gpu-type "A100"
echo "✅ 已添加 2 个 GPU 节点"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 步骤 3: 查看初始状态"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
lab-gpu status
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 步骤 4: 提交示例任务"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 任务 1: GPU 显存分配示例 (高优先级)
echo "🚀 任务 1: GPU 显存分配示例 (2GB, 20秒)"
TASK1=$(lab-gpu submit --mem 2G --priority high \
    "python examples/gpu_alloc.py --mock --gb 2 --sleep 20" | grep -oP 'task \K\d+')
echo "   ✅ 已提交任务 ID: $TASK1 (高优先级)"
echo ""

# 任务 2: GPU burst 示例 (普通优先级)
echo "🚀 任务 2: GPU 周期性显存申请示例 (1GB, 3个周期)"
TASK2=$(lab-gpu submit --mem 1G --priority normal \
    "python examples/gpu_burst.py --mock --gb 1 --cycles 3" | grep -oP 'task \K\d+')
echo "   ✅ 已提交任务 ID: $TASK2 (普通优先级)"
echo ""

# 任务 3: GPU sleep 示例 (低优先级)
echo "🚀 任务 3: GPU 长时间占用示例 (4GB, 60秒)"
TASK3=$(lab-gpu submit --mem 4G --priority low \
    "python examples/gpu_sleep.py --mock --gb 4 --sleep 60" | grep -oP 'task \K\d+')
echo "   ✅ 已提交任务 ID: $TASK3 (低优先级)"
echo ""

# 任务 4: 模拟 OOM 错误 (用于测试自愈功能)
echo "🚀 任务 4: 模拟 OOM 错误 (测试自愈功能)"
TASK4=$(lab-gpu submit --mem 2G --priority normal \
    "python examples/gpu_oom.py --mock-oom" | grep -oP 'task \K\d+')
echo "   ✅ 已提交任务 ID: $TASK4 (普通优先级, 会触发 OOM)"
echo ""

# 任务 5: 小显存快速任务 (回填测试)
echo "🚀 任务 5: 小显存快速任务 (0.5GB, 测试回填策略)"
TASK5=$(lab-gpu submit --mem 0.5G --priority normal \
    "python examples/gpu_alloc.py --mock --gb 0.5 --sleep 5" | grep -oP 'task \K\d+')
echo "   ✅ 已提交任务 ID: $TASK5 (普通优先级, 小任务)"
echo ""

# 任务 6: 简单的 echo 命令
echo "🚀 任务 6: 简单测试任务"
TASK6=$(lab-gpu submit --mem 1G --priority high \
    "echo 'Lab-GPU Test Task' && sleep 3" | grep -oP 'task \K\d+')
echo "   ✅ 已提交任务 ID: $TASK6 (高优先级)"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 步骤 5: 执行调度"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
lab-gpu server tick
echo "✅ 调度完成"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 步骤 6: 查看任务状态"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
lab-gpu status
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 步骤 7: 查看详细 JSON 状态"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
lab-gpu status --json | python -m json.tool
echo ""

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     脚本执行完成！                                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "💡 接下来你可以："
echo ""
echo "   1️⃣  启动 TUI 可视化界面（推荐）"
echo "      lab-gpu tui"
echo ""
echo "   2️⃣  查看特定任务的日志"
echo "      lab-gpu logs $TASK1"
echo "      lab-gpu logs $TASK2 -f  # 实时跟踪"
echo ""
echo "   3️⃣  查看任务状态"
echo "      lab-gpu status"
echo "      lab-gpu status --json"
echo ""
echo "   4️⃣  抢占任务（如果需要）"
echo "      lab-gpu server preempt --task-id $TASK1"
echo ""
echo "   5️⃣  提交更多任务"
echo "      lab-gpu submit --mem 10G \"python your_script.py\""
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 已提交的任务 ID："
echo "   - 任务 1 (GPU 分配): $TASK1"
echo "   - 任务 2 (GPU Burst): $TASK2"
echo "   - 任务 3 (GPU Sleep): $TASK3"
echo "   - 任务 4 (OOM 测试): $TASK4"
echo "   - 任务 5 (小任务): $TASK5"
echo "   - 任务 6 (简单任务): $TASK6"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
