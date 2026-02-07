# Python SDK 联动调度器设计（本地原型 + 多机预留）

日期：2026-02-01

## 目标
- 为用户程序提供一个轻量 Python SDK：一行代码申请 GPU，自动绑定 `CUDA_VISIBLE_DEVICES`。
- 提供仅获取分配结果的接口（node + gpu_id），以便用户自定义绑定策略。
- 提供可选的“托管运行”模式，SDK 运行训练命令并返回错误信息（含 OOM 解析）。
- 先落地本地原型（内存版 Master/Scheduler），保留后续多机网络化的接口形态。

## 范围
- 新增 `lab_gpu/sdk.py`（或 `lab_gpu/client.py`）实现 SDK。
- 新增最小单元测试。
- README 增加一张 Mermaid 框架图。
- 不实现真实多机网络通信（仅预留接口）。

## 关键接口

### 1) 轻量申请（自动绑定）
```python
placement = labgpu.acquire(mem="10G", priority="normal", timeout=None)
# 自动设置 CUDA_VISIBLE_DEVICES
```

行为：
- 默认阻塞，`timeout=None` 表示无限等待。
- `timeout=0` 表示立即失败（抛异常或返回 None，优先抛异常）。
- 设置 `LABGPU_ASSIGNED_NODE` / `LABGPU_ASSIGNED_GPU`。

### 2) 仅申请（不绑定）
```python
placement = labgpu.request_device(mem="10G", priority="normal", timeout=30)
# 返回 {task_id, node, gpu_id}
```

### 3) 托管运行（可选）
```python
result = labgpu.run(cmd="python train.py", mem="10G")
# 返回 exit_code / stderr 摘要 / oom 信息
```

行为：
- 内部调用现有 `Agent` 逻辑，复用日志与 OOM 解析。
- 启动前先分配 GPU 并绑定。
- 非 0 退出时返回错误摘要。

## 后端抽象
- `Client` 接口对外暴露 `request_device/acquire/run/release`。
- `Backend` 抽象接口：`request_task()`, `wait_for_assignment()`, `release()`。
- 当前实现 `LocalBackend`：直接使用内存版 `Master/Scheduler`。
- 未来可替换为 `HttpBackend`（不影响调用侧）。

## 错误处理
- 参数校验失败：`ValueError`。
- 超时：`LabGpuTimeoutError`。
- 无可用 GPU：在 `timeout=0` 或超时场景抛异常。
- 托管运行失败：返回 `exit_code` + `stderr` 摘要 + OOM 信息（若检测到）。

## 测试计划（最小）
- `request_device()` 返回 `node + gpu_id`。
- `acquire()` 设置 `CUDA_VISIBLE_DEVICES` 与 `LABGPU_ASSIGNED_*`。
- `timeout` 行为：`None` 阻塞、`0` 立即失败、有超时抛异常。
- `run()` 返回非 0 退出码与错误摘要。

## README 框架图
- 使用 Mermaid：展示 Python 程序 → SDK → LocalBackend(Master/Scheduler) → GPU 节点。
- 托管运行路径：SDK → Agent → 训练命令 → 日志/错误回传。

## 迁移路径（多机）
- 当需要真正多机时：实现 `HttpBackend` 与 Master API。
- SDK 调用接口不变，业务侧无需改动。
