from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from valideval.stats.bootstrap import bootstrap_mean_ci
from valideval.stats.materiality import materiality_label
from valideval.stats.multiplicity import adjust_p_values


def run_stats_check(results_dir: str | Path, output_dir: str | Path) -> dict[str, Any]:
    source = Path(results_dir)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    scores: list[float] = []
    p_values: list[float] = []
    for path in sorted(source.glob("*.json")) if source.exists() else []:
        payload = json.loads(path.read_text(encoding="utf-8"))
        metrics = payload.get("summary_metrics", {})
        for key in ("auc", "pr_auc", "score", "effect_size"):
            value = metrics.get(key)
            if isinstance(value, int | float):
                scores.append(float(value))
        p_value = metrics.get("p_value")
        if isinstance(p_value, int | float):
            p_values.append(float(p_value))
    adjusted = adjust_p_values(p_values, method="bh") if p_values else []
    effect = max(scores) - min(scores) if len(scores) >= 2 else (scores[0] if scores else None)
    payload = {
        "schema_version": "0.1",
        "status": "ok" if scores or p_values else "empty",
        "results_dir": str(source),
        "n_scores": len(scores),
        "n_p_values": len(p_values),
        "bootstrap_mean_ci": bootstrap_mean_ci(scores, n_boot=200, seed=0) if scores else {},
        "multiplicity": {"method": "bh", "adjusted_p_values": adjusted},
        "effect_size_proxy": effect,
        "materiality": materiality_label(effect),
        "warnings": ["Materiality and significance are reported separately."],
    }
    (destination / "stats_check.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    (destination / "stats_check.md").write_text(_render_stats_check(payload), encoding="utf-8")
    return payload


def _render_stats_check(payload: dict[str, Any]) -> str:
    return (
        "\n".join(
            [
                "# Statistical Grounding Check",
                "",
                f"- Status: `{payload['status']}`",
                f"- Scores inspected: {payload['n_scores']}",
                f"- P-values inspected: {payload['n_p_values']}",
                f"- Materiality: `{payload['materiality']}`",
                "",
                "This check is a reporting guardrail, not a substitute for the preregistered validation protocol.",
            ]
        )
        + "\n"
    )
