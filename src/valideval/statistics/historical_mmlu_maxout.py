from __future__ import annotations

import json
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from valideval.execution.manifest import atomic_write_json, atomic_write_text
from valideval.statistics.rank_inference_v7_1 import (
    pairwise_multiplicity_analysis,
    simultaneous_rank_confidence_sets,
)
from valideval.statistics.rank_nulls import subject_accuracy_matrix


def historical_weighting_summary(
    matrix: pd.DataFrame,
    families: Mapping[str, str],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Compare canonical, balanced-subject, and trimmed-subject MMLU estimands."""

    frame = matrix.astype(float)
    if frame.empty or not set(np.unique(frame.to_numpy())).issubset({0.0, 1.0}):
        raise ValueError("historical MMLU matrix must be non-empty and binary")
    if set(map(str, frame.index)) != set(map(str, families)):
        raise ValueError("model-family map must exactly cover the historical matrix")
    subjects = {str(item): str(item).split("::", 1)[0] for item in frame.columns}
    subject_scores = subject_accuracy_matrix(frame, subjects)
    subject_sizes = pd.Series(subjects).value_counts().reindex(subject_scores.columns).astype(float)
    lower, upper = np.quantile(subject_sizes.to_numpy(), [0.10, 0.90])
    trimmed_weights = subject_sizes.clip(lower=lower, upper=upper)
    scores = {
        "CANONICAL_ITEM_WEIGHTED": frame.mean(axis=1),
        "BALANCED_SUBJECT_WEIGHTED": subject_scores.mean(axis=1),
        "TRIMMED_SUBJECT_WEIGHTED": subject_scores.mul(trimmed_weights, axis=1).sum(axis=1)
        / trimmed_weights.sum(),
    }
    rows: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "models": int(frame.shape[0]),
        "items": int(frame.shape[1]),
        "subjects": int(subject_scores.shape[1]),
        "families": len(set(map(str, families.values()))),
        "trimmed_subject_weight_quantiles": [float(lower), float(upper)],
        "estimands": {},
    }
    for estimand, values in scores.items():
        ranks = values.rank(ascending=False, method="average")
        order = sorted(values.index.astype(str), key=lambda model: (ranks.loc[model], model))
        summary["estimands"][estimand] = {
            "winner": order[0],
            "top_5": order[:5],
        }
        for model in values.index.astype(str):
            rows.append(
                {
                    "estimand": estimand,
                    "model_id": model,
                    "model_family": str(families[model]),
                    "score": float(values.loc[model]),
                    "rank": float(ranks.loc[model]),
                }
            )
    summary["winner_stable"] = (
        len({entry["winner"] for entry in summary["estimands"].values()}) == 1
    )
    summary["top_5_stable"] = (
        len({tuple(entry["top_5"]) for entry in summary["estimands"].values()}) == 1
    )
    return pd.DataFrame(rows), summary


def run_historical_mmlu_maxout(
    *,
    matrix_path: str | Path,
    family_path: str | Path,
    output_root: str | Path,
    bootstrap_draws: int = 300,
    seed: int = 7214000,
    quick: bool = False,
) -> dict[str, Any]:
    started = time.perf_counter()
    matrix = pd.read_csv(matrix_path, index_col=0)
    family_frame = pd.read_csv(family_path)
    families = dict(zip(family_frame["model_id"], family_frame["model_family"], strict=True))
    weighting, summary = historical_weighting_summary(matrix, families)
    subjects = {str(item): str(item).split("::", 1)[0] for item in matrix.columns}
    trimmed_draws = _trimmed_subject_bootstrap(
        matrix,
        subjects,
        n_bootstrap=bootstrap_draws,
        seed=seed,
    )
    trimmed_scores = weighting.loc[weighting["estimand"] == "TRIMMED_SUBJECT_WEIGHTED"].set_index(
        "model_id"
    )["score"]
    trimmed_rank_sets = simultaneous_rank_confidence_sets(
        trimmed_draws,
        observed_scores=trimmed_scores,
        confidence_level=0.95,
        resampling_unit="nested_subject_item_trimmed_subject_weight",
    )
    trimmed_pairs = pairwise_multiplicity_analysis(trimmed_draws)
    # The canonical draws are a declared input rather than inferred from matrix_path.
    canonical_path = Path("results/v7_1/study_h/canonical_item_weighted_bootstrap_draws.csv")
    canonical_draws = pd.read_csv(canonical_path)
    convergence = _bootstrap_convergence(canonical_draws, matrix.mean(axis=1))
    jackknife = _jackknife_summary(matrix, subjects, families)
    canonical_deduplicated = json.loads(
        Path("results/v7_1/estimand_conditions/summary.json").read_text(encoding="utf-8")
    )
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    frames = {
        "weighting_sensitivity": weighting,
        "trimmed_subject_bootstrap_draws": trimmed_draws,
        "trimmed_subject_simultaneous_rank_sets": trimmed_rank_sets,
        "trimmed_subject_pairwise_multiplicity": trimmed_pairs,
        "bootstrap_convergence": pd.DataFrame(convergence),
        "jackknife_summary": pd.DataFrame(jackknife),
    }
    for name, frame in frames.items():
        atomic_write_text(output / f"{name}.csv", frame.to_csv(index=False, lineterminator="\n"))
    payload = {
        "schema_version": "valideval.historical-mmlu-maxout.v7.2.1",
        "status": "HISTORICAL_MMLU_CPU_MAXOUT_COMPLETE",
        "mode": "NON_EVIDENCE_FIXTURE" if quick else "FULL_REGISTERED",
        "evidence_class": "NON_EVIDENCE_FIXTURE" if quick else "HISTORICAL_SENSITIVITY",
        **summary,
        "trimmed_simultaneous_rank_set_count": int(len(trimmed_rank_sets)),
        "trimmed_pairwise_bh_calls": int(trimmed_pairs["reject_bh"].sum()),
        "trimmed_pairwise_holm_calls": int(trimmed_pairs["reject_holm"].sum()),
        "bootstrap_convergence": convergence,
        "jackknife": jackknife,
        "canonical_vs_deduplicated": canonical_deduplicated,
        "runtime_seconds": time.perf_counter() - started,
        "claim_boundary": (
            "This is sensitivity analysis on the historical 39×14,042 MMLU panel. It does not "
            "turn one weighting or deletion scheme into a uniquely correct global ranking."
        ),
    }
    atomic_write_json(output / "summary.json", payload)
    return payload


def _trimmed_subject_bootstrap(
    matrix: pd.DataFrame,
    subjects: Mapping[str, str],
    *,
    n_bootstrap: int,
    seed: int,
) -> pd.DataFrame:
    if n_bootstrap < 100:
        raise ValueError("trimmed bootstrap requires at least 100 draws")
    subject_series = pd.Series(
        [subjects[str(column)] for column in matrix.columns],
        index=matrix.columns,
    )
    names = np.asarray(sorted(subject_series.unique()))
    indices = {subject: np.flatnonzero(subject_series.to_numpy() == subject) for subject in names}
    sizes = np.asarray([len(indices[subject]) for subject in names], dtype=float)
    lower, upper = np.quantile(sizes, [0.10, 0.90])
    weights = {subject: float(np.clip(len(indices[subject]), lower, upper)) for subject in names}
    values = matrix.to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    draws = np.empty((n_bootstrap, matrix.shape[0]), dtype=float)
    for replicate in range(n_bootstrap):
        sampled_subjects = rng.choice(names, size=len(names), replace=True)
        subject_means = []
        subject_weights = []
        for subject in sampled_subjects:
            available = indices[str(subject)]
            sampled_items = rng.choice(available, size=len(available), replace=True)
            subject_means.append(np.mean(values[:, sampled_items], axis=1))
            subject_weights.append(weights[str(subject)])
        draws[replicate] = np.average(
            np.column_stack(subject_means),
            axis=1,
            weights=np.asarray(subject_weights),
        )
    return pd.DataFrame(draws, columns=matrix.index.astype(str))


def _bootstrap_convergence(
    draws: pd.DataFrame,
    observed_scores: pd.Series,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    observed = observed_scores.copy()
    observed.index = observed.index.astype(str)
    for count in (100, 250, 500, 1000):
        used = min(count, len(draws))
        subset = draws.iloc[:used]
        ranks = simultaneous_rank_confidence_sets(subset, observed_scores=observed)
        pairs = pairwise_multiplicity_analysis(subset)
        rows.append(
            {
                "requested_draws": count,
                "used_draws": used,
                "mean_rank_set_width": float(
                    (ranks["simultaneous_rank_upper"] - ranks["simultaneous_rank_lower"]).mean()
                ),
                "pairwise_bh_calls": int(pairs["reject_bh"].sum()),
                "pairwise_holm_calls": int(pairs["reject_holm"].sum()),
                "convergence_status": "AVAILABLE" if count <= len(draws) else "NOT_AVAILABLE",
            }
        )
    return rows


def _jackknife_summary(
    matrix: pd.DataFrame,
    subjects: Mapping[str, str],
    families: Mapping[str, str],
) -> list[dict[str, Any]]:
    baseline_scores = matrix.mean(axis=1)
    baseline_ranks = baseline_scores.rank(ascending=False, method="average")
    baseline_winner = str(baseline_ranks.idxmin())
    rows: list[dict[str, Any]] = []
    subject_series = pd.Series(subjects)
    for subject in sorted(subject_series.unique()):
        retained = [column for column in matrix.columns if subjects[str(column)] != subject]
        ranks = matrix[retained].mean(axis=1).rank(ascending=False, method="average")
        rows.append(
            {
                "jackknife_unit": "SUBJECT",
                "removed_id": subject,
                "winner_changed": str(ranks.idxmin()) != baseline_winner,
                "maximum_absolute_rank_change": float((ranks - baseline_ranks).abs().max()),
            }
        )
    for model in sorted(matrix.index.astype(str)):
        retained = matrix.drop(index=model)
        ranks = retained.mean(axis=1).rank(ascending=False, method="average")
        rows.append(
            {
                "jackknife_unit": "MODEL",
                "removed_id": model,
                "winner_changed": model == baseline_winner,
                "maximum_absolute_rank_change": float(
                    (ranks - baseline_ranks.drop(index=model)).abs().max()
                ),
            }
        )
    for family in sorted(set(map(str, families.values()))):
        removed = [model for model, value in families.items() if str(value) == family]
        retained = matrix.drop(index=removed)
        ranks = retained.mean(axis=1).rank(ascending=False, method="average")
        rows.append(
            {
                "jackknife_unit": "MODEL_FAMILY",
                "removed_id": family,
                "winner_changed": baseline_winner in removed,
                "maximum_absolute_rank_change": float(
                    (ranks - baseline_ranks.drop(index=removed)).abs().max()
                ),
            }
        )
    return rows
