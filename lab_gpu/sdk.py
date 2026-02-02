from __future__ import annotations

from dataclasses import dataclass
import os
import time
from typing import Optional

from .master import Master
from .models import GPU, Node, Priority, Task


class LabGpuTimeoutError(RuntimeError):
    pass


@dataclass
class Placement:
    task_id: int
    node: str
    gpu_id: int


class LocalBackend:
    def __init__(self, master: Optional[Master] = None) -> None:
        self.master = master or Master()
        if not self.master.state.nodes:
            self.master.register_node(
                Node(
                    name="local",
                    gpus=[GPU(gpu_id=0, total_vram_gb=24.0, used_vram_gb=0.0)],
                )
            )

    def request_device(self, spec: dict, timeout: Optional[float]) -> Placement:
        task_id = len(self.master.scheduler.state.tasks) + 1
        task = Task(
            task_id=task_id,
            user=spec.get("user", "me"),
            cmd=spec.get("cmd", ""),
            min_vram_gb=spec["min_vram_gb"],
            priority=spec["priority"],
            env=spec.get("env"),
            gpu_type=spec.get("gpu_type"),
            time_limit_s=spec.get("time_limit"),
        )
        self.master.submit(task)

        start_ts = time.time()
        while True:
            self.master.schedule_once()
            task_state = self.master.scheduler.state.tasks[task_id]
            if task_state.assigned_node is not None and task_state.assigned_gpu is not None:
                return Placement(task_id=task_id, node=task_state.assigned_node, gpu_id=task_state.assigned_gpu)

            if timeout == 0:
                raise LabGpuTimeoutError("No available GPU for request.")
            if timeout is not None and (time.time() - start_ts) >= timeout:
                raise LabGpuTimeoutError("Timed out waiting for GPU allocation.")
            time.sleep(0.1)


class Client:
    def __init__(self, backend: Optional[LocalBackend] = None) -> None:
        self.backend = backend or LocalBackend()

    def request_device(
        self,
        *,
        mem: str,
        priority: str = "normal",
        timeout: Optional[float] = None,
        gpu_type: Optional[str] = None,
        time_limit: Optional[int] = None,
    ) -> Placement:
        min_vram_gb = _parse_mem_gb(mem)
        spec = {
            "min_vram_gb": min_vram_gb,
            "priority": Priority(priority),
            "gpu_type": gpu_type,
            "time_limit": time_limit,
        }
        return self.backend.request_device(spec, timeout)

    def acquire(self, **kwargs) -> Placement:
        placement = self.request_device(**kwargs)
        os.environ["CUDA_VISIBLE_DEVICES"] = str(placement.gpu_id)
        os.environ["LABGPU_ASSIGNED_NODE"] = placement.node
        os.environ["LABGPU_ASSIGNED_GPU"] = str(placement.gpu_id)
        return placement


def _parse_mem_gb(value: str) -> float:
    return float(str(value).rstrip("Gg"))
