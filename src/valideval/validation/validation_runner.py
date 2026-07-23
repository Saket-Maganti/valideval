from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np

from valideval.audit.runner import DIAGNOSTICS
from valideval.config import load_yaml
from valideval.schemas import DiagnosticResult
from valideval.validation.detector_metrics import (
    calibration_curve,
    metric_bundle,
    monotonicity_score,
    null_distribution,
    spearman_with_true_strength,
    threshold_at_target_fpr,
)
from valideval.validation.materiality import (
    classify_materiality,
    redundancy_materiality,
    saturation_materiality,
    scoring_materiality,
    shortcut_materiality,
)
from valideval.validation.multiplicity import annotate_flags, expected_false_flags
from valideval.validation.synthetic_benchmark import (
    IRT_VALIDATION_MODEL_IDS,
    SyntheticBenchmark,
    build_controlled_matrices,
    generate_synthetic_benchmark,
)
from valideval.validation.validation_report import (
    write_experiment_report,
    write_summary_report,
)

DEFAULT_STRENGTH_GRID = [round(index / 10, 1) for index in range(11)]
DEFAULT_SEEDS = [0, 1, 2]
DEFAULT_N_ITEMS = 64

DEFAULT_EXPERIMENTS = [
    {"diagnostic": "shortcut", "flaw_type": "shortcut_signal"},
    {"diagnostic": "answer_distribution", "flaw_type": "label_imbalance"},
    {"diagnostic": "answer_distribution", "flaw_type": "answer_length_artifact"},
    {"diagnostic": "distractor_quality", "flaw_type": "dead_distractors"},
    {"diagnostic": "redundancy", "flaw_type": "redundancy"},
    {"diagnostic": "irt", "flaw_type": "low_discrimination"},
    {"diagnostic": "irt", "flaw_type": "negative_discrimination"},
    {"diagnostic": "reliability", "flaw_type": "prompt_format_fragility"},
    {"diagnostic": "extraction_robustness", "flaw_type": "extraction_ambiguity"},
    {"diagnostic": "extraction_robustness", "flaw_type": "scoring_ambiguity"},
    {"diagnostic": "saturation", "flaw_type": "too_easy_saturation"},
    {"diagnostic": "saturation", "flaw_type": "too_hard_floor"},
]

EXPERIMENTAL_FLAWS = {
    "keyword_artifact": "Current keyword artifact validation is not well identified because the base synthetic context intentionally contains construct-relevant lexical signal.",
    "context_irrelevance": "Context-irrelevance validation needs a dedicated diagnostic score; current core diagnostics only partially probe it.",
    "context_leakage": "Context-leakage validation needs a leakage-specific detector score; shortcut ablations are only a proxy.",
}


