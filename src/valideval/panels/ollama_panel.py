from __future__ import annotations

from pathlib import Path
from typing import Any

from valideval.no_run_preflight import (
    NO_RUN_FORBIDDEN_ACTIONS,
    manifest_status,
    path_status,
    require_dry_run,
    write_manifest,
)
from valideval.panels.loader import load_panel_preflight_config


def build_ollama_panel_preflight(
    *,
    config: str | Path,
    output: str | Path,
    dry_run: bool,
    execute_inference: bool = False,
) -> dict[str, Any]:
    require_dry_run(
        dry_run=dry_run,
        execute=execute_inference,
        execute_flag="--execute-inference",
        action="Ollama panel preflight",
    )
    config_check = path_status(config, required=True)
    payload: dict[str, Any] = {
        "mode": "dry_run_only",
        "status": manifest_status(config_check),
        "config_check": config_check,
        "server_contacted": False,
        "inference_run": False,
        "forbidden_actions": NO_RUN_FORBIDDEN_ACTIONS,
        "benchmark_compatibility": [],
        "planned_models": [],
        "notes": [
            "This preflight validates config metadata only.",
            "It does not call an Ollama server and does not generate model outputs.",
        ],
    }
    if config_check["exists"]:
        data = load_panel_preflight_config(config)
        payload["panel_id"] = data.get("panel_id")
        payload["runner"] = data.get("runner", "ollama")
        payload["planned_models"] = [
            {
                "model_id": str(row.get("model_id")),
                "role": row.get("role", "local_candidate"),
                "requires_inference": True,
            }
            for row in data.get("models", [])
        ]
        payload["benchmark_compatibility"] = data.get(
            "benchmark_compatibility",
            ["toy_mcq", "mmlu", "gpqa_diamond", "gsm8k", "truthfulqa"],
        )
    manifest_path = write_manifest(output, payload)
    payload["manifest_path"] = str(manifest_path)
    return payload
