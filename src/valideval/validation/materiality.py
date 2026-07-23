from __future__ import annotations

from typing import Any

DEFAULT_THRESHOLDS = {
    "shortcut_retention_material": 0.70,
    "score_delta_material": 0.05,
    "ranking_delta_material": 1,
    "saturation_top_range": 0.03,
    "redundancy_fraction_material": 0.20,
    "effective_item_fraction_material": 0.80,
}


def classify_materiality(
    *,
    diagnostic: str,
    effect_size: float | None,
    ranking_changed: bool = False,
    decision_changed: bool = False,
    thresholds: dict[str, float] | None = None,
) -> str:
    cfg = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    if effect_size is None:
        return "uncalibrated"
    effect = abs(float(effect_size))
    if decision_changed:
        return "decision-changing"
    if ranking_changed:
        return "ranking-changing"
    if diagnostic == "shortcut" and effect >= cfg["shortcut_retention_material"]:
        return "practically material"
    if diagnostic in {"extraction_robustness", "prompt_sensitivity", "reliability"}:
        if effect >= cfg["score_delta_material"]:
            return "practically material"
    if diagnostic == "redundancy" and effect >= cfg["redundancy_fraction_material"]:
        return "practically material"
    if diagnostic == "saturation" and effect <= cfg["saturation_top_range"]:
        return "practically material"
    if effect > 0:
        return "statistically detectable"
    return "negligible"


def shortcut_materiality(retention: float | None, full_score: float | None) -> dict[str, Any]:
    if retention is None or full_score is None:
        return {"status": "uncalibrated", "reason": "Retention or full score unavailable."}
    explained = float(retention) * float(full_score)
    return {
        "status": classify_materiality(diagnostic="shortcut", effect_size=float(retention)),
        "shortcut_retention": float(retention),
        "full_score": float(full_score),
        "shortcut_explained_score_fraction": explained,
        "rule": "Material when shortcut-only retention is high enough to explain a meaningful fraction of full performance.",
    }


def scoring_materiality(score_shift: float | None, ranking_changed: bool) -> dict[str, Any]:
    return {
        "status": classify_materiality(
            diagnostic="extraction_robustness",
            effect_size=score_shift,
            ranking_changed=ranking_changed,
        ),
        "score_shift": score_shift,
        "ranking_changed": ranking_changed,
        "rule": "Material when extractor/scorer choice changes rank order or score by a configured threshold.",
    }


def saturation_materiality(
    *,
    top_score_range: float | None,
    uncertainty_width: float | None = None,
) -> dict[str, Any]:
    if top_score_range is None:
        return {"status": "uncalibrated", "reason": "Top score range unavailable."}
    decision_changed = uncertainty_width is not None and float(top_score_range) < float(
        uncertainty_width
    )
    return {
        "status": classify_materiality(
            diagnostic="saturation",
            effect_size=float(top_score_range),
            decision_changed=decision_changed,
        ),
        "top_score_range": float(top_score_range),
        "uncertainty_width": uncertainty_width,
        "rule": "Material when top-model differences are smaller than uncertainty or configured range.",
    }


def redundancy_materiality(
    *,
    raw_item_count: int,
    effective_item_count: float | None,
) -> dict[str, Any]:
    if not raw_item_count or effective_item_count is None:
        return {"status": "uncalibrated", "reason": "Effective item count unavailable."}
    fraction_lost = max(0.0, 1.0 - float(effective_item_count) / raw_item_count)
    return {
        "status": classify_materiality(diagnostic="redundancy", effect_size=fraction_lost),
        "raw_item_count": raw_item_count,
        "effective_item_count": float(effective_item_count),
        "item_fraction_lost": fraction_lost,
        "rule": "Material when redundancy substantially lowers effective item count.",
    }
