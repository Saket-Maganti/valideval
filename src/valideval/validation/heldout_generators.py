from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from valideval.config import load_yaml
from valideval.validation.validation_runner import run_single_validation

GENERATOR_FAMILIES = {
    "paraphrased_shortcut_artifact": ("shortcut", "shortcut_signal", "keyword_artifact"),
    "distractor_plausibility_skew": (
        "distractor_quality",
        "dead_distractors",
        "answer_length_artifact",
    ),
    "item_cluster_redundancy": ("redundancy", "redundancy", "context_leakage"),
    "ability_dependent_inversion": ("irt", "low_discrimination", "negative_discrimination"),
    "coverage_blindspot": ("shortcut", "context_irrelevance", "context_leakage"),
    "extraction_ambiguity": ("extraction_robustness", "scoring_ambiguity", "extraction_ambiguity"),
}


def run_heldout_validation(
    config_path: str | Path | None,
    output_dir: str | Path,
) -> dict[str, Any]:
    cfg = load_yaml(config_path) if config_path else {}
    families = cfg.get("families", list(GENERATOR_FAMILIES))
    strength_grid = [float(value) for value in cfg.get("strength_grid", [0.0, 1.0])]
    seeds = [int(value) for value in cfg.get("seeds", [0])]
    n_items = int(cfg.get("n_items", 48))
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    rows = []
    for family in families:
        diagnostic, original_flaw, heldout_flaw = GENERATOR_FAMILIES[family]
        original = run_single_validation(
            diagnostic,
            original_flaw,
            strength_grid=strength_grid,
            seeds=seeds,
            n_items=n_items,
            output_dir=destination / "_runs" / f"{family}_original",
        )
        heldout = run_single_validation(
            diagnostic,
            heldout_flaw,
            strength_grid=strength_grid,
            seeds=seeds,
            n_items=n_items,
            output_dir=destination / "_runs" / f"{family}_heldout",
        )
        original_auc = original["metrics"].get("auc")
        heldout_auc = heldout["metrics"].get("auc")
        transfer_drop = (
            None
            if original_auc is None or heldout_auc is None
            else float(original_auc) - float(heldout_auc)
        )
        rows.append(
            {
                "family": family,
                "diagnostic": diagnostic,
                "original_flaw": original_flaw,
                "heldout_flaw": heldout_flaw,
                "original_auc": original_auc,
                "heldout_auc": heldout_auc,
                "transfer_drop": transfer_drop,
                "paper_eligible": bool(
                    heldout_auc is not None
                    and heldout_auc >= 0.75
                    and (transfer_drop or 0.0) <= 0.25
                ),
            }
        )
    payload = {
        "schema_version": "0.1",
        "status": "ok",
        "rows": rows,
        "warnings": [
            "Held-out generator validation is synthetic transfer evidence, not real benchmark evidence."
        ],
    }
    _write_outputs(destination, payload)
    return payload


def _write_outputs(destination: Path, payload: dict[str, Any]) -> None:
    rows = payload["rows"]
    with (destination / "heldout_transfer.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["family"])
        writer.writeheader()
        writer.writerows(rows)
    (destination / "heldout_transfer.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (destination / "summary.md").write_text(
        "# Held-Out Synthetic Generator Validation\n\n"
        f"- Families tested: {len(rows)}\n"
        f"- Paper-eligible families: {sum(1 for row in rows if row['paper_eligible'])}\n\n"
        "Large transfer drops should be reported as detector-specificity limitations.\n",
        encoding="utf-8",
    )
