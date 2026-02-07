# Lab-GPU 批量提交使用文档

本手册面向需要一次性提交多个实验的用户，重点介绍 `tasks.json` 格式与 `run_batch.sh` 的批量调度方式。

## 1. 前置条件

- 已安装 Lab-GPU（`python -m pip install .`）
- 已启动 Master 并注册节点（或使用脚本自动启动）
- 若运行 GPU 脚本，需安装 PyTorch + CUDA

## 2. tasks.json 格式

示例：
```json
{
  "tasks": [
    {"cmd": "python examples/gpu_matmul.py --size 2048 --iters 5", "mem": "6G", "priority": "normal"},
    {"cmd": "python examples/gpu_spin.py --seconds 20", "mem": "4G", "priority": "low"},
    {"cmd": "python examples/gpu_transfer.py --mb 256 --iters 20", "mem": "8G", "priority": "high"}
  ]
}
```

字段说明：
- `cmd`：要执行的命令（必填）
- `mem` / `min_vram_gb`：显存需求（二选一）
- `priority`：`high | normal | low`
- `env`：conda 环境名（可选）
- `gpu_type`：指定 GPU 型号（可选）
- `time_limit`：回填策略使用的时长（秒，可选）

## 3. 一键批量提交（推荐）

使用仓库自带脚本 `run_batch.sh`：

```bash
chmod +x run_batch.sh
./run_batch.sh tasks.json
```

可选环境变量：
- `HOST`：Master 监听地址（默认 `127.0.0.1`）
- `MAX_RETRY`：失败重试次数（默认 1）
- `LOG_ROOT`：日志路径提示（默认 `/nas/logs`）

脚本行为：
- 自动提交任务
- 自动 `tick` 调度
- 失败任务按次数重试
- 任务完成后提示日志目录

## 4. 测试用 GPU 脚本

仓库包含以下脚本，可直接放入 `tasks.json`：
- `examples/gpu_matmul.py`：矩阵乘法压力测试
- `examples/gpu_spin.py`：持续小计算负载
- `examples/gpu_transfer.py`：GPU ↔ CPU 传输测试

如果机器没有 GPU，可加 `--mock` 进行干跑：
```bash
python examples/gpu_matmul.py --mock
```

## 5. 常见问题

**Q：任务一直 Pending？**  
需要持续执行 `lab-gpu server tick`。`run_batch.sh` 会自动做这件事。

**Q：日志找不到？**  
默认 `/nas/logs/{task_id}.log`，无权限时可在执行命令里指定 `--log-root`。

