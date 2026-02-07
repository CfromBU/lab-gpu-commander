from __future__ import annotations

from fastapi import FastAPI

from .http_models import AgentRegister, TaskSubmit
from .master import Master
from .models import GPU, Node, Priority, Task

app = FastAPI()
_master = Master()


def _parse_mem_gb(value: str) -> float:
    return float(value.rstrip("Gg"))


@app.post("/agents/register")
def register(req: AgentRegister) -> dict:
    gpu_list = []
    node_gpu_type = None
    for gpu in req.gpus:
        if "type" in gpu and gpu["type"]:
            node_gpu_type = gpu["type"]
        gpu_list.append(
            GPU(
                gpu_id=int(gpu["id"]),
                total_vram_gb=float(gpu.get("total_vram_gb", gpu.get("total", 0.0))),
                used_vram_gb=float(gpu.get("used_vram_gb", 0.0)),
            )
        )
    _master.register_node(Node(name=req.node, gpus=gpu_list, gpu_type=node_gpu_type))
    return {"ok": True}


@app.post("/tasks")
def submit(req: TaskSubmit) -> dict:
    mem_gb = _parse_mem_gb(req.mem)
    task = Task(
        task_id=len(_master.scheduler.state.tasks) + 1,
        user="me",
        cmd=req.cmd,
        min_vram_gb=mem_gb,
        priority=Priority(req.priority),
        gpu_type=req.gpu_type,
        time_limit_s=req.time_limit,
    )
    _master.submit(task)
    return {"ok": True, "task_id": task.task_id}


@app.post("/schedule/tick")
def tick() -> dict:
    assignments = _master.schedule_once()
    return {"assignments": assignments}


@app.get("/status")
def status() -> dict:
    return _master.summary()
