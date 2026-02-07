"""Lab GPU scheduler package."""

from .sdk import Client, LabGpuTimeoutError, Placement

try:  # optional server API
    from .server_api import app as server_app
except Exception:  # pragma: no cover - optional dependency
    server_app = None

__all__ = ["Client", "LabGpuTimeoutError", "Placement", "server_app"]
