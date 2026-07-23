from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations
from typing import Any

import numpy as np

from valideval.forensics.duplicates import _similarity, _template
from valideval.forensics.provenance import item_text
from valideval.forensics.report import risk_from_fraction, signal
from valideval.schemas import BenchmarkItem
from valideval.scoring.mcq_utils import accepted_labels


def split_leakage_report(items: list[BenchmarkItem]) -> dict[str, Any]:
    by_split: dict[str, list[BenchmarkItem]] = defaultdict(list)
    for item in items:
        split = item.metadata.get("split")
        if split:
            by_split[str(split)].append(item)
    if len(by_split) < 2:
        return signal(
            status="unavailable",
            risk_level="unknown/unmeasured",
            warnings=["Split leakage was not measured because fewer than two splits were present."],
        )

    leakage_matrix: dict[str, Any] = {}
    high_risk_items = set()
    pair_count = 0
    risky_pair_count = 0
    for left_split, right_split in combinations(sorted(by_split), 2):
        pair_key = f"{left_split}__vs__{right_split}"
        pair_metrics = _pair_split_metrics(by_split[left_split], by_split[right_split])
        leakage_matrix[pair_key] = pair_metrics
        high_risk_items.update(pair_metrics["high_risk_item_ids"])
        pair_count += pair_metrics["comparisons"]
        risky_pair_count += pair_metrics["risky_pairs"]

    answer_distribution = {
        split: dict(Counter(label for item in split_items for label in accepted_labels(item)))
        for split, split_items in by_split.items()
    }
    difficulty_distribution = {
        split: {
            "mean_declared_difficulty": float(
                np.mean(
                    [
                        float(item.metadata.get("difficulty", np.nan))
                        for item in split_items
                        if item.metadata.get("difficulty") is not None
                    ]
                )
            )
            if any(item.metadata.get("difficulty") is not None for item in split_items)
            else None
        }
        for split, split_items in by_split.items()
    }
    temporal_violations = [
        item.item_id
        for item in items
        if item.metadata.get("source_date")
        and item.metadata.get("split_cutoff_date")
        and str(item.metadata["source_date"]) > str(item.metadata["split_cutoff_date"])
    ]
    leakage_fraction = risky_pair_count / pair_count if pair_count else 0.0
    return signal(
        status="measured",
        risk_level=risk_from_fraction(leakage_fraction),
        metrics={
            "split_counts": {split: len(split_items) for split, split_items in by_split.items()},
            "leakage_matrix": leakage_matrix,
            "high_risk_item_list": sorted(high_risk_items),
            "answer_distribution_by_split": answer_distribution,
            "difficulty_distribution_by_split": difficulty_distribution,
            "temporal_split_violations": temporal_violations,
        },
        warnings=["Split leakage signals are local evidence and require source-level review."],
    )


def _pair_split_metrics(
    left_items: list[BenchmarkItem],
    right_items: list[BenchmarkItem],
) -> dict[str, Any]:
    exact = []
    near = []
    source = []
    template = []
    entity = []
    high_risk = set()
    for left in left_items:
        left_entities = set(_entities(left.prompt))
        for right in right_items:
            if item_text(left).strip().lower() == item_text(right).strip().lower():
                exact.append([left.item_id, right.item_id])
            if _similarity(item_text(left), item_text(right)) >= 0.75:
                near.append([left.item_id, right.item_id])
            if left.source_document and left.source_document == right.source_document:
                source.append([left.item_id, right.item_id])
            if _template(left.prompt) == _template(right.prompt):
                template.append([left.item_id, right.item_id])
            if left_entities and left_entities & set(_entities(right.prompt)):
                entity.append([left.item_id, right.item_id])
    for pairs in [exact, near, source, template]:
        for left_id, right_id in pairs:
            high_risk.update([left_id, right_id])
    risky_pairs = len(exact) + len(near) + len(source) + len(template)
    return {
        "exact_overlap_pairs": exact,
        "near_overlap_pairs": near,
        "source_document_overlap_pairs": source,
        "template_overlap_pairs": template,
        "entity_overlap_pairs": entity,
        "comparisons": len(left_items) * len(right_items),
        "risky_pairs": risky_pairs,
        "high_risk_item_ids": sorted(high_risk),
    }


def _entities(text: str) -> list[str]:
    return [token for token in text.split() if token[:1].isupper()]
