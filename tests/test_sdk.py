from lab_gpu.sdk import LabGpuTimeoutError, Placement


def test_sdk_exports_types():
    assert LabGpuTimeoutError
    assert Placement

import os
from lab_gpu.sdk import Client


def test_acquire_sets_env(monkeypatch):
    client = Client()
    placement = client.acquire(mem="1G", timeout=0)
    assert placement
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == str(placement.gpu_id)
    assert os.environ.get("LABGPU_ASSIGNED_NODE") == placement.node
    assert os.environ.get("LABGPU_ASSIGNED_GPU") == str(placement.gpu_id)

import pytest
from lab_gpu.sdk import LabGpuTimeoutError


def test_timeout_zero_raises():
    client = Client()
    with pytest.raises(LabGpuTimeoutError):
        client.request_device(mem="999G", timeout=0)


def test_run_returns_exit_code():
    client = Client()
    result = client.run(cmd="python -c 'import sys; sys.exit(2)'", mem="1G", log_root="/tmp")
    assert result.exit_code == 2
