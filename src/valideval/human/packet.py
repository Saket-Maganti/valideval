from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from valideval.benchmarks.base import Benchmark
from valideval.human.common import read_json, stable_json_hash, write_json
from valideval.io.cache import load_predictions
from valideval.io.jsonl import write_jsonl
from valideval.schemas import AnnotationPacket, AnnotationTask, BenchmarkItem, ModelPrediction

DEFAULT_GUIDELINES = """# Annotation Guidelines

Review each packet item independently. Judge whether the model output satisfies the rubric for the item under review. Human labels are evidence under this protocol; they are not assumed to be perfect.

Use anonymized annotator IDs. Mark ambiguity when the rubric, context, gold answer, or model output leaves more than one reasonable interpretation. Mark invalid item when the item should not be scored without author review.
"""

DEFAULT_RUBRIC = """# Rubric

For multiple-choice items, label the model output as `correct` when it clearly selects an accepted gold answer, `incorrect` when it clearly selects a non-accepted answer, and `unscorable` when the output cannot be mapped to the rubric. For open-ended items, use the benchmark-provided gold answer and aliases if available. Record uncertainty and rationale instead of forcing certainty.
"""

STRATEGIES = {
    "random",
    "high-disagreement",
    "low-discrimination",
    "shortcut-suspicious",
    "scorer-sensitive",
    "coverage-balanced",
    "ranking-critical",
}


def generate_annotation_packet(
    benchmark: Benchmark,
    panel_id: str,
    *,
    cache_root: str | Path = "cache",
    output_dir: str | Path,
    sample_size: int = 100,
    strategy: str = "random",
    seed: int = 0,
    rubric: str | None = None,
    guidelines: str | None = None,
) -> dict[str, Any]:
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown annotation sampling strategy: {strategy}")
    if sample_size <= 0:
        raise ValueError("sample_size must be positive.")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    items = benchmark.load_items()
    predictions, warnings = _load_full_predictions(
        cache_root,
        benchmark.benchmark_id,
        panel_id,
    )
    diagnostics = _load_sampling_diagnostics(output.parent)
    candidates = _candidate_tasks(
        benchmark,
        items,
        predictions,
        strategy=strategy,
        rubric=rubric or DEFAULT_RUBRIC,
    )
    selected = _select_candidates(
        candidates,
        sample_size=sample_size,
        strategy=strategy,
        seed=seed,
        diagnostics=diagnostics,
        predictions=predictions,
    )
    tasks = [_to_task(candidate, rubric or DEFAULT_RUBRIC) for candidate in selected]
    version_hash = stable_json_hash(
        {
            "benchmark_id": benchmark.benchmark_id,
            "panel_id": panel_id,
            "strategy": strategy,
            "sample_size": sample_size,
            "task_hashes": [task.task_hash for task in tasks],
        }
    )
    packet = AnnotationPacket(
        packet_id=f"packet_{version_hash[:12]}",
        benchmark_id=benchmark.benchmark_id,
        panel_id=panel_id,
        sampling_strategy=strategy,
        sample_size=len(tasks),
        tasks=tasks,
        guidelines=guidelines or DEFAULT_GUIDELINES,
        rubric=rubric or DEFAULT_RUBRIC,
        version_hash=version_hash,
        manifest={
            "requested_sample_size": sample_size,
            "available_candidate_count": len(candidates),
            "prediction_source": "cache/predictions_full.jsonl" if predictions else "items_only",
            "sampling_strategy": strategy,
            "seed": seed,
            "warnings": warnings,
            "limitations": [
                "Annotation packets are sampling aids and do not constitute human validation until judgments are imported.",
                "High-disagreement and ranking-critical sampling depend on cached toy/model-panel artifacts when available.",
            ],
        },
    )

    items_path = output / "items.jsonl"
    write_jsonl(items_path, tasks)
    guidelines_path = output / "guidelines.md"
    rubric_path = output / "rubric.md"
    packet_path = output / "packet.json"
    manifest_path = output / "manifest.json"
    guidelines_path.write_text(packet.guidelines, encoding="utf-8")
    rubric_path.write_text(packet.rubric, encoding="utf-8")
    write_json(packet_path, packet.model_dump(mode="json"))
    write_json(
        manifest_path,
        {
            "schema_version": "0.1",
            "packet_id": packet.packet_id,
            "benchmark_id": packet.benchmark_id,
            "panel_id": packet.panel_id,
            "sampling_strategy": packet.sampling_strategy,
            "sample_size": packet.sample_size,
            "version_hash": packet.version_hash,
            **packet.manifest,
            "artifacts": {
                "items_jsonl": str(items_path),
                "guidelines_md": str(guidelines_path),
                "rubric_md": str(rubric_path),
                "packet_json": str(packet_path),
            },
        },
    )
    return {
        "items_jsonl": str(items_path),
        "guidelines_md": str(guidelines_path),
        "rubric_md": str(rubric_path),
        "packet_json": str(packet_path),
        "manifest_json": str(manifest_path),
        "packet_id": packet.packet_id,
        "n_tasks": len(tasks),
        "warnings": warnings,
    }


def _load_full_predictions(
    cache_root: str | Path,
    benchmark_id: str,
    panel_id: str,
) -> tuple[list[ModelPrediction], list[str]]:
    try:
        return load_predictions(cache_root, benchmark_id, panel_id, "full"), []
    except FileNotFoundError:
        return [], [
            "Cached full-prompt predictions were unavailable; packet contains item-only tasks."
        ]


