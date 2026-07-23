from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from typing import Any

import numpy as np

from valideval.benchmarks.base import Benchmark
from valideval.diagnostics.base import MatrixInput, matrix_mapping
from valideval.io.cache import load_predictions, prediction_path
from valideval.schemas import DiagnosticResult, ModelPrediction
from valideval.scoring.extraction import (
    alias_aware_match,
    invalid_output_detector,
    lenient_letter,
    normalized_exact_match,
    numeric_tolerance,
    refusal_detector,
    regex_final_answer,
    strict_letter,
)
from valideval.scoring.mcq_utils import accepted_labels


class ExtractionRobustnessDiagnostic:
    name = "extraction_robustness"
    version = "0.1"

    def run(
        self,
        benchmark: Benchmark,
        predictions: MatrixInput,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> DiagnosticResult:
        cfg = dict(config or {})
        matrix_mapping(predictions)
        records = _load_records(benchmark.benchmark_id, cfg)
        items = {item.item_id: item for item in benchmark.load_items()}
        warnings = []
        if not records:
            warnings.append(
                "Cached full-condition predictions were unavailable; extraction robustness could not inspect raw outputs."
            )

        per_model_counts: dict[str, Counter[str]] = {}
        per_item: dict[str, Any] = {}
        strict_scores = []
        lenient_scores = []
        regex_scores = []
        invalid_outputs = 0
        refusals = 0
        disagreements = 0

        for record in records:
            item = items[record.item_id]
            accepted = set(accepted_labels(item))
            strict = strict_letter(record.raw_output or record.prediction)
            lenient = lenient_letter(record.raw_output or record.prediction)
            regex = regex_final_answer(record.raw_output or record.prediction)
            invalid = invalid_output_detector(record.raw_output or record.prediction)
            refusal = refusal_detector(record.raw_output or record.prediction)
            normalized_exact_match(record.prediction, aliases=accepted_labels(item))
            alias_aware_match(record.prediction, aliases=accepted_labels(item))
            numeric_tolerance(record.prediction)

            strict_score = 1.0 if strict.value in accepted else 0.0
            lenient_score = 1.0 if lenient.value in accepted else 0.0
            regex_score = 1.0 if regex.value in accepted else 0.0
            strict_scores.append(strict_score)
            lenient_scores.append(lenient_score)
            regex_scores.append(regex_score)
            invalid_outputs += int(invalid.invalid)
            refusals += int(refusal.refusal)
            disagreements += int(len({strict.value, lenient.value, regex.value} - {None}) > 1)
            per_model_counts.setdefault(record.model_id, Counter()).update(
                {
                    "n": 1,
                    "strict_score": strict_score,
                    "lenient_score": lenient_score,
                    "regex_score": regex_score,
                    "invalid": int(invalid.invalid),
                    "refusal": int(refusal.refusal),
                }
            )
            per_item.setdefault(
                record.item_id, {"n": 0, "invalid_outputs": 0, "extractor_disagreements": 0}
            )
            per_item[record.item_id]["n"] += 1
            per_item[record.item_id]["invalid_outputs"] += int(invalid.invalid)
            per_item[record.item_id]["extractor_disagreements"] += int(
                len({strict.value, lenient.value, regex.value} - {None}) > 1
            )

        ambiguous_items = [
            item.item_id
            for item in benchmark.load_items()
            if len(accepted_labels(item)) > 1 or "ambiguous_scoring_risk" in item.construct_tags
        ]
        for item_id, metrics in per_item.items():
            n = metrics["n"] or 1
            metrics["invalid_output_rate"] = metrics["invalid_outputs"] / n
            metrics["extractor_disagreement_rate"] = metrics["extractor_disagreements"] / n
            metrics["scoring_ambiguity_flag"] = item_id in ambiguous_items

        per_model = {
            model_id: {
                "strict_score": counts["strict_score"] / counts["n"],
                "lenient_score": counts["lenient_score"] / counts["n"],
                "regex_final_answer_score": counts["regex_score"] / counts["n"],
                "invalid_output_rate": counts["invalid"] / counts["n"],
                "refusal_rate": counts["refusal"] / counts["n"],
            }
            for model_id, counts in per_model_counts.items()
            if counts["n"]
        }

        n_records = len(records) or 1
        strict_mean = float(np.mean(strict_scores)) if strict_scores else float("nan")
        lenient_mean = float(np.mean(lenient_scores)) if lenient_scores else float("nan")
        regex_mean = float(np.mean(regex_scores)) if regex_scores else float("nan")
        if lenient_scores and lenient_mean - strict_mean > float(cfg.get("shift_warn", 0.05)):
            warnings.append(
                "Lenient extraction changes scores relative to strict extraction; inspect scoring-rule robustness."
            )

        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics={
                "strict_letter_score": strict_mean,
                "lenient_letter_score": lenient_mean,
                "regex_final_answer_score": regex_mean,
                "strict_vs_lenient_score_shift": lenient_mean - strict_mean
                if strict_scores
                else float("nan"),
                "extraction_disagreement_rate": disagreements / n_records,
                "invalid_output_rate": invalid_outputs / n_records,
                "refusal_rate": refusals / n_records,
                "ambiguous_item_count": len(ambiguous_items),
                "ambiguous_items": ambiguous_items,
            },
            per_model_metrics=per_model,
            per_item_metrics=per_item,
            warnings=warnings,
            limitations=[
                "Extraction robustness is based on cached raw outputs and implemented extractors; it does not replace human scoring-rule validation."
            ],
        )


def _load_records(benchmark_id: str, cfg: dict[str, Any]) -> list[ModelPrediction]:
    cache_root = cfg.get("cache_root")
    panel_id = cfg.get("panel_id")
    variant = cfg.get("variant", "full")
    if not cache_root or not panel_id:
        return []
    path = prediction_path(cache_root, benchmark_id, panel_id, variant)
    if not path.exists():
        return []
    return load_predictions(cache_root, benchmark_id, panel_id, variant)
