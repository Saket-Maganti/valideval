from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np

from valideval.benchmarks.base import Benchmark
from valideval.psychometrics.reliability_stats import kendall_tau, spearman_correlation
from valideval.schemas import ResponseMatrix


def select_items_by_mode(
    benchmark: Benchmark,
    item_stats: dict[str, dict[str, Any]],
    *,
    mode: str,
    k: int,
    seed: int = 0,
) -> list[str]:
    item_ids = list(item_stats)
    k = max(0, min(k, len(item_ids)))
    if k == 0:
        return []
    if mode == "random_baseline":
        rng = np.random.default_rng(seed)
        return rng.choice(item_ids, size=k, replace=False).tolist()
    if mode in {"top_discrimination", "maximum_information", "high_reliability"}:
        key = {
            "top_discrimination": "discrimination",
            "maximum_information": "information_proxy",
            "high_reliability": "information_proxy",
        }[mode]
        filtered = item_stats.items()
        if mode == "high_reliability":
            filtered = [
                (item_id, stats)
                for item_id, stats in item_stats.items()
                if not stats.get("negative_discrimination")
                and not stats.get("near_zero_discrimination")
            ]
        ordered = sorted(
            filtered,
            key=lambda pair: (float(pair[1].get(key, 0.0)), pair[0]),
            reverse=True,
        )
        selected = [item_id for item_id, _ in ordered[:k]]
        return selected or select_items_by_mode(
            benchmark, item_stats, mode="maximum_information", k=k, seed=seed
        )
    if mode == "low_contamination_risk":
        risky_tags = {
            "answer_prior_artifact",
            "duplicate_near_duplicate",
            "lexical_shortcut",
        }
        item_lookup = {item.item_id: item for item in benchmark.load_items()}
        low_risk = [
            item_id
            for item_id in item_ids
            if item_id not in item_lookup
            or not (set(item_lookup[item_id].construct_tags) & risky_tags)
        ]
        ordered = sorted(
            low_risk,
            key=lambda item_id: float(item_stats[item_id].get("information_proxy", 0.0)),
            reverse=True,
        )
        selected = ordered[:k]
        if len(selected) < k:
            selected.extend(item_id for item_id in item_ids if item_id not in selected)
        return selected[:k]
    if mode in {"balanced_by_construct_tag", "coverage_constrained"}:
        return _balanced_by_tag(benchmark, item_stats, k)
    raise ValueError(f"Unknown subset mode: {mode}")


def evaluate_subset_modes(
    benchmark: Benchmark,
    matrix: ResponseMatrix,
    item_stats: dict[str, dict[str, Any]],
    *,
    sizes: list[int],
    modes: list[str] | None = None,
    random_trials: int = 50,
    seed: int = 0,
) -> dict[str, Any]:
    frame = matrix.to_dataframe().astype(float)
    full_scores = frame.mean(axis=1)
    modes = modes or [
        "top_discrimination",
        "maximum_information",
        "balanced_by_construct_tag",
        "low_contamination_risk",
        "high_reliability",
        "coverage_constrained",
        "random_baseline",
    ]
    output: dict[str, Any] = {}
    for size in [size for size in sizes if 0 < size <= frame.shape[1]]:
        size_payload: dict[str, Any] = {}
        random_fidelities = []
        for trial in range(random_trials):
            selected = select_items_by_mode(
                benchmark,
                item_stats,
                mode="random_baseline",
                k=size,
                seed=seed + trial,
            )
            random_scores = frame[selected].mean(axis=1)
            random_fidelities.append(
                spearman_correlation(full_scores.tolist(), random_scores.tolist())
            )
        random_fidelities = [value for value in random_fidelities if not np.isnan(value)]

        for mode in modes:
            selected = select_items_by_mode(
                benchmark,
                item_stats,
                mode=mode,
                k=size,
                seed=seed,
            )
            subset_scores = frame[selected].mean(axis=1)
            size_payload[mode] = {
                "selected_items": selected,
                "spearman_with_full": spearman_correlation(
                    full_scores.tolist(), subset_scores.tolist()
                ),
                "kendall_with_full": kendall_tau(full_scores.tolist(), subset_scores.tolist()),
                "top_3_agreement": top_k_agreement(
                    full_scores.to_dict(), subset_scores.to_dict(), k=min(3, frame.shape[0])
                ),
                "random_mean_spearman_with_full": float(np.mean(random_fidelities))
                if random_fidelities
                else float("nan"),
                "random_trials": random_trials,
            }
        output[str(size)] = size_payload
    return output


def top_k_agreement(
    baseline_scores: dict[str, float],
    subset_scores: dict[str, float],
    *,
    k: int,
) -> float:
    baseline_top = set(_ordered_models(baseline_scores)[:k])
    subset_top = set(_ordered_models(subset_scores)[:k])
    return len(baseline_top & subset_top) / k if k else 0.0


def _ordered_models(scores: dict[str, float]) -> list[str]:
    return sorted(scores, key=lambda model_id: (scores[model_id], model_id), reverse=True)


def _balanced_by_tag(
    benchmark: Benchmark,
    item_stats: dict[str, dict[str, Any]],
    k: int,
) -> list[str]:
    by_tag: dict[str, list[str]] = defaultdict(list)
    for item in benchmark.load_items():
        if item.item_id not in item_stats:
            continue
        tags = item.construct_tags or ["untagged"]
        for tag in tags:
            by_tag[tag].append(item.item_id)
    if not by_tag:
        return select_items_by_mode(benchmark, item_stats, mode="maximum_information", k=k, seed=0)
    for tag, item_ids in by_tag.items():
        by_tag[tag] = sorted(
            set(item_ids),
            key=lambda item_id: float(item_stats[item_id].get("information_proxy", 0.0)),
            reverse=True,
        )

    selected: list[str] = []
    tags = sorted(by_tag)
    while len(selected) < k and tags:
        progressed = False
        for tag in tags:
            while by_tag[tag] and by_tag[tag][0] in selected:
                by_tag[tag].pop(0)
            if by_tag[tag] and len(selected) < k:
                selected.append(by_tag[tag].pop(0))
                progressed = True
        if not progressed:
            break
    if len(selected) < k:
        fallback = sorted(
            item_stats,
            key=lambda item_id: float(item_stats[item_id].get("information_proxy", 0.0)),
            reverse=True,
        )
        selected.extend(item_id for item_id in fallback if item_id not in selected)
    return selected[:k]
