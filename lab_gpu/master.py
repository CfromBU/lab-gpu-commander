from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import os
import time

from .models import Node, OOMSignal, Task, TaskStatus
from .scheduler import Scheduler


@dataclass
class MasterState:
    nodes: Dict[str, Node] = field(default_factory=dict)
    history: List[int] = field(default_factory=list)
    oom_events: int = 0
    runtimes: Dict[int, "TaskRuntime"] = field(default_factory=dict)
    last_oom_task: Optional[int] = None


@dataclass
class TaskRuntime:
    task_id: int
    pid: int
    log_path: str
    started_ts: float = field(default_factory=time.time)


class Master:
    def __init__(self, scheduler: Optional[Scheduler] = None) -> None:
        self.scheduler = scheduler or Scheduler()
        self.state = MasterState()

    def register_node(self, node: Node) -> None:
        self.state.nodes[node.name] = node

    def submit(self, task: Task) -> None:
        self.scheduler.submit(task)

    def on_oom(self, signal: OOMSignal) -> None:
        self.state.oom_events += 1
        self.state.last_oom_task = signal.task_id
        self.scheduler.apply_oom_recovery(signal.task_id, signal.missing_gb)

    def schedule_once(self) -> List[tuple[int, str, int]]:
        return self.scheduler.schedule(list(self.state.nodes.values()))

    def mark_failed(self, task_id: int) -> None:
        self.scheduler.update_task_status(task_id, TaskStatus.FAILED)
        self.state.history.append(task_id)

    def mark_succeeded(self, task_id: int) -> None:
        self.scheduler.update_task_status(task_id, TaskStatus.SUCCEEDED)
        self.state.history.append(task_id)

    def summary(self) -> dict:
        tasks = list(self.scheduler.state.tasks.values())
        pending = len([t for t in tasks if t.status == TaskStatus.PENDING])
        running = [t for t in tasks if t.status == TaskStatus.RUNNING]
        failed = len([t for t in tasks if t.status == TaskStatus.FAILED])
        total_gpus = 0
        busy_gpus = 0
        for node in self.state.nodes.values():
            for gpu in node.gpus:
                total_gpus += 1
                if gpu.used_vram_gb > 0:
                    busy_gpus += 1
        return {
            "tasks": len(tasks),
            "pending": pending,
            "running": len(running),
            "failed": failed,
            "busy": busy_gpus,
            "total": total_gpus,
            "my_running": len([t for t in running if t.user == "me"]),
            "ooms": self.state.oom_events,
            "last_oom_task": self.state.last_oom_task,
            "running_tasks": [{"id": t.task_id, "label": t.cmd[:60]} for t in running],
            "recent": [
                {
                    "id": t.task_id,
                    "status": t.status.value,
                    "node": t.assigned_node,
                }
                for t in tasks[-5:]
            ],
        }

    def register_runtime(self, task_id: int, pid: int, log_path: str) -> None:
        self.state.runtimes[task_id] = TaskRuntime(task_id=task_id, pid=pid, log_path=log_path)

    def clear_runtime(self, task_id: int) -> None:
        self.state.runtimes.pop(task_id, None)

    def _pid_alive(self, pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def preempt_task(self, task_id: int, soft_timeout_s: int = 300, term_timeout_s: int = 30) -> str:
        runtime = self.state.runtimes.get(task_id)
        if not runtime:
            return "not-running"
        from .agent import Agent

        agent = Agent()
        agent.soft_preempt(runtime.pid, runtime.log_path)
        deadline = time.time() + soft_timeout_s
        while time.time() < deadline:
            if not self._pid_alive(runtime.pid):
                self.clear_runtime(task_id)
                return "soft-exit"
            time.sleep(1)
        agent.hard_preempt(runtime.pid)
        deadline = time.time() + term_timeout_s
        while time.time() < deadline:
            if not self._pid_alive(runtime.pid):
                self.clear_runtime(task_id)
                return "term-exit"
            time.sleep(1)
        agent.force_kill(runtime.pid)
        self.clear_runtime(task_id)
        return "killed"

    def retry_task(self, task_id: int) -> None:
        self.scheduler.reset_task(task_id)

    def move_task_to_front(self, task_id: int) -> None:
        self.scheduler.move_to_front(task_id)

    def kill_task(self, task_id: int) -> str:
        if task_id in self.state.runtimes:
            result = self.preempt_task(task_id, soft_timeout_s=5, term_timeout_s=5)
        else:
            result = "not-running"
        self.scheduler.update_task_status(task_id, TaskStatus.FAILED)
        self.state.history.append(task_id)
        return result
