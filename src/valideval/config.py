from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML config must contain a mapping at top level: {source}")
    return data


def load_default_config(path: str | Path = "configs/default.yaml") -> dict[str, Any]:
    source = Path(path)
    if not source.exists():
        return {}
    return load_yaml(source)
