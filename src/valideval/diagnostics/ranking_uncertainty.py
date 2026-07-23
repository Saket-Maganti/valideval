from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from valideval.benchmarks.base import Benchmark
from valideval.diagnostics.base import MatrixInput, matrix_mapping
from valideval.psychometrics.ranking_uncertainty import bootstrap_rank_uncertainty
from valideval.schemas import DiagnosticResult


class RankingUncertaintyDiagnostic:
    name = "ranking_uncertainty"
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
        if "full" not in matrices:
            raise ValueError("Ranking-uncertainty diagnostic requires a 'full' matrix.")
        report = bootstrap_rank_uncertainty(
            matrices["full"],
            n_boot=int(cfg.get("bootstrap_samples", 500)),
            seed=int(cfg.get("seed", 0)),
            top_k=int(cfg.get("top_k", 3)),
        )
        warnings = []
        if report["ranking_flip_detector"]:
            warnings.append(
                "Bootstrap rank distributions show possible ranking instability under item resampling."
            )
        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics=report,
            warnings=warnings,
            limitations=[
                "Rank uncertainty is conditional on the observed item set and bootstrap resampling assumptions."
            ],
        )
