# Lab-GPU 快速上手指南

## 🚀 5 分钟快速开始

### 1. 启动服务并添加节点

```bash
# 激活你的环境
conda activate graphAR

# 启动 master
lab-gpu server start --role master --host 127.0.0.1

# 添加 GPU 节点（根据你的实际配置修改）
lab-gpu server add-node --name node-1 --gpus 2 --vram 24 --gpu-type "RTX 3090"
```

### 2. 提交任务（三选一）

#### 选项 A：单个任务
```bash
lab-gpu submit --mem 10G --priority normal "python train.py"
```

#### 选项 B：使用你的 tasks.json
```bash
lab-gpu submit-batch --file tasks.json
```

#### 选项 C：先测试再提交
```bash
# 先看看能否分配（不实际提交）
lab-gpu submit-batch --file tasks.json --dry-run

# 确认后再提交
lab-gpu submit-batch --file tasks.json
```

### 3. 执行调度并查看状态

```bash
# 触发调度
lab-gpu server tick

# 查看状态
lab-gpu status

# 或者使用 TUI 可视化界面
lab-gpu tui
```

## 📋 tasks.json 格式说明

你的 `tasks.json` 当前格式：

```json
{
  "tasks": [
    {"cmd": "python train_a.py", "mem": "10G", "priority": "normal"},
    {"cmd": "python train_b.py", "min_vram_gb": 8, "priority": "high", "time_limit": 1200}
  ]
}
```

### 支持的字段：

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `cmd` | 字符串 | **必填**，要执行的命令 | `"python train.py"` |
| `mem` | 字符串 | 显存需求（带单位） | `"10G"`, `"16G"` |
| `min_vram_gb` | 数字 | 显存需求（GB，与 mem 二选一） | `8`, `12` |
| `priority` | 字符串 | 优先级：high/normal/low | `"high"` |
| `env` | 字符串 | Conda 环境名 | `"graphAR"` |
| `gpu_type` | 字符串 | 指定 GPU 型号 | `"RTX 3090"` |
| `time_limit` | 数字 | 时间限制（秒） | `3600` |

### 示例配置：

```json
{
  "tasks": [
    {
      "cmd": "python train_resnet.py --epochs 100",
      "mem": "16G",
      "priority": "high",
      "env": "graphAR",
      "gpu_type": "RTX 3090"
    },
    {
      "cmd": "python train_bert.py",
      "min_vram_gb": 24,
      "priority": "normal",
      "time_limit": 7200
    },
    {
      "cmd": "python long_experiment.py",
      "mem": "12G",
      "priority": "low",
      "env": "pytorch"
    }
  ]
}
```

## 🎯 常见使用场景

### 场景 1：提交一批训练任务
```bash
# 编辑 tasks.json，添加你的任务
# 然后批量提交
lab-gpu submit-batch --file tasks.json
lab-gpu server tick
lab-gpu status
```

### 场景 2：查看和管理任务
```bash
# 使用 TUI 界面（推荐）
lab-gpu tui

# 或者命令行
lab-gpu status --json
lab-gpu logs 1 -f  # 查看任务 1 的日志
```

### 场景 3：优先执行重要任务
```bash
# 提交高优先级任务
lab-gpu submit --mem 16G --priority high "python urgent_exp.py"
lab-gpu server tick
```

### 场景 4：测试任务配置
```bash
# 先 dry-run 看看能否分配
lab-gpu submit --mem 32G --priority high --dry-run "python large_model.py"

# 如果返回 placement: null，说明显存不足，需要调整
```

## 💡 实用技巧

1. **优先级策略**
   - `high`：紧急任务，优先调度
   - `normal`：普通任务
   - `low`：不急的任务，会在夜间自动加速

2. **时间限制**
   - 设置 `time_limit` 可以让短任务通过回填策略优先运行

3. **环境管理**
   - 使用 `env` 字段指定 conda 环境
   - 或在命令中使用 `conda run -n env_name python script.py`

4. **日志查看**
   - 默认日志位置：`/nas/logs/{task_id}.log`
   - 可以用 `--log-root` 改变日志目录

## 🔧 故障排除

### 问题：任务提交后状态一直是 Pending: 0
**解决**：需要手动执行 `lab-gpu server tick` 触发调度

### 问题：任务无法分配 GPU
**解决**：
1. 检查是否添加了 GPU 节点：`lab-gpu status`
2. 检查显存需求是否超过节点容量
3. 使用 `--dry-run` 测试分配

### 问题：需要修改日志目录
**解决**：
```bash
lab-gpu agent run --task-id 1 --mem-used 10 --log-root ./logs "python train.py"
```

## 📚 更多信息

详细文档请参考：`README.md`
