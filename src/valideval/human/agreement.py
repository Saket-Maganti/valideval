from __future__ import annotations

import math
import random
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any

from valideval.human.common import (
    load_annotation_tasks,
    load_human_judgments,
    task_lookup,
    write_json,
)
from valideval.schemas import AnnotationAgreementReport, AnnotationTask, HumanJudgment
from valideval.scoring.agreement import cohen_kappa


def compute_agreement_report(
    judgments: list[HumanJudgment],
    *,
    benchmark_id: str,
    panel_id: str,
    tasks: list[AnnotationTask] | None = None,
    n_boot: int = 200,
    seed: int = 0,
) -> AnnotationAgreementReport:
    tasks = tasks or []
    grouped = _group_by_task(judgments)
    comparable = {key: values for key, values in grouped.items() if len(values) >= 2}
    task_by_id = task_lookup(tasks)
    raw = _raw_agreement(comparable)
    report = AnnotationAgreementReport(
        benchmark_id=benchmark_id,
        panel_id=panel_id,
        n_items=len({judgment.item_id for judgment in judgments}),
        n_tasks=len(grouped),
        n_judgments=len(judgments),
        n_annotators=len({judgment.anonymized_annotator for judgment in judgments}),
        raw_agreement=_finite_or_none(raw),
        cohen_kappa=_finite_or_none(_pairwise_cohen(comparable)),
        fleiss_kappa=_finite_or_none(_fleiss_kappa(comparable)),
        krippendorff_alpha=_krippendorff_nominal_alpha(comparable),
        bootstrap_ci=_bootstrap_ci(comparable, n_boot=n_boot, seed=seed),
        confusion_matrix=_confusion_matrix(comparable),
        agreement_by_tag=_agreement_by_tag(comparable, task_by_id),
        agreement_by_item_type=_agreement_by_item_type(comparable, task_by_id),
        agreement_by_model=_agreement_by_model(comparable),
        ambiguity_rate=_finite_or_none(_ambiguity_rate(grouped)),
        warnings=_agreement_warnings(judgments, comparable),
        limitations=[
            "Agreement statistics summarize available imported labels only.",
            "Human annotations are not treated as perfect ground truth; adjudication may still be required.",
        ],
        metadata={
            "comparable_task_count": len(comparable),
            "bootstrap_samples": n_boot,
            "seed": seed,
        },
    )
    return report


def write_agreement_report(
    *,
    output_dir: str | Path,
    benchmark_id: str,
    panel_id: str,
    n_boot: int = 200,
    seed: int = 0,
) -> dict[str, Any]:
    output = Path(output_dir)
    tasks = load_annotation_tasks(output)
    judgments = load_human_judgments(output)
    report = compute_agreement_report(
        judgments,
        benchmark_id=benchmark_id,
        panel_id=panel_id,
        tasks=tasks,
        n_boot=n_boot,
        seed=seed,
    )
    path = output / "agreement_report.json"
    write_json(path, report.model_dump(mode="json"))
    return {"agreement_report_json": str(path), **report.model_dump(mode="json")}


def _group_by_task(judgments: list[HumanJudgment]) -> dict[str, list[HumanJudgment]]:
    grouped: dict[str, list[HumanJudgment]] = {}
    for judgment in judgments:
        grouped.setdefault(judgment.task_id, []).append(judgment)
    return grouped


def _raw_agreement(grouped: dict[str, list[HumanJudgment]]) -> float:
    values: list[float] = []
    for group in grouped.values():
        pairs = list(combinations(group, 2))
        if not pairs:
            continue
        values.append(
            sum(_norm(left.label) == _norm(right.label) for left, right in pairs) / len(pairs)
        )
    return float(sum(values) / len(values)) if values else float("nan")


