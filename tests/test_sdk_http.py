from lab_gpu.sdk import HttpBackend


def test_http_backend_placeholder():
    backend = HttpBackend(base_url="http://localhost:8000")
    assert backend.base_url
