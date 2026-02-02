from lab_gpu.sdk import LabGpuTimeoutError, Placement


def test_sdk_exports_types():
    assert LabGpuTimeoutError
    assert Placement
