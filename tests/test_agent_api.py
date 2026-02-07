from lab_gpu.agent_api import run


def test_agent_run_endpoint():
    resp = run({"task_id": 1, "cmd": "python -c 'print(1)'", "mem_used": 0, "log_root": "/tmp"})
    assert "exit_code" in resp
