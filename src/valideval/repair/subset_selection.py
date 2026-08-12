from __future__ import annotations

from typing import Any

from valideval.repair.policies import get_policy


def select_subset(
    rows: list[dict[str, Any]],
    *,
    policy_name: str = "conservative",
    target_size: int | None = None,
) -> dict[str, Any]:
    policy = get_policy(policy_name)
    if policy.get("v7_validation_required"):
        raise ValueError(
            f"{policy_name} is a V7 confirmatory policy and must be applied through the "
            "cross-fitted held-out validation workflow"
        )
    removed: dict[str, list[str]] = {}
    selected = []

    for row in rows:
        item_id = str(row["item_id"])
        reasons = removal_reasons(row, policy)
        if (
            reasons
            and _truthy(row.get("coverage_critical"))
            and policy.get("keep_coverage_critical")
        ):
            selected.append(item_id)
            removed[item_id] = ["coverage_critical_override", *reasons]
            continue
        if reasons:
            removed[item_id] = reasons
            continue
        selected.append(item_id)

    if policy_name == "high_information":
        selected = _select_high_information(rows, selected, removed, policy, target_size)
    elif target_size is not None and target_size > 0 and len(selected) > target_size:
        selected = _trim_to_target(rows, selected, removed, target_size)

    return {
        "policy": policy_name,
        "policy_description": policy["description"],
        "selected_item_ids": selected,
        "removed_items": {
            item_id: reasons
            for item_id, reasons in removed.items()
            if not reasons or reasons[0] != "coverage_critical_override"
        },
        "coverage_critical_overrides": {
            item_id: reasons
            for item_id, reasons in removed.items()
            if reasons and reasons[0] == "coverage_critical_override"
        },
    }


def removal_reasons(row: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    reasons = []
    discrimination = _float(row.get("discrimination"))
    min_discrimination = policy.get("min_discrimination")
    if policy.get("remove_negative_discrimination") and _truthy(row.get("negative_discrimination")):
        reasons.append("negative_discrimination")
    if (
        min_discrimination is not None
        and discrimination is not None
        and discrimination < float(min_discrimination)
    ):
        reasons.append("low_discrimination")
    if policy.get("remove_duplicates") and row.get("duplicate_cluster"):
        reasons.append("duplicate_cluster")
    shortcut = _float(row.get("shortcut_suspiciousness"))
    if shortcut is not None and shortcut >= float(policy.get("max_shortcut_suspiciousness", 1.0)):
        reasons.append("shortcut_risk")
    overlap_level = str(row.get("contamination_overlap") or "")
    if overlap_level in policy.get("remove_overlap_levels", set()):
        reasons.append("local_overlap_risk")
    prompt_instability = _float(row.get("prompt_instability"))
    max_prompt_instability = policy.get("max_prompt_instability")
    if (
        max_prompt_instability is not None
        and prompt_instability is not None
        and prompt_instability > float(max_prompt_instability)
    ):
        reasons.append("prompt_instability")
    scorer_instability = _float(row.get("scorer_instability"))
    max_scorer_instability = policy.get("max_scorer_instability")
    if (
        max_scorer_instability is not None
        and scorer_instability is not None
        and scorer_instability > float(max_scorer_instability)
    ):
        reasons.append("scorer_instability")
    return reasons


def _select_high_information(
    rows: list[dict[str, Any]],
    selected: list[str],
    removed: dict[str, list[str]],
    policy: dict[str, Any],
    target_size: int | None,
) -> list[str]:
    selected_set = set(selected)
    coverage_critical = [
        row["item_id"]
        for row in rows
        if row["item_id"] in selected_set and _truthy(row["coverage_critical"])
    ]
    if target_size is None:
        target_size = max(len(coverage_critical), int(round(len(rows) * policy["target_fraction"])))
    candidates = [
        row
        for row in rows
        if row["item_id"] in selected_set and row["item_id"] not in set(coverage_critical)
    ]
    candidates.sort(
        key=lambda row: (
            _float(row.get("discrimination")) or 0.0,
            -(_float(row.get("shortcut_suspiciousness")) or 0.0),
            str(row["item_id"]),
        ),
        reverse=True,
    )
    keep = list(coverage_critical)
    for row in candidates:
        if len(keep) >= target_size:
            removed[str(row["item_id"])] = ["lower_information_than_selected_subset"]
            continue
        keep.append(str(row["item_id"]))
    return sorted(keep, key=lambda item_id: _item_order(rows, item_id))


def _trim_to_target(
    rows: list[dict[str, Any]],
    selected: list[str],
    removed: dict[str, list[str]],
    target_size: int,
) -> list[str]:
    selected_rows = [row for row in rows if row["item_id"] in set(selected)]
    selected_rows.sort(
        key=lambda row: (
            _truthy(row.get("coverage_critical")),
            _float(row.get("discrimination")) or 0.0,
            -(_float(row.get("shortcut_suspiciousness")) or 0.0),
        ),
        reverse=True,
    )
    keep = [str(row["item_id"]) for row in selected_rows[:target_size]]
    for row in selected_rows[target_size:]:
        removed[str(row["item_id"])] = ["target_size_trim"]
    return sorted(keep, key=lambda item_id: _item_order(rows, item_id))


def _item_order(rows: list[dict[str, Any]], item_id: str) -> int:
    for index, row in enumerate(rows):
        if row["item_id"] == item_id:
            return index
    return len(rows)


def _float(value: Any) -> float | None:
    if value in {None, "", "n/a"}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}
