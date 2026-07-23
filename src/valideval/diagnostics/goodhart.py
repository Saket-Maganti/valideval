from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

from valideval.benchmarks.base import Benchmark
from valideval.diagnostics.base import MatrixInput, matrix_mapping
from valideval.schemas import DiagnosticResult


class GoodhartDiagnostic:
    name = "goodhart"
    version = "0.2"

    def run(
        self,
        benchmark: Benchmark,
        predictions: MatrixInput,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> DiagnosticResult:
        cfg = dict(config or {})
        intervention_path = cfg.get("intervention_path") or cfg.get("longitudinal_path")
        if not intervention_path:
            return DiagnosticResult(
                benchmark_id=benchmark.benchmark_id,
                diagnostic_name=self.name,
                version=self.version,
                summary_metrics={"status": "requires_longitudinal_or_intervention_data"},
                warnings=[
                    "Goodhart and consequential-validity diagnostics require longitudinal, deployment, "
                    "or intervention data.",
                    "Provide intervention_path in diagnostic config with pre/post scores or "
                    "optimization-round records.",
                    "No consequential validity estimate was computed.",
                ],
            )

        records = _load_intervention_records(Path(intervention_path))
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
        benchmark_scores = frame.mean(axis=1)
        summary, per_model, warnings = _analyze_interventions(records, benchmark_scores)
        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics=summary,
            per_item_metrics=per_model,
            warnings=warnings,
            limitations=[
                "Intervention drift signals are evidence of potential Goodhart effects, not proof.",
                "Deployment outcomes require independent validation beyond benchmark optimization.",
            ],
        )


def _load_intervention_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Intervention data file not found: {path}")
    if path.suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and "records" in payload:
            return list(payload["records"])
        raise ValueError("Intervention JSON must be a list or contain a records array.")
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def _analyze_interventions(
    records: list[dict[str, Any]], benchmark_scores: Any
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    per_model: dict[str, Any] = {}
    drifts = []
    gaming_signals = []
    for record in records:
        model_id = str(record.get("model_id", ""))
        if not model_id:
            continue
        pre = record.get("pre_score")
        post = record.get("post_score")
        if pre is None or post is None:
            continue
        pre_score = float(pre)
        post_score = float(post)
        drift = post_score - pre_score
        benchmark_score = (
            float(benchmark_scores[model_id]) if model_id in benchmark_scores.index else None
        )
        benchmark_drift_gap = None
        if benchmark_score is not None:
            benchmark_drift_gap = benchmark_score - post_score
        per_model[model_id] = {
            "pre_score": pre_score,
            "post_score": post_score,
            "score_drift": drift,
            "benchmark_score": benchmark_score,
            "benchmark_drift_gap": benchmark_drift_gap,
            "intervention": record.get("intervention"),
        }
        drifts.append(drift)
        if drift > 0.05 and benchmark_score is not None and benchmark_score > post_score + 0.1:
            gaming_signals.append(model_id)

    warnings = []
    if len(drifts) < 2:
        warnings.append("Fewer than two intervention records; drift estimates are unstable.")
    if not drifts:
        return (
            {"status": "no_overlap", "matched_model_count": 0},
            per_model,
            ["No intervention records matched available models."],
        )

    mean_drift = float(np.mean(drifts))
    return (
        {
            "status": "measured",
            "matched_model_count": len(drifts),
            "mean_score_drift": mean_drift,
            "potential_gaming_model_count": len(gaming_signals),
            "potential_gaming_models": gaming_signals,
            "interpretation": _drift_interpretation(mean_drift, len(gaming_signals)),
        },
        per_model,
        warnings,
    )


def _drift_interpretation(mean_drift: float, gaming_count: int) -> str:
    if gaming_count > 0:
        return (
            "Evidence consistent with potential Goodhart/consequential-validity threats for "
            f"{gaming_count} model(s) under this intervention protocol."
        )
    if mean_drift >= 0.05:
        return (
            "Evidence consistent with post-intervention score improvement; "
            "requires validation against external outcomes."
        )
    if mean_drift <= -0.05:
        return (
            "Evidence consistent with post-intervention score decline; "
            "benchmark optimization may not transfer."
        )
    return "No strong local evidence of intervention drift under this protocol."