def run_validation_config(
    config_path: str | Path,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    cfg = load_yaml(config_path)
    report_dir = output_dir or cfg.get("output_dir", "validation_reports")
    return run_validation_suite(
        experiments=cfg.get("experiments", DEFAULT_EXPERIMENTS),
        strength_grid=[float(value) for value in cfg.get("strength_grid", DEFAULT_STRENGTH_GRID)],
        seeds=[int(value) for value in cfg.get("seeds", DEFAULT_SEEDS)],
        n_items=int(cfg.get("n_items", DEFAULT_N_ITEMS)),
        output_dir=report_dir,
        target_fpr=float(cfg.get("target_fpr", 0.05)),
        multiplicity_method=str(cfg.get("multiplicity_method", "bh")),
    )


def run_single_validation(
    diagnostic: str,
    flaw_type: str,
    *,
    strength_grid: list[float] | None = None,
    seeds: list[int] | None = None,
    n_items: int = DEFAULT_N_ITEMS,
    output_dir: str | Path = "validation_reports",
    target_fpr: float = 0.05,
    multiplicity_method: str = "bh",
) -> dict[str, Any]:
    result = _run_experiment(
        diagnostic=diagnostic,
        flaw_type=flaw_type,
        strength_grid=strength_grid or DEFAULT_STRENGTH_GRID,
        seeds=seeds or DEFAULT_SEEDS,
        n_items=n_items,
        output_dir=Path(output_dir),
        target_fpr=target_fpr,
        multiplicity_method=multiplicity_method,
    )
    write_experiment_report(result, output_dir)
    write_summary_report([result], output_dir)
    return result


def run_validation_suite(
    *,
    experiments: list[dict[str, Any]],
    strength_grid: list[float] | None = None,
    seeds: list[int] | None = None,
    n_items: int = DEFAULT_N_ITEMS,
    output_dir: str | Path = "validation_reports",
    target_fpr: float = 0.05,
    multiplicity_method: str = "bh",
) -> dict[str, Any]:
    report_dir = Path(output_dir)
    results = []
    for experiment in experiments:
        result = _run_experiment(
            diagnostic=str(experiment["diagnostic"]),
            flaw_type=str(experiment["flaw_type"]),
            strength_grid=strength_grid or DEFAULT_STRENGTH_GRID,
            seeds=seeds or DEFAULT_SEEDS,
            n_items=int(experiment.get("n_items", n_items)),
            output_dir=report_dir,
            target_fpr=target_fpr,
            multiplicity_method=multiplicity_method,
        )
        result["report_paths"] = write_experiment_report(result, report_dir)
        results.append(result)
    summary_paths = write_summary_report(results, report_dir)
    return {"results": results, "summary_paths": summary_paths}


def _run_experiment(
    *,
    diagnostic: str,
    flaw_type: str,
    strength_grid: list[float],
    seeds: list[int],
    n_items: int,
    output_dir: Path,
    target_fpr: float,
    multiplicity_method: str,
) -> dict[str, Any]:
    if diagnostic not in DIAGNOSTICS:
        raise ValueError(f"Unknown diagnostic for validation: {diagnostic}")

    rows: list[dict[str, Any]] = []
    run_summaries: list[dict[str, Any]] = []
    warnings: list[str] = []
    limitations: list[str] = [
        "Synthetic detector validation is not real benchmark evidence.",
        "Detector metrics are conditional on the generator, controlled panel, and score extraction rule.",
    ]
    if flaw_type in EXPERIMENTAL_FLAWS:
        warnings.append(EXPERIMENTAL_FLAWS[flaw_type])
    if diagnostic == "irt" and flaw_type == "negative_discrimination":
        limitations.append(
            "Negative-discrimination validation keeps clean anchor items in the synthetic benchmark; "
            "a benchmark where nearly every item rewards the wrong ability ordering cannot be oriented "
            "from the response matrix alone."
        )

    cache_root = output_dir / "_cache" / f"{diagnostic}_{flaw_type}"
    panel_id = "synthetic_validation"
    variants = _variants_for(diagnostic, flaw_type)
    model_ids = _model_ids_for(diagnostic, flaw_type)

    for strength in strength_grid:
        for seed in seeds:
            benchmark = generate_synthetic_benchmark(
                flaw_type=flaw_type,
                flaw_strength=float(strength),
                seed=int(seed),
                n_items=n_items,
            )
            matrices = build_controlled_matrices(
                benchmark,
                variants=variants,
                cache_root=cache_root,
                panel_id=panel_id,
                seed=int(seed),
                model_ids=model_ids,
            )
            result = _run_diagnostic(
                diagnostic,
                benchmark,
                matrices,
                cache_root=cache_root,
                panel_id=panel_id,
                output_dir=output_dir / "_diagnostic_artifacts" / f"{diagnostic}_{flaw_type}",
                seed=int(seed),
                variants=variants,
            )
            warnings.extend(_unique_new(warnings, result.warnings))
            limitations.extend(_unique_new(limitations, result.limitations))
            item_scores = _extract_item_scores(
                result,
                benchmark,
                diagnostic=diagnostic,
                flaw_type=flaw_type,
            )
            labels = _ground_truth_labels(benchmark)
            for item_id in benchmark.load_items():
                score = float(item_scores.get(item_id.item_id, 0.0))
                rows.append(
                    {
                        "seed": int(seed),
                        "strength": float(strength),
                        "item_id": item_id.item_id,
                        "is_flawed": bool(labels.get(item_id.item_id, False)),
                        "score": score,
                    }
                )
            run_summaries.append(
                _run_summary(
                    result,
                    benchmark,
                    diagnostic=diagnostic,
                    flaw_type=flaw_type,
                    strength=float(strength),
                    seed=int(seed),
                    item_scores=item_scores,
                )
            )

    y_true = [bool(row["is_flawed"]) for row in rows]
    scores = [float(row["score"]) for row in rows]
    strengths = [float(row["strength"]) for row in rows]
    clean_scores = [float(row["score"]) for row in rows if float(row["strength"]) == 0.0]
    threshold = threshold_at_target_fpr(clean_scores, target_fpr=target_fpr)
    if threshold is not None:
        threshold = float(np.nextafter(threshold, math.inf))
    metrics = metric_bundle(y_true, scores, clean_scores=clean_scores, threshold=threshold)
    null = null_distribution(clean_scores)
    strength_scores = _score_by_strength(rows)
    monotonicity = monotonicity_score(
        [entry["strength"] for entry in strength_scores],
        [entry["mean_score"] for entry in strength_scores],
    )
    strength_corr = spearman_with_true_strength(strengths, scores)
    flags = _corrected_flags(
        rows,
        threshold=metrics["threshold"],
        null_scores=clean_scores,
        method=multiplicity_method,
    )
    materiality = _materiality_summary(
        run_summaries,
        diagnostic=diagnostic,
        flaw_type=flaw_type,
        metrics=metrics,
    )
    credibility = _credibility_status(metrics, monotonicity, flaw_type)
    if credibility == "quarantine":
        warnings.append(
            "This diagnostic/flaw pairing should be treated as unvalidated or quarantined under this harness."
        )
    elif credibility == "prototype_only":
        warnings.append(
            "This diagnostic/flaw pairing is prototype-only; use cautious language and inspect thresholds before real audits."
        )

    return {
        "schema_version": "0.1",
        "report_type": "synthetic_diagnostic_validation",
        "diagnostic": diagnostic,
        "flaw_type": flaw_type,
        "n_items": n_items,
        "n_seeds": len(seeds),
        "strength_grid": [float(value) for value in strength_grid],
        "target_fpr": target_fpr,
        "metrics": metrics,
        "auc": metrics.get("auc"),
        "pr_auc": metrics.get("pr_auc"),
        "fpr_at_threshold": metrics.get("false_positive_rate"),
        "threshold_at_5pct_fpr": threshold,
        "monotonicity": monotonicity,
        "score_strength_correlation": strength_corr,
        "calibration_curve": calibration_curve(y_true, scores, n_bins=10),
        "null_distribution": null,
        "threshold_recommendation": {
            "threshold": threshold,
            "target_fpr": target_fpr,
            "scope": "synthetic generator only",
            "warning": "Do not reuse this threshold on a real benchmark without validation.",
        },
        "multiplicity": {
            "method": multiplicity_method,
            "expected_false_flags_under_null": expected_false_flags(
                clean_scores,
                metrics["threshold"],
            ),
            "corrected_item_flags": flags[: min(len(flags), 50)],
            "n_flags_reported": min(len(flags), 50),
            "n_flags_total": len(flags),
        },
        "materiality": materiality,
        "score_by_strength": strength_scores,
        "run_summaries": run_summaries,
        "credibility_status": credibility,
        "warnings": sorted(set(warnings)),
        "limitations": sorted(set(limitations)),
        "artifacts": {
            "validation_report_dir": str(output_dir),
            "intermediate_cache_root": str(cache_root),
            "intermediate_cache_note": (
                "Synthetic prediction caches are intermediate run artifacts; the durable "
                "review artifacts are the validation report JSON and Markdown files."
            ),
        },
    }


def _run_diagnostic(
    diagnostic: str,
    benchmark: SyntheticBenchmark,
    matrices: dict[str, Any],
    *,
    cache_root: Path,
    panel_id: str,
    output_dir: Path,
    seed: int,
    variants: list[str],
) -> DiagnosticResult:
    diagnostic_cls = DIAGNOSTICS[diagnostic]
    config = {
        "cache_root": str(cache_root),
        "panel_id": panel_id,
        "output_dir": str(output_dir),
        "seed": seed,
        "variants": [variant for variant in variants if variant != "full"],
        "bootstrap_samples": 20,
        "random_subset_trials": 20,
        "min_models_warn": 12 if diagnostic == "irt" else 5,
    }
    return diagnostic_cls().run(benchmark, matrices, config=config)


def _extract_item_scores(
    result: DiagnosticResult,
    benchmark: SyntheticBenchmark,
    *,
    diagnostic: str,
    flaw_type: str,
) -> dict[str, float]:
    if diagnostic == "shortcut":
        return {
            item_id: float(
                max(
                    [
                        value
                        for variant, value in metrics.get("variant_scores", {}).items()
                        if variant
                        in {"label_prior_only", "metadata_only", "context_removed", "question_only"}
                    ]
                    or [metrics.get("max_ablated_score", 0.0)]
                )
            )
            for item_id, metrics in result.per_item_metrics.items()
        }
    if diagnostic == "answer_distribution" and flaw_type == "label_imbalance":
        balances = result.summary_metrics.get("label_balance", {})
        return {
            item.item_id: float(balances.get(_primary_answer(item), 0.0))
            for item in benchmark.load_items()
        }
    if diagnostic == "answer_distribution" and flaw_type == "answer_length_artifact":
        return {
            item_id: float(metrics.get("longest_option_correct", False))
            for item_id, metrics in result.per_item_metrics.items()
        }
    if diagnostic == "answer_distribution":
        return {
            item_id: float(
                bool(metrics.get("has_negation_cue"))
                or bool(metrics.get("has_all_none_option"))
                or bool(metrics.get("repeated_phrase"))
            )
            for item_id, metrics in result.per_item_metrics.items()
        }
    if diagnostic == "distractor_quality":
        return {
            item_id: float(metrics.get("dead_distractor_fraction", 0.0))
            for item_id, metrics in result.per_item_metrics.items()
        }
    if diagnostic == "redundancy":
        redundant = _redundant_item_ids(result.summary_metrics)
        return {item.item_id: float(item.item_id in redundant) for item in benchmark.load_items()}
    if diagnostic == "irt" and flaw_type == "negative_discrimination":
        return {
            item_id: max(0.0, -float(metrics.get("discrimination", 0.0)))
            for item_id, metrics in result.per_item_metrics.items()
        }
    if diagnostic == "irt":
        return {
            item_id: max(0.0, 1.0 - min(abs(float(metrics.get("discrimination", 0.0))), 1.0))
            for item_id, metrics in result.per_item_metrics.items()
        }
    if diagnostic == "reliability":
        scores = {}
        format_variants = {
            "terse_instructions",
            "verbose_instructions",
            "json_only",
            "answer_letter_only",
        }
        for item_id, metrics in result.per_item_metrics.items():
            agreements = metrics.get("variant_agreements", {})
            selected = (
                [value for variant, value in agreements.items() if variant in format_variants]
                if flaw_type == "prompt_format_fragility"
                else list(agreements.values())
            )
            stability = (
                float(np.mean(selected))
                if selected
                else float(metrics.get("mean_item_stability", 1.0))
            )
            scores[item_id] = max(0.0, 1.0 - stability)
        return scores
    if diagnostic == "extraction_robustness":
        return {
            item_id: max(
                float(metrics.get("extractor_disagreement_rate", 0.0)),
                float(metrics.get("invalid_output_rate", 0.0)),
                float(metrics.get("scoring_ambiguity_flag", False)),
            )
            for item_id, metrics in result.per_item_metrics.items()
        }
    if diagnostic == "saturation" and flaw_type == "too_hard_floor":
        return {
            item_id: max(0.0, 1.0 - float(metrics.get("mean_score", 1.0)))
            for item_id, metrics in result.per_item_metrics.items()
        }
    if diagnostic == "saturation":
        return {
            item_id: float(metrics.get("top_model_mean_score", 0.0))
            for item_id, metrics in result.per_item_metrics.items()
        }
    return {item.item_id: 0.0 for item in benchmark.load_items()}


def _run_summary(
    result: DiagnosticResult,
    benchmark: SyntheticBenchmark,
    *,
    diagnostic: str,
    flaw_type: str,
    strength: float,
    seed: int,
    item_scores: dict[str, float],
) -> dict[str, Any]:
    labels = _ground_truth_labels(benchmark)
    positive_scores = [score for item_id, score in item_scores.items() if labels.get(item_id)]
    negative_scores = [score for item_id, score in item_scores.items() if not labels.get(item_id)]
    return {
        "diagnostic": diagnostic,
        "flaw_type": flaw_type,
        "strength": strength,
        "seed": seed,
        "mean_score": float(np.mean(list(item_scores.values()))) if item_scores else 0.0,
        "mean_positive_score": float(np.mean(positive_scores)) if positive_scores else None,
        "mean_negative_score": float(np.mean(negative_scores)) if negative_scores else None,
        "diagnostic_summary": result.summary_metrics,
    }


def _materiality_summary(
    run_summaries: list[dict[str, Any]],
    *,
    diagnostic: str,
    flaw_type: str,
    metrics: dict[str, Any],
) -> dict[str, Any]:
    strongest = max(run_summaries, key=lambda row: row["strength"])
    summary = strongest.get("diagnostic_summary", {})
    if diagnostic == "shortcut":
        variants = summary.get("variants", {})
        retention_values = [
            item.get("shortcut_retention")
            for item in variants.values()
            if item.get("shortcut_retention") is not None
        ]
        retention = float(np.mean(retention_values)) if retention_values else None
        return shortcut_materiality(retention, summary.get("full_score"))
    if diagnostic == "redundancy":
        return redundancy_materiality(
            raw_item_count=int(summary.get("n_items", 0)),
            effective_item_count=summary.get("effective_item_count"),
        )
    if diagnostic == "saturation":
        return saturation_materiality(top_score_range=summary.get("top_model_score_range"))
    if diagnostic == "extraction_robustness":
        return scoring_materiality(
            summary.get("strict_vs_lenient_score_shift"),
            ranking_changed=False,
        )
    return {
        "status": classify_materiality(
            diagnostic=diagnostic,
            effect_size=metrics.get("auc"),
        ),
        "rule": "Generic prototype materiality: detector separability is not the same as practical benchmark materiality.",
    }


def _variants_for(diagnostic: str, flaw_type: str) -> list[str]:
    if diagnostic == "shortcut":
        return [
            "full",
            "question_only",
            "context_removed",
            "context_shuffled",
            "label_prior_only",
            "metadata_only",
            "answer_length_only",
            "irrelevant_context",
        ]
    if diagnostic == "reliability":
        return [
            "full",
            "context_removed",
            "context_shuffled",
            "terse_instructions",
            "verbose_instructions",
            "json_only",
            "answer_letter_only",
        ]
    if diagnostic in {"prompt_sensitivity"}:
        return ["full", "terse_instructions", "verbose_instructions"]
    return ["full"]


def _model_ids_for(diagnostic: str, flaw_type: str) -> list[str] | None:
    if diagnostic == "irt" and flaw_type in {
        "low_discrimination",
        "negative_discrimination",
    }:
        return list(IRT_VALIDATION_MODEL_IDS)
    return None


def _score_by_strength(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    strengths = sorted({float(row["strength"]) for row in rows})
    output = []
    for strength in strengths:
        selected = [row for row in rows if float(row["strength"]) == strength]
        positives = [row for row in selected if bool(row["is_flawed"])]
        negatives = [row for row in selected if not bool(row["is_flawed"])]
        output.append(
            {
                "strength": strength,
                "n": len(selected),
                "mean_score": float(np.mean([row["score"] for row in selected]))
                if selected
                else 0.0,
                "mean_positive_score": float(np.mean([row["score"] for row in positives]))
                if positives
                else None,
                "mean_negative_score": float(np.mean([row["score"] for row in negatives]))
                if negatives
                else None,
            }
        )
    return output


def _corrected_flags(
    rows: list[dict[str, Any]],
    *,
    threshold: float,
    null_scores: list[float],
    method: str,
) -> list[dict[str, Any]]:
    if not rows:
        return []
    max_strength = max(float(row["strength"]) for row in rows)
    selected = [row for row in rows if float(row["strength"]) == max_strength]
    return annotate_flags(
        [str(row["item_id"]) for row in selected],
        [float(row["score"]) for row in selected],
        null_scores=null_scores,
        threshold=threshold,
        method=method,
    )


def _credibility_status(
    metrics: dict[str, Any],
    monotonicity: float | None,
    flaw_type: str,
) -> str:
    if flaw_type in EXPERIMENTAL_FLAWS:
        return "prototype_only"
    auc = metrics.get("auc")
    fpr = metrics.get("false_positive_rate")
    if auc is None:
        return "uncalibrated"
    if (
        auc >= 0.75
        and (fpr is None or fpr <= 0.10)
        and (monotonicity is None or monotonicity >= 0.55)
    ):
        return "credible_under_synthetic_harness"
    if auc >= 0.60:
        return "prototype_only"
    return "quarantine"


def _ground_truth_labels(benchmark: SyntheticBenchmark) -> dict[str, bool]:
    return {
        item.item_id: bool(item.metadata.get("is_flawed", False)) for item in benchmark.load_items()
    }


def _primary_answer(item) -> str:
    if isinstance(item.answer, list):
        return str(item.answer[0]).upper()
    return str(item.answer).upper()


def _redundant_item_ids(summary: dict[str, Any]) -> set[str]:
    redundant: set[str] = set()
    for cluster_key in ["clusters", "shared_context_clusters", "repeated_template_clusters"]:
        for cluster in summary.get(cluster_key, []) or []:
            if len(cluster) > 1:
                redundant.update(sorted(cluster)[1:])
    return redundant


def _unique_new(existing: list[str], candidates: list[str]) -> list[str]:
    seen = set(existing)
    return [candidate for candidate in candidates if candidate not in seen]
