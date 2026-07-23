from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

import numpy as np

from valideval.benchmarks.base import Benchmark
from valideval.schemas import ModelPrediction, ResponseMatrix
from valideval.scoring.extraction import invalid_output_detector, refusal_detector


def calibration_and_abstention_report(
    benchmark: Benchmark,
    full_predictions: list[ModelPrediction],
    matrices: dict[str, ResponseMatrix],
    *,
    n_bins: int = 10,
) -> dict[str, Any]:
    warnings = []
    confidences = _confidence_values(full_predictions)
    if not confidences:
        warnings.append(
            "No confidence/logprob values were available; numeric calibration output requires confidence outputs."
        )
        return {
            "calibration_status": "requires_confidence_outputs",
            "ece": None,
            "brier": None,
            "nll": None,
            "confidence_correctness": {"mean_confidence": None, "accuracy": None},
            "overconfidence_on_low_validity_items": None,
            "calibration_by_construct_tag": {},
            "prompt_consistency_proxy": _prompt_consistency_summary(matrices),
            "abstention": abstention_report(full_predictions),
            "warnings": warnings,
        }

    correctness = {
        (record.model_id, record.item_id): float(record.score) for record in full_predictions
    }
    rows = [
        {
            "model_id": model_id,
            "item_id": item_id,
            "confidence": confidence,
            "correct": correctness.get((model_id, item_id), float("nan")),
        }
        for (model_id, item_id), confidence in confidences.items()
        if (model_id, item_id) in correctness
    ]
    ece = expected_calibration_error(rows, n_bins=n_bins)
    brier = (
        float(np.mean([(row["confidence"] - row["correct"]) ** 2 for row in rows]))
        if rows
        else float("nan")
    )
    nll = (
        float(
            np.mean(
                [
                    -(
                        row["correct"] * math.log(max(row["confidence"], 1e-8))
                        + (1.0 - row["correct"]) * math.log(max(1.0 - row["confidence"], 1e-8))
                    )
                    for row in rows
                ]
            )
        )
        if rows
        else float("nan")
    )

    by_tag = _calibration_by_tag(benchmark, rows)
    low_validity_items = {
        item.item_id
        for item in benchmark.load_items()
        if set(item.construct_tags)
        & {
            "answer_prior_artifact",
            "low_discrimination",
            "ambiguous_scoring_risk",
            "duplicate_near_duplicate",
        }
    }
    low_validity_rows = [row for row in rows if row["item_id"] in low_validity_items]
    overconfidence_low_validity = (
        float(np.mean([max(0.0, row["confidence"] - row["correct"]) for row in low_validity_rows]))
        if low_validity_rows
        else float("nan")
    )

    abstention = abstention_report(full_predictions)
    return {
        "ece": ece,
        "brier": brier,
        "nll": nll,
        "confidence_correctness": _confidence_correctness(rows),
        "overconfidence_on_low_validity_items": overconfidence_low_validity,
        "calibration_by_construct_tag": by_tag,
        "abstention": abstention,
        "warnings": warnings,
    }


def expected_calibration_error(rows: list[dict[str, float | str]], *, n_bins: int = 10) -> float:
    if not rows:
        return float("nan")
    ece = 0.0
    for bin_index in range(n_bins):
        lower = bin_index / n_bins
        upper = (bin_index + 1) / n_bins
        bucket = [
            row
            for row in rows
            if lower <= float(row["confidence"]) < upper
            or (bin_index == n_bins - 1 and float(row["confidence"]) <= upper)
        ]
        if not bucket:
            continue
        accuracy = float(np.mean([float(row["correct"]) for row in bucket]))
        confidence = float(np.mean([float(row["confidence"]) for row in bucket]))
        ece += (len(bucket) / len(rows)) * abs(accuracy - confidence)
    return float(ece)


