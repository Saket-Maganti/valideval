from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np

from valideval.audit.ranking import compare_rankings, naive_accuracy_ranking
from valideval.schemas import ResponseMatrix


def compute_repair_diff(
    rows: list[dict[str, Any]],
    selected_item_ids: list[str],
    removed_items: dict[str, list[str]],
    matrix: ResponseMatrix | None,
) -> dict[str, Any]:
    selected = set(selected_item_ids)
    original_count = len(rows)
    repaired_count = len(selected)
    return {
        "original_item_count": original_count,
        "repaired_item_count": repaired_count,
        "removed_item_count": original_count - repaired_count,
        "ranking_fidelity": _ranking_fidelity(matrix, selected_item_ids),
        "coverage_change": _coverage_change(rows, selected),
        "discrimination_improvement": _mean_change(rows, selected, "discrimination"),
        "duplicate_reduction": _fraction_reduction(rows, selected, "duplicate_cluster"),
        "shortcut_risk_reduction": _mean_reduction(rows, selected, "shortcut_suspiciousness"),
        "reliability_change": _reliability_change(rows, selected),
        "ci_change": _ci_change(matrix, selected_item_ids),
        "removed_items_by_reason": _removed_items_by_reason(removed_items),
        "selected_item_ids": selected_item_ids,
    }


def render_repair_report(diff: dict[str, Any], *, policy: str, policy_description: str) -> str:
    coverage = diff["coverage_change"]
    ranking = diff["ranking_fidelity"]
    return "\n".join(
        [
            "# Repair Report",
            "",
            f"- Policy: {policy}",
            f"- Policy description: {policy_description}",
            f"- Original item count: {diff['original_item_count']}",
            f"- Repaired item count: {diff['repaired_item_count']}",
            f"- Removed item count: {diff['removed_item_count']}",
            f"- Ranking fidelity Spearman: {_fmt(ranking.get('spearman'))}",
            f"- Ranking fidelity Kendall: {_fmt(ranking.get('kendall'))}",
            f"- Coverage tags before: {coverage.get('tag_counts_before', {})}",
            f"- Coverage tags after: {coverage.get('tag_counts_after', {})}",
            f"- Lost coverage tags: {', '.join(coverage.get('lost_tags', [])) or 'none'}",
            (
                "- Mean discrimination before/after: "
                f"{_fmt(diff['discrimination_improvement'].get('before'))} / "
                f"{_fmt(diff['discrimination_improvement'].get('after'))}"
            ),
            (
                "- Duplicate fraction before/after: "
                f"{_fmt(diff['duplicate_reduction'].get('before_fraction'))} / "
                f"{_fmt(diff['duplicate_reduction'].get('after_fraction'))}"
            ),
            (
                "- Mean shortcut risk before/after: "
                f"{_fmt(diff['shortcut_risk_reduction'].get('before'))} / "
                f"{_fmt(diff['shortcut_risk_reduction'].get('after'))}"
            ),
            (
                "- Mean item stability before/after: "
                f"{_fmt(diff['reliability_change'].get('before_mean_item_stability'))} / "
                f"{_fmt(diff['reliability_change'].get('after_mean_item_stability'))}"
            ),
            (
                "- Mean model standard error before/after: "
                f"{_fmt(diff['ci_change'].get('before_mean_standard_error'))} / "
                f"{_fmt(diff['ci_change'].get('after_mean_standard_error'))}"
            ),
            f"- Removed items by reason: {diff['removed_items_by_reason']}",
            "",
            (
                "Repair is advisory. Removed-item lists are evidence consistent with possible "
                "validity threats under this protocol, not automatic truth."
            ),
            "",
        ]
    )


def _ranking_fidelity(
    matrix: ResponseMatrix | None,
    selected_item_ids: list[str],
) -> dict[str, Any]:
    if matrix is None or not selected_item_ids:
        return {"available": False, "reason": "No matrix or selected items available."}
    frame = matrix.to_dataframe().astype(float)
    selected = [item_id for item_id in selected_item_ids if item_id in frame.columns]
    if not selected:
        return {"available": False, "reason": "Selected items are not in the matrix."}
    full_ranking = naive_accuracy_ranking(matrix)
    subset_matrix = ResponseMatrix(
        model_ids=matrix.model_ids,
        item_ids=selected,
        values=frame[selected].values.tolist(),
        metadata={**matrix.metadata, "repair_subset": True},
    )
    subset_ranking = naive_accuracy_ranking(subset_matrix)
    return {"available": True, **compare_rankings(full_ranking, subset_ranking)}


