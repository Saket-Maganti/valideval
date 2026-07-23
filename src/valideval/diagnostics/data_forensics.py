from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from valideval.benchmarks.base import Benchmark
from valideval.diagnostics.base import MatrixInput
from valideval.forensics.contamination import run_data_forensics
from valideval.schemas import DiagnosticResult


class DataForensicsDiagnostic:
    name = "data_forensics"
    version = "0.1"

    def run(
        self,
        benchmark: Benchmark,
        predictions: MatrixInput,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> DiagnosticResult:
        cfg = dict(config or {})
        report = run_data_forensics(
            benchmark,
            corpus_path=cfg.get("corpus_path"),
            benchmark_config={"benchmark_id": benchmark.benchmark_id},
            diagnostic_config=cfg,
        )
        signals = report["signals"]
        warnings = list(report["warnings"])
        for signal_payload in signals.values():
            warnings.extend(signal_payload.get("warnings", []))
        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics={
                "signals": {
                    key: {
                        "status": value.get("status"),
                        "risk_level": value.get("risk_level"),
                        "metrics": value.get("metrics", {}),
                    }
                    for key, value in signals.items()
                },
                "searched": report["searched"],
                "not_searched": report["not_searched"],
                "hashes": report["hashes"],
            },
            per_item_metrics=_per_item(signals),
            warnings=warnings,
            limitations=[
                "Forensics signals are local, corpus-dependent evidence and must not be read as proof of contamination or cleanliness."
            ],
            artifacts={"manifest_hashes": report["hashes"]},
        )


def _per_item(signals: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for signal_name, payload in signals.items():
        metrics = payload.get("metrics", {})
        per_item = metrics.get("per_item")
        if not isinstance(per_item, dict):
            continue
        for item_id, values in per_item.items():
            output.setdefault(item_id, {})[signal_name] = values
    return output
