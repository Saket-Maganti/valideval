from __future__ import annotations

from typing import Any


def benjamini_hochberg(p_values: list[float]) -> list[float]:
    return _step_up_q_values(p_values, harmonic_factor=1.0)


def benjamini_yekutieli(p_values: list[float]) -> list[float]:
    n = len(p_values)
    factor = sum(1.0 / idx for idx in range(1, n + 1)) if n else 1.0
    return _step_up_q_values(p_values, harmonic_factor=factor)


def bonferroni(p_values: list[float]) -> list[float]:
    n = len(p_values)
    return [min(max(float(p), 0.0) * n, 1.0) for p in p_values]


def holm(p_values: list[float]) -> list[float]:
    n = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda pair: pair[1])
    adjusted = [1.0] * n
    running = 0.0
    for rank, (index, p_value) in enumerate(indexed):
        value = min((n - rank) * max(float(p_value), 0.0), 1.0)
        running = max(running, value)
        adjusted[index] = running
    return adjusted


def empirical_p_values(scores: list[float], null_scores: list[float]) -> list[float]:
    if not null_scores:
        return [1.0 for _ in scores]
    null = [float(score) for score in null_scores]
    denom = len(null) + 1
    return [
        (1 + sum(1 for null_score in null if null_score >= float(score))) / denom
        for score in scores
    ]


def expected_false_flags(null_scores: list[float], threshold: float) -> dict[str, Any]:
    if not null_scores:
        return {"null_count": 0, "expected_false_flag_rate": None, "expected_false_flags": None}
    flags = [float(score) >= threshold for score in null_scores]
    rate = sum(flags) / len(flags)
    return {
        "null_count": len(flags),
        "threshold": threshold,
        "expected_false_flag_rate": rate,
        "expected_false_flags": sum(flags),
    }


def audit_wide_error_budget(
    families: dict[str, list[float]],
    *,
    alpha: float = 0.05,
    method: str = "bh",
) -> dict[str, Any]:
    output = {}
    for family, p_values in families.items():
        q_values = correct_p_values(p_values, method=method)
        output[family] = {
            "n_tests": len(p_values),
            "alpha": alpha,
            "discoveries": sum(1 for q_value in q_values if q_value <= alpha),
            "q_values": q_values,
        }
    return output


def correct_p_values(p_values: list[float], *, method: str = "bh") -> list[float]:
    if method == "bh":
        return benjamini_hochberg(p_values)
    if method == "by":
        return benjamini_yekutieli(p_values)
    if method == "bonferroni":
        return bonferroni(p_values)
    if method == "holm":
        return holm(p_values)
    raise ValueError(f"Unknown multiplicity method: {method}")


def annotate_flags(
    item_ids: list[str],
    scores: list[float],
    *,
    null_scores: list[float],
    threshold: float,
    method: str = "bh",
    effect_scale: float = 1.0,
) -> list[dict[str, Any]]:
    p_values = empirical_p_values(scores, null_scores)
    q_values = correct_p_values(p_values, method=method)
    expected = expected_false_flags(null_scores, threshold)
    return [
        {
            "item_id": item_id,
            "score": float(score),
            "raw_p_value": p_value,
            "q_value": q_value,
            "effect_size": float(score) / effect_scale if effect_scale else float(score),
            "flagged": float(score) >= threshold,
            "multiplicity_method": method,
            "expected_false_flag_context": expected,
        }
        for item_id, score, p_value, q_value in zip(
            item_ids, scores, p_values, q_values, strict=True
        )
    ]


def _step_up_q_values(p_values: list[float], *, harmonic_factor: float) -> list[float]:
    n = len(p_values)
    if n == 0:
        return []
    indexed = sorted(enumerate(p_values), key=lambda pair: pair[1])
    adjusted = [1.0] * n
    running = 1.0
    for reverse_rank, (index, p_value) in enumerate(reversed(indexed), start=1):
        rank = n - reverse_rank + 1
        value = min(max(float(p_value), 0.0) * n * harmonic_factor / rank, 1.0)
        running = min(running, value)
        adjusted[index] = running
    return adjusted
