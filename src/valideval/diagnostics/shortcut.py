from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from valideval.benchmarks.base import Benchmark
from valideval.diagnostics.base import MatrixInput, matrix_mapping
from valideval.psychometrics.bootstrap import bootstrap_ci
from valideval.schemas import DiagnosticResult


class ShortcutDiagnostic:
    name = "shortcut"
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
            raise ValueError("Shortcut diagnostic requires a 'full' response matrix.")

        full = matrices["full"].to_dataframe().astype(float)
        requested_variants = cfg.get(
            "variants",
            [
                "question_only",
                "choices_only",
                "context_removed",
                "context_shuffled",
                "label_prior_only",
                "metadata_only",
                "answer_length_only",
                "format_only",
                "irrelevant_context",
                "retrieval_only",
            ],
        )
        available_variants = [variant for variant in requested_variants if variant in matrices]
        warnings: list[str] = []
        missing = sorted(set(requested_variants) - set(available_variants))
        if missing:
            warnings.append(f"Missing ablation matrices: {', '.join(missing)}.")

        if not benchmark.construct_spec.construct_critical_fields:
            warnings.append(
                "Benchmark does not define construct-critical fields; ablation variants are conservative."
            )

        full_score = float(np.nanmean(full.values))
        if full_score < float(cfg.get("low_full_score_warn", 0.20)):
            warnings.append(
                "Full-condition performance is low; shortcut retention estimates are unstable."
            )

        per_model: dict[str, Any] = {}
        for model_id in full.index:
            full_model_score = float(full.loc[model_id].mean())
            per_model[model_id] = {"full_score": full_model_score, "variants": {}}
            for variant in available_variants:
                ablated = matrices[variant].to_dataframe().astype(float).reindex_like(full)
                ablated_score = float(ablated.loc[model_id].mean())
                retention = ablated_score / full_model_score if full_model_score > 0 else None
                per_model[model_id]["variants"][variant] = {
                    "ablated_score": ablated_score,
                    "absolute_drop": full_model_score - ablated_score,
                    "relative_drop": (full_model_score - ablated_score) / full_model_score
                    if full_model_score > 0
                    else None,
                    "shortcut_retention": retention,
                }

        per_item: dict[str, Any] = {}
        for item_id in full.columns:
            full_item_score = float(full[item_id].mean())
            variant_scores: dict[str, float] = {}
            for variant in available_variants:
                ablated = matrices[variant].to_dataframe().astype(float).reindex_like(full)
                variant_scores[variant] = float(ablated[item_id].mean())
            max_ablated = max(variant_scores.values()) if variant_scores else float("nan")
            retention = max_ablated / full_item_score if full_item_score > 0 else None
            per_item[item_id] = {
                "full_score": full_item_score,
                "variant_scores": variant_scores,
                "max_ablated_score": max_ablated,
                "max_shortcut_retention": retention,
                "suspiciousness": float(max(0.0, max_ablated - full_item_score))
                if variant_scores
                else 0.0,
            }

        variant_metrics: dict[str, Any] = {}
        for variant in available_variants:
            ablated = matrices[variant].to_dataframe().astype(float).reindex_like(full)
            ablated_score = float(np.nanmean(ablated.values))
            retention = ablated_score / full_score if full_score > 0 else None
            variant_metrics[variant] = {
                "full_score": full_score,
                "ablated_score": ablated_score,
                "absolute_drop": full_score - ablated_score,
                "relative_drop": (full_score - ablated_score) / full_score
                if full_score > 0
                else None,
                "shortcut_retention": retention,
                "full_score_ci": bootstrap_ci(
                    full.values.ravel(),
                    n_boot=int(cfg.get("bootstrap_samples", 500)),
                    seed=int(cfg.get("seed", 0)),
                ),
                "ablated_score_ci": bootstrap_ci(
                    ablated.values.ravel(),
                    n_boot=int(cfg.get("bootstrap_samples", 500)),
                    seed=int(cfg.get("seed", 0)) + 1,
                ),
            }

        high_retention_variants = [
            variant
            for variant, metrics in variant_metrics.items()
            if metrics["shortcut_retention"] is not None
            and metrics["shortcut_retention"] >= float(cfg.get("high_retention_threshold", 0.70))
        ]
        if high_retention_variants:
            warnings.append(
                "High retained performance under ablation suggests possible shortcut availability "
                f"for: {', '.join(high_retention_variants)}."
            )

        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics={
                "full_score": full_score,
                "variants": variant_metrics,
                "high_retention_variants": high_retention_variants,
            },
            per_model_metrics=per_model,
            per_item_metrics=per_item,
            warnings=warnings,
        )
