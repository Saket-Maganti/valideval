from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

import numpy as np

from valideval.benchmarks.base import Benchmark
from valideval.diagnostics.base import MatrixInput, matrix_mapping
from valideval.psychometrics.bootstrap import bootstrap_ci
from valideval.psychometrics.reliability_stats import exact_agreement, spearman_correlation
from valideval.schemas import DiagnosticResult


class ReliabilityDiagnostic:
    name = "reliability"
    version = "0.2"

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
            raise ValueError("Reliability diagnostic requires a 'full' response matrix.")

        full = matrices["full"].to_dataframe().astype(float)
        requested_variants = cfg.get(
            "variants", [variant for variant in matrices if variant != "full"]
        )
        variants = [
            variant for variant in requested_variants if variant in matrices and variant != "full"
        ]
        warnings: list[str] = []
        if not variants:
            warnings.append(
                "Only the full matrix was available; reliability across variants cannot be estimated."
            )

        variant_metrics: dict[str, Any] = {}
        rank_correlations = []
        sensitivities = []
        item_stabilities = []
        per_item: dict[str, Any] = {item_id: {"variant_agreements": {}} for item_id in full.columns}

        for variant in variants:
            variant_frame = matrices[variant].to_dataframe().astype(float).reindex_like(full)
            full_model_scores = full.mean(axis=1)
            variant_model_scores = variant_frame.mean(axis=1)
            rank_corr = spearman_correlation(
                full_model_scores.tolist(), variant_model_scores.tolist()
            )
            if not math.isnan(rank_corr):
                rank_correlations.append(rank_corr)
            delta = (full - variant_frame).abs()
            sensitivity = float(np.nanmean(delta.values))
            sensitivities.append(sensitivity)
            agreement = exact_agreement(
                [bool(value >= 0.5) for value in full.values.ravel()],
                [bool(value >= 0.5) for value in variant_frame.values.ravel()],
            )
            item_stabilities.append(agreement)
            for item_id in full.columns:
                item_agreement = exact_agreement(
                    [bool(value >= 0.5) for value in full[item_id].tolist()],
                    [bool(value >= 0.5) for value in variant_frame[item_id].tolist()],
                )
                per_item[item_id]["variant_agreements"][variant] = item_agreement
            variant_metrics[variant] = {
                "rank_correlation_with_full": rank_corr,
                "mean_absolute_score_delta": sensitivity,
                "binary_agreement_with_full": agreement,
                "score_delta_ci": bootstrap_ci(delta.values.ravel(), n_boot=500, seed=0),
            }

        model_scores_by_variant: dict[str, list[float]] = {model_id: [] for model_id in full.index}
        for model_id in full.index:
            model_scores_by_variant[model_id].append(float(full.loc[model_id].mean()))
            for variant in variants:
                variant_frame = matrices[variant].to_dataframe().astype(float).reindex_like(full)
                model_scores_by_variant[model_id].append(float(variant_frame.loc[model_id].mean()))

        per_model = {
            model_id: {
                "mean_score_across_variants": float(np.mean(scores)),
                "score_variance_across_variants": float(np.var(scores)),
                "scores_by_condition": {
                    condition: float(score)
                    for condition, score in zip(["full", *variants], scores, strict=True)
                },
            }
            for model_id, scores in model_scores_by_variant.items()
        }

        reliability_estimate = (
            float(np.mean(rank_correlations)) if rank_correlations else float("nan")
        )
        seed_retest_available = any(variant.startswith("full_seed_") for variant in matrices)
        if sensitivities and float(np.mean(sensitivities)) > float(
            cfg.get("sensitivity_warn", 0.25)
        ):
            warnings.append(
                "Scores change substantially across prompt variants; evidence is consistent with "
                "low perturbation stability."
            )
        if not seed_retest_available:
            warnings.append(
                "Seed/test-retest reliability was not estimated because no full_seed_* matrices were available."
            )

        for metrics in per_item.values():
            agreements = list(metrics["variant_agreements"].values())
            metrics["mean_item_stability"] = (
                float(np.mean(agreements)) if agreements else float("nan")
            )

        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics={
                "benchmark_level_reliability_estimate": reliability_estimate,
                "mean_rank_correlation_across_variants": reliability_estimate,
                "rank_stability": reliability_estimate,
                "prompt_format_reliability": reliability_estimate,
                "seed_test_retest_reliability": None,
                "scorer_reliability": None,
                "mean_perturbation_sensitivity": float(np.mean(sensitivities))
                if sensitivities
                else float("nan"),
                "mean_item_stability_fraction": float(np.mean(item_stabilities))
                if item_stabilities
                else float("nan"),
                "variants": variant_metrics,
            },
            per_model_metrics=per_model,
            per_item_metrics=per_item,
            warnings=warnings,
            limitations=[
                "Reliability v2 metrics are based on available cached variants; seed and scorer reliability require additional matrices or scorer outputs."
            ],
        )
