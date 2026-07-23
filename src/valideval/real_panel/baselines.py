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

BASELINE_SPECS = [
    {
        "name": "accuracy_only_ranking",
        "claim_state": "RESULT_REQUIRED",
        "description": "Compare the future validity-adjusted ordering to plain accuracy.",
    },
    {
        "name": "random_item_subset",
        "claim_state": "RESULT_REQUIRED",
        "description": "Estimate whether future findings survive random item subsets.",
    },
    {
        "name": "subject_stratified_subset",
        "claim_state": "RESULT_REQUIRED",
        "description": "Check whether subject composition explains future rank changes.",
    },
    {
        "name": "naive_difficulty",
        "claim_state": "RESULT_REQUIRED",
        "description": "Use item difficulty alone as a confounding baseline.",
    },
    {
        "name": "naive_disagreement",
        "claim_state": "RESULT_REQUIRED",
        "description": "Use raw model disagreement without validity diagnostics.",
    },
    {
        "name": "diagnostic_vs_diagnostic",
        "claim_state": "RESULT_REQUIRED",
        "description": "Compare diagnostic families against one another.",
    },
    {
        "name": "mmlu_redux_external_label",
        "claim_state": "BLOCKED_UNTIL_DIRECT_HASH_ALIGNMENT",
        "description": "Treat MMLU-Redux as weak/negative external stress-test evidence.",
    },
    {
        "name": "subject_confounding",
        "claim_state": "RESULT_REQUIRED",
        "description": "Check subject labels as a confounding explanation.",
    },
]


def build_baseline_dry_run_manifest(
    *,
    config: str | Path,
    output: str | Path,
    dry_run: bool,
    execute_confirmatory_real_panel: bool = False,
) -> dict[str, Any]:
    require_dry_run(
        dry_run=dry_run,
        execute=execute_confirmatory_real_panel,
        execute_flag="--execute-confirmatory-real-panel",
        action="real-panel baseline scaffold",
    )
    config_check = path_status(config, required=True)
    payload: dict[str, Any] = {
        "mode": "dry_run_only",
        "status": manifest_status(config_check),
        "evidence_state": "RESULT_REQUIRED",
        "config_check": config_check,
        "baseline_specs": BASELINE_SPECS,
        "planned_outputs": [
            "real_panel_baseline_comparison.json",
            "real_panel_baseline_comparison.md",
            "real_panel_baseline_comparison.csv",
        ],
        "forbidden_actions": NO_RUN_FORBIDDEN_ACTIONS,
        "notes": [
            "No baseline metrics are computed by this scaffold.",
            "MMLU-Redux baseline claims remain blocked until direct/hash alignment exists.",
        ],
    }
    if config_check["exists"]:
        data = load_yaml_config(config)
        payload["config"] = {
            "benchmark": data.get("benchmark"),
            "panel": data.get("panel"),
            "matrix_path": data.get("matrix_path"),
            "baseline_count": len(data.get("baselines", [])),
        }
    manifest_path = write_manifest(output, payload)
    payload["manifest_path"] = str(manifest_path)
    return payload


def compute_baseline_metrics(*args: Any, **kwargs: Any) -> None:
    raise NotImplementedError(
        "Real-panel baseline computation is RESULT_REQUIRED and disabled in the no-run build."
    )
