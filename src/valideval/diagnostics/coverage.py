from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping
from typing import Any

from valideval.benchmarks.base import Benchmark
from valideval.diagnostics.base import MatrixInput
from valideval.schemas import DiagnosticResult


class CoverageDiagnostic:
    name = "coverage"
    version = "0.2"

    def run(
        self,
        benchmark: Benchmark,
        predictions: MatrixInput,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> DiagnosticResult:
        cfg = dict(config or {})
        items = benchmark.load_items()
        tag_counts = Counter(tag for item in items for tag in item.construct_tags)
        total = sum(tag_counts.values())
        probabilities = [count / total for count in tag_counts.values()] if total else []
        entropy = -sum(p * math.log(p, 2) for p in probabilities) if probabilities else 0.0
        max_entropy = math.log(len(tag_counts), 2) if tag_counts else 0.0
        balance_score = entropy / max_entropy if max_entropy > 0 else 0.0
        singleton_tags = [tag for tag, count in tag_counts.items() if count == 1]
        underrepresented = [
            tag
            for tag, count in tag_counts.items()
            if count <= int(cfg.get("min_items_per_tag", 2))
        ]
        expected_tags = set(cfg.get("expected_tags", benchmark.construct_spec.construct_tags))
        missing_tags = sorted(expected_tags - set(tag_counts))
        warnings = [
            "Content validity has subjective components; treat tag coverage as auditable metadata."
        ]
        if missing_tags:
            warnings.append(f"Expected construct tags not observed: {', '.join(missing_tags)}.")
        if singleton_tags:
            warnings.append(
                f"Singleton construct tags detected: {', '.join(sorted(singleton_tags)[:8])}."
            )
        if balance_score < 0.5 and tag_counts:
            warnings.append(
                "Tag distribution is imbalanced; construct coverage may be narrow under this protocol."
            )

        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics={
                "n_items": len(items),
                "n_unique_tags": len(tag_counts),
                "tag_entropy_bits": entropy,
                "max_entropy_bits": max_entropy,
                "balance_score": balance_score,
                "singleton_tag_count": len(singleton_tags),
                "singleton_tags": sorted(singleton_tags),
                "underrepresented_tags": sorted(underrepresented),
                "missing_expected_tags": missing_tags,
                "tag_distribution": dict(tag_counts),
            },
            per_item_metrics={
                item.item_id: {
                    "construct_tags": item.construct_tags,
                    "is_singleton_tag_item": any(
                        tag_counts[tag] == 1 for tag in item.construct_tags
                    ),
                }
                for item in items
            },
            warnings=warnings,
        )