def _pairwise_cohen(grouped: dict[str, list[HumanJudgment]]) -> float:
    annotators = sorted(
        {judgment.anonymized_annotator for values in grouped.values() for judgment in values}
    )
    kappas: list[float] = []
    for left_annotator, right_annotator in combinations(annotators, 2):
        left_labels: list[str] = []
        right_labels: list[str] = []
        for group in grouped.values():
            by_annotator = {judgment.anonymized_annotator: judgment for judgment in group}
            if left_annotator in by_annotator and right_annotator in by_annotator:
                left_labels.append(_norm(by_annotator[left_annotator].label))
                right_labels.append(_norm(by_annotator[right_annotator].label))
        if left_labels:
            categories = {
                label: index for index, label in enumerate(sorted(set(left_labels + right_labels)))
            }
            kappas.append(
                cohen_kappa(
                    [categories[label] for label in left_labels],
                    [categories[label] for label in right_labels],
                )
            )
    finite = [value for value in kappas if math.isfinite(value)]
    return float(sum(finite) / len(finite)) if finite else float("nan")


def _fleiss_kappa(grouped: dict[str, list[HumanJudgment]]) -> float:
    rows = [values for values in grouped.values() if len(values) >= 2]
    if not rows:
        return float("nan")
    category_counts = Counter(_norm(judgment.label) for row in rows for judgment in row)
    total_ratings = sum(category_counts.values())
    if total_ratings == 0:
        return float("nan")
    p_category = {label: count / total_ratings for label, count in category_counts.items()}
    p_expected = sum(value * value for value in p_category.values())
    p_items: list[float] = []
    for row in rows:
        counts = Counter(_norm(judgment.label) for judgment in row)
        n = len(row)
        p_items.append(sum(count * (count - 1) for count in counts.values()) / (n * (n - 1)))
    p_observed = sum(p_items) / len(p_items)
    if p_expected == 1.0:
        return 1.0
    return float((p_observed - p_expected) / (1.0 - p_expected))


def _krippendorff_nominal_alpha(
    grouped: dict[str, list[HumanJudgment]],
) -> dict[str, Any]:
    """Compute nominal Krippendorff alpha for variable numbers of annotators.

    Coincidences are weighted by ``1 / (n_item - 1)`` so each usable judgment has
    equal marginal weight. Missing or single-rated items are excluded explicitly.
    """

    coincidence: dict[str, dict[str, float]] = {}
    usable_items = 0
    for group in grouped.values():
        labels = [_norm(judgment.label) for judgment in group if _norm(judgment.label)]
        if len(labels) < 2:
            continue
        usable_items += 1
        weight = 1.0 / (len(labels) - 1)
        for left_index, left in enumerate(labels):
            coincidence.setdefault(left, {})
            for right_index, right in enumerate(labels):
                if left_index != right_index:
                    coincidence[left][right] = coincidence[left].get(right, 0.0) + weight
    marginals = {label: sum(row.values()) for label, row in coincidence.items()}
    total = sum(marginals.values())
    if usable_items == 0 or total <= 1.0:
        return {
            "status": "unavailable",
            "level": "nominal",
            "reason": "At least one item with two non-empty ratings is required.",
        }
    observed_disagreement = (
        sum(
            value
            for left, row in coincidence.items()
            for right, value in row.items()
            if left != right
        )
        / total
    )
    expected_disagreement = (total * total - sum(value * value for value in marginals.values())) / (
        total * (total - 1.0)
    )
    if expected_disagreement <= 0.0:
        value = 1.0 if observed_disagreement == 0.0 else None
    else:
        value = 1.0 - observed_disagreement / expected_disagreement
    return {
        "status": "measured" if value is not None else "unavailable",
        "level": "nominal",
        "value": value,
        "usable_item_count": usable_items,
        "observed_disagreement": observed_disagreement,
        "expected_disagreement": expected_disagreement,
    }


