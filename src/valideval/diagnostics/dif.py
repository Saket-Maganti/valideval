from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from itertools import combinations
from typing import Any

from valideval.benchmarks.base import Benchmark
from valideval.diagnostics.base import MatrixInput, matrix_mapping
from valideval.schemas import DiagnosticResult


class DIFDiagnostic:
    name = "dif"
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
            raise ValueError("DIF diagnostic requires a 'full' matrix.")
        frame = matrices["full"].to_dataframe().astype(float)
        groups = _groups_for_models(list(frame.index), cfg.get("groups"))
        group_to_models: dict[str, list[str]] = defaultdict(list)
        for model_id, group in groups.items():
            if model_id in frame.index:
                group_to_models[group].append(model_id)
        group_to_models = {
            group: models for group, models in group_to_models.items() if len(models) >= 1
        }

        per_item: dict[str, Any] = {}
        suspicious_items = []
        threshold = float(cfg.get("effect_size_threshold", 0.30))
        for item_id in frame.columns:
            item_payload = {}
            item_mean = float(frame[item_id].mean())
            effects = []
            for group, models in group_to_models.items():
                group_mean = float(frame.loc[models, item_id].mean())
                group_overall = float(frame.loc[models].mean(axis=1).mean())
                residual = group_mean - item_mean
                item_payload[group] = {
                    "group_mean": group_mean,
                    "group_overall_mean": group_overall,
                    "residual": residual,
                    "n_models": len(models),
                }
            for left, right in combinations(group_to_models, 2):
                effect = item_payload[left]["residual"] - item_payload[right]["residual"]
                effects.append(abs(effect))
                item_payload[f"{left}__minus__{right}_effect_size"] = effect
            max_effect = max(effects) if effects else 0.0
            item_payload["max_abs_effect_size"] = max_effect
            item_payload["suspicious"] = max_effect >= threshold
            if item_payload["suspicious"]:
                suspicious_items.append(item_id)
            per_item[item_id] = item_payload

        group_scores = {
            group: float(frame.loc[models].mean().mean())
            for group, models in group_to_models.items()
        }
        group_advantages = {
            f"{left}__minus__{right}": group_scores[left] - group_scores[right]
            for left, right in combinations(group_scores, 2)
        }
        warnings = [
            "DIF here means model-family benchmark behavior, not human demographic fairness."
        ]
        if suspicious_items:
            warnings.append(
                "Some items show group-conditioned residual differences; evidence is consistent with possible model-group DIF under this panel."
            )

        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics={
                "groups": group_to_models,
                "benchmark_level_group_scores": group_scores,
                "benchmark_level_group_advantage": group_advantages,
                "suspicious_item_count": len(suspicious_items),
                "suspicious_items": suspicious_items,
            },
            per_item_metrics=per_item,
            warnings=warnings,
            limitations=[
                "DIF-like diagnostics require meaningful model-group metadata and sufficient models per group."
            ],
        )


def _groups_for_models(model_ids: list[str], configured: Any | None) -> dict[str, str]:
    if isinstance(configured, dict):
        return {model_id: str(configured.get(model_id, "ungrouped")) for model_id in model_ids}
    groups = {}
    for model_id in model_ids:
        if model_id in {"always_a", "majority_label", "keyword_matcher", "noisy_weak"}:
            groups[model_id] = "small_or_shallow"
        elif model_id in {"context_aware", "noisy_strong", "format_fragile"}:
            groups[model_id] = "reasoning_or_context"
        else:
            groups[model_id] = "shortcut_or_artifact"
    return groups
