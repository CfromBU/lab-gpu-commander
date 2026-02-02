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
