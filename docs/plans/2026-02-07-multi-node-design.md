# 多机多卡调度与便捷批量提交设计

日期：2026-02-07

## 目标
- 支持多机多卡调度：Master 统一分配，Agent 在各节点执行任务并回报状态。
- 在不破坏现有 CLI/SDK 的前提下引入网络通信层，保留本地内存版原型。
- 为批量任务提供更便捷的提交方式与更稳定的调度触发机制。

## 架构概览
- **Master 服务**：统一调度中心，维护任务队列与节点资源。
- **Agent 服务**：运行在各节点，负责 GPU 资源上报与本地执行。
- **通信层**：采用 HTTP/JSON（FastAPI）实现，后续可替换为 gRPC。
- **调度逻辑**：复用现有 Scheduler，分配结果为 `(task_id, node, gpu_id)`。

## 核心流程
1) Agent 启动后注册节点与 GPU 资源到 Master。
2) Agent 定期心跳上报 GPU 使用率、僵尸标记、进程信息。
3) 用户提交任务到 Master。
4) Master 调度并选择节点/GPU。
5) Master 调用目标 Agent 执行任务。
6) Agent 回报执行结果与日志路径；Master 更新任务状态与 OOM 处理。

## API（最小集）
- `POST /agents/register`
  - 入参：`{"node":"node-1","gpus":[{"id":0,"total_vram_gb":24,"type":"3090"}]}`
- `POST /agents/heartbeat`
  - 入参：GPU 使用与健康状态
- `POST /tasks`
  - 入参：`{"cmd":"python train.py","mem":"10G","priority":"normal","time_limit":3600}`
- `POST /schedule/tick`
  - 触发一次调度
- `POST /agents/{node}/run`
  - 下发任务并绑定 GPU
- `POST /agents/{node}/report`
  - 回报 `exit_code` / `oom` / `log_path`

## 可靠性与错误处理
- **心跳超时**：节点心跳超过阈值则标记为不可调度。
- **任务租约**：调度时分配 `lease_id`，未续约则回收重调度。
- **幂等提交**：支持 `client_task_id` 防止重复提交。
- **OOM 处理**：复用现有 OOM 语义解析与显存升级重试策略。

## 批量提交体验
- CLI 保持 `submit-batch --file tasks.json`。
- 提供 `run_batch.sh`（提交 + tick + 状态轮询 + 失败重试）。
- 后续可扩展 SDK `Client.submit_batch()` 统一入口。

## 迁移路径
1) Master API 与 Agent 心跳/注册
2) Agent 远程执行与回报
3) CLI/SDK 切换为 HTTP Backend
4) 增强租约、断线恢复与权限控制

