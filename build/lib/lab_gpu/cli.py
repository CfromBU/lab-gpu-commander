from __future__ import annotations

import json
import time
from typing import Any, Optional
import typer

from .agent import Agent
from .master import Master
from .models import GPU, Node, Priority, Task
from .policy import load_policy
from .tui import LabTui

app = typer.Typer(add_completion=False)
server_app = typer.Typer()
agent_app = typer.Typer()
app.add_typer(server_app, name="server")
app.add_typer(agent_app, name="agent")

_master = Master()


def _parse_mem_gb(value: str) -> float:
    return float(value.rstrip("Gg"))


def _task_from_payload(payload: dict[str, Any], task_id: int) -> Task:
    mem_value = payload.get("mem")
    if mem_value is None:
        mem_value = payload.get("min_vram_gb")
    if mem_value is None:
        raise typer.BadParameter("Task requires 'mem' like '10G' or 'min_vram_gb'.")
    mem_gb = _parse_mem_gb(str(mem_value))
    priority = Priority(payload.get("priority", Priority.NORMAL))
    return Task(
        task_id=task_id,
        user=payload.get("user", "me"),
        cmd=payload["cmd"],
        min_vram_gb=mem_gb,
        priority=priority,
        env=payload.get("env"),
        gpu_type=payload.get("gpu_type"),
        time_limit_s=payload.get("time_limit"),
    )


@server_app.command("start")
def server_start(
    role: str = typer.Option(..., "--role"),
    host: str = typer.Option("127.0.0.1", "--host"),
    policy: Optional[str] = typer.Option(None, "--policy"),
) -> None:
    if policy:
        config = load_policy(policy)
        if config:
            _master.scheduler.policy.night_start = config.night_start
            _master.scheduler.policy.night_end = config.night_end
            _master.scheduler.policy.base_idle_util_threshold = config.base_idle_util_threshold
            _master.scheduler.policy.night_idle_util_threshold = config.night_idle_util_threshold
            _master.scheduler.policy.backfill_time_limit_s = config.backfill_time_limit_s
            _master.scheduler.policy.night_low_bonus = config.night_low_bonus
            typer.echo(f"Loaded policy from {policy}")
        else:
            typer.echo(f"Policy file {policy} not loaded, using defaults.")
    typer.echo(f"Starting lab-gpu {role} on {host} (demo mode)")

@server_app.command("add-node")
def server_add_node(
    name: str = typer.Option(..., "--name"),
    gpus: int = typer.Option(1, "--gpus"),
    vram: float = typer.Option(24.0, "--vram"),
    gpu_type: Optional[str] = typer.Option(None, "--gpu-type"),
) -> None:
    gpu_list = [GPU(gpu_id=i, total_vram_gb=vram, used_vram_gb=0.0) for i in range(gpus)]
    _master.register_node(Node(name=name, gpus=gpu_list, gpu_type=gpu_type))
    typer.echo(f"Registered node {name} ({gpus} GPU)")

@server_app.command("tick")
def server_tick() -> None:
    assignments = _master.schedule_once()
    if not assignments:
        typer.echo("No assignments made.")
        raise typer.Exit(code=0)
    for task_id, node, gpu_id in assignments:
        typer.echo(f"Assigned task {task_id} -> {node} gpu:{gpu_id}")


@server_app.command("preempt")
def server_preempt(
    task_id: int = typer.Option(..., "--task-id"),
    soft_timeout: int = typer.Option(300, "--soft-timeout"),
    term_timeout: int = typer.Option(30, "--term-timeout"),
) -> None:
    result = _master.preempt_task(task_id, soft_timeout_s=soft_timeout, term_timeout_s=term_timeout)
    typer.echo(f"Preemption result: {result}")


