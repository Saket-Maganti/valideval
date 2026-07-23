from __future__ import annotations

from itertools import combinations
from pathlib import Path
from typing import Any

from valideval.benchmarks.base import Benchmark
from valideval.human.common import (
    load_annotation_tasks,
    load_human_judgments,
    stable_json_hash,
    task_lookup,
    write_json,
)
from valideval.io.jsonl import write_jsonl
from valideval.schemas import AnnotationTask, BenchmarkItem, HumanJudgment, JudgePrediction
from valideval.scoring.extraction import (
    detect_refusal,
    lenient_letter,
    regex_final_answer,
    strict_letter,
)
from valideval.scoring.mcq import normalize_mcq_label
from valideval.scoring.mcq_utils import accepted_labels

JUDGE_VARIANTS = ("strict", "lenient", "regex", "mock")


def build_judge_predictions(
    benchmark: Benchmark,
    tasks: list[AnnotationTask],
    *,
    variants: tuple[str, ...] = JUDGE_VARIANTS,
) -> list[JudgePrediction]:
    items = {item.item_id: item for item in benchmark.load_items()}
    predictions: list[JudgePrediction] = []
    for task in tasks:
        item = items[task.item_id]
        for variant in variants:
            payload = _judge_task(benchmark, item, task, variant)
            payload["version_hash"] = stable_json_hash(payload)
            predictions.append(JudgePrediction(**payload))
    return predictions


def write_judge_reliability_report(
    benchmark: Benchmark,
    *,
    output_dir: str | Path,
    benchmark_id: str,
    panel_id: str,
    variants: tuple[str, ...] = JUDGE_VARIANTS,
) -> dict[str, Any]:
    output = Path(output_dir)
    tasks = load_annotation_tasks(output)
    judgments = load_human_judgments(output)
    judge_predictions = build_judge_predictions(benchmark, tasks, variants=variants)
    predictions_path = output / "judge_predictions.jsonl"
    write_jsonl(predictions_path, judge_predictions)
    report = judge_reliability_report(
        benchmark,
        tasks,
        judgments,
        judge_predictions,
        benchmark_id=benchmark_id,
        panel_id=panel_id,
    )
    report_path = output / "judge_reliability.json"
    write_json(report_path, report)
    return {
        **report,
        "judge_predictions_jsonl": str(predictions_path),
        "judge_reliability_json": str(report_path),
    }


def judge_reliability_report(
    benchmark: Benchmark,
    tasks: list[AnnotationTask],
    judgments: list[HumanJudgment],
    judge_predictions: list[JudgePrediction],
    *,
    benchmark_id: str,
    panel_id: str,
) -> dict[str, Any]:
    items = {item.item_id: item for item in benchmark.load_items()}
    task_by_id = task_lookup(tasks)
    metrics = {
        "judge_human_agreement": _judge_human_agreement(
            judgments,
            judge_predictions,
            task_by_id,
            items,
        ),
        "inter_judge_agreement": _inter_judge_agreement(judge_predictions),
        "judge_variance": _judge_variance(judge_predictions),
        "answer_length_bias": _answer_length_bias(tasks, judge_predictions),
        "verbosity_bias": _answer_length_bias(tasks, judge_predictions),
        "refusal_bias": _refusal_bias(tasks, judge_predictions),
        "judge_prompt_sensitivity": _prompt_sensitivity(tasks, judge_predictions),
        "variant_count": len({prediction.variant for prediction in judge_predictions}),
        "prediction_count": len(judge_predictions),
    }
    return {
        "schema_version": "0.1",
        "benchmark_id": benchmark_id,
        "panel_id": panel_id,
        "metrics": metrics,
        "warnings": _judge_warnings(judgments, judge_predictions),
        "limitations": [
            "Rule and mock judges are deterministic scoring probes, not a substitute for human adjudication.",
            "Optional LLM judges are not required and are reported as unavailable in offline toy workflows.",
        ],
        "optional_llm_judge": {
            "status": "unavailable",
            "reason": "No paid or remote LLM judge is required by this workflow.",
        },
    }


