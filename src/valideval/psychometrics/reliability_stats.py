from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from itertools import combinations
from math import sqrt

import numpy as np


def _rank_average(values: Sequence[float]) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    order = np.argsort(array, kind="mergesort")
    ranks = np.empty(len(array), dtype=float)
    sorted_values = array[order]
    start = 0
    while start < len(array):
        end = start + 1
        while end < len(array) and sorted_values[end] == sorted_values[start]:
            end += 1
        average_rank = (start + 1 + end) / 2.0
        ranks[order[start:end]] = average_rank
        start = end
    return ranks


def pearson_correlation(x: Sequence[float], y: Sequence[float]) -> float:
    x_array = np.asarray(x, dtype=float)
    y_array = np.asarray(y, dtype=float)
    if len(x_array) != len(y_array) or len(x_array) < 2:
        return float("nan")
    x_centered = x_array - np.mean(x_array)
    y_centered = y_array - np.mean(y_array)
    denom = sqrt(float(np.sum(x_centered**2) * np.sum(y_centered**2)))
    if denom == 0:
        return float("nan")
    return float(np.sum(x_centered * y_centered) / denom)


def spearman_correlation(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x) != len(y) or len(x) < 2:
        return float("nan")
    return pearson_correlation(_rank_average(x), _rank_average(y))


def kendall_tau(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x) != len(y) or len(x) < 2:
        return float("nan")
    concordant = 0
    discordant = 0
    for i, j in combinations(range(len(x)), 2):
        dx = x[i] - x[j]
        dy = y[i] - y[j]
        product = dx * dy
        if product > 0:
            concordant += 1
        elif product < 0:
            discordant += 1
    total = concordant + discordant
    return float((concordant - discordant) / total) if total else float("nan")


def exact_agreement(a: Sequence[int | bool], b: Sequence[int | bool]) -> float:
    if len(a) != len(b) or not a:
        return float("nan")
    return float(sum(int(x == y) for x, y in zip(a, b, strict=True)) / len(a))


def cohen_kappa(a: Sequence[int | bool], b: Sequence[int | bool]) -> float:
    if len(a) != len(b) or not a:
        return float("nan")
    observed = exact_agreement(a, b)
    counts_a = Counter(a)
    counts_b = Counter(b)
    total = len(a)
    expected = sum(
        (counts_a[key] / total) * (counts_b[key] / total) for key in set(counts_a) | set(counts_b)
    )
    if expected == 1.0:
        return 1.0
    return float((observed - expected) / (1.0 - expected))
