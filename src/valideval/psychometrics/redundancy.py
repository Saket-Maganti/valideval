from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from valideval.benchmarks.base import Benchmark
from valideval.schemas import BenchmarkItem, ResponseMatrix
from valideval.scoring.mcq_utils import accepted_labels, tokenize


def redundancy_report(
    benchmark: Benchmark,
    matrix: ResponseMatrix | None = None,
    *,
    near_duplicate_threshold: float = 0.82,
) -> dict[str, Any]:
    items = benchmark.load_items()
    clusters = _cluster_items(items, near_duplicate_threshold=near_duplicate_threshold)
    shared_context_clusters = _shared_context_clusters(items)
    repeated_template_clusters = _repeated_template_clusters(items)
    answer_pattern_clusters = _answer_pattern_clusters(items)
    redundant_item_ids = set()
    for cluster in clusters + shared_context_clusters + repeated_template_clusters:
        if len(cluster) > 1:
            redundant_item_ids.update(cluster[1:])
    redundancy_fraction = len(redundant_item_ids) / len(items) if items else 0.0
    payload: dict[str, Any] = {
        "n_items": len(items),
        "clusters": clusters,
        "shared_context_clusters": shared_context_clusters,
        "repeated_template_clusters": repeated_template_clusters,
        "answer_pattern_duplicate_clusters": answer_pattern_clusters,
        "redundant_item_count": len(redundant_item_ids),
        "redundancy_fraction": redundancy_fraction,
        "effective_item_count": max(1.0, len(items) * (1.0 - redundancy_fraction)),
    }
    if matrix is not None:
        payload["cluster_weighted_accuracy"] = cluster_weighted_accuracy(matrix, clusters)
    return payload


def cluster_weighted_accuracy(
    matrix: ResponseMatrix,
    clusters: list[list[str]],
) -> dict[str, float]:
    frame = matrix.to_dataframe().astype(float)
    cluster_lookup: dict[str, int] = {}
    for cluster_index, cluster in enumerate(clusters):
        for item_id in cluster:
            cluster_lookup[item_id] = cluster_index
    for item_id in frame.columns:
        cluster_lookup.setdefault(item_id, len(cluster_lookup))
    weights = {
        item_id: 1.0 / len(clusters[cluster_lookup[item_id]])
        if cluster_lookup[item_id] < len(clusters)
        else 1.0
        for item_id in frame.columns
    }
    total_weight = sum(weights.values()) or 1.0
    return {
        model_id: float(
            sum(frame.loc[model_id, item_id] * weights[item_id] for item_id in frame.columns)
            / total_weight
        )
        for model_id in frame.index
    }


def _cluster_items(
    items: list[BenchmarkItem],
    *,
    near_duplicate_threshold: float,
) -> list[list[str]]:
    parent = {item.item_id: item.item_id for item in items}

    def find(item_id: str) -> str:
        while parent[item_id] != item_id:
            parent[item_id] = parent[parent[item_id]]
            item_id = parent[item_id]
        return item_id

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for i, left in enumerate(items):
        for right in items[i + 1 :]:
            if _item_similarity(left, right) >= near_duplicate_threshold:
                union(left.item_id, right.item_id)
    clusters: dict[str, list[str]] = defaultdict(list)
    for item in items:
        clusters[find(item.item_id)].append(item.item_id)
    return [sorted(cluster) for cluster in clusters.values() if len(cluster) > 1]


def _item_similarity(left: BenchmarkItem, right: BenchmarkItem) -> float:
    left_tokens = set(tokenize(f"{left.prompt} {left.context or ''}"))
    right_tokens = set(tokenize(f"{right.prompt} {right.context or ''}"))
    if not left_tokens and not right_tokens:
        return 1.0
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _shared_context_clusters(items: list[BenchmarkItem]) -> list[list[str]]:
    by_context: dict[str, list[str]] = defaultdict(list)
    for item in items:
        context = (item.context or "").strip().lower()
        if context:
            by_context[context].append(item.item_id)
    return [sorted(cluster) for cluster in by_context.values() if len(cluster) > 1]


def _repeated_template_clusters(items: list[BenchmarkItem]) -> list[list[str]]:
    by_template: dict[str, list[str]] = defaultdict(list)
    for item in items:
        template = re.sub(r"\b\d+\b", "<num>", item.prompt.lower())
        template = re.sub(r"\b[A-Z][a-z]+\b", "<name>", template)
        template = re.sub(r"\s+", " ", template).strip()
        by_template[template].append(item.item_id)
    return [sorted(cluster) for cluster in by_template.values() if len(cluster) > 1]


def _answer_pattern_clusters(items: list[BenchmarkItem]) -> list[list[str]]:
    by_pattern: dict[str, list[str]] = defaultdict(list)
    for item in items:
        by_pattern["|".join(accepted_labels(item))].append(item.item_id)
    return [sorted(cluster) for cluster in by_pattern.values() if len(cluster) > 3]
