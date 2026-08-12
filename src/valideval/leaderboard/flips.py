from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from valideval.audit.ranking import compare_rankings, naive_accuracy_ranking
from valideval.schemas import ResponseMatrix, utc_now


def detect_ranking_flips(
    ranking_views: dict[str, Any],
    *,
    matrix: ResponseMatrix | None = None,
    output_dir: str | Path | None = None,
    repair_diff_path: str | Path | None = None,
) -> dict[str, Any]:
    views = ranking_views.get("views", ranking_views)
    raw = views.get("raw_accuracy", {}).get("ranking", [])
    comparisons = {}
    for name in [
        "irt_latent_ability",
        "reliability_adjusted_score",
        "shortcut_penalized_view",
        "prompt_stable_ranking",
        "extraction_robust_ranking",
        "contamination_risk_aware_view",
        "saturation_aware_interpretation",
    ]:
        comparisons[f"raw_vs_{name}"] = _compare(raw, views.get(name, {}).get("ranking", []))

    comparisons["full_vs_repaired_subset"] = _full_vs_repaired_subset(
        matrix,
        repair_diff_path,
        raw,
    )
    comparisons["strict_vs_lenient_scorer"] = _missing(
        "No alternate lenient scorer matrix was available."
    )
    comparisons["judge_a_vs_judge_b"] = _missing("No judge A/B outputs were available.")
    comparisons["full_panel_vs_subset_panel"] = _missing("No subset-panel audit was available.")

    payload = {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "comparisons": comparisons,
        "warnings": [
            "Ranking flips indicate sensitivity between views; they do not identify the true ranking.",
            "Missing-evidence comparisons are reported explicitly rather than guessed.",
        ],
    }
    if output_dir is not None:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        (output / "ranking_flips.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    return payload


def _compare(raw: list[dict[str, Any]], alternative: list[dict[str, Any]]) -> dict[str, Any]:
    if not raw or not alternative:
        return _missing("One or both ranking views were unavailable.")
    comparison = compare_rankings(raw, alternative)
    return {
        "available": True,
        "spearman": comparison["spearman"],
        "kendall": comparison["kendall"],
        "flip_count": len(comparison["rank_flips"]),
        "rank_flips": comparison["rank_flips"],
    }


def _full_vs_repaired_subset(
    matrix: ResponseMatrix | None,
    repair_diff_path: str | Path | None,
    raw: list[dict[str, Any]],
) -> dict[str, Any]:
    if matrix is None or not repair_diff_path or not Path(repair_diff_path).exists():
        return _missing("No repaired-subset diff was available.")
    payload = json.loads(Path(repair_diff_path).read_text(encoding="utf-8"))
    selected = payload.get("selection", {}).get("selected_item_ids", [])
    if not selected:
        return _missing("Repair diff did not include selected items.")
    frame = matrix.to_dataframe().astype(float)
    selected = [item_id for item_id in selected if item_id in frame.columns]
    if not selected:
        return _missing("Selected items were not present in the response matrix.")
    subset = ResponseMatrix(
        model_ids=matrix.model_ids,
        item_ids=selected,
        values=frame[selected].values.tolist(),
        metadata={**matrix.metadata, "subset": "repaired"},
    )
    return _compare(raw, naive_accuracy_ranking(subset))


def _missing(reason: str) -> dict[str, Any]:
    return {
        "available": False,
        "reason": reason,
        "flip_count": None,
        "rank_flips": [],
    }
