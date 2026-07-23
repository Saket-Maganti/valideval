from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from valideval.config import load_yaml
from valideval.validation.validation_runner import (
    DEFAULT_N_ITEMS,
    DEFAULT_SEEDS,
    run_single_validation,
)

DEFAULT_DIAGNOSTICS = [
    "shortcut",
    "answer_distribution",
    "distractor_quality",
    "redundancy",
    "irt",
    "reliability",
    "extraction_robustness",
    "saturation",
]
DEFAULT_FLAWS = [
    "shortcut_signal",
    "label_imbalance",
    "dead_distractors",
    "redundancy",
    "low_discrimination",
    "prompt_format_fragility",
    "extraction_ambiguity",
    "too_easy_saturation",
]


def run_cross_flaw_validation(
    config_path: str | Path | None,
    output_dir: str | Path,
) -> dict[str, Any]:
    cfg = load_yaml(config_path) if config_path else {}
    diagnostics = cfg.get("diagnostics", DEFAULT_DIAGNOSTICS)
    flaws = cfg.get("flaws", DEFAULT_FLAWS)
    strength_grid = [float(value) for value in cfg.get("strength_grid", [0.0, 1.0])]
    seeds = [int(value) for value in cfg.get("seeds", DEFAULT_SEEDS[:1])]
    n_items = int(cfg.get("n_items", DEFAULT_N_ITEMS))
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for diagnostic in diagnostics:
        for flaw in flaws:
            result = run_single_validation(
                diagnostic,
                flaw,
                strength_grid=strength_grid,
                seeds=seeds,
                n_items=n_items,
                output_dir=destination / "_runs" / f"{diagnostic}_{flaw}",
            )
            auc = result["metrics"].get("auc")
            fpr = result["metrics"].get("false_positive_rate")
            target = _target_flaw_for(diagnostic) == flaw
            rows.append(
                {
                    "diagnostic": diagnostic,
                    "flaw_type": flaw,
                    "target_pairing": target,
                    "auc": auc,
                    "false_positive_rate": fpr,
                    "specificity": result["metrics"].get("specificity"),
                    "paper_eligible": bool(
                        target and auc is not None and auc >= 0.80 and (fpr or 0.0) <= 0.10
                    ),
                }
            )

    payload = {
        "schema_version": "0.1",
        "status": "ok",
        "rows": rows,
        "warnings": [
            "Cross-flaw validation is synthetic evidence only; use it to qualify detector specificity, not to make real benchmark claims."
        ],
    }
    _write_cross_flaw_outputs(destination, payload)
    return payload


def _target_flaw_for(diagnostic: str) -> str:
    return {
        "shortcut": "shortcut_signal",
        "answer_distribution": "label_imbalance",
        "distractor_quality": "dead_distractors",
        "redundancy": "redundancy",
        "irt": "low_discrimination",
        "reliability": "prompt_format_fragility",
        "extraction_robustness": "extraction_ambiguity",
        "saturation": "too_easy_saturation",
    }.get(diagnostic, "")


def _write_cross_flaw_outputs(destination: Path, payload: dict[str, Any]) -> None:
    rows = payload["rows"]
    with (destination / "cross_flaw_matrix.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["diagnostic"])
        writer.writeheader()
        writer.writerows(rows)
    with (destination / "heatmap_data.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["diagnostic", "flaw_type", "auc", "target_pairing"]
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {key: row[key] for key in ("diagnostic", "flaw_type", "auc", "target_pairing")}
            )
    (destination / "cross_flaw_matrix.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (destination / "summary.md").write_text(_render_summary(payload), encoding="utf-8")


def _render_summary(payload: dict[str, Any]) -> str:
    rows = payload["rows"]
    off_target = [
        row for row in rows if not row["target_pairing"] and (row.get("auc") or 0) >= 0.80
    ]
    return (
        "\n".join(
            [
                "# Cross-Flaw Diagnostic Specificity",
                "",
                f"- Pairings tested: {len(rows)}",
                f"- Strong off-target activations: {len(off_target)}",
                "",
                "Diagnostics with strong off-target activation should be downgraded or marked non-paper-eligible until investigated.",
            ]
        )
        + "\n"
    )
