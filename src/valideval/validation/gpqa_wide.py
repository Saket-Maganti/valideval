from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from valideval.diagnostics.panel_validity import write_panel_validity_report


def gpqa_wide_readiness(
    *,
    predictions_path: str | Path,
    matrix_path: str | Path,
    output_path: str | Path = "GPQA_WIDE_PANEL_READINESS.md",
    min_models: int = 50,
    min_items: int = 198,
    chance: float = 0.25,
) -> dict[str, Any]:
    predictions = Path(predictions_path)
    matrix = Path(matrix_path)
    blockers = []
    if not predictions.exists():
        blockers.append("missing_wide_predictions")
    if not matrix.exists():
        blockers.append("missing_wide_matrix")
    panel_payload: dict[str, Any] | None = None
    if matrix.exists():
        report_dir = Path(output_path).with_suffix("")
        panel_payload = write_panel_validity_report(
            matrix,
            report_dir,
            chance=chance,
            min_models=min_models,
            min_items=min_items,
        )
        blockers.extend(panel_payload.get("blockers", []))
    payload = {
        "schema_version": "0.1",
        "status": "ready" if not blockers else "blocked",
        "predictions_path": str(predictions),
        "matrix_path": str(matrix),
        "min_models": min_models,
        "min_items": min_items,
        "blockers": sorted(set(blockers)),
        "panel_validity": panel_payload,
        "warnings": [
            "Small local GPQA panels remain protocol-only. Public artifacts must not expose raw GPQA question text."
        ],
    }
    Path(output_path).write_text(_render_gpqa_readiness(payload), encoding="utf-8")
    Path(output_path).with_suffix(".json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return payload


def _render_gpqa_readiness(payload: dict[str, Any]) -> str:
    lines = [
        "# GPQA Wide-Panel Readiness",
        "",
        f"- Status: `{payload['status']}`",
        f"- Predictions: `{payload['predictions_path']}`",
        f"- Matrix: `{payload['matrix_path']}`",
        f"- Minimum models: {payload['min_models']}",
        f"- Minimum items: {payload['min_items']}",
        "",
        "Small local GPQA results are protocol feasibility only, not item-validity evidence.",
    ]
    if payload["blockers"]:
        lines.extend(["", "## Blockers", *[f"- `{blocker}`" for blocker in payload["blockers"]]])
    return "\n".join(lines) + "\n"