def _bootstrap_ci(
    grouped: dict[str, list[HumanJudgment]],
    *,
    n_boot: int,
    seed: int,
) -> dict[str, Any]:
    keys = list(grouped)
    if not keys or n_boot <= 0:
        return {"metric": "raw_agreement", "status": "unavailable"}
    rng = random.Random(seed)
    values: list[float] = []
    for _ in range(n_boot):
        sample = {f"{key}#{i}": grouped[rng.choice(keys)] for i, key in enumerate(keys)}
        value = _raw_agreement(sample)
        if math.isfinite(value):
            values.append(value)
    if not values:
        return {"metric": "raw_agreement", "status": "unavailable"}
    values.sort()
    low = values[int(0.025 * (len(values) - 1))]
    high = values[int(0.975 * (len(values) - 1))]
    return {
        "metric": "raw_agreement",
        "status": "measured",
        "n_boot": n_boot,
        "low": low,
        "high": high,
    }


def _confusion_matrix(grouped: dict[str, list[HumanJudgment]]) -> dict[str, dict[str, int]]:
    matrix: dict[str, dict[str, int]] = {}
    for group in grouped.values():
        ordered = sorted(group, key=lambda judgment: judgment.anonymized_annotator)
        for left, right in combinations(ordered, 2):
            left_label = _norm(left.label)
            right_label = _norm(right.label)
            matrix.setdefault(left_label, {})
            matrix[left_label][right_label] = matrix[left_label].get(right_label, 0) + 1
    return matrix


def _agreement_by_tag(
    grouped: dict[str, list[HumanJudgment]],
    task_by_id: dict[str, AnnotationTask],
) -> dict[str, Any]:
    tag_to_group: dict[str, dict[str, list[HumanJudgment]]] = {}
    for key, group in grouped.items():
        task = task_by_id.get(key)
        tags = task.tags if task is not None else []
        for tag in tags or ["untagged"]:
            tag_to_group.setdefault(tag, {})[key] = group
    return {
        tag: {
            "n_tasks": len(values),
            "raw_agreement": _finite_or_none(_raw_agreement(values)),
        }
        for tag, values in sorted(tag_to_group.items())
    }


def _agreement_by_item_type(
    grouped: dict[str, list[HumanJudgment]],
    task_by_id: dict[str, AnnotationTask],
) -> dict[str, Any]:
    type_to_group: dict[str, dict[str, list[HumanJudgment]]] = {}
    for key, group in grouped.items():
        task = task_by_id.get(key)
        item_type = "multiple_choice" if task and task.metadata.get("choices") else "open_ended"
        type_to_group.setdefault(item_type, {})[key] = group
    return {
        item_type: {
            "n_tasks": len(values),
            "raw_agreement": _finite_or_none(_raw_agreement(values)),
        }
        for item_type, values in sorted(type_to_group.items())
    }


def _agreement_by_model(grouped: dict[str, list[HumanJudgment]]) -> dict[str, Any]:
    model_to_group: dict[str, dict[str, list[HumanJudgment]]] = {}
    for key, group in grouped.items():
        model = group[0].model_id or "unknown_model"
        model_to_group.setdefault(model, {})[key] = group
    return {
        model: {
            "n_tasks": len(values),
            "raw_agreement": _finite_or_none(_raw_agreement(values)),
        }
        for model, values in sorted(model_to_group.items())
    }


def _ambiguity_rate(grouped: dict[str, list[HumanJudgment]]) -> float:
    if not grouped:
        return float("nan")
    ambiguous = 0
    for group in grouped.values():
        labels = {_norm(judgment.label) for judgment in group}
        if len(labels) > 1 or any(judgment.ambiguity_flag for judgment in group):
            ambiguous += 1
    return ambiguous / len(grouped)


def _agreement_warnings(
    judgments: list[HumanJudgment],
    comparable: dict[str, list[HumanJudgment]],
) -> list[str]:
    warnings: list[str] = []
    if not judgments:
        warnings.append("No imported human judgments were found; agreement is unmeasured.")
    elif not comparable:
        warnings.append(
            "No task has two or more annotators; inter-annotator agreement is unmeasured."
        )
    if len({judgment.anonymized_annotator for judgment in judgments}) < 2 and judgments:
        warnings.append(
            "Only one annotator is present; agreement metrics require multiple annotators."
        )
    return warnings


def _norm(label: str) -> str:
    return str(label).strip().lower()


def _finite_or_none(value: float | None) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return float(value)
