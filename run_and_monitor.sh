#!/bin/bash
# Lab-GPU 示例任务 + 自动启动 TUI 监控
# 提交任务后自动打开可视化界面

# 激活环境
source ~/miniconda3/etc/profile.d/conda.sh
conda activate graphAR
cd /home/cwx/workspace/gpudirector

clear
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     Lab-GPU 示例任务 + TUI 监控                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 1. 启动服务
echo "⚙️  启动 Master 服务..."
lab-gpu server start --role master --host 127.0.0.1

# 2. 添加节点
echo "📡 添加 GPU 节点..."
lab-gpu server add-node --name node-1 --gpus 2 --vram 24 --gpu-type "RTX 3090"

# 3. 提交多个示例任务
echo ""
echo "📝 提交示例任务..."
echo ""

# 高优先级任务
echo "   [1] 高优先级 GPU 分配任务 (2GB)"
lab-gpu submit --mem 2G --priority high \
    "python examples/gpu_alloc.py --mock --gb 2 --sleep 30"

# 普通优先级任务
echo "   [2] 普通优先级 GPU Burst 任务 (1GB)"
lab-gpu submit --mem 1G --priority normal \
    "python examples/gpu_burst.py --mock --gb 1 --cycles 3"

echo "   [3] 普通优先级长时间任务 (4GB)"
lab-gpu submit --mem 4G --priority normal \
    "python examples/gpu_sleep.py --mock --gb 4 --sleep 60"

# 低优先级任务
echo "   [4] 低优先级任务 (3GB)"
lab-gpu submit --mem 3G --priority low \
    "python examples/gpu_alloc.py --mock --gb 3 --sleep 40"

# 小任务（测试回填）
echo "   [5] 小任务 - 测试回填策略 (0.5GB)"
lab-gpu submit --mem 0.5G --priority normal \
    "python examples/gpu_alloc.py --mock --gb 0.5 --sleep 5"

# 4. 执行调度
echo ""
echo "⚙️  执行调度..."
lab-gpu server tick

# 5. 显示状态
echo ""
echo "📊 当前状态："
lab-gpu status
echo ""

# 6. 启动 TUI
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎨 启动 TUI 可视化界面..."
echo ""
echo "💡 TUI 快捷键："
echo "   k - 杀死任务"
echo "   r - 重试任务"
echo "   t - 提升到队首"
echo "   q - 退出"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
sleep 2

# 启动 TUI
lab-gpu tui
