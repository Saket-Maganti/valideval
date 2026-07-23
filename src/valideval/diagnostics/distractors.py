from __future__ import annotations

import csv
import json
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

from valideval.benchmarks.base import Benchmark
from valideval.diagnostics.base import MatrixInput, matrix_mapping
from valideval.forensics.provenance import stable_hash
from valideval.io.cache import load_predictions, prediction_path
from valideval.schemas import DiagnosticResult, ModelPrediction
from valideval.scoring.exact_match import normalize_text
from valideval.scoring.mcq import normalize_mcq_label
from valideval.scoring.mcq_utils import (
    accepted_labels,
    correct_choice_text,
    incorrect_choice_map,
    item_choice_map,
    jaccard_similarity,
    tokenize,
)


class DistractorQualityDiagnostic:
    name = "distractor_quality"
    version = "0.1"

    def run(
        self,
        benchmark: Benchmark,
        predictions: MatrixInput,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> DiagnosticResult:
        cfg = dict(config or {})
        sanitized = bool(cfg.get("sanitized"))
        matrices = matrix_mapping(predictions)
        full = matrices.get("full")
        strong_models: set[str] = set()
        if full is not None:
            frame = full.to_dataframe().astype(float)
            model_scores = frame.mean(axis=1)
            cutoff = float(np.nanquantile(model_scores.values, 0.75))
            strong_models = {
                model_id for model_id, score in model_scores.items() if float(score) >= cutoff
            }

        prediction_records = _load_full_predictions(benchmark.benchmark_id, cfg)
        selected_by_item = _selection_counts(prediction_records)
        strong_selected_by_item = _selection_counts(
            [record for record in prediction_records if record.model_id in strong_models]
        )

        rows = []
        sanitized_rows = []
        per_item: dict[str, Any] = {}
        dead_distractors = 0
        total_distractors = 0
        similarity_values = []
        confusing_distractors = 0
        implausible_distractors = 0
        discrimination_scores = []

        for item in benchmark.load_items():
            accepted = set(accepted_labels(item))
            correct_text = correct_choice_text(item)
            choices = item_choice_map(item)
            normalized_choice_counts = Counter(normalize_text(text) for text in choices.values())
            item_selection_total = sum(selected_by_item.get(item.item_id, Counter()).values())
            item_rows = []
            if sanitized:
                for label, text in choices.items():
                    selection_count = selected_by_item.get(item.item_id, Counter()).get(label, 0)
                    role = "correct" if label in accepted else "distractor"
                    similarity = (
                        1.0 if role == "correct" else jaccard_similarity(correct_text, text)
                    )
                    duplicate_choice = normalized_choice_counts.get(normalize_text(text), 0) > 1
                    sanitized_rows.append(
                        {
                            "item_id": item.item_id,
                            "choice_label": label,
                            "role": role,
                            "length_tokens": len(tokenize(text)),
                            "length_chars": len(text),
                            "lexical_overlap_bucket": _overlap_bucket(similarity, role=role),
                            "lexical_overlap_hash": stable_hash(
                                {
                                    "item_id": item.item_id,
                                    "choice_label": label,
                                    "role": role,
                                    "overlap_bucket": _overlap_bucket(similarity, role=role),
                                    "overlap_rounded": round(similarity, 2),
                                }
                            ),
                            "duplicate_choice": duplicate_choice,
                            "dead_distractor": role == "distractor" and selection_count == 0,
                            "selection_rate": selection_count / item_selection_total
                            if item_selection_total
                            else 0.0,
                        }
                    )
            for label, text in incorrect_choice_map(item).items():
                total_distractors += 1
                selection_count = selected_by_item.get(item.item_id, Counter()).get(label, 0)
                strong_selection_count = strong_selected_by_item.get(item.item_id, Counter()).get(
                    label, 0
                )
                similarity = jaccard_similarity(correct_text, text)
                similarity_values.append(similarity)
                if selection_count == 0:
                    dead_distractors += 1
                    implausible_distractors += 1
                if strong_selection_count > 0:
                    confusing_distractors += 1
                discrimination = strong_selection_count - selection_count
                discrimination_scores.append(discrimination)
                row = {
                    "item_id": item.item_id,
                    "distractor_label": label,
                    "distractor_text": text,
                    "accepted_labels": "|".join(sorted(accepted)),
                    "selection_count": selection_count,
                    "strong_model_selection_count": strong_selection_count,
                    "lexical_similarity_to_correct": similarity,
                    "dead_distractor": selection_count == 0,
                    "confusing_for_strong_models": strong_selection_count > 0,
                    "distractor_discrimination_score": discrimination,
                }
                rows.append(row)
                item_rows.append(row)
            per_item[item.item_id] = {
                "dead_distractor_fraction": (
                    sum(1 for row in item_rows if row["dead_distractor"]) / len(item_rows)
                    if item_rows
                    else 0.0
                ),
                "max_similarity_to_correct": max(
                    [row["lexical_similarity_to_correct"] for row in item_rows] or [0.0]
                ),
                "confusing_distractors": [
                    row["distractor_label"]
                    for row in item_rows
                    if row["confusing_for_strong_models"]
                ],
            }

        csv_path = None if sanitized else _write_csv(rows, cfg)
        sanitized_artifacts = _write_sanitized_artifacts(sanitized_rows, cfg) if sanitized else {}
        warnings = []
        if prediction_records == []:
            warnings.append(
                "Cached full-condition predictions were unavailable; selection-frequency metrics use zeros."
            )
        if total_distractors and dead_distractors / total_distractors > 0.5:
            warnings.append(
                "Many distractors were never selected under this panel; evidence is consistent with possible implausible distractors."
            )

        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics={
                "total_distractors": total_distractors,
                "dead_distractor_fraction": dead_distractors / total_distractors
                if total_distractors
                else 0.0,
                "confusing_distractor_count": confusing_distractors,
                "implausible_distractor_count": implausible_distractors,
                "mean_lexical_similarity_to_correct": float(np.mean(similarity_values))
                if similarity_values
                else 0.0,
                "mean_distractor_discrimination_score": float(np.mean(discrimination_scores))
                if discrimination_scores
                else 0.0,
                "strong_models": sorted(strong_models),
                "sanitized": sanitized,
                "raw_choice_text_included": not sanitized,
            },
            per_item_metrics=per_item,
            warnings=warnings,
            artifacts={
                "distractor_quality_csv": str(csv_path) if csv_path else None,
                **sanitized_artifacts,
            },
            limitations=[
                "Distractor selection frequencies are conditional on the available model panel and prompt variant.",
                "Sanitized mode omits raw question text and full choice text.",
            ],
        )


