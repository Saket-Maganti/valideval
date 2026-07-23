from __future__ import annotations

from pathlib import Path
from typing import Any

from valideval.no_run_preflight import (
    NO_RUN_FORBIDDEN_ACTIONS,
    load_yaml_config,
    manifest_status,
    path_status,
    require_dry_run,
    write_manifest,
)

FUTURE_POWER_MATERIALITY_METRICS = [
    "minimum_detectable_effect",
    "expected_ci_width",
    "sample_size_item_count_sensitivity",
    "false_positive_budget",
    "materiality_threshold",
    "detectability_vs_materiality_gap",
]


def build_power_materiality_preflight(
    *,
    config: str | Path,
    output: str | Path,
    dry_run: bool,
    execute_analysis: bool = False,
) -> dict[str, Any]:
    require_dry_run(
        dry_run=dry_run,
        execute=execute_analysis,
        execute_flag="--execute-analysis",
        action="power/materiality preflight",
    )
    config_check = path_status(config, required=True)
    payload: dict[str, Any] = {
        "mode": "dry_run_only",
        "status": manifest_status(config_check),
        "config_check": config_check,
        "future_metrics": FUTURE_POWER_MATERIALITY_METRICS,
        "simulations_run": False,
        "metrics_computed": False,
        "claim_state": "RESULT_REQUIRED",
        "forbidden_actions": NO_RUN_FORBIDDEN_ACTIONS,
    }
    if config_check["exists"]:
        data = load_yaml_config(config)
        payload["benchmark"] = data.get("benchmark")
        payload["claim_state"] = data.get("claim_state", payload["claim_state"])
        payload["planned_item_counts"] = data.get("planned_item_counts", [])
        payload["planned_effect_sizes"] = data.get("planned_effect_sizes", [])
    manifest_path = write_manifest(output, payload)
    payload["manifest_path"] = str(manifest_path)
    return payload
