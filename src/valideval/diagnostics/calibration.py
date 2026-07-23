from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from valideval.benchmarks.base import Benchmark
from valideval.diagnostics.base import MatrixInput, matrix_mapping
from valideval.io.cache import load_predictions, prediction_path
from valideval.psychometrics.calibration import calibration_and_abstention_report
from valideval.schemas import DiagnosticResult


class CalibrationDiagnostic:
    name = "calibration"
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
        records = _load_full_predictions(benchmark.benchmark_id, cfg)
        report = calibration_and_abstention_report(
            benchmark,
            records,
            matrices,
            n_bins=int(cfg.get("n_bins", 10)),
        )
        warnings = list(report.pop("warnings", []))
        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics=report,
            warnings=warnings,
            limitations=[
                "Numeric calibration metrics are disabled unless real confidence or logprob values are available; prompt consistency is reported only as a stability proxy."
            ],
        )


def _load_full_predictions(benchmark_id: str, cfg: dict[str, Any]):
    cache_root = cfg.get("cache_root")
    panel_id = cfg.get("panel_id")
    if not cache_root or not panel_id:
        return []
    path = prediction_path(cache_root, benchmark_id, panel_id, "full")
    if not path.exists():
        return []
    return load_predictions(cache_root, benchmark_id, panel_id, "full")
