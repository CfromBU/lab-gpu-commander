from lab_gpu.http_models import AgentRegister, TaskSubmit
from lab_gpu.server_api import register, submit, tick


def test_master_register_and_submit():
    resp = register(AgentRegister(node="node-1", gpus=[{"id": 0, "total_vram_gb": 24.0}]))
    assert resp["ok"] is True
    resp = submit(TaskSubmit(cmd="python train.py", mem="10G", priority="normal"))
    assert resp["ok"] is True
    resp = tick()
    assert "assignments" in resp
