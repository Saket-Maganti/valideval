from __future__ import annotations

from pathlib import Path
from typing import Any

from valideval.benchmarks.gsm8k import inspect_gsm8k_schema
from valideval.benchmarks.truthfulqa import inspect_truthfulqa_schema
from valideval.no_run_preflight import (
    NO_RUN_FORBIDDEN_ACTIONS,
    load_yaml_config,
    manifest_status,
    path_status,
    require_dry_run,
    write_manifest,
)


def build_benchmark_preflight(
    *,
    config: str | Path,
    output: str | Path,
    dry_run: bool,
    execute_evaluation: bool = False,
) -> dict[str, Any]:
    require_dry_run(
        dry_run=dry_run,
        execute=execute_evaluation,
        execute_flag="--execute-evaluation",
        action="second benchmark preflight",
    )
    config_check = path_status(config, required=True)
    checks = [config_check]
    payload: dict[str, Any] = {
        "mode": "dry_run_only",
        "config_check": config_check,
        "forbidden_actions": NO_RUN_FORBIDDEN_ACTIONS,
        "download_run": False,
        "evaluation_run": False,
        "notes": [
            "This preflight checks config and optional fixture schema only.",
            "It does not download benchmark data or run evaluations.",
        ],
    }
    if config_check["exists"]:
        data = load_yaml_config(config)
        benchmark = str(data.get("benchmark_id", data.get("benchmark", "")))
        fixture = data.get("fixture_path")
        payload["benchmark_id"] = benchmark
        payload["claim_state"] = data.get("claim_state", "RESULT_REQUIRED")
        payload["planned_outputs"] = data.get("planned_outputs", [])
        if fixture and benchmark == "gsm8k":
            payload["fixture_schema"] = inspect_gsm8k_schema(fixture)
            checks.append(payload["fixture_schema"])
        elif fixture and benchmark == "truthfulqa":
            payload["fixture_schema"] = inspect_truthfulqa_schema(fixture)
            checks.append(payload["fixture_schema"])
        elif fixture:
            payload["fixture_schema"] = path_status(fixture, required=False)
            checks.append(payload["fixture_schema"])
    payload["status"] = manifest_status(*checks)
    manifest_path = write_manifest(output, payload)
    payload["manifest_path"] = str(manifest_path)
    return payload
