from __future__ import annotations

import math
from typing import Any

import numpy as np


def roc_auc(y_true: list[bool | int], scores: list[float]) -> float | None:
    labels, values = _clean_pairs(y_true, scores)
    positives = [score for label, score in zip(labels, values, strict=True) if label]
    negatives = [score for label, score in zip(labels, values, strict=True) if not label]
    if not positives or not negatives:
        return None
    wins = 0.0
    for positive in positives:
        for negative in negatives:
            if positive > negative:
                wins += 1.0
            elif positive == negative:
                wins += 0.5
    return wins / (len(positives) * len(negatives))


def precision_recall_auc(y_true: list[bool | int], scores: list[float]) -> float | None:
    labels, values = _clean_pairs(y_true, scores)
    if not labels or not any(labels):
        return None
    order = np.argsort(values)[::-1]
    total_positive = sum(labels)
    recalls = [0.0]
    precisions = [1.0]
    tp = 0
    fp = 0
    for index in order:
        if labels[int(index)]:
            tp += 1
        else:
            fp += 1
        recalls.append(tp / total_positive)
        precisions.append(tp / max(tp + fp, 1))
    area = 0.0
    for idx in range(1, len(recalls)):
        area += (recalls[idx] - recalls[idx - 1]) * precisions[idx]
    return float(area)


def sensitivity(y_true: list[bool | int], scores: list[float], threshold: float) -> float | None:
    counts = _confusion(y_true, scores, threshold)
    denom = counts["tp"] + counts["fn"]
    return counts["tp"] / denom if denom else None


def specificity(y_true: list[bool | int], scores: list[float], threshold: float) -> float | None:
    counts = _confusion(y_true, scores, threshold)
    denom = counts["tn"] + counts["fp"]
    return counts["tn"] / denom if denom else None


def false_positive_rate(
    y_true: list[bool | int], scores: list[float], threshold: float
) -> float | None:
    spec = specificity(y_true, scores, threshold)
    return None if spec is None else 1.0 - spec


def false_negative_rate(
    y_true: list[bool | int], scores: list[float], threshold: float
) -> float | None:
    sens = sensitivity(y_true, scores, threshold)
    return None if sens is None else 1.0 - sens


def precision(y_true: list[bool | int], scores: list[float], threshold: float) -> float | None:
    counts = _confusion(y_true, scores, threshold)
    denom = counts["tp"] + counts["fp"]
    return counts["tp"] / denom if denom else None


def recall(y_true: list[bool | int], scores: list[float], threshold: float) -> float | None:
    return sensitivity(y_true, scores, threshold)


def f1(y_true: list[bool | int], scores: list[float], threshold: float) -> float | None:
    p = precision(y_true, scores, threshold)
    r = recall(y_true, scores, threshold)
    if p is None or r is None or p + r == 0:
        return None
    return 2.0 * p * r / (p + r)


def monotonicity_score(strengths: list[float], scores: list[float]) -> float | None:
    pairs = [
        (float(strength), float(score))
        for strength, score in zip(strengths, scores, strict=True)
        if _finite(strength) and _finite(score)
    ]
    if len(pairs) < 2:
        return None
    pairs.sort(key=lambda pair: pair[0])
    comparisons = 0
    nondecreasing = 0
    for left, right in zip(pairs, pairs[1:], strict=False):
        if right[0] == left[0]:
            continue
        comparisons += 1
        if right[1] >= left[1]:
            nondecreasing += 1
    return nondecreasing / comparisons if comparisons else None


def spearman_with_true_strength(strengths: list[float], scores: list[float]) -> float | None:
    pairs = [
        (float(strength), float(score))
        for strength, score in zip(strengths, scores, strict=True)
        if _finite(strength) and _finite(score)
    ]
    if len(pairs) < 2:
        return None
    left = _ranks([pair[0] for pair in pairs])
    right = _ranks([pair[1] for pair in pairs])
    if np.std(left) == 0 or np.std(right) == 0:
        return None
    return float(np.corrcoef(left, right)[0, 1])


