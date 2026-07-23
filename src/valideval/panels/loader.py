from __future__ import annotations

from pathlib import Path
from typing import Any

from valideval.no_run_preflight import load_yaml_config


def load_panel_preflight_config(path: str | Path) -> dict[str, Any]:
    data = load_yaml_config(path)
    if "panel_id" not in data:
        raise ValueError("Panel config requires panel_id.")
    models = data.get("models", [])
    if not isinstance(models, list) or not models:
        raise ValueError("Panel config requires a non-empty models list.")
    for index, row in enumerate(models):
        if not isinstance(row, dict) or not row.get("model_id"):
            raise ValueError(f"Panel model row {index} requires model_id.")
    return data
