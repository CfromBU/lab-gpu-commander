#!/bin/bash
# Lab-GPU 使用示例脚本

# 激活环境
conda activate graphAR

echo "=== 步骤 1: 启动 Master 服务 ==="
lab-gpu server start --role master --host 127.0.0.1

echo -e "\n=== 步骤 2: 添加 GPU 节点 ==="
lab-gpu server add-node --name gpu-node-1 --gpus 2 --vram 24 --gpu-type "RTX 3090"

echo -e "\n=== 步骤 3: 查看初始状态 ==="
lab-gpu status

echo -e "\n=== 步骤 4: 提交单个任务 ==="
lab-gpu submit --mem 8G --priority high "python examples/gpu_alloc.py --mock --gb 0.5"

echo -e "\n=== 步骤 5: 批量提交任务 ==="
lab-gpu submit-batch --file tasks.json

echo -e "\n=== 步骤 6: 执行调度 ==="
lab-gpu server tick

echo -e "\n=== 步骤 7: 查看任务状态 ==="
lab-gpu status --json

echo -e "\n=== 步骤 8: 启动 TUI 界面（可选）==="
echo "运行: lab-gpu tui"
