from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from valideval.benchmarks.base import Benchmark
from valideval.diagnostics.base import MatrixInput, matrix_mapping
from valideval.psychometrics.redundancy import redundancy_report
from valideval.schemas import DiagnosticResult


class RedundancyDiagnostic:
    name = "redundancy"
    version = "0.1"

    def run(
        self,
        benchmark: Benchmark,
        predictions: MatrixInput,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> DiagnosticResult:
        cfg = dict(config or {})
        matrices = matrix_mapping(predictions)
        matrix = matrices.get("full")
        report = redundancy_report(
            benchmark,
            matrix,
            near_duplicate_threshold=float(cfg.get("near_duplicate_threshold", 0.82)),
        )
        warnings = []
        if report["redundancy_fraction"] > 0:
            warnings.append(
                "Duplicate or near-duplicate clusters were detected; evidence is consistent with redundancy affecting effective item count."
            )
        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics=report,
            warnings=warnings,
            limitations=[
                "Near-duplicate detection uses lexical similarity and simple template rules; manual review is required."
            ],
        )
