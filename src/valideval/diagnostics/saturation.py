from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

from valideval.benchmarks.base import Benchmark
from valideval.diagnostics.base import MatrixInput, matrix_mapping
from valideval.schemas import DiagnosticResult


class SaturationDiagnostic:
    name = "saturation"
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
            raise ValueError("Saturation diagnostic requires a 'full' matrix.")
        frame = matrices["full"].to_dataframe().astype(float)
        model_scores = frame.mean(axis=1).sort_values(ascending=False)
        top_n = min(int(cfg.get("top_n", 3)), len(model_scores))
        top_models = list(model_scores.index[:top_n])
        top_frame = frame.loc[top_models]
        item_means = frame.mean(axis=0)
        top_item_means = top_frame.mean(axis=0)
        solved_by_all_top = float(np.mean(top_item_means >= 0.999)) if top_n else float("nan")
        failed_by_all = float(np.mean(item_means <= 0.001)) if frame.shape[1] else float("nan")
        discriminating_items = [
            item_id
            for item_id in frame.columns
            if 0.05 < float(item_means[item_id]) < 0.95 and float(frame[item_id].std()) > 0.05
        ]
        top_score_range = (
            float(model_scores.iloc[0] - model_scores.iloc[top_n - 1]) if top_n else float("nan")
        )
        ceiling_proximity = float(model_scores.iloc[0]) if len(model_scores) else float("nan")
        compression_index = (
            1.0 - (float(model_scores.std()) / max(float(model_scores.mean()), 1e-8))
            if len(model_scores) > 1
            else float("nan")
        )
        saturation_by_tag = _saturation_by_tag(benchmark, frame, top_models)
        category = _category(
            ceiling_proximity, solved_by_all_top, len(discriminating_items), frame.shape[1]
        )
        warnings = []
        if category in {"moderate", "severe"}:
            warnings.append(
                f"Evidence is consistent with {category} benchmark saturation under this model panel."
            )
        if frame.shape[0] < 5:
            warnings.append("Saturation evidence is limited with very few models.")

        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics={
                "top_models": top_models,
                "top_model_score_range": top_score_range,
                "fraction_solved_by_all_top_models": solved_by_all_top,
                "fraction_failed_by_all_models": failed_by_all,
                "effective_discriminating_item_count": len(discriminating_items),
                "ceiling_proximity": ceiling_proximity,
                "benchmark_compression_index": compression_index,
                "saturation_category": category,
                "saturation_by_construct_tag": saturation_by_tag,
                "historical_saturation": _historical_saturation(cfg),
            },
            per_item_metrics={
                item_id: {
                    "mean_score": float(item_means[item_id]),
                    "top_model_mean_score": float(top_item_means[item_id]),
                    "discriminating": item_id in discriminating_items,
                }
                for item_id in frame.columns
            },
            warnings=warnings,
            limitations=[
                "Saturation is conditional on the audited model panel; historical saturation requires comparable audit snapshots."
            ],
        )


def _category(ceiling: float, solved_top: float, discriminating_count: int, n_items: int) -> str:
    if n_items < 10:
        return "insufficient evidence"
    discriminating_fraction = discriminating_count / n_items if n_items else 0.0
    if ceiling >= 0.9 or solved_top >= 0.75 or discriminating_fraction < 0.15:
        return "severe"
    if ceiling >= 0.8 or solved_top >= 0.5 or discriminating_fraction < 0.3:
        return "moderate"
    if ceiling >= 0.7 or solved_top >= 0.25:
        return "mild"
    return "not saturated"


def _saturation_by_tag(
    benchmark: Benchmark,
    frame,
    top_models: list[str],
) -> dict[str, dict[str, float | int]]:
    by_tag: dict[str, list[str]] = defaultdict(list)
    for item in benchmark.load_items():
        if item.item_id not in frame.columns:
            continue
        for tag in item.construct_tags or ["untagged"]:
            by_tag[tag].append(item.item_id)
    output = {}
    for tag, item_ids in sorted(by_tag.items()):
        top_frame = frame.loc[top_models, item_ids] if top_models else frame[item_ids]
        output[tag] = {
            "n_items": len(item_ids),
            "mean_score": float(frame[item_ids].mean().mean()),
            "fraction_solved_by_all_top_models": float(np.mean(top_frame.mean(axis=0) >= 0.999)),
        }
    return output


def _historical_saturation(cfg: dict[str, Any]) -> dict[str, Any]:
    snapshot_dir = cfg.get("snapshot_dir")
    if not snapshot_dir:
        return {"available": False, "reason": "No snapshot_dir configured."}
    paths = sorted(Path(snapshot_dir).glob("*.json"))
    return {"available": bool(paths), "snapshot_count": len(paths)}
