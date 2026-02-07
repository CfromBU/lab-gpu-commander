#!/bin/bash
# 简化版：使用 Lab-GPU 运行示例任务
# 适合快速测试

# 激活环境
source ~/miniconda3/etc/profile.d/conda.sh
conda activate graphAR
cd /home/cwx/workspace/gpudirector

echo "🚀 启动 Lab-GPU 并运行示例任务..."
echo ""

# 启动服务
lab-gpu server start --role master --host 127.0.0.1

# 添加 GPU 节点
lab-gpu server add-node --name node-1 --gpus 2 --vram 24

# 提交示例任务
echo "📝 提交任务..."
lab-gpu submit --mem 2G --priority high "python examples/gpu_alloc.py --mock --gb 2 --sleep 10"
lab-gpu submit --mem 1G --priority normal "python examples/gpu_burst.py --mock --gb 1 --cycles 2"
lab-gpu submit --mem 0.5G --priority normal "echo 'Test Task' && sleep 3"

# 执行调度
echo ""
echo "⚙️  执行调度..."
lab-gpu server tick

# 查看状态
echo ""
echo "📊 任务状态："
lab-gpu status

echo ""
echo "✅ 完成！运行 'lab-gpu tui' 查看可视化界面"
