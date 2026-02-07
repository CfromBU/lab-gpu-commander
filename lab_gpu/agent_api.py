from __future__ import annotations

from fastapi import FastAPI

from .agent import Agent

app = FastAPI()
_agent = Agent()


@app.post("/run")
def run(payload: dict) -> dict:
    task_id = int(payload.get("task_id", 0))
    cmd = payload.get("cmd")
    env = payload.get("env")
    mem_used = float(payload.get("mem_used", 0.0))
    log_root = payload.get("log_root", "/nas/logs")
    exit_code, oom = _agent.run_task(
        task_id=task_id,
        cmd=cmd,
        env=env,
        current_used_gb=mem_used,
        log_root=log_root,
    )
    return {"exit_code": exit_code, "oom": None if oom is None else oom.__dict__}
