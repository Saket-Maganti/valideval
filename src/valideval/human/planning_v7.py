from __future__ import annotations

import math
from collections.abc import Sequence

import pandas as pd


def annotation_power_plan(
    sample_sizes: Sequence[int] = (50, 100, 150, 200, 300, 500),
    *,
    expected_precision: float = 0.70,
    control_prevalence: float = 0.20,
    expected_agreement: float = 0.80,
    confidence_level: float = 0.95,
    stratum_count: int = 4,
    adjudication_fraction: float = 0.20,
    benchmark_defect_fraction: float = 0.75,
) -> pd.DataFrame:
    """Plan binomial precision, enrichment, prevalence, and agreement uncertainty."""

    probabilities = (expected_precision, control_prevalence, expected_agreement)
    if any(not 0.0 < value < 1.0 for value in probabilities):
        raise ValueError("planning probabilities must be in (0, 1)")
    if confidence_level != 0.95:
        raise ValueError("the deterministic V7 planner currently supports 95% intervals")
    if stratum_count != 4:
        raise ValueError("the frozen V7 design requires four strata")
    if not 0.0 <= adjudication_fraction <= 1.0:
        raise ValueError("adjudication_fraction must lie in [0, 1]")
    if not 0.0 < benchmark_defect_fraction < 1.0:
        raise ValueError("benchmark_defect_fraction must lie in (0, 1)")
    rows = []
    for sample_size in sample_sizes:
        if sample_size <= 0:
            raise ValueError("sample sizes must be positive")
        flagged_issues = int(round(sample_size * expected_precision))
        control_issues = int(round(sample_size * control_prevalence))
        precision_lower, precision_upper = wilson_interval(flagged_issues, sample_size)
        control_lower, control_upper = wilson_interval(control_issues, sample_size)
        enrichment = expected_precision / control_prevalence
        log_enrichment_se = math.sqrt(
            (1.0 - expected_precision) / (sample_size * expected_precision)
            + (1.0 - control_prevalence) / (sample_size * control_prevalence)
        )
        agreement_count = int(round(sample_size * expected_agreement))
        agreement_lower, agreement_upper = wilson_interval(agreement_count, sample_size)
        total_unique_items = sample_size * stratum_count
        class_successes = int(round(sample_size * 0.50))
        class_lower, class_upper = wilson_interval(class_successes, sample_size)
        rows.append(
            {
                "design": _design_name(sample_size),
                "items_per_stratum": int(sample_size),
                "stratum_count": stratum_count,
                "annotations_per_stratum": int(sample_size),
                "total_unique_items": total_unique_items,
                "annotators_per_item_primary": 2,
                "adjudication_fraction": adjudication_fraction,
                "total_raw_labels": total_unique_items * 2,
                "total_raw_labels_2_annotators": total_unique_items * 2,
                "total_raw_labels_3_annotators": total_unique_items * 3,
                "annotators_2_total_labels": total_unique_items * 2,
                "annotators_3_total_labels": total_unique_items * 3,
                "expected_adjudication_labels": int(
                    math.ceil(total_unique_items * adjudication_fraction)
                ),
                "planned_benchmark_defect_items": int(
                    round(total_unique_items * benchmark_defect_fraction)
                ),
                "planned_pipeline_extraction_scoring_items": int(
                    total_unique_items - round(total_unique_items * benchmark_defect_fraction)
                ),
                "expected_precision": expected_precision,
                "precision_ci_lower": precision_lower,
                "precision_ci_upper": precision_upper,
                "expected_control_prevalence": control_prevalence,
                "control_prevalence_ci_lower": control_lower,
                "control_prevalence_ci_upper": control_upper,
                "expected_enrichment": enrichment,
                "enrichment_ci_lower": math.exp(math.log(enrichment) - 1.96 * log_enrichment_se),
                "enrichment_ci_upper": math.exp(math.log(enrichment) + 1.96 * log_enrichment_se),
                "expected_agreement": expected_agreement,
                "agreement_ci_lower": agreement_lower,
                "agreement_ci_upper": agreement_upper,
                "assumed_class_specific_precision": 0.50,
                "class_specific_precision_ci_lower": class_lower,
                "class_specific_precision_ci_upper": class_upper,
                "resource_accounting_status": "HUMAN_STUDY_RESOURCE_ACCOUNTING_READY",
                "planning_only": True,
            }
        )
    return pd.DataFrame(rows)


def wilson_interval(successes: int, trials: int) -> tuple[float, float]:
    if trials <= 0 or not 0 <= successes <= trials:
        raise ValueError("successes/trials are invalid")
    z = 1.959963984540054
    proportion = successes / trials
    denominator = 1.0 + z**2 / trials
    center = (proportion + z**2 / (2.0 * trials)) / denominator
    half = (
        z
        * math.sqrt(proportion * (1.0 - proportion) / trials + z**2 / (4.0 * trials**2))
        / denominator
    )
    return max(0.0, center - half), min(1.0, center + half)


def _design_name(items_per_stratum: int) -> str:
    if items_per_stratum <= 50:
        return "pilot"
    if items_per_stratum <= 150:
        return "minimum_confirmatory"
    if items_per_stratum <= 300:
        return "recommended_confirmatory"
    return "high_precision_confirmatory"
