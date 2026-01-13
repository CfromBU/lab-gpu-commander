from __future__ import annotations

from dataclasses import dataclass
import os
import re
import signal
import subprocess
import threading
from typing import Iterable, Optional, Tuple

from .models import OOMSignal


OOM_REGEX = re.compile(
    r"RuntimeError: CUDA out of memory.*?Tried to allocate ([0-9.]+) ([A-Za-z]+)",
    re.IGNORECASE,
)


@dataclass
class ProcessSample:
    pid: int
    used_vram_gb: float
    util_pct: float
    io_read_kb: float
    io_write_kb: float
    duration_s: float


class Agent:
    def __init__(self, on_oom=None) -> None:
        self.on_oom = on_oom

    def parse_oom(self, stderr_lines: Iterable[str], current_used_gb: float) -> Optional[OOMSignal]:
        tail = list(stderr_lines)[-100:]
        for line in reversed(tail):
            match = OOM_REGEX.search(line)
            if match:
                amount = float(match.group(1))
                unit = match.group(2).lower()
                missing_gb = amount
                if unit.startswith("mi"):
                    missing_gb = amount / 1024
                elif unit.startswith("ki"):
                    missing_gb = amount / (1024 * 1024)
                elif unit.startswith("gi"):
                    missing_gb = amount
                new_min = current_used_gb + missing_gb + 1.0
                return OOMSignal(task_id=-1, missing_gb=round(missing_gb, 2), new_min_vram_gb=round(new_min, 2))
        return None

    def handle_process_exit(self, task_id: int, exit_code: int, stderr_lines: Iterable[str], current_used_gb: float) -> Optional[OOMSignal]:
        if exit_code == 0:
            return None
        oom = self.parse_oom(stderr_lines, current_used_gb)
        if oom:
            oom.task_id = task_id
            if self.on_oom:
                self.on_oom(oom)
        return oom

    def detect_zombies(self, samples: Iterable[ProcessSample], util_threshold: float = 1.0, min_duration_s: float = 300.0) -> list[int]:
        zombies = []
        for sample in samples:
            if sample.used_vram_gb <= 0:
                continue
            if sample.util_pct <= util_threshold and sample.duration_s >= min_duration_s:
                if sample.io_read_kb == 0 and sample.io_write_kb == 0:
                    zombies.append(sample.pid)
        return zombies

    def soft_preempt(self, pid: int, log_path: str) -> None:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("[WARN] Preemption requested. Please save checkpoint within 5 mins.\n")
            f.flush()
        os.kill(pid, signal.SIGUSR1)

    def hard_preempt(self, pid: int) -> None:
        os.kill(pid, signal.SIGTERM)

    def force_kill(self, pid: int) -> None:
        os.kill(pid, signal.SIGKILL)

    def build_command(self, cmd: str, env: Optional[str]) -> str:
        if env:
            return f"source ~/anaconda3/etc/profile.d/conda.sh && conda activate {env} && {cmd}"
        return cmd

    def run_task(
        self,
        task_id: int,
        cmd: str,
        env: Optional[str],
        current_used_gb: float,
        log_root: str = "/nas/logs",
        on_start=None,
    ) -> Tuple[int, Optional[OOMSignal]]:
        try:
            os.makedirs(log_root, exist_ok=True)
        except PermissionError as exc:  # pragma: no cover - environment dependent
            raise PermissionError(f"Cannot create log directory {log_root}") from exc
        log_path = os.path.join(log_root, f"{task_id}.log")
        stderr_lines: list[str] = []

        with open(log_path, "a", encoding="utf-8", buffering=1) as log_file:
            full_cmd = self.build_command(cmd, env)
            proc = subprocess.Popen(
                ["bash", "-lc", full_cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            if on_start:
                on_start(proc.pid, log_path)

            def _stream(stream):
                for line in iter(stream.readline, ""):
                    log_file.write(line)
                    if stream is proc.stderr:
                        stderr_lines.append(line.rstrip("\n"))
                stream.close()

            threads = []
            if proc.stdout:
                threads.append(threading.Thread(target=_stream, args=(proc.stdout,)))
            if proc.stderr:
                threads.append(threading.Thread(target=_stream, args=(proc.stderr,)))
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            exit_code = proc.wait()

        oom = self.handle_process_exit(task_id, exit_code, stderr_lines, current_used_gb)
        return exit_code, oom