def abstention_report(records: list[ModelPrediction]) -> dict[str, Any]:
    if not records:
        return {
            "coverage": float("nan"),
            "selective_risk": float("nan"),
            "appropriate_refusal_rate": float("nan"),
            "inappropriate_refusal_rate": float("nan"),
            "risk_coverage_auc": float("nan"),
            "deferral_utility": float("nan"),
        }
    abstained = [
        refusal_detector(record.raw_output or record.prediction).refusal
        or invalid_output_detector(record.raw_output or record.prediction).invalid
        for record in records
    ]
    answered = [not value for value in abstained]
    answered_records = [
        record for record, did_answer in zip(records, answered, strict=True) if did_answer
    ]
    incorrect_records = [record for record in records if record.score < 0.5]
    appropriate_refusals = [
        did_abstain and record.score < 0.5
        for record, did_abstain in zip(records, abstained, strict=True)
    ]
    inappropriate_refusals = [
        did_abstain and record.score >= 0.5
        for record, did_abstain in zip(records, abstained, strict=True)
    ]
    coverage = sum(answered) / len(records)
    selective_risk = (
        sum(1 for record in answered_records if record.score < 0.5) / len(answered_records)
        if answered_records
        else float("nan")
    )
    base_risk = len(incorrect_records) / len(records)
    deferral_utility = (
        base_risk - selective_risk if not math.isnan(selective_risk) else float("nan")
    )
    return {
        "coverage": coverage,
        "selective_risk": selective_risk,
        "appropriate_refusal_rate": sum(appropriate_refusals) / len(records),
        "inappropriate_refusal_rate": sum(inappropriate_refusals) / len(records),
        "risk_coverage_auc": coverage * (1.0 - selective_risk)
        if not math.isnan(selective_risk)
        else float("nan"),
        "deferral_utility": deferral_utility,
    }


def _confidence_values(records: list[ModelPrediction]) -> dict[tuple[str, str], float]:
    output = {}
    for record in records:
        confidence = record.metadata.get("confidence")
        if confidence is None and record.logprob is not None:
            confidence = math.exp(float(record.logprob))
        if confidence is not None:
            output[(record.model_id, record.item_id)] = min(max(float(confidence), 0.0), 1.0)
    return output


def _consistency_confidence(matrices: dict[str, ResponseMatrix]) -> dict[tuple[str, str], float]:
    if "full" not in matrices:
        return {}
    full = matrices["full"].to_dataframe().astype(float)
    variant_frames = [
        matrix.to_dataframe().astype(float).reindex_like(full)
        for variant, matrix in matrices.items()
        if variant != "full"
    ]
    if not variant_frames:
        return {(model_id, item_id): 0.5 for model_id in full.index for item_id in full.columns}
    output = {}
    for model_id in full.index:
        for item_id in full.columns:
            values = [frame.loc[model_id, item_id] for frame in variant_frames]
            output[(model_id, item_id)] = float(
                np.mean([value == full.loc[model_id, item_id] for value in values])
            )
    return output


def _prompt_consistency_summary(matrices: dict[str, ResponseMatrix]) -> dict[str, Any]:
    values = list(_consistency_confidence(matrices).values())
    return {
        "status": "not_calibration",
        "mean_prompt_consistency": float(np.mean(values)) if values else None,
        "n_model_item_pairs": len(values),
        "interpretation": (
            "Prompt consistency is a perturbation-stability proxy. It is not a numeric "
            "calibration estimate and should not be reported as ECE, Brier, or NLL."
        ),
    }


def _calibration_by_tag(
    benchmark: Benchmark,
    rows: list[dict[str, float | str]],
) -> dict[str, dict[str, float | int]]:
    rows_by_item = defaultdict(list)
    for row in rows:
        rows_by_item[str(row["item_id"])].append(row)
    by_tag: dict[str, list[dict[str, float | str]]] = defaultdict(list)
    for item in benchmark.load_items():
        for tag in item.construct_tags or ["untagged"]:
            by_tag[tag].extend(rows_by_item[item.item_id])
    return {
        tag: {
            "n": len(tag_rows),
            "ece": expected_calibration_error(tag_rows, n_bins=5),
            "mean_confidence": float(np.mean([float(row["confidence"]) for row in tag_rows]))
            if tag_rows
            else float("nan"),
            "accuracy": float(np.mean([float(row["correct"]) for row in tag_rows]))
            if tag_rows
            else float("nan"),
        }
        for tag, tag_rows in sorted(by_tag.items())
    }


def _confidence_correctness(rows: list[dict[str, float | str]]) -> dict[str, float]:
    if not rows:
        return {"mean_confidence": float("nan"), "accuracy": float("nan")}
    return {
        "mean_confidence": float(np.mean([float(row["confidence"]) for row in rows])),
        "accuracy": float(np.mean([float(row["correct"]) for row in rows])),
    }