@app.command()
def submit(
    cmd: str = typer.Argument(...),
    mem: str = typer.Option(..., "--mem"),
    priority: Priority = typer.Option(Priority.NORMAL, "--priority"),
    env: Optional[str] = typer.Option(None, "--env"),
    gpu_type: Optional[str] = typer.Option(None, "--gpu-type"),
    time_limit: Optional[int] = typer.Option(None, "--time-limit"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    mem_gb = _parse_mem_gb(mem)
    task = Task(
        task_id=len(_master.scheduler.state.tasks) + 1,
        user="me",
        cmd=cmd,
        min_vram_gb=mem_gb,
        priority=priority,
        env=env,
        gpu_type=gpu_type,
        time_limit_s=time_limit,
    )
    if dry_run:
        placement = None
        for node in _master.state.nodes.values():
            for gpu in node.gpus:
                if gpu.free_vram_gb >= task.min_vram_gb:
                    placement = {"node": node.name, "gpu": gpu.gpu_id}
                    break
            if placement:
                break
        typer.echo(
            json.dumps(
                {
                    "task_id": task.task_id,
                    "min_vram_gb": task.min_vram_gb,
                    "priority": task.priority.value,
                    "placement": placement,
                }
            )
        )
        raise typer.Exit(code=0)
    _master.submit(task)
    typer.echo(f"Submitted task {task.task_id}")


@app.command("submit-batch")
def submit_batch(
    file: str = typer.Option(..., "--file"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    try:
        with open(file, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        raise typer.BadParameter(f"File not found: {file}")
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"Invalid JSON: {exc}")

    tasks_payload = payload.get("tasks") if isinstance(payload, dict) else payload
    if not isinstance(tasks_payload, list):
        raise typer.BadParameter("Batch file must be a list or contain a top-level 'tasks' list.")

    results = []
    for entry in tasks_payload:
        if not isinstance(entry, dict):
            raise typer.BadParameter("Each task entry must be a JSON object.")
        task = _task_from_payload(entry, task_id=len(_master.scheduler.state.tasks) + 1)
        if dry_run:
            placement = None
            for node in _master.state.nodes.values():
                for gpu in node.gpus:
                    if gpu.free_vram_gb >= task.min_vram_gb:
                        placement = {"node": node.name, "gpu": gpu.gpu_id}
                        break
                if placement:
                    break
            results.append(
                {
                    "task_id": task.task_id,
                    "min_vram_gb": task.min_vram_gb,
                    "priority": task.priority.value,
                    "placement": placement,
                }
            )
        else:
            _master.submit(task)
            results.append({"task_id": task.task_id, "status": "submitted"})

    typer.echo(json.dumps(results))


@app.command()
def status(json_output: bool = typer.Option(False, "--json")) -> None:
    payload = _master.summary()
    payload["running"] = payload.pop("running_tasks")
    if json_output:
        typer.echo(json.dumps(payload))
    else:
        typer.echo(
            f"Tasks: {payload['tasks']} Pending: {payload['pending']} "
            f"Running: {len(payload['running'])} OOMs: {payload['ooms']}"
        )


@app.command()
def logs(task_id: int, follow: bool = typer.Option(False, "-f")) -> None:
    path = f"/nas/logs/{task_id}.log"
    try:
        with open(path, "r", encoding="utf-8") as f:
            if not follow:
                typer.echo(path)
                return
            f.seek(0, 2)
            while True:
                line = f.readline()
                if line:
                    typer.echo(line.rstrip("\n"))
                else:
                    time.sleep(0.5)
    except FileNotFoundError:
        typer.echo("Log file not found. Task may not have started yet.")


@app.command()
def tui() -> None:
    LabTui(_master).run()


@agent_app.command("run")
def agent_run(
    task_id: int = typer.Option(..., "--task-id"),
    mem_used: float = typer.Option(0.0, "--mem-used"),
    env: Optional[str] = typer.Option(None, "--env"),
    log_root: str = typer.Option("/nas/logs", "--log-root"),
    cmd: str = typer.Argument(...),
) -> None:
    agent = Agent(on_oom=_master.on_oom)
    if task_id not in _master.scheduler.state.tasks:
        task = Task(
            task_id=task_id,
            user="me",
            cmd=cmd,
            min_vram_gb=mem_used if mem_used > 0 else 0.0,
            priority=Priority.NORMAL,
            env=env,
        )
        _master.submit(task)
    try:
        exit_code, oom = agent.run_task(
            task_id,
            cmd,
            env,
            current_used_gb=mem_used,
            log_root=log_root,
            on_start=lambda pid, log_path: _master.register_runtime(task_id, pid, log_path),
        )
    except PermissionError as exc:
        typer.echo(f"Log path error: {exc}")
        raise typer.Exit(code=1)
    _master.clear_runtime(task_id)
    if exit_code == 0:
        _master.mark_succeeded(task_id)
    else:
        if oom:
            typer.echo(f"OOM detected for task {task_id}. New min VRAM: {oom.new_min_vram_gb}G")
        else:
            _master.mark_failed(task_id)
    raise typer.Exit(code=exit_code)


if __name__ == "__main__":
    app()
