from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Any

from valideval.benchmarks.base import Benchmark
from valideval.human.common import (
    load_annotation_tasks,
    load_human_judgments,
    load_judge_predictions,
    write_json,
)
from valideval.schemas import AnnotationTask, BenchmarkItem, HumanJudgment, JudgePrediction
from valideval.scoring.mcq import normalize_mcq_label
from valideval.scoring.mcq_utils import accepted_labels

AMBIGUITY_FIELDS = [
    "task_id",
    "item_id",
    "model_id",
    "ambiguity_level",
    "reasons",
    "human_labels",
    "judge_labels",
    "gold_answer",
    "model_output",
    "notes",
]


def detect_scoring_ambiguity(
    benchmark: Benchmark,
    tasks: list[AnnotationTask] | None = None,
    judgments: list[HumanJudgment] | None = None,
    judge_predictions: list[JudgePrediction] | None = None,
    *,
    output_dir: str | Path,
) -> dict[str, Any]:
    output = Path(output_dir)
    tasks = tasks if tasks is not None else load_annotation_tasks(output)
    judgments = judgments if judgments is not None else load_human_judgments(output)
    judge_predictions = (
        judge_predictions if judge_predictions is not None else load_judge_predictions(output)
    )
    items = {item.item_id: item for item in benchmark.load_items()}
    human_by_task = _human_by_task(judgments)
    judge_by_task = _judge_by_task(judge_predictions)
    rows = []
    for task in tasks:
        item = items[task.item_id]
        reasons = _ambiguity_reasons(
            item,
            task,
            human_by_task.get(task.task_id, []),
            judge_by_task.get(task.task_id, []),
        )
        if not reasons:
            continue
        human_labels = sorted(
            {_norm(judgment.label) for judgment in human_by_task.get(task.task_id, [])}
        )
        judge_labels = sorted(
            {
                f"{prediction.variant}:{_norm(prediction.label)}"
                for prediction in judge_by_task.get(task.task_id, [])
            }
        )
        rows.append(
            {
                "task_id": task.task_id,
                "item_id": task.item_id,
                "model_id": task.model_id or "",
                "ambiguity_level": _level(reasons),
                "reasons": ";".join(reasons),
                "human_labels": ";".join(human_labels),
                "judge_labels": ";".join(judge_labels),
                "gold_answer": "|".join(_as_list(item.answer)),
                "model_output": task.model_output,
                "notes": _notes(reasons),
            }
        )

    csv_path = output / "scoring_ambiguity.csv"
    json_path = output / "scoring_ambiguity.json"
    _write_csv(csv_path, rows)
    reason_counts = Counter(
        reason for row in rows for reason in str(row["reasons"]).split(";") if reason
    )
    summary: dict[str, Any] = {
        "schema_version": "0.1",
        "benchmark_id": benchmark.benchmark_id,
        "n_tasks_reviewed": len(tasks),
        "n_ambiguous_tasks": len(rows),
        "ambiguity_rate": len(rows) / len(tasks) if tasks else None,
        "reason_counts": dict(reason_counts),
        "examples": rows[:10],
        "artifacts": {"scoring_ambiguity_csv": str(csv_path)},
        "limitations": [
            "Ambiguity flags are triage signals and do not prove that the gold label is wrong.",
            "Human disagreement and judge disagreement should be adjudicated before changing scores.",
        ],
    }
    write_json(json_path, summary)
    return {
        **summary,
        "reason_counts": dict(reason_counts),
        "scoring_ambiguity_csv": str(csv_path),
        "scoring_ambiguity_json": str(json_path),
    }


def _ambiguity_reasons(
    item: BenchmarkItem,
    task: AnnotationTask,
    judgments: list[HumanJudgment],
    judge_predictions: list[JudgePrediction],
) -> list[str]:
    reasons: list[str] = []
    human_labels = {_norm(judgment.label) for judgment in judgments}
    if len(human_labels) > 1:
        reasons.append("human_disagreement")
    if any(judgment.ambiguity_flag for judgment in judgments):
        reasons.append("human_ambiguity_flag")
    if any(judgment.invalid_item_flag for judgment in judgments):
        reasons.append("invalid_item_flag")

    judge_labels = {_norm(prediction.label) for prediction in judge_predictions}
    if len(judge_labels) > 1:
        reasons.append("judge_disagreement")
    by_variant = {prediction.variant: _norm(prediction.label) for prediction in judge_predictions}
    if by_variant.get("strict") and by_variant.get("lenient"):
        if by_variant["strict"] != by_variant["lenient"]:
            reasons.append("strict_lenient_disagreement")

    if isinstance(item.answer, list) and len(item.answer) > 1:
        reasons.append("multiple_valid_answers")
    if not item.choices and not item.metadata.get("aliases") and not isinstance(item.answer, list):
        reasons.append("missing_aliases")
    if len(task.rubric.strip()) < 40:
        reasons.append("underspecified_rubric")
    lowered = f"{item.prompt} {item.context or ''}".lower()
    if "ambiguous" in lowered or "ambiguous_scoring_risk" in item.construct_tags:
        reasons.append("ambiguous_context")

    if _human_majority_conflicts_with_gold(item, judgments):
        reasons.append("possibly_wrong_gold_label")
    return sorted(set(reasons))


def _human_majority_conflicts_with_gold(
    item: BenchmarkItem,
    judgments: list[HumanJudgment],
) -> bool:
    labels = [normalize_mcq_label(judgment.label) for judgment in judgments]
    labels = [label for label in labels if label]
    if len(labels) < 2:
        return False
    majority, count = Counter(labels).most_common(1)[0]
    if count <= len(labels) / 2:
        return False
    return majority not in set(accepted_labels(item))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=AMBIGUITY_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _human_by_task(judgments: list[HumanJudgment]) -> dict[str, list[HumanJudgment]]:
    grouped: dict[str, list[HumanJudgment]] = {}
    for judgment in judgments:
        grouped.setdefault(judgment.task_id, []).append(judgment)
    return grouped


def _judge_by_task(predictions: list[JudgePrediction]) -> dict[str, list[JudgePrediction]]:
    grouped: dict[str, list[JudgePrediction]] = {}
    for prediction in predictions:
        grouped.setdefault(prediction.task_id, []).append(prediction)
    return grouped


def _level(reasons: list[str]) -> str:
    if {"human_disagreement", "judge_disagreement"} <= set(reasons):
        return "high"
    if len(reasons) >= 2:
        return "moderate"
    return "low"


def _notes(reasons: list[str]) -> str:
    if "possibly_wrong_gold_label" in reasons:
        return "Review gold label before using this task for score interpretation."
    if "strict_lenient_disagreement" in reasons:
        return "Review scoring/extraction rule sensitivity."
    return "Adjudication recommended before score repair."


def _as_list(value: str | list[str]) -> list[str]:
    return value if isinstance(value, list) else [value]


def _norm(label: str) -> str:
    return str(label).strip().lower()
