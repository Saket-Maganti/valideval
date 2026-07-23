from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

from valideval.benchmarks.base import Benchmark
from valideval.diagnostics.base import MatrixInput, matrix_mapping
from valideval.schemas import DiagnosticResult


class PredictiveDiagnostic:
    name = "predictive"
    version = "0.2"

    def run(
        self,
        benchmark: Benchmark,
        predictions: MatrixInput,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> DiagnosticResult:
        cfg = dict(config or {})
        criterion_path = cfg.get("external_criterion_path") or cfg.get("criterion_path")
        if not criterion_path:
            return DiagnosticResult(
                benchmark_id=benchmark.benchmark_id,
                diagnostic_name=self.name,
                version=self.version,
                summary_metrics={"status": "requires_external_criterion"},
                warnings=[
                    "Predictive validity requires an external criterion outcome dataset.",
                    "Provide external_criterion_path in diagnostic config with model-level or "
                    "item-level criterion scores.",
                    "No predictive validity estimate was computed.",
                ],
            )

        records = _load_criterion_records(Path(criterion_path))
        matrices = matrix_mapping(predictions)
        primary_variant = str(cfg.get("primary_full_variant", "full"))
        if primary_variant not in matrices:
            return DiagnosticResult(
                benchmark_id=benchmark.benchmark_id,
                diagnostic_name=self.name,
                version=self.version,
                summary_metrics={"status": "missing_matrix"},
                warnings=[f"Primary matrix variant '{primary_variant}' not available."],
            )

        frame = matrices[primary_variant].to_dataframe().astype(float)
        model_records = [record for record in records if "model_id" in record]
        item_records = [
            record for record in records if "item_id" in record and "criterion_score" in record
        ]

        if model_records:
            summary, per_model, warnings = _model_level_predictive(frame, model_records)
        elif item_records:
            summary, per_model, warnings = _item_level_predictive(frame.T, item_records)
        else:
            return DiagnosticResult(
                benchmark_id=benchmark.benchmark_id,
                diagnostic_name=self.name,
                version=self.version,
                summary_metrics={"status": "invalid_criterion_format"},
                warnings=[
                    "Criterion file must include model_id+criterion_score or item_id+criterion_score records."
                ],
            )

        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics=summary,
            per_item_metrics=per_model,
            warnings=warnings,
            limitations=[
                "Predictive validity correlations are protocol-dependent evidence, not proof of construct validity.",
                "External criterion quality must be independently validated.",
            ],
        )


def _load_criterion_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"External criterion file not found: {path}")
    if path.suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and "records" in payload:
            return list(payload["records"])
        raise ValueError("Criterion JSON must be a list or contain a records array.")
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def _model_level_predictive(
    frame: Any, records: list[dict[str, Any]]
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    benchmark_scores = frame.mean(axis=1)
    pairs = []
    per_model: dict[str, Any] = {}
    for record in records:
        model_id = str(record["model_id"])
        criterion = float(record["criterion_score"])
        if model_id not in benchmark_scores.index:
            continue
        benchmark_score = float(benchmark_scores[model_id])
        pairs.append((benchmark_score, criterion))
        per_model[model_id] = {
            "benchmark_score": benchmark_score,
            "criterion_score": criterion,
            "score_delta": benchmark_score - criterion,
        }
    warnings = []
    if len(pairs) < 3:
        warnings.append(
            "Fewer than three matched model-level criterion records; correlation is unstable."
        )
    if not pairs:
        return (
            {"status": "no_overlap", "matched_model_count": 0},
            per_model,
            ["No model IDs overlapped between criterion file and response matrix."],
        )
    benchmark_values, criterion_values = zip(*pairs, strict=True)
    correlation = float(np.corrcoef(benchmark_values, criterion_values)[0, 1])
    return (
        {
            "status": "measured",
            "analysis_level": "model",
            "matched_model_count": len(pairs),
            "pearson_correlation": correlation,
            "interpretation": _correlation_interpretation(correlation),
        },
        per_model,
        warnings,
    )


def _item_level_predictive(
    frame: Any, records: list[dict[str, Any]]
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    criterion_by_item = {
        str(record["item_id"]): float(record["criterion_score"]) for record in records
    }
    overlap_ids = [item_id for item_id in criterion_by_item if item_id in frame.index]
    per_item: dict[str, Any] = {}
    pairs = []
    for item_id in overlap_ids:
        benchmark_score = float(frame.loc[item_id].mean())
        criterion = criterion_by_item[item_id]
        pairs.append((benchmark_score, criterion))
        per_item[item_id] = {
            "benchmark_score": benchmark_score,
            "criterion_score": criterion,
        }
    warnings = []
    if len(pairs) < 5:
        warnings.append(
            "Fewer than five matched item-level criterion records; correlation is unstable."
        )
    if not pairs:
        return (
            {"status": "no_overlap", "matched_item_count": 0},
            per_item,
            ["No item IDs overlapped between criterion file and response matrix."],
        )
    benchmark_values, criterion_values = zip(*pairs, strict=True)
    correlation = float(np.corrcoef(benchmark_values, criterion_values)[0, 1])
    return (
        {
            "status": "measured",
            "analysis_level": "item",
            "matched_item_count": len(pairs),
            "pearson_correlation": correlation,
            "interpretation": _correlation_interpretation(correlation),
        },
        per_item,
        warnings,
    )


def _correlation_interpretation(correlation: float) -> str:
    magnitude = abs(correlation)
    if magnitude >= 0.7:
        strength = "strong"
    elif magnitude >= 0.4:
        strength = "moderate"
    elif magnitude >= 0.2:
        strength = "weak"
    else:
        strength = "negligible"
    direction = "positive" if correlation >= 0 else "negative"
    return (
        f"Evidence consistent with {strength} {direction} association between benchmark and "
        "external criterion under this protocol."
    )
