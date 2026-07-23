from __future__ import annotations

from pathlib import Path
from typing import Any

from valideval.calibration.logprob_schema import inspect_logprob_schema
from valideval.no_run_preflight import (
    NO_RUN_FORBIDDEN_ACTIONS,
    load_yaml_config,
    manifest_status,
    path_status,
    require_dry_run,
    write_manifest,
)

FUTURE_CALIBRATION_METRICS = [
    "ECE",
    "adaptive_ECE",
    "Brier",
    "NLL",
    "accuracy_confidence_curve",
    "calibration_by_subject",
    "calibration_by_diagnostic_flag",
]


def build_calibration_preflight(
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
        action="calibration preflight",
    )
    config_check = path_status(config, required=True)
    checks = [config_check]
    payload: dict[str, Any] = {
        "mode": "dry_run_only",
        "config_check": config_check,
        "future_metrics": FUTURE_CALIBRATION_METRICS,
        "metrics_computed": False,
        "forbidden_actions": NO_RUN_FORBIDDEN_ACTIONS,
    }
    if config_check["exists"]:
        data = load_yaml_config(config)
        input_path = data.get("logprob_input")
        payload["benchmark"] = data.get("benchmark")
        payload["claim_state"] = data.get("claim_state", "BLOCKED_UNTIL_LOGPROB_OUTPUTS_EXIST")
        if input_path:
            payload["input_schema"] = inspect_logprob_schema(input_path)
            checks.append(payload["input_schema"])
        else:
            payload["input_schema"] = {
                "path": None,
                "required": False,
                "status": "not_supplied",
                "schema_status": "not_checked",
            }
    payload["status"] = manifest_status(*checks)
    manifest_path = write_manifest(output, payload)
    payload["manifest_path"] = str(manifest_path)
    return payload
