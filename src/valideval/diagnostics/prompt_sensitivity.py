from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

import numpy as np

from valideval.benchmarks.base import Benchmark
from valideval.diagnostics.base import MatrixInput, matrix_mapping
from valideval.io.cache import load_predictions, prediction_path
from valideval.psychometrics.reliability_stats import spearman_correlation
from valideval.schemas import DiagnosticResult
from valideval.scoring.extraction import invalid_output_detector


class PromptSensitivityDiagnostic:
    name = "prompt_sensitivity"
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
            raise ValueError("Prompt-sensitivity diagnostic requires a 'full' matrix.")
        full = matrices["full"].to_dataframe().astype(float)
        requested = cfg.get(
            "variants",
            [
                "zero_shot_direct",
                "few_shot",
                "chain_of_thought_allowed",
                "direct_answer_only",
                "json_only",
                "answer_letter_only",
                "randomized_option_order",
                "alternate_system_prompt",
                "no_system_prompt",
                "terse_instructions",
                "verbose_instructions",
            ],
        )
        variants = [variant for variant in requested if variant in matrices and variant != "full"]
        warnings = []
        missing = sorted(set(requested) - set(variants))
        if missing:
            warnings.append(f"Missing prompt-template matrices: {', '.join(missing)}.")

        full_scores = full.mean(axis=1)
        full_ranks = _ranks(full_scores.to_dict())
        rank_correlations = []
        variant_metrics: dict[str, Any] = {}
        rank_flips: list[dict[str, Any]] = []
        extraction_failure_rates = {}

        for variant in variants:
            frame = matrices[variant].to_dataframe().astype(float).reindex_like(full)
            scores = frame.mean(axis=1)
            rank_corr = spearman_correlation(full_scores.tolist(), scores.tolist())
            if not math.isnan(rank_corr):
                rank_correlations.append(rank_corr)
            ranks = _ranks(scores.to_dict())
            flips = [
                {
                    "model_id": model_id,
                    "full_rank": full_ranks[model_id],
                    "variant_rank": ranks[model_id],
                }
                for model_id in full_ranks
                if abs(full_ranks[model_id] - ranks[model_id])
                >= int(cfg.get("rank_flip_threshold", 2))
            ]
            rank_flips.extend({"variant": variant, **flip} for flip in flips)
            extraction_failure_rates[variant] = _invalid_output_rate(
                benchmark.benchmark_id, variant, cfg
            )
            variant_metrics[variant] = {
                "mean_score": float(np.nanmean(frame.values)),
                "score_delta_from_full": float(np.nanmean(frame.values) - np.nanmean(full.values)),
                "rank_correlation_with_full": rank_corr,
                "rank_flips": flips,
                "extraction_failure_rate": extraction_failure_rates[variant],
            }

        per_model = {}
        for model_id in full.index:
            scores = [float(full.loc[model_id].mean())]
            scores.extend(
                float(
                    matrices[variant]
                    .to_dataframe()
                    .astype(float)
                    .reindex_like(full)
                    .loc[model_id]
                    .mean()
                )
                for variant in variants
            )
            per_model[model_id] = {
                "mean_score_across_prompt_templates": float(np.mean(scores)),
                "score_variance_across_prompt_templates": float(np.var(scores)),
                "min_score": float(np.min(scores)),
                "max_score": float(np.max(scores)),
            }

        robustness = float(np.mean(rank_correlations)) if rank_correlations else float("nan")
        if rank_flips:
            warnings.append(
                "Prompt-specific ranking flips were observed; evidence is consistent with prompt-format sensitivity under this panel."
            )

        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics={
                "prompt_robustness_coefficient": robustness,
                "mean_rank_stability": robustness,
                "n_prompt_templates": len(variants),
                "score_variance_mean": float(
                    np.mean(
                        [
                            metrics["score_variance_across_prompt_templates"]
                            for metrics in per_model.values()
                        ]
                    )
                )
                if per_model
                else 0.0,
                "prompt_specific_ranking_flips": rank_flips,
                "extraction_failure_rates": extraction_failure_rates,
                "variants": variant_metrics,
            },
            per_model_metrics=per_model,
            warnings=warnings,
            limitations=[
                "Prompt-sensitivity estimates are conditional on the prompt templates implemented by the benchmark adapter."
            ],
        )


def _ranks(scores: dict[str, float]) -> dict[str, int]:
    ordered = sorted(scores, key=lambda model_id: (scores[model_id], model_id), reverse=True)
    return {model_id: index + 1 for index, model_id in enumerate(ordered)}


def _invalid_output_rate(benchmark_id: str, variant: str, cfg: dict[str, Any]) -> float:
    cache_root = cfg.get("cache_root")
    panel_id = cfg.get("panel_id")
    if not cache_root or not panel_id:
        return 0.0
    path = prediction_path(cache_root, benchmark_id, panel_id, variant)
    if not path.exists():
        return 0.0
    records = load_predictions(cache_root, benchmark_id, panel_id, variant)
    if not records:
        return 0.0
    invalid = sum(1 for record in records if invalid_output_detector(record.prediction).invalid)
    return invalid / len(records)