def _coverage_change(rows: list[dict[str, Any]], selected: set[str]) -> dict[str, Any]:
    before = _tag_counts(rows)
    after = _tag_counts([row for row in rows if row["item_id"] in selected])
    return {
        "tag_counts_before": dict(before),
        "tag_counts_after": dict(after),
        "lost_tags": sorted(set(before) - set(after)),
    }


def _tag_counts(rows: list[dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        tags = [tag for tag in str(row.get("coverage_tag", "")).split(";") if tag]
        counts.update(tags or ["untagged"])
    return counts


def _mean_change(
    rows: list[dict[str, Any]],
    selected: set[str],
    field: str,
) -> dict[str, Any]:
    before = _numeric_values(rows, field)
    after = _numeric_values([row for row in rows if row["item_id"] in selected], field)
    return {
        "before": float(np.mean(before)) if before else None,
        "after": float(np.mean(after)) if after else None,
    }


def _mean_reduction(
    rows: list[dict[str, Any]],
    selected: set[str],
    field: str,
) -> dict[str, Any]:
    change = _mean_change(rows, selected, field)
    before = change["before"]
    after = change["after"]
    change["reduction"] = before - after if before is not None and after is not None else None
    return change


def _fraction_reduction(
    rows: list[dict[str, Any]],
    selected: set[str],
    field: str,
) -> dict[str, Any]:
    before = _fraction(rows, field)
    after = _fraction([row for row in rows if row["item_id"] in selected], field)
    return {
        "before_fraction": before,
        "after_fraction": after,
        "reduction": before - after,
    }


def _reliability_change(rows: list[dict[str, Any]], selected: set[str]) -> dict[str, Any]:
    before_instability = _numeric_values(rows, "prompt_instability")
    after_instability = _numeric_values(
        [row for row in rows if row["item_id"] in selected],
        "prompt_instability",
    )
    before = 1.0 - float(np.mean(before_instability)) if before_instability else None
    after = 1.0 - float(np.mean(after_instability)) if after_instability else None
    return {
        "before_mean_item_stability": before,
        "after_mean_item_stability": after,
        "change": after - before if before is not None and after is not None else None,
    }


def _ci_change(matrix: ResponseMatrix | None, selected_item_ids: list[str]) -> dict[str, Any]:
    if matrix is None:
        return {"available": False}
    frame = matrix.to_dataframe().astype(float)
    selected = [item_id for item_id in selected_item_ids if item_id in frame.columns]
    before = _mean_standard_error(frame.values)
    after = _mean_standard_error(frame[selected].values) if selected else None
    return {
        "available": True,
        "before_mean_standard_error": before,
        "after_mean_standard_error": after,
        "change": after - before if after is not None else None,
    }


def _mean_standard_error(values) -> float:
    frame = np.asarray(values, dtype=float)
    if frame.size == 0:
        return float("nan")
    n_items = frame.shape[1] if frame.ndim == 2 else len(frame)
    model_means = np.nanmean(frame, axis=1)
    ses = np.sqrt(np.maximum(model_means * (1.0 - model_means), 0.0) / max(n_items, 1))
    return float(np.nanmean(ses))


def _removed_items_by_reason(removed_items: dict[str, list[str]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    by_reason: dict[str, list[str]] = {}
    for item_id, reasons in removed_items.items():
        for reason in reasons:
            counts[reason] += 1
            by_reason.setdefault(reason, []).append(item_id)
    return {"counts": dict(counts), "items": by_reason}


def _numeric_values(rows: list[dict[str, Any]], field: str) -> list[float]:
    output = []
    for row in rows:
        value = row.get(field)
        if value in {None, "", "n/a"}:
            continue
        try:
            output.append(float(value))
        except (TypeError, ValueError):
            continue
    return output


def _fraction(rows: list[dict[str, Any]], field: str) -> float:
    if not rows:
        return 0.0
    return sum(1 for row in rows if row.get(field)) / len(rows)


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        if value != value:
            return "n/a"
        return f"{value:.3f}"
    return str(value)
