from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional, Tuple
import time

from .models import Node, Priority, Task, TaskStatus, PRIORITY_WEIGHT


@dataclass
class SchedulerPolicy:
    night_start: str = "00:00"
    night_end: str = "08:00"
    base_idle_util_threshold: float = 0.05
    night_idle_util_threshold: float = 0.20
    backfill_time_limit_s: int = 3600
    night_low_bonus: float = 0.5


@dataclass
class SchedulerState:
    tasks: Dict[int, Task] = field(default_factory=dict)
    pending_queue: List[int] = field(default_factory=list)
    active_counts: Dict[str, int] = field(default_factory=dict)


class Scheduler:
    def __init__(self, policy: Optional[SchedulerPolicy] = None) -> None:
        self.policy = policy or SchedulerPolicy()
        self.state = SchedulerState()

    def submit(self, task: Task) -> None:
        self.state.tasks[task.task_id] = task
        self.state.pending_queue.append(task.task_id)

    def update_task_status(self, task_id: int, status: TaskStatus) -> None:
        task = self.state.tasks[task_id]
        task.status = status
        if status == TaskStatus.RUNNING:
            self.state.active_counts[task.user] = self.state.active_counts.get(task.user, 0) + 1
        if status in {TaskStatus.FAILED, TaskStatus.SUCCEEDED}:
            self.state.active_counts[task.user] = max(0, self.state.active_counts.get(task.user, 1) - 1)

    def _fair_share_score(self, task: Task) -> float:
        active = self.state.active_counts.get(task.user, 0)
        score = PRIORITY_WEIGHT[task.priority] - (active * 0.1)
        if self._is_night() and task.priority == Priority.LOW:
            score += self.policy.night_low_bonus
        return score

    def _is_night(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now()
        start = self._parse_time(self.policy.night_start)
        end = self._parse_time(self.policy.night_end)
        if start <= end:
            return start <= now.time() <= end
        return now.time() >= start or now.time() <= end

    @staticmethod
    def _parse_time(value: str) -> dt_time:
        parts = value.split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        return dt_time(hour=hour, minute=minute)

    def _ordered_pending(self) -> List[Task]:
        pending = [self.state.tasks[tid] for tid in self.state.pending_queue]
        pending = [t for t in pending if t.status == TaskStatus.PENDING]
        return sorted(pending, key=lambda t: (-self._fair_share_score(t), t.submit_ts))

    def _node_fits(self, task: Task, node: Node, gpu) -> bool:
        if task.gpu_type and node.gpu_type and task.gpu_type != node.gpu_type:
            return False
        return gpu.free_vram_gb >= task.min_vram_gb and not gpu.zombie

    def _head_schedulable(self, head: Task, nodes: List[Node]) -> bool:
        for node in nodes:
            for gpu in node.gpus:
                if self._node_fits(head, node, gpu):
                    return True
        return False

    def _backfill_ok(self, task: Task) -> bool:
        if task.time_limit_s is None:
            return False
        return task.time_limit_s <= self.policy.backfill_time_limit_s

    def schedule(self, nodes: List[Node]) -> List[Tuple[int, str, int]]:
        assignments: List[Tuple[int, str, int]] = []
        ordered = self._ordered_pending()
        if not ordered:
            return assignments

        head = ordered[0]
        head_schedulable = self._head_schedulable(head, nodes)

        for task in ordered:
            if task.status != TaskStatus.PENDING:
                continue
            if task != head and not head_schedulable:
                if not self._backfill_ok(task) and not (self._is_night() and task.priority == Priority.LOW):
                    continue
            assigned = False
            for node in nodes:
                for gpu in node.gpus:
                    if self._node_fits(task, node, gpu):
                        assignments.append((task.task_id, node.name, gpu.gpu_id))
                        gpu.used_vram_gb += task.min_vram_gb
                        task.assigned_node = node.name
                        task.assigned_gpu = gpu.gpu_id
                        task.start_ts = time.time()
                        self.update_task_status(task.task_id, TaskStatus.RUNNING)
                        assigned = True
                        break
                if assigned:
                    break
        return assignments

    def apply_oom_recovery(self, task_id: int, missing_gb: float) -> None:
        task = self.state.tasks[task_id]
        new_min = task.min_vram_gb + missing_gb + 1.0
        task.min_vram_gb = round(new_min, 2)
        task.retry_count += 1
        task.status = TaskStatus.PENDING
        if task_id not in self.state.pending_queue:
            self.state.pending_queue.append(task_id)

    def move_to_front(self, task_id: int) -> None:
        if task_id in self.state.pending_queue:
            self.state.pending_queue.remove(task_id)
        self.state.pending_queue.insert(0, task_id)

    def reset_task(self, task_id: int) -> None:
        task = self.state.tasks[task_id]
        task.status = TaskStatus.PENDING
        task.assigned_node = None
        task.assigned_gpu = None
        task.start_ts = None
        if task_id not in self.state.pending_queue:
            self.state.pending_queue.append(task_id)
