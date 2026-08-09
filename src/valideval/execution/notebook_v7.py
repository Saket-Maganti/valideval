from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from valideval.execution.config import load_run_config, load_yaml_mapping, semantic_config_hash
from valideval.execution.models import load_panel_config
from valideval.execution.notebook import build_fixture_run
from valideval.execution.runner import (
    _apply_robustness_contract,
    _load_contract,
    _validate_robustness_panel,
    run_from_config,
)


def run_notebook_config_v7(
    config_path: str | Path,
    *,
    mode: str = "fixture",
    output_root: str | Path = "kaggle_v7_outputs",
) -> dict[str, Any]:
    """Validate a V7 config and run either a non-evidence fixture or the exact run."""

    source = Path(config_path).resolve()
    root = _repository_root(source)
    config = load_run_config(source, repository_root=root)
    if config.schema_version != "7.0":
        raise ValueError("the V7 notebook runner rejects non-V7 configurations")
    panel = load_panel_config(root / config.panel_config)
    contract = _load_contract(root / config.benchmark_contract, config.benchmark_id)
    if config.robustness_config:
        robustness = load_yaml_mapping(root / config.robustness_config)
        contract = _apply_robustness_contract(contract, robustness, config.benchmark_id)
        _validate_robustness_panel(panel, robustness)
    if mode == "fixture":
        result = build_fixture_run(
            config.benchmark_id,
            Path(output_root),
            run_suffix=f"{config.stage.lower()}-{config.run_id}",
        )
        return {
            **result,
            "schema_version": "7.0",
            "production_config_hash": semantic_config_hash(config),
            "production_config_validated": True,
            "production_model_count": len(panel["models"]),
            "production_item_count": int(contract["expected_item_count"]),
            "evidence_class": "NON_EVIDENCE_FIXTURE",
        }
    allowed = {
        config.mode,
        "resume",
        "validate_only",
        "package_only",
    }
    if mode not in allowed:
        raise ValueError(
            f"mode {mode!r} is not allowed for {config.stage}; expected {sorted(allowed)}"
        )
    override = None if mode == config.mode else mode
    return run_from_config(source, mode_override=override, output_root=output_root)


def _repository_root(source: Path) -> Path:
    configured = os.environ.get("VALIDEVAL_REPOSITORY_ROOT", "").strip()
    if configured:
        return Path(configured).resolve()
    for parent in (source.parent, *source.parents):
        if (parent / "pyproject.toml").is_file() and (parent / "src/valideval").is_dir():
            return parent
    raise ValueError(f"could not locate ValidEval repository from {source}")