def _judge_task(
    benchmark: Benchmark,
    item: BenchmarkItem,
    task: AnnotationTask,
    variant: str,
) -> dict[str, Any]:
    output = task.model_output or ""
    if variant == "strict":
        extraction = strict_letter(output)
        judge_type = "rule_based"
    elif variant == "regex":
        extraction = regex_final_answer(output)
        judge_type = "regex"
    elif variant == "mock":
        extraction = lenient_letter(output)
        judge_type = "local_mock"
    elif variant == "lenient":
        extraction = lenient_letter(output)
        judge_type = "rule_based"
    else:
        raise ValueError(f"Unknown judge variant: {variant}")

    if extraction.invalid or extraction.value is None:
        label = "unscorable"
        confidence = 0.4
    else:
        score = benchmark.score_prediction(item, extraction.value)
        label = "correct" if score.is_correct else "incorrect"
        confidence = 0.9 if variant in {"strict", "regex"} else 0.75
    rationale = f"{variant} extraction={extraction.value!r}; invalid={extraction.invalid}"
    return {
        "judge_id": f"{judge_type}_{variant}",
        "judge_type": judge_type,
        "variant": variant,
        "task_id": task.task_id,
        "item_id": task.item_id,
        "model_id": task.model_id,
        "label": label,
        "confidence": confidence,
        "rationale": rationale,
        "metadata": {
            "extraction_mode": extraction.mode,
            "extracted_value": extraction.value,
            "refusal": detect_refusal(output),
        },
    }


def _judge_human_agreement(
    judgments: list[HumanJudgment],
    judge_predictions: list[JudgePrediction],
    task_by_id: dict[str, AnnotationTask],
    items: dict[str, BenchmarkItem],
) -> dict[str, Any]:
    if not judgments:
        return {"status": "unavailable", "reason": "No imported human judgments."}
    by_task = _judge_by_task(judge_predictions)
    comparisons = []
    by_variant: dict[str, list[bool]] = {}
    for judgment in judgments:
        task = task_by_id.get(judgment.task_id)
        item = items.get(judgment.item_id)
        human_label = _normalize_human_label(judgment, task, item)
        for prediction in by_task.get(judgment.task_id, []):
            judge_label = _norm(prediction.label)
            match = human_label == judge_label
            comparisons.append(match)
            by_variant.setdefault(prediction.variant, []).append(match)
    if not comparisons:
        return {"status": "unavailable", "reason": "No matched human/judge task keys."}
    return {
        "status": "measured",
        "agreement": sum(comparisons) / len(comparisons),
        "n_comparisons": len(comparisons),
        "by_variant": {
            variant: sum(values) / len(values) if values else None
            for variant, values in sorted(by_variant.items())
        },
    }


def _inter_judge_agreement(judge_predictions: list[JudgePrediction]) -> dict[str, Any]:
    grouped = _judge_by_task(judge_predictions)
    pairs: list[bool] = []
    for predictions in grouped.values():
        for left, right in combinations(predictions, 2):
            pairs.append(_norm(left.label) == _norm(right.label))
    if not pairs:
        return {"status": "unavailable", "reason": "Fewer than two judge predictions per task."}
    return {"status": "measured", "agreement": sum(pairs) / len(pairs), "n_pairs": len(pairs)}


def _judge_variance(judge_predictions: list[JudgePrediction]) -> dict[str, Any]:
    grouped = _judge_by_task(judge_predictions)
    if not grouped:
        return {"status": "unavailable"}
    varying = sum(
        1
        for predictions in grouped.values()
        if len({_norm(prediction.label) for prediction in predictions}) > 1
    )
    return {
        "status": "measured",
        "task_variance_rate": varying / len(grouped),
        "n_varying_tasks": varying,
    }


def _answer_length_bias(
    tasks: list[AnnotationTask],
    judge_predictions: list[JudgePrediction],
) -> dict[str, Any]:
    if not tasks or not judge_predictions:
        return {"status": "unavailable"}
    lengths = {task.task_id: len(task.model_output or "") for task in tasks}
    median = _median(list(lengths.values()))
    short: list[float] = []
    long: list[float] = []
    for prediction in judge_predictions:
        label_value = _binary_correct(prediction.label)
        if label_value is None:
            continue
        bucket = long if lengths.get(prediction.task_id, 0) > median else short
        bucket.append(label_value)
    if not short or not long:
        return {"status": "unavailable", "reason": "Both short and long output buckets are needed."}
    short_rate = sum(short) / len(short)
    long_rate = sum(long) / len(long)
    return {
        "status": "measured",
        "long_minus_short_correct_rate": long_rate - short_rate,
        "short_bucket_correct_rate": short_rate,
        "long_bucket_correct_rate": long_rate,
        "median_output_length": median,
    }