def _candidate_tasks(
    benchmark: Benchmark,
    items: list[BenchmarkItem],
    predictions: list[ModelPrediction],
    *,
    strategy: str,
    rubric: str,
) -> list[dict[str, Any]]:
    items_by_id = {item.item_id: item for item in items}
    candidates: list[dict[str, Any]] = []
    if predictions:
        for prediction in predictions:
            item = items_by_id[prediction.item_id]
            candidates.append(
                {
                    "task_id": f"{item.item_id}::{prediction.model_id}",
                    "item": item,
                    "model_id": prediction.model_id,
                    "model_output": prediction.raw_output or prediction.prediction,
                    "prediction": prediction,
                    "prompt": benchmark.render_prompt(item, variant="full"),
                    "rubric": rubric,
                    "sampling_strategy": strategy,
                }
            )
        return sorted(candidates, key=lambda row: row["task_id"])

    for item in items:
        candidates.append(
            {
                "task_id": f"{item.item_id}::item",
                "item": item,
                "model_id": None,
                "model_output": "",
                "prediction": None,
                "prompt": benchmark.render_prompt(item, variant="full"),
                "rubric": rubric,
                "sampling_strategy": strategy,
            }
        )
    return sorted(candidates, key=lambda row: row["task_id"])


def _select_candidates(
    candidates: list[dict[str, Any]],
    *,
    sample_size: int,
    strategy: str,
    seed: int,
    diagnostics: dict[str, Any],
    predictions: list[ModelPrediction],
) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    limit = min(sample_size, len(candidates))
    if strategy == "coverage-balanced":
        return _coverage_balanced(candidates, limit=limit, rng=rng)
    if strategy == "random":
        shuffled = list(candidates)
        rng.shuffle(shuffled)
        return sorted(shuffled[:limit], key=lambda row: row["task_id"])

    scores = {
        row["task_id"]: _strategy_score(
            row,
            strategy=strategy,
            diagnostics=diagnostics,
            predictions=predictions,
        )
        for row in candidates
    }
    jitter = {row["task_id"]: rng.random() * 1e-9 for row in candidates}
    return sorted(
        candidates,
        key=lambda row: (scores[row["task_id"]] + jitter[row["task_id"]], row["task_id"]),
        reverse=True,
    )[:limit]


def _coverage_balanced(
    candidates: list[dict[str, Any]],
    *,
    limit: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in candidates:
        tags = row["item"].construct_tags or ["untagged"]
        grouped.setdefault(tags[0], []).append(row)
    for rows in grouped.values():
        rng.shuffle(rows)
    selected: list[dict[str, Any]] = []
    tag_order = sorted(grouped)
    while len(selected) < limit and any(grouped.values()):
        for tag in tag_order:
            if grouped[tag]:
                selected.append(grouped[tag].pop())
                if len(selected) >= limit:
                    break
    return sorted(selected, key=lambda row: row["task_id"])


def _strategy_score(
    row: dict[str, Any],
    *,
    strategy: str,
    diagnostics: dict[str, Any],
    predictions: list[ModelPrediction],
) -> float:
    item_id = row["item"].item_id
    if strategy == "high-disagreement":
        labels = {
            prediction.prediction
            for prediction in predictions
            if prediction.item_id == item_id and prediction.prompt_variant == "full"
        }
        return float(max(0, len(labels) - 1))
    if strategy == "low-discrimination":
        irt = diagnostics.get("irt", {}).get("per_item_metrics", {}).get(item_id, {})
        discrimination = irt.get("discrimination")
        if discrimination is None:
            return 0.0
        return 1.0 / (1.0 + abs(float(discrimination)))
    if strategy == "shortcut-suspicious":
        shortcut = diagnostics.get("shortcut", {}).get("per_item_metrics", {}).get(item_id, {})
        return float(shortcut.get("suspiciousness") or 0.0)
    if strategy == "scorer-sensitive":
        extraction = diagnostics.get("extraction_robustness", {}).get("per_item_metrics", {})
        item_metrics = extraction.get(item_id, {})
        return float(item_metrics.get("extractor_disagreement_rate") or 0.0)
    if strategy == "ranking-critical":
        irt = diagnostics.get("irt", {}).get("per_item_metrics", {}).get(item_id, {})
        discrimination = abs(float(irt.get("discrimination") or 0.0))
        difficulty = abs(float(irt.get("difficulty") or 0.0))
        return discrimination + max(0.0, 1.0 - difficulty)
    return 0.0


def _to_task(candidate: dict[str, Any], rubric: str) -> AnnotationTask:
    item: BenchmarkItem = candidate["item"]
    prediction: ModelPrediction | None = candidate["prediction"]
    payload = {
        "task_id": candidate["task_id"],
        "item_id": item.item_id,
        "prompt": candidate["prompt"],
        "model_output": candidate["model_output"],
        "gold_answer": item.answer,
        "model_id": candidate["model_id"],
        "rubric": rubric,
        "tags": item.construct_tags,
        "metadata": {
            "context": item.context,
            "choices": item.choices,
            "prompt_variant": prediction.prompt_variant if prediction else "full",
            "prediction_score": prediction.score if prediction else None,
            "prediction_is_correct": prediction.is_correct if prediction else None,
            "item_metadata": item.metadata,
            "sampling_strategy": candidate["sampling_strategy"],
        },
    }
    return AnnotationTask(
        **payload,
        sampling_strategy=candidate["sampling_strategy"],
        task_hash=stable_json_hash(payload),
    )


def _load_sampling_diagnostics(audit_dir: Path) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {}
    for name in ["irt", "shortcut", "extraction_robustness", "ranking_significance"]:
        diagnostics[name] = read_json(audit_dir / f"{name}.json")
    return diagnostics
