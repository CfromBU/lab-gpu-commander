from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None


@dataclass
class PolicyConfig:
    night_start: str = "00:00"
    night_end: str = "08:00"
    base_idle_util_threshold: float = 0.05
    night_idle_util_threshold: float = 0.20
    backfill_time_limit_s: int = 3600
    night_low_bonus: float = 0.5


def _parse_simple_yaml(text: str) -> dict:
    data: dict = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, val = line.split(":", 1)
        data[key.strip()] = val.strip().strip('"').strip("'")
    return data


def load_policy(path: str) -> Optional[PolicyConfig]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return None

    payload = None
    if yaml is not None:
        try:
            payload = yaml.safe_load(content)
        except Exception:
            payload = None
    if payload is None:
        payload = _parse_simple_yaml(content)

    if not isinstance(payload, dict):
        return None

    config = PolicyConfig()
    for key, value in payload.items():
        if not hasattr(config, key):
            continue
        field = getattr(config, key)
        if isinstance(field, float):
            setattr(config, key, float(value))
        elif isinstance(field, int):
            setattr(config, key, int(value))
        else:
            setattr(config, key, str(value))
    return config
