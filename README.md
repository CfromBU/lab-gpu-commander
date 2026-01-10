# Lab-GPU-Commander (lab-gpu)

这是一个可运行的实验室 GPU 调度器 Demo：包含 Python CLI、内存版 Master/Agent、基础调度策略、OOM 自愈，以及 VS Code 插件骨架。核心逻辑已经配齐 pytest 测试，适合继续扩展为分布式系统。

## 功能概览
- 多级优先级 + 公平共享调度（High/Normal/Low）
- 智能回填（基于 time limit 的回填门控）
- 夜间策略加速 Low 队列（night boost）
- OOM 语义解析与自动回填升级显存需求
- 僵尸进程检测（低利用率 + 无 IO）
- 抢占流程（SIGUSR1 → SIGTERM → SIGKILL）
- Textual TUI 看板（支持 kill / retry / top）
- VS Code 右键提交 + 状态栏轮询 + OOM 提示

## 安装

```
python -m pip install .
```

可选依赖：

```
python -m pip install ".[test]"
python -m pip install ".[server]"  # FastAPI 可选依赖，后续扩展 API 用
```

## CLI 快速开始
注册节点、提交任务并触发调度：

```
lab-gpu server start --role master --host 127.0.0.1
lab-gpu server add-node --name node-1 --gpus 2 --vram 24 --gpu-type "RTX 3090"
lab-gpu submit --mem 10G --priority normal "python train.py"
lab-gpu server tick
lab-gpu status
```

Dry-run（只模拟分配，不提交）：

```
lab-gpu submit --mem 10G --priority high --dry-run "python train.py"
```

Agent 本地执行（带日志 + OOM 解析）：

```
lab-gpu agent run --task-id 1 --mem-used 10 --env my-conda "python train.py"
```

如未安装入口脚本，可用模块方式运行：

```
python -m lab_gpu.cli status
```

日志查看：

```
lab-gpu logs 1
lab-gpu logs 1 -f
```

抢占运行中的任务：

```
lab-gpu server preempt --task-id 1 --soft-timeout 300 --term-timeout 30
```

## Policy 文件（夜间模式）
示例 `policy.yaml`：

```
night_start: "00:00"
night_end: "08:00"
base_idle_util_threshold: 0.05
night_idle_util_threshold: 0.20
backfill_time_limit_s: 3600
night_low_bonus: 0.5
```

加载策略：

```
lab-gpu server start --role master --policy policy.yaml
```

## TUI 交互
启动：

```
lab-gpu tui
```

快捷键：
- `k`：杀死选中的任务
- `r`：重试选中的任务
- `t`：提升选中任务到队首
- `q`：退出

命令行输入框：
- `list`：切换列表模式
- `top <id>`：将指定任务提升到队首

## VS Code 插件说明
`vscode/extension.ts` 已实现：
- 右键 “Submit to GPU Queue”
- 自动记忆上次显存输入
- 状态栏轮询 `lab-gpu status --json`
- OOM 自动重试弹窗提示
- QuickPick 查看运行中任务并打开日志

## 测试

```
pytest -q
```

覆盖范围：
- 回填策略（头阻塞时允许小任务先跑）
- OOM 自愈策略（显存升级 + retry 计数）
- 公平调度排序
- 僵尸进程检测

## 示例显存程序（手动测试）
目录：`examples/`

- `gpu_alloc.py`：申请固定显存并保持一段时间
- `gpu_oom.py`：逐步申请显存触发 OOM（支持 mock）
- `gpu_burst.py`：周期性申请/释放显存
- `gpu_sleep.py`：申请显存后长时间空转

示例命令（需要 PyTorch + CUDA）：

```
python examples/gpu_alloc.py --gb 2 --sleep 20
python examples/gpu_burst.py --gb 1 --cycles 3
python examples/gpu_sleep.py --gb 4 --sleep 120
```

模拟 OOM（无需 GPU）：

```
python examples/gpu_oom.py --mock-oom
```

与 lab-gpu 联动（本地 demo）：

```
lab-gpu server add-node --name node-1 --gpus 1 --vram 24
lab-gpu submit --mem 2G --priority normal "python examples/gpu_alloc.py --gb 2 --sleep 30"
lab-gpu server tick
lab-gpu agent run --task-id 1 --mem-used 2 "python examples/gpu_alloc.py --gb 2 --sleep 30"
```

模拟 OOM 回路（无需 GPU）：

```
python -m lab_gpu.cli agent run --task-id 99 --mem-used 10 --log-root ./logs "python examples/gpu_oom.py --mock-oom"
```

## 说明
- 当前是单进程 Demo：Master/Agent 运行在同一 CLI 进程中。
- 日志默认写入 `/nas/logs/{task_id}.log`，可通过 `agent run --log-root` 改路径。
