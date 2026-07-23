from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from valideval.benchmarks.base import Benchmark
from valideval.diagnostics.base import MatrixInput, matrix_mapping
from valideval.psychometrics.power import power_summary
from valideval.psychometrics.redundancy import redundancy_report
from valideval.schemas import DiagnosticResult


class PowerDiagnostic:
    name = "power"
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
            raise ValueError("Power diagnostic requires a 'full' matrix.")
        redundancy = redundancy_report(benchmark, matrices["full"])
        summary = power_summary(
            matrices["full"],
            redundancy_fraction=float(redundancy["redundancy_fraction"]),
            n_boot=int(cfg.get("bootstrap_samples", 500)),
            seed=int(cfg.get("seed", 0)),
        )
        warning_points = float(summary["do_not_overinterpret_within_points"])
        warnings = [
            f"Do not overinterpret model score differences within approximately {warning_points:.2f} percentage points under this protocol."
        ]
        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics={
                **summary,
                "redundancy_adjustment": {
                    "redundancy_fraction": redundancy["redundancy_fraction"],
                    "effective_item_count": redundancy["effective_item_count"],
                },
            },
            per_model_metrics={
                model_id: {"standard_error": se}
                for model_id, se in summary["model_standard_errors"].items()
            },
            warnings=warnings,
            limitations=[
                "Power estimates assume item independence after a simple redundancy adjustment; they are planning aids, not definitive uncertainty bounds."
            ],
        )
