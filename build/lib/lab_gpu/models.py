from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time


class Priority(str, Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"
    SUCCEEDED = "succeeded"


PRIORITY_WEIGHT = {
    Priority.HIGH: 3,
    Priority.NORMAL: 2,
    Priority.LOW: 1,
}


@dataclass
class Task:
    task_id: int
    user: str
    cmd: str
    min_vram_gb: float
    priority: Priority
    status: TaskStatus = TaskStatus.PENDING
    gpu_type: Optional[str] = None
    env: Optional[str] = None
    time_limit_s: Optional[int] = None
    submit_ts: float = field(default_factory=time.time)
    start_ts: Optional[float] = None
    retry_count: int = 0
    assigned_node: Optional[str] = None
    assigned_gpu: Optional[int] = None


@dataclass
class GPU:
    gpu_id: int
    total_vram_gb: float
    used_vram_gb: float = 0.0
    util_pct: float = 0.0
    unmanaged_vram_gb: float = 0.0
    zombie: bool = False

    @property
    def free_vram_gb(self) -> float:
        return max(0.0, self.total_vram_gb - self.used_vram_gb - self.unmanaged_vram_gb)


@dataclass
class Node:
    name: str
    gpus: list[GPU]
    gpu_type: Optional[str] = None


@dataclass
class OOMSignal:
    task_id: int
    missing_gb: float
    new_min_vram_gb: float
