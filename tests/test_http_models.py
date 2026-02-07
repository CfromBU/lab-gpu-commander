from lab_gpu.http_models import AgentRegister, TaskSubmit


def test_http_models_validate():
    AgentRegister(node="node-1", gpus=[{"id": 0, "total_vram_gb": 24.0, "type": "3090"}])
    TaskSubmit(cmd="python train.py", mem="10G", priority="normal")
