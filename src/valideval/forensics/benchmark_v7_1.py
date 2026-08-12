from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd

FORENSIC_CLASSES = (
    "EXACT_DUPLICATE",
    "NEAR_DUPLICATE_CANDIDATE",
    "OPTION_PERMUTATION",
    "CROSS_SPLIT_OVERLAP",
    "CROSS_BENCHMARK_OVERLAP",
    "NO_MATCH",
)


def analyze_frozen_manifest_forensics(
    manifests: Mapping[str, str | Path],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Run every forensic comparison supported by content-addressed frozen manifests."""

    records: list[dict[str, Any]] = []
    by_normalized_hash: dict[str, list[dict[str, str]]] = defaultdict(list)
    benchmark_counts: dict[str, int] = {}
    for benchmark, path_value in sorted(manifests.items()):
        path = Path(path_value)
        payload = json.loads(path.read_text(encoding="utf-8"))
        items = payload.get("items")
        if not isinstance(items, list):
            raise ValueError(f"manifest items must be a list: {path}")
        benchmark_counts[str(benchmark)] = len(items)
        local: dict[str, list[str]] = defaultdict(list)
        for item in items:
            normalized_hash = str(item.get("normalized_text_hash", ""))
            item_id = str(item["item_id"])
            local[normalized_hash].append(item_id)
            by_normalized_hash[normalized_hash].append(
                {"benchmark": str(benchmark), "item_id": item_id}
            )
        matched: set[str] = set()
        for normalized_hash, item_ids in sorted(local.items()):
            if normalized_hash and len(item_ids) > 1:
                matched.update(item_ids)
                records.append(
                    {
                        "match_type": "EXACT_DUPLICATE",
                        "benchmark_a": benchmark,
                        "benchmark_b": benchmark,
                        "item_ids": "|".join(sorted(item_ids)),
                        "normalized_text_hash": normalized_hash,
                        "promotion_status": "CONFIRMED_BY_EXACT_NORMALIZED_HASH",
                    }
                )
        for item in items:
            if str(item["item_id"]) not in matched:
                records.append(
                    {
                        "match_type": "NO_MATCH",
                        "benchmark_a": benchmark,
                        "benchmark_b": benchmark,
                        "item_ids": str(item["item_id"]),
                        "normalized_text_hash": str(item.get("normalized_text_hash", "")),
                        "promotion_status": "NO_EXACT_MANIFEST_MATCH",
                    }
                )
    for normalized_hash, matches in sorted(by_normalized_hash.items()):
        benchmarks = {row["benchmark"] for row in matches}
        if normalized_hash and len(benchmarks) > 1:
            records.append(
                {
                    "match_type": "CROSS_BENCHMARK_OVERLAP",
                    "benchmark_a": sorted(benchmarks)[0],
                    "benchmark_b": sorted(benchmarks)[-1],
                    "item_ids": "|".join(sorted(row["item_id"] for row in matches)),
                    "normalized_text_hash": normalized_hash,
                    "promotion_status": "CONFIRMED_BY_EXACT_NORMALIZED_HASH",
                }
            )
    table = pd.DataFrame(records)
    summary = {
        "status": "BENCHMARK_FORENSICS_V7_1_READY",
        "benchmark_item_counts": benchmark_counts,
        "observed_match_type_counts": table["match_type"].value_counts().to_dict(),
        "supported_checks": [
            "within-benchmark exact item identity",
            "normalized exact duplicates",
            "cross-benchmark normalized exact overlap",
        ],
        "unavailable_checks": {
            "CROSS_SPLIT_OVERLAP": "Frozen Study-C manifests contain one test split per benchmark.",
            "NEAR_DUPLICATE_CANDIDATE": (
                "Frozen manifests intentionally omit prompt text; n-gram and MinHash retrieval "
                "must run during source-data freeze or on a separately approved text artifact."
            ),
            "OPTION_PERMUTATION": "Frozen manifests omit option text and gold-option equivalence.",
            "semantic_candidate_retrieval": (
                "No embedding or prompt-text artifact is present; no semantic candidate was fabricated."
            ),
        },
        "semantic_promotion_rule": "MANUAL_CONFIRMATION_REQUIRED",
        "contamination_claim_permitted": False,
        "claim_boundary": (
            "Duplicate or overlap evidence is a benchmark forensic signal and does not establish "
            "pretraining contamination."
        ),
    }
    return table, summary
