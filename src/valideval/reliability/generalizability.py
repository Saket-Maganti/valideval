from __future__ import annotations

from collections.abc import Mapping


def generalizability_coefficients(
    components: Mapping[str, float | int | str],
    *,
    items: int,
    subjects: int,
    families: int,
    checkpoints_per_family: int = 1,
) -> dict[str, float]:
    """Compute relative G-coefficients for four predeclared benchmark uses."""

    if min(items, subjects, families, checkpoints_per_family) <= 0:
        raise ValueError("design counts must be positive")
    model = float(components["model"])
    family = float(components["family"])
    subject = float(components["subject"])
    item = float(components["item"])
    model_subject = float(components["model_x_subject"])
    family_subject = float(components["family_x_subject"])
    residual = float(components["residual"])
    signal = model + family
    aggregate_error = (
        model_subject / subjects + family_subject / (subjects * families) + residual / items
    )
    pairwise_error = 2.0 * aggregate_error
    subject_conditioned_error = model_subject + residual / max(items / subjects, 1.0)
    family_selection_error = (
        family_subject / subjects
        + model / checkpoints_per_family
        + residual / (items * checkpoints_per_family)
    )
    return {
        "aggregate_benchmark_score": _ratio(signal, aggregate_error),
        "pairwise_model_comparison": _ratio(2.0 * model, pairwise_error),
        "top_k_selection": _ratio(signal, aggregate_error + item / items + subject / subjects),
        "subject_conditioned_score": _ratio(model, subject_conditioned_error),
        "best_family_selection": _ratio(family, family_selection_error),
    }


def _ratio(signal: float, error: float) -> float:
    denominator = max(signal + error, 0.0)
    return float(signal / denominator) if denominator > 0.0 else 0.0
