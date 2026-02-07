from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class AgentRegister(BaseModel):
    node: str
    gpus: list[dict]


class TaskSubmit(BaseModel):
    cmd: str
    mem: str
    priority: str = "normal"
    time_limit: Optional[int] = None
    gpu_type: Optional[str] = None
