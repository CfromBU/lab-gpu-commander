from __future__ import annotations

from dataclasses import dataclass


class LabGpuTimeoutError(RuntimeError):
    pass


@dataclass
class Placement:
    task_id: int
    node: str
    gpu_id: int
