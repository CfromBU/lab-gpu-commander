# Lab-GPU 用户手册

本手册面向第一次使用 Lab-GPU 的用户，提供从安装到批量运行、SDK 集成、日志与故障排查的完整流程。示例均为本地内存版 Demo，适合快速验证与扩展。

## 目录
1. 快速开始（CLI）
2. 核心概念
3. CLI 详细用法
4. 批量任务与脚本化运行
5. Python SDK 用法
6. TUI 看板
7. 日志与权限
8. Policy（夜间模式与回填）
9. VS Code 插件
10. 常见问题与故障排查

---

## 1. 快速开始（CLI）

### 1.1 安装

```bash
python -m pip install .
```

可选依赖：
```bash
python -m pip install ".[test]"
python -m pip install ".[server]"  # FastAPI 可选依赖，后续扩展 API 用
python -m pip install "pyyaml"      # 读取 policy.yaml 时可用（未安装时走简易解析）
```

### 1.2 启动 Master 并注册节点

```bash
lab-gpu server start --role master --host 127.0.0.1
lab-gpu server add-node --name node-1 --gpus 2 --vram 24 --gpu-type "RTX 3090"
```

### 1.3 提交任务并触发调度

```bash
lab-gpu submit --mem 10G --priority normal "python train.py"
lab-gpu server tick
lab-gpu status
```

如果想可视化：
```bash
lab-gpu tui
```

---

## 2. 核心概念

- **Master**：调度中心，维护队列与节点状态。
- **Node/GPU**：资源节点，包含 GPU 列表与显存容量。
- **Task**：提交的运行任务，包含显存需求、优先级、可选时间限制等。
- **优先级**：`high / normal / low`，影响调度排序。
- **回填（backfill）**：允许短任务在头阻塞时先跑，提高资源利用率。
- **夜间加速**：夜间策略会提升低优先级队列。
- **OOM 自愈**：检测到 OOM 后自动提升显存需求并重试。
- **抢占**：`SIGUSR1 → SIGTERM → SIGKILL`，可逐步终止任务。

---

## 3. CLI 详细用法

### 3.1 提交任务

```bash
lab-gpu submit --mem 10G --priority normal "python train.py"
```

### 3.2 Dry-run（只模拟分配）

```bash
lab-gpu submit --mem 10G --priority high --dry-run "python train.py"
```

### 3.3 查看状态与日志

```bash
lab-gpu status
lab-gpu status --json
lab-gpu logs 1
lab-gpu logs 1 -f
```

### 3.4 抢占与终止

```bash
lab-gpu server preempt --task-id 1 --soft-timeout 300 --term-timeout 30
```

### 3.5 Agent 本地执行（带 OOM 解析）

```bash
lab-gpu agent run --task-id 1 --mem-used 10 --env my-conda "python train.py"
```

---

## 4. 批量任务与脚本化运行

### 4.1 tasks.json 格式

```json
{
  "tasks": [
    {"cmd": "python exp1.py", "mem": "10G", "priority": "normal"},
    {"cmd": "python exp2.py", "min_vram_gb": 12, "priority": "high", "time_limit": 1200},
    {"cmd": "python exp3.py", "mem": "8G", "priority": "low"}
  ]
}
```

字段说明：
- `cmd`：必填，执行命令
- `mem` / `min_vram_gb`：显存需求（二选一）
- `priority`：`high/normal/low`
- `env`：conda 环境名（可选）
- `gpu_type`：指定 GPU 型号（可选）
- `time_limit`：秒，回填策略使用

提交批量任务：
```bash
lab-gpu submit-batch --file tasks.json
lab-gpu server tick
```

### 4.2 批量脚本（推荐）

仓库提供 `run_batch.sh`：
- 自动提交任务
- 自动 tick 调度
- 失败任务重试
- 输出日志目录提示

```bash
chmod +x run_batch.sh
./run_batch.sh tasks.json
```

可选环境变量：
- `HOST`：master host（默认 `127.0.0.1`）
- `MAX_RETRY`：失败重试次数（默认 1）
- `LOG_ROOT`：日志路径提示（默认 `/nas/logs`）

---

## 5. Python SDK 用法

SDK 提供三种模式：申请+绑定 / 只申请 / 托管运行。

### 5.1 一行申请并绑定

```python
from lab_gpu import Client

client = Client()
placement = client.acquire(mem="10G")
print(placement.node, placement.gpu_id)
```

### 5.2 只申请，不改环境变量

```python
from lab_gpu import Client

client = Client()
placement = client.request_device(mem="10G", timeout=30)
print(placement.node, placement.gpu_id)
```

### 5.3 托管运行

```python
from lab_gpu import Client

client = Client()
result = client.run(cmd="python train.py", mem="10G", log_root="/tmp")
print(result.exit_code, result.oom)
```

### 5.4 超时语义

- `timeout=None`：无限等待
- `timeout=0`：立即失败（抛 `LabGpuTimeoutError`）
- `timeout>0`：超时秒数

### 5.5 多机预留说明

当前 Demo 返回 `node="local"`，未来接入多机时会返回真实节点名。

---

## 6. TUI 看板

启动：
```bash
lab-gpu tui
```

快捷键：
- `k`：杀死任务
- `r`：重试任务
- `t`：提升队首
- `q`：退出

命令输入框：
- `list`：切换列表模式
- `top <id>`：将指定任务提升到队首

---

## 7. 日志与权限

- 默认日志路径：`/nas/logs/{task_id}.log`
- 如无权限创建目录：用 `--log-root` 指定可写目录

示例：
```bash
lab-gpu agent run --task-id 1 --mem-used 10 --log-root ./logs "python train.py"
```

---

## 8. Policy（夜间模式与回填）

`policy.yaml` 示例：
```yaml
night_start: "00:00"
night_end: "08:00"
base_idle_util_threshold: 0.05
night_idle_util_threshold: 0.20
backfill_time_limit_s: 3600
night_low_bonus: 0.5
```

加载：
```bash
lab-gpu server start --role master --policy policy.yaml
```

---

## 9. VS Code 插件

构建：
```bash
cd vscode
npm install
npm run compile
```

调试：
- VS Code 打开 `vscode/` 目录，按 `F5`

打包：
```bash
cd vscode
npx vsce package
```

---

## 10. 常见问题与故障排查

**Q1：任务提交后一直 Pending**
- 需要手动 `lab-gpu server tick` 触发调度。

**Q2：任务无法分配 GPU**
- 检查节点是否已注册：`lab-gpu status`
- 检查显存需求是否超过节点容量
- 用 `--dry-run` 试探

**Q3：日志写入失败**
- `agent run` 默认写 `/nas/logs`，无权限时用 `--log-root`

**Q4：想在脚本里批量跑多个实验**
- 推荐使用 `tasks.json` + `run_batch.sh`

---

如果你需要“多机版 Master/Agent 通讯层”，建议先用当前 SDK/CLI 原型验证策略，再扩展为 HTTP/gRPC 接口。
