from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from valideval.benchmarks.base import Benchmark
from valideval.schemas import BenchmarkItem

PROVENANCE_FIELDS = [
    "source_url",
    "source_document",
    "snapshot",
    "license",
    "created_by",
    "generated_by_model",
    "human_verified",
    "appears_in_paper_examples",
    "appears_in_readme",
    "appears_in_hf_preview",
]


def stable_hash(payload: Any) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def item_text(item: BenchmarkItem) -> str:
    choices = "\n".join(item.choices or [])
    answer = "|".join(item.answer) if isinstance(item.answer, list) else str(item.answer)
    return "\n\n".join(
        part
        for part in [
            item.context or "",
            item.prompt,
            choices,
            answer,
        ]
        if part
    )


def prompt_template_hash(benchmark: Benchmark, items: list[BenchmarkItem]) -> str:
    if not items:
        return stable_hash([])
    first = items[0]
    prompts = {
        variant: benchmark.render_prompt(first, variant=variant)
        for variant in benchmark.available_prompt_variants()
    }
    return stable_hash(prompts)


def audit_manifest_hashes(
    benchmark: Benchmark,
    *,
    benchmark_config: dict[str, Any] | None = None,
    diagnostic_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    items = benchmark.load_items()
    split_counts = Counter(str(item.metadata.get("split", "unspecified")) for item in items)
    return {
        "dataset_id": benchmark.benchmark_id,
        "item_count": len(items),
        "split_counts": dict(sorted(split_counts.items())),
        "item_ids_hash": stable_hash([item.item_id for item in items]),
        "item_text_hash": stable_hash([item_text(item) for item in items]),
        "benchmark_config_hash": stable_hash(
            benchmark_config or {"benchmark_id": benchmark.benchmark_id}
        ),
        "scorer_hash": stable_hash(
            {
                "benchmark_class": benchmark.__class__.__name__,
                "scorer": getattr(benchmark.score_prediction, "__name__", "score_prediction"),
            }
        ),
        "prompt_template_hash": prompt_template_hash(benchmark, items),
        "diagnostic_config_hash": stable_hash(diagnostic_config or {}),
    }


def provenance_completeness(items: list[BenchmarkItem]) -> dict[str, Any]:
    per_item = {}
    missing_counts = Counter()
    complete_count = 0
    for item in items:
        missing = [field for field in PROVENANCE_FIELDS if getattr(item, field, None) is None]
        for field in missing:
            missing_counts[field] += 1
        if not missing:
            complete_count += 1
        per_item[item.item_id] = {
            "missing_fields": missing,
            "completeness_fraction": (len(PROVENANCE_FIELDS) - len(missing))
            / len(PROVENANCE_FIELDS),
            "human_verified": item.human_verified,
            "generated_by_model": item.generated_by_model,
        }
    n_items = len(items)
    return {
        "status": "measured",
        "completeness_fraction": complete_count / n_items if n_items else 0.0,
        "field_missing_counts": dict(sorted(missing_counts.items())),
        "per_item": per_item,
    }


def write_manifest(path: str | Path, payload: dict[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output