def _load_full_predictions(benchmark_id: str, cfg: dict[str, Any]) -> list[ModelPrediction]:
    cache_root = cfg.get("cache_root")
    panel_id = cfg.get("panel_id")
    if not cache_root or not panel_id:
        return []
    variant = str(cfg.get("selection_variant") or cfg.get("primary_full_variant") or "full")
    path = prediction_path(cache_root, benchmark_id, panel_id, variant)
    if not path.exists():
        return []
    return load_predictions(cache_root, benchmark_id, panel_id, variant)


def _selection_counts(records: list[ModelPrediction]) -> dict[str, Counter[str]]:
    counts: dict[str, Counter[str]] = {}
    for record in records:
        label = normalize_mcq_label(record.prediction)
        if label:
            counts.setdefault(record.item_id, Counter()).update([label])
    return counts


def _write_csv(rows: list[dict[str, object]], cfg: dict[str, Any]) -> Path | None:
    output_dir = cfg.get("output_dir")
    if not output_dir:
        return None
    path = Path(output_dir) / "distractor_quality.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return path
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def _write_sanitized_artifacts(
    rows: list[dict[str, object]], cfg: dict[str, Any]
) -> dict[str, str | None]:
    output_dir = cfg.get("output_dir")
    if not output_dir:
        return {
            "distractor_quality_sanitized_csv": None,
            "distractor_quality_sanitized_json": None,
            "distractor_quality_sanitized_md": None,
        }
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    csv_path = output / "distractor_quality_sanitized.csv"
    json_path = output / "distractor_quality_sanitized.json"
    md_path = output / "distractor_quality_sanitized.md"
    if rows:
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    else:
        csv_path.write_text("", encoding="utf-8")
    payload = {
        "schema_version": "0.1",
        "artifact_class": "sanitized_distractor_quality",
        "raw_question_text_included": False,
        "raw_choice_text_included": False,
        "rows": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_sanitized_markdown(rows), encoding="utf-8")
    return {
        "distractor_quality_sanitized_csv": str(csv_path),
        "distractor_quality_sanitized_json": str(json_path),
        "distractor_quality_sanitized_md": str(md_path),
    }


def _sanitized_markdown(rows: list[dict[str, object]]) -> str:
    total = len(rows)
    distractors = [row for row in rows if row.get("role") == "distractor"]
    dead = sum(1 for row in distractors if row.get("dead_distractor") is True)
    duplicate = sum(1 for row in rows if row.get("duplicate_choice") is True)
    buckets = Counter(str(row.get("lexical_overlap_bucket")) for row in rows)
    lines = [
        "# Sanitized Distractor Quality",
        "",
        "This artifact intentionally omits raw GPQA question text and full answer-choice text.",
        "",
        "## Summary",
        "",
        f"- Choice rows: {total}",
        f"- Distractor rows: {len(distractors)}",
        f"- Dead distractors: {dead}",
        f"- Duplicate-choice flags: {duplicate}",
        "",
        "## Lexical Overlap Buckets",
        "",
    ]
    lines.extend(f"- {bucket}: {count}" for bucket, count in sorted(buckets.items()))
    lines.extend(
        [
            "",
            "Rows contain item IDs, choice labels, role, length metrics, overlap buckets/hashes, duplicate flags, dead-distractor flags, and selection rates only.",
            "",
        ]
    )
    return "\n".join(lines)


def _overlap_bucket(similarity: float, *, role: str) -> str:
    if role == "correct":
        return "correct"
    if similarity == 0:
        return "none"
    if similarity < 0.20:
        return "low"
    if similarity < 0.50:
        return "medium"
    return "high"
