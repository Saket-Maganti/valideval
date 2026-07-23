from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

import numpy as np

from valideval.benchmarks.base import Benchmark
from valideval.diagnostics.base import MatrixInput, matrix_mapping
from valideval.psychometrics.irt_models import (
    bootstrap_irt_uncertainty,
    estimate_2pl_proxy,
    estimate_irt_proxy,
    estimate_rasch_1pl,
    select_high_information_subset,
)
from valideval.psychometrics.multidimensional import tag_skill_profiles
from valideval.psychometrics.reliability_stats import kendall_tau, spearman_correlation
from valideval.psychometrics.subsets import evaluate_subset_modes
from valideval.schemas import DiagnosticResult


class IRTDiagnostic:
    name = "irt"
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
        matrix = matrices.get("full") or next(iter(matrices.values()))
        frame = matrix.to_dataframe().astype(float)
        warnings: list[str] = []
        min_models_warn = int(cfg.get("min_models_warn", 5))
        if frame.shape[0] < min_models_warn:
            warnings.append(
                f"IRT proxy estimates are unstable with fewer than {min_models_warn} models."
            )
        if frame.shape[1] < 5:
            warnings.append("IRT proxy estimates are unstable with very few items.")

        estimates = estimate_irt_proxy(matrix)
        rasch = estimate_rasch_1pl(matrix, max_iter=int(cfg.get("max_iter", 200)))
        two_pl = estimate_2pl_proxy(matrix)
        uncertainty = bootstrap_irt_uncertainty(
            matrix,
            n_boot=int(cfg.get("bootstrap_samples", 100)),
            seed=int(cfg.get("seed", 0)),
        )
        skill_profiles = tag_skill_profiles(
            benchmark,
            matrix,
            min_items_per_tag=int(cfg.get("min_items_per_tag", 3)),
        )
        warnings.extend(rasch.get("warnings", []))
        warnings.extend(two_pl.get("warnings", []))
        warnings.extend(skill_profiles.get("warnings", []))
        item_stats = estimates["item_stats"]
        for item_id, stats in item_stats.items():
            stats["difficulty_ci"] = uncertainty["item_difficulty_ci"].get(item_id, {})
            stats["discrimination_ci"] = uncertainty["item_discrimination_ci"].get(item_id, {})
            stats["rasch_difficulty"] = rasch.get("item_difficulties", {}).get(item_id)
            stats["two_pl_slope_proxy"] = two_pl.get("item_slopes", {}).get(item_id)
        raw_accuracy = estimates["raw_accuracy"]
        model_abilities = estimates["model_abilities"]

        negative_items = [
            item_id
            for item_id, stats in item_stats.items()
            if bool(stats["negative_discrimination"])
        ]
        near_zero_items = [
            item_id
            for item_id, stats in item_stats.items()
            if bool(stats["near_zero_discrimination"])
        ]
        too_easy_items = [
            item_id for item_id, stats in item_stats.items() if bool(stats["too_easy"])
        ]
        too_hard_items = [
            item_id for item_id, stats in item_stats.items() if bool(stats["too_hard"])
        ]

        subset_sizes = [int(size) for size in cfg.get("subset_sizes", [5, 10, 20])]
        subset_sizes = [size for size in subset_sizes if 0 < size <= frame.shape[1]]
        subsets: dict[str, Any] = {}
        full_scores = frame.mean(axis=1)
        rng = np.random.default_rng(int(cfg.get("seed", 0)))
        trials = int(cfg.get("random_subset_trials", 100))
        for size in subset_sizes:
            selected = select_high_information_subset(item_stats, size)
            selected_scores = frame[selected].mean(axis=1)
            selected_spearman = spearman_correlation(full_scores.tolist(), selected_scores.tolist())
            selected_kendall = kendall_tau(full_scores.tolist(), selected_scores.tolist())

            random_spearman_values = []
            all_items = list(frame.columns)
            for _ in range(trials):
                random_subset = rng.choice(all_items, size=size, replace=False).tolist()
                random_scores = frame[random_subset].mean(axis=1)
                corr = spearman_correlation(full_scores.tolist(), random_scores.tolist())
                if not math.isnan(corr):
                    random_spearman_values.append(corr)

            subsets[str(size)] = {
                "selected_items": selected,
                "selected_spearman_with_full": selected_spearman,
                "selected_kendall_with_full": selected_kendall,
                "random_mean_spearman_with_full": float(np.mean(random_spearman_values))
                if random_spearman_values
                else float("nan"),
                "random_trials": trials,
            }
        subset_modes = evaluate_subset_modes(
            benchmark,
            matrix,
            item_stats,
            sizes=subset_sizes,
            random_trials=trials,
            seed=int(cfg.get("seed", 0)),
        )

        if negative_items:
            warnings.append(
                "Negative-discrimination items are evidence consistent with item-quality threats "
                "under this model panel."
            )
        if near_zero_items:
            warnings.append(
                "Near-zero discrimination items may contribute little ranking information under this panel."
            )

        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics={
                "n_models": frame.shape[0],
                "n_items": frame.shape[1],
                "estimation_layers": {
                    "proxy": True,
                    "rasch_1pl": bool(rasch.get("available", False)),
                    "two_pl_proxy": bool(two_pl.get("available", False)),
                    "bootstrap_uncertainty": True,
                },
                "discrimination_estimation": estimates.get("discrimination_estimation", {}),
                "near_zero_discrimination_fraction": len(near_zero_items) / frame.shape[1],
                "negative_discrimination_items": len(negative_items),
                "negative_discrimination_item_ids": negative_items,
                "near_zero_discrimination_item_ids": near_zero_items,
                "too_easy_fraction": len(too_easy_items) / frame.shape[1],
                "too_hard_fraction": len(too_hard_items) / frame.shape[1],
                "ranking_correlation_raw_vs_ability": estimates[
                    "ranking_correlation_raw_vs_ability"
                ],
                "recommended_subsets": subsets,
                "subset_modes": subset_modes,
                "model_skill_profile": skill_profiles["model_skill_profile"],
                "tag_summary": skill_profiles["tag_summary"],
                "rasch_1pl": {
                    key: value
                    for key, value in rasch.items()
                    if key not in {"model_abilities", "item_difficulties"}
                },
                "two_pl": {key: value for key, value in two_pl.items() if key != "item_slopes"},
            },
            per_model_metrics={
                model_id: {
                    "raw_accuracy": float(raw_accuracy[model_id]),
                    "latent_ability_proxy": float(model_abilities[model_id]),
                    "ability_ci": uncertainty["ability_ci"].get(model_id, {}),
                    "rasch_ability": rasch.get("model_abilities", {}).get(model_id),
                }
                for model_id in raw_accuracy
            },
            per_item_metrics=item_stats,
            warnings=warnings,
            limitations=[
                "IRT v2 uses layered estimates with graceful fallback; proxy, Rasch, and 2PL-proxy values should not be treated as ground truth."
            ],
        )
