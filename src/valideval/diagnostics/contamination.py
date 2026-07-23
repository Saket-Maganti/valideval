from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from valideval.benchmarks.base import Benchmark
from valideval.diagnostics.base import MatrixInput
from valideval.forensics.duplicates import internal_duplicate_report
from valideval.forensics.overlap import scan_corpus_overlap
from valideval.schemas import DiagnosticResult


class ContaminationDiagnostic:
    name = "contamination"
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
        duplicate_signal = internal_duplicate_report(
            items,
            near_duplicate_threshold=float(cfg.get("near_duplicate_threshold", 0.82)),
        )
        overlap_signal = scan_corpus_overlap(
            benchmark,
            cfg.get("corpus_path"),
            ngram_n=int(cfg.get("ngram_n", 5)),
        )
        overlap_metrics = overlap_signal.get("metrics", {})
        duplicate_metrics = duplicate_signal.get("metrics", {})
        per_overlap = overlap_metrics.get("per_item", {})
        duplicate_ids = set(duplicate_metrics.get("duplicate_item_ids", []))

        warnings = [
            "Overlap is evidence, not proof, of contamination.",
            "Absence of overlap is not proof of cleanliness.",
        ]
        if not cfg.get("corpus_path"):
            warnings.append(
                "No external corpus was supplied; only intra-benchmark duplicates were checked."
            )
        warnings.extend(overlap_signal.get("warnings", []))
        warnings.extend(duplicate_signal.get("warnings", []))

        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics={
                "intra_benchmark_duplicate_rate": duplicate_metrics.get("duplicate_fraction", 0.0),
                "external_exact_overlap_rate": overlap_metrics.get("exact_match_rate", 0.0),
                "external_question_overlap_rate": overlap_metrics.get("question_match_rate", 0.0),
                "overlap_risk_level": overlap_signal.get("risk_level"),
                "duplicate_risk_level": duplicate_signal.get("risk_level"),
            },
            per_item_metrics={
                item.item_id: {
                    "duplicate_prompt": item.item_id in duplicate_ids,
                    "external_exact_match": per_overlap.get(item.item_id, {}).get(
                        "exact_match", False
                    ),
                    "external_question_match": per_overlap.get(item.item_id, {}).get(
                        "question_match", False
                    ),
                }
                for item in items
            },
            warnings=warnings,
            limitations=[
                "Contamination evidence is local and corpus-dependent; this diagnostic does not prove cleanliness."
            ],
        )
