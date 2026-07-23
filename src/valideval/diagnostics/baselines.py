from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from valideval.baselines import evaluate_baselines
from valideval.benchmarks.base import Benchmark
from valideval.diagnostics.base import MatrixInput, matrix_mapping
from valideval.schemas import DiagnosticResult


class BaselineDiagnostic:
    name = "baselines"
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
        baseline_results = evaluate_baselines(
            benchmark,
            baseline_ids=cfg.get("baseline_ids"),
            seed=int(cfg.get("seed", 0)),
        )

        per_model: dict[str, Any] = {}
        best_strong_model_score = None
        if "full" in matrices:
            full = matrices["full"].to_dataframe().astype(float)
            model_scores = full.mean(axis=1)
            per_model = {
                model_id: {"full_score": float(score)} for model_id, score in model_scores.items()
            }
            best_strong_model_score = float(np.nanmax(model_scores.values))

        baseline_scores = {
            result.baseline_id: {
                "score": result.score,
                "n_items": len(result.predictions),
                "warnings": result.warnings,
            }
            for result in baseline_results
        }
        best_baseline = max(baseline_results, key=lambda result: result.score)
        dumb_baseline_gap = (
            best_strong_model_score - best_baseline.score
            if best_strong_model_score is not None
            else None
        )

        warnings = [
            "Baselines are heuristic probes; high baseline performance is a possible validity threat, not proof of invalidity."
        ]
        warnings.extend(
            warning
            for result in baseline_results
            for warning in result.warnings
            if warning not in warnings
        )
        per_item: dict[str, Any] = {}
        for result in baseline_results:
            for prediction in result.predictions:
                per_item.setdefault(prediction.item_id, {})[result.baseline_id] = {
                    "prediction": prediction.prediction,
                    "score": prediction.score,
                }

        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics={
                "baseline_scores": baseline_scores,
                "best_shallow_baseline": {
                    "baseline_id": best_baseline.baseline_id,
                    "score": best_baseline.score,
                },
                "best_strong_model_score": best_strong_model_score,
                "dumb_baseline_gap": dumb_baseline_gap,
            },
            per_model_metrics=per_model,
            per_item_metrics=per_item,
            warnings=warnings,
            limitations=[
                "The baseline zoo is intentionally shallow and deterministic; it is a screen for artifacts, not an empirical model panel."
            ],
        )
