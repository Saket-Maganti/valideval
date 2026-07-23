from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from valideval.diagnostics.panel_validity import write_panel_validity_report
from valideval.io.jsonl import write_jsonl
from valideval.validation.external_flag_validation import validate_flags_against_ground_truth


def run_mmlu_redux_validation(
    *,
    predictions_path: str | Path,
    matrix_path: str | Path,
    ground_truth_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    predictions = Path(predictions_path)
    matrix = Path(matrix_path)
    ground_truth = Path(ground_truth_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    missing = [
        name
        for name, path in {
            "predictions": predictions,
            "matrix": matrix,
            "ground_truth": ground_truth,
        }.items()
        if not path.exists()
    ]
    if missing:
        payload = {
            "schema_version": "0.1",
            "status": "blocked",
            "missing_inputs": missing,
            "required_inputs": {
                "predictions": str(predictions),
                "matrix": str(matrix),
                "ground_truth": str(ground_truth),
            },
            "warnings": ["No MMLU-Redux claims should be made until all inputs exist."],
        }
        _write_readiness(destination, payload)
        return payload

    panel = write_panel_validity_report(
        matrix, destination / "panel_validity", min_models=30, min_items=20
    )
    flags_path = destination / "flags.jsonl"
    _derive_matrix_flags(matrix, flags_path)
    metrics = validate_flags_against_ground_truth(
        flags_path,
        ground_truth,
        destination,
        benchmark="mmlu",
        bootstrap_samples=100,
    )
    payload = {
        "schema_version": "0.1",
        "status": "ok" if panel["status"] == "pass" else "blocked_panel",
        "panel_validity": panel,
        "external_validation": metrics,
        "artifacts": {
            "readme": str(destination / "README.md"),
            "metrics": str(destination / "metrics.json"),
            "joined": str(destination / "joined.jsonl"),
            "paper_table": str(destination / "paper_table_mmlu_redux.md"),
        },
    }
    _write_readiness(destination, payload)
    _write_paper_table(destination, metrics)
    return payload


def _derive_matrix_flags(matrix_path: Path, flags_path: Path) -> None:
    frame = pd.read_csv(matrix_path, index_col=0).astype(float)
    item_mean = frame.mean(axis=0, skipna=True)
    item_std = frame.std(axis=0, skipna=True)
    rows = []
    for item_key in frame.columns:
        subset, item_id = _split_item_key(str(item_key))
        mean = float(item_mean[item_key])
        std = float(item_std[item_key])
        rows.append(
            {
                "benchmark": "mmlu",
                "subset": subset,
                "item_id": item_id,
                "diagnostic": "matrix_item_anomaly",
                "score": max(abs(mean - 0.5) * 2.0, 1.0 - min(std * 4.0, 1.0)),
                "severity": "medium",
                "direction": "higher_is_more_suspicious",
                "evidence_summary": "Derived from wide matrix item mean/std as a build-only baseline flag.",
            }
        )
    write_jsonl(flags_path, rows)


def _split_item_key(item_key: str) -> tuple[str, str]:
    if "::" in item_key:
        subset, item_id = item_key.split("::", 1)
        return subset, item_id
    return "default", item_key


def _write_readiness(destination: Path, payload: dict[str, Any]) -> None:
    (destination / "README.md").write_text(_render_readme(payload), encoding="utf-8")
    (destination / "pipeline_status.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _render_readme(payload: dict[str, Any]) -> str:
    lines = ["# MMLU-Redux Validation Pipeline", "", f"- Status: `{payload['status']}`"]
    if payload.get("missing_inputs"):
        lines.extend(
            ["", "## Missing Inputs", *[f"- `{name}`" for name in payload["missing_inputs"]]]
        )
    lines.append("")
    lines.append(
        "This pipeline is evidence-first. It writes blockers instead of fabricating MMLU-Redux results."
    )
    return "\n".join(lines) + "\n"


def _write_paper_table(destination: Path, metrics: dict[str, Any]) -> None:
    lines = [
        "| Diagnostic | AUROC | AUPRC | Precision@k | Recall@k |",
        "|---|---:|---:|---:|---:|",
    ]
    for diagnostic, row in metrics.get("diagnostics", {}).items():
        lines.append(
            f"| {diagnostic} | {_fmt(row.get('auroc'))} | {_fmt(row.get('auprc'))} | {_fmt(row.get('precision_at_k'))} | {_fmt(row.get('recall_at_k'))} |"
        )
    (destination / "paper_table_mmlu_redux.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    (destination / "enrichment_curve.csv").write_text("diagnostic,placeholder\n", encoding="utf-8")


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, int | float):
        return f"{float(value):.3f}"
    return str(value)