def _refusal_bias(
    tasks: list[AnnotationTask],
    judge_predictions: list[JudgePrediction],
) -> dict[str, Any]:
    refusals = {task.task_id: detect_refusal(task.model_output or "") for task in tasks}
    refusal_values: list[float] = []
    non_refusal_values: list[float] = []
    for prediction in judge_predictions:
        value = _binary_correct(prediction.label)
        if value is None:
            continue
        if refusals.get(prediction.task_id):
            refusal_values.append(value)
        else:
            non_refusal_values.append(value)
    if not refusal_values or not non_refusal_values:
        return {
            "status": "unavailable",
            "reason": "Both refusal and non-refusal outputs are needed.",
        }
    refusal_rate = sum(refusal_values) / len(refusal_values)
    non_refusal_rate = sum(non_refusal_values) / len(non_refusal_values)
    return {
        "status": "measured",
        "refusal_minus_non_refusal_correct_rate": refusal_rate - non_refusal_rate,
        "refusal_correct_rate": refusal_rate,
        "non_refusal_correct_rate": non_refusal_rate,
    }


def _prompt_sensitivity(
    tasks: list[AnnotationTask],
    judge_predictions: list[JudgePrediction],
) -> dict[str, Any]:
    variants = {
        task.metadata.get("prompt_variant")
        for task in tasks
        if task.metadata.get("prompt_variant") is not None
    }
    if len(variants) < 2:
        return {
            "status": "unavailable",
            "reason": "Packet tasks do not include multiple prompt variants.",
        }
    grouped: dict[tuple[str, str | None], list[JudgePrediction]] = {}
    for prediction in judge_predictions:
        grouped.setdefault((prediction.item_id, prediction.model_id), []).append(prediction)
    varying = sum(
        1
        for values in grouped.values()
        if len({_norm(prediction.label) for prediction in values}) > 1
    )
    return {"status": "measured", "variance_rate": varying / len(grouped) if grouped else 0.0}


def _judge_warnings(
    judgments: list[HumanJudgment],
    judge_predictions: list[JudgePrediction],
) -> list[str]:
    warnings: list[str] = []
    if not judge_predictions:
        warnings.append("No judge predictions were produced; judge reliability is unmeasured.")
    if not judgments:
        warnings.append(
            "Judge-human agreement is unavailable because no human judgments were imported."
        )
    return warnings


def _judge_by_task(
    judge_predictions: list[JudgePrediction],
) -> dict[str, list[JudgePrediction]]:
    grouped: dict[str, list[JudgePrediction]] = {}
    for prediction in judge_predictions:
        grouped.setdefault(prediction.task_id, []).append(prediction)
    return grouped


def _normalize_human_label(
    judgment: HumanJudgment,
    task: AnnotationTask | None,
    item: BenchmarkItem | None,
) -> str:
    label = _norm(judgment.label)
    if label in {"correct", "incorrect", "unscorable"}:
        return label
    if label in {"1", "true", "yes", "pass"}:
        return "correct"
    if label in {"0", "false", "no", "fail"}:
        return "incorrect"
    mcq_label = normalize_mcq_label(label)
    if item and mcq_label:
        return "correct" if mcq_label in set(accepted_labels(item)) else "incorrect"
    if task and item:
        score = task.metadata.get("prediction_score")
        if score is not None and label in {"gold", "accepted"}:
            return "correct" if float(score) >= 1.0 else "incorrect"
    return label


def _binary_correct(label: str) -> float | None:
    normalized = _norm(label)
    if normalized == "correct":
        return 1.0
    if normalized == "incorrect":
        return 0.0
    return None


def _median(values: list[int]) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def _norm(label: str | None) -> str:
    return str(label or "").strip().lower()