def calibration_curve(
    y_true: list[bool | int],
    scores: list[float],
    *,
    n_bins: int = 10,
) -> list[dict[str, float | int]]:
    labels, values = _clean_pairs(y_true, scores)
    if not values:
        return []
    low = min(values)
    high = max(values)
    if low == high:
        high = low + 1e-8
    bins = []
    for idx in range(n_bins):
        lower = low + (idx / n_bins) * (high - low)
        upper = low + ((idx + 1) / n_bins) * (high - low)
        bucket = [
            label
            for label, score in zip(labels, values, strict=True)
            if lower <= score < upper or (idx == n_bins - 1 and score <= upper)
        ]
        if not bucket:
            bins.append(
                {"bin": idx, "n": 0, "mean_score": (lower + upper) / 2, "positive_rate": 0.0}
            )
            continue
        bucket_scores = [
            score
            for score in values
            if lower <= score < upper or (idx == n_bins - 1 and score <= upper)
        ]
        bins.append(
            {
                "bin": idx,
                "n": len(bucket),
                "mean_score": float(np.mean(bucket_scores)),
                "positive_rate": float(np.mean(bucket)),
            }
        )
    return bins


def null_distribution(scores: list[float]) -> dict[str, Any]:
    values = [float(score) for score in scores if _finite(score)]
    if not values:
        return {"n": 0, "mean": None, "std": None, "p95": None, "p99": None}
    return {
        "n": len(values),
        "mean": float(np.mean(values)),
        "std": float(np.std(values)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "p95": float(np.quantile(values, 0.95)),
        "p99": float(np.quantile(values, 0.99)),
    }


def threshold_at_target_fpr(clean_scores: list[float], target_fpr: float = 0.05) -> float | None:
    values = sorted(float(score) for score in clean_scores if _finite(score))
    if not values:
        return None
    quantile = min(max(1.0 - target_fpr, 0.0), 1.0)
    return float(np.quantile(values, quantile))


def metric_bundle(
    y_true: list[bool | int],
    scores: list[float],
    *,
    clean_scores: list[float] | None = None,
    threshold: float | None = None,
) -> dict[str, Any]:
    threshold = threshold if threshold is not None else threshold_at_target_fpr(clean_scores or [])
    if threshold is None:
        finite_scores = [score for score in scores if _finite(score)]
        threshold = float(np.median(finite_scores)) if finite_scores else 0.5
    return {
        "auc": roc_auc(y_true, scores),
        "pr_auc": precision_recall_auc(y_true, scores),
        "threshold": threshold,
        "sensitivity": sensitivity(y_true, scores, threshold),
        "specificity": specificity(y_true, scores, threshold),
        "false_positive_rate": false_positive_rate(y_true, scores, threshold),
        "false_negative_rate": false_negative_rate(y_true, scores, threshold),
        "precision": precision(y_true, scores, threshold),
        "recall": recall(y_true, scores, threshold),
        "f1": f1(y_true, scores, threshold),
    }


def _confusion(
    y_true: list[bool | int],
    scores: list[float],
    threshold: float,
) -> dict[str, int]:
    labels, values = _clean_pairs(y_true, scores)
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    for label, score in zip(labels, values, strict=True):
        predicted = score >= threshold
        if predicted and label:
            counts["tp"] += 1
        elif predicted and not label:
            counts["fp"] += 1
        elif not predicted and label:
            counts["fn"] += 1
        else:
            counts["tn"] += 1
    return counts


def _clean_pairs(y_true: list[bool | int], scores: list[float]) -> tuple[list[bool], list[float]]:
    labels: list[bool] = []
    values: list[float] = []
    for label, score in zip(y_true, scores, strict=True):
        value = float(score)
        if not _finite(value):
            continue
        labels.append(bool(label))
        values.append(value)
    return labels, values


def _ranks(values: list[float]) -> np.ndarray:
    order = np.argsort(values)
    ranks = np.empty(len(values), dtype=float)
    ranks[order] = np.arange(len(values), dtype=float)
    return ranks


def _finite(value: float) -> bool:
    return not (math.isnan(float(value)) or math.isinf(float(value)))
