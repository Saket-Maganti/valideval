from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from valideval.forensics.provenance import item_text
from valideval.forensics.report import risk_from_fraction, signal
from valideval.forensics.semantic_duplicates import semantic_duplicate_report
from valideval.schemas import BenchmarkItem
from valideval.scoring.mcq_utils import accepted_labels, correct_choice_text, tokenize


def internal_duplicate_report(
    items: list[BenchmarkItem],
    *,
    near_duplicate_threshold: float = 0.82,
    semantic_duplicate_threshold: float = 0.85,
    enable_semantic_duplicates: bool = True,
) -> dict[str, Any]:
    clusters = {
        "exact_prompt": _clusters_by_key(items, lambda item: _norm(item.prompt)),
        "near_duplicate": _near_duplicate_clusters(items, threshold=near_duplicate_threshold),
        "shared_context": _clusters_by_key(items, lambda item: _norm(item.context or "")),
        "same_source": _clusters_by_key(items, lambda item: item.source_document or ""),
        "same_template": _clusters_by_key(items, lambda item: _template(item.prompt)),
        "answer_duplicate": _clusters_by_key(items, _answer_key),
        "rationale_duplicate": _clusters_by_key(
            items, lambda item: _norm(str(item.metadata.get("rationale", "")))
        ),
    }
    duplicate_ids = set()
    for cluster_list in clusters.values():
        for cluster in cluster_list:
            duplicate_ids.update(cluster[1:])
    duplicate_fraction = len(duplicate_ids) / len(items) if items else 0.0
    semantic = (
        semantic_duplicate_report(items, threshold=semantic_duplicate_threshold)
        if enable_semantic_duplicates
        else {
            "status": "unavailable",
            "risk_level": "unknown/unmeasured",
            "reason": "Semantic duplicate detection was disabled in config.",
        }
    )
    semantic_ids = set()
    if semantic.get("status") == "measured":
        semantic_ids.update(semantic.get("metrics", {}).get("duplicate_item_ids", []))
    combined_ids = sorted(set(duplicate_ids) | semantic_ids)
    payload = {
        "duplicate_clusters": clusters,
        "duplicate_fraction": duplicate_fraction,
        "cluster_sizes": {
            name: [len(cluster) for cluster in cluster_list]
            for name, cluster_list in clusters.items()
        },
        "effective_independent_item_count": len(items) - len(duplicate_ids),
        "semantic_duplicates": semantic,
        "combined_duplicate_item_ids": combined_ids,
        "duplicate_item_ids": sorted(duplicate_ids),
    }
    warnings = [
        "Duplicate detection uses local lexical/template signals plus optional TF-IDF semantic clusters."
    ]
    if semantic.get("status") == "measured":
        warnings.extend(semantic.get("warnings", []))
    return signal(
        status="measured",
        risk_level=risk_from_fraction(duplicate_fraction),
        metrics=payload,
        warnings=warnings,
    )


def _clusters_by_key(items: list[BenchmarkItem], key_fn) -> list[list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for item in items:
        key = key_fn(item)
        if key:
            groups[key].append(item.item_id)
    return [sorted(group) for group in groups.values() if len(group) > 1]


def _near_duplicate_clusters(
    items: list[BenchmarkItem],
    *,
    threshold: float,
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

    for index, left in enumerate(items):
        for right in items[index + 1 :]:
            if _similarity(item_text(left), item_text(right)) >= threshold:
                union(left.item_id, right.item_id)

    groups: dict[str, list[str]] = defaultdict(list)
    for item in items:
        groups[find(item.item_id)].append(item.item_id)
    return [sorted(group) for group in groups.values() if len(group) > 1]


def _similarity(left: str, right: str) -> float:
    left_tokens = set(tokenize(left))
    right_tokens = set(tokenize(right))
    if not left_tokens and not right_tokens:
        return 1.0
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _template(prompt: str) -> str:
    value = prompt.lower()
    value = re.sub(r"\b\d+\b", "<num>", value)
    value = re.sub(r"'[^']+'", "<quoted>", value)
    value = re.sub(r"\b[a-z]{4,}\b", "<word>", value)
    return re.sub(r"\s+", " ", value).strip()


def _answer_key(item: BenchmarkItem) -> str:
    if item.choices:
        return _norm(correct_choice_text(item))
    return _norm("|".join(accepted_labels(item)))


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()
