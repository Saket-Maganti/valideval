from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np

from valideval.benchmarks.base import Benchmark
from valideval.schemas import ResponseMatrix


def tag_skill_profiles(
    benchmark: Benchmark,
    matrix: ResponseMatrix,
    *,
    min_items_per_tag: int = 3,
) -> dict[str, Any]:
    frame = matrix.to_dataframe().astype(float)
    tag_to_items: dict[str, list[str]] = defaultdict(list)
    for item in benchmark.load_items():
        for tag in item.construct_tags or ["untagged"]:
            if item.item_id in frame.columns:
                tag_to_items[tag].append(item.item_id)

    warnings = [
        f"Construct tag '{tag}' has only {len(item_ids)} item(s); skill estimates are unstable."
        for tag, item_ids in sorted(tag_to_items.items())
        if len(item_ids) < min_items_per_tag
    ]
    profiles: dict[str, dict[str, float]] = {}
    tag_summary: dict[str, dict[str, float | int]] = {}
    for model_id in frame.index:
        profiles[model_id] = {}
        for tag, item_ids in tag_to_items.items():
            profiles[model_id][tag] = float(frame.loc[model_id, item_ids].mean())
    for tag, item_ids in tag_to_items.items():
        tag_scores = frame[item_ids].mean(axis=1)
        tag_summary[tag] = {
            "n_items": len(item_ids),
            "mean_score": float(np.mean(tag_scores.values)),
            "score_variance": float(np.var(tag_scores.values)),
        }
    return {
        "model_skill_profile": profiles,
        "tag_summary": tag_summary,
        "warnings": warnings,
    }
