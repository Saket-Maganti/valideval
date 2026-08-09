from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from valideval.diagnostics.inference import item_discrimination_scores
from valideval.statistics.rank_nulls import normalize_subject_ids, validate_binary_response_matrix


def leave_one_item_influence(matrix: pd.DataFrame, *, top_k: int = 5) -> pd.DataFrame:
    """Compute exact leave-one-item score, winner, and top-k influence."""

    frame = validate_binary_response_matrix(matrix)
    if frame.isna().any().any():
        raise ValueError("exact leave-one-item influence currently requires a complete matrix")
    if not 0 < top_k < frame.shape[0]:
        raise ValueError("top_k must be between 1 and the number of models minus one")
    values = frame.to_numpy(dtype=float)
    full_scores = values.mean(axis=1)
    full_order = np.argsort(-full_scores, kind="stable")
    full_winner = int(full_order[0])
    runner_up = int(full_order[1])
    full_top = set(full_order[:top_k].tolist())
    removed_scores = (values.sum(axis=1)[:, None] - values) / (frame.shape[1] - 1)
    removed_winners = np.argmax(removed_scores, axis=0)
    score_delta = removed_scores - full_scores[:, None]
    rows = []
    for item in range(frame.shape[1]):
        order = np.argsort(-removed_scores[:, item], kind="stable")
        removed_top = set(order[:top_k].tolist())
        rows.append(
            {
                "item_id": str(frame.columns[item]),
                "full_winner": str(frame.index[full_winner]),
                "winner_without_item": str(frame.index[removed_winners[item]]),
                "winner_changed": bool(removed_winners[item] != full_winner),
                "top_k_changed": bool(removed_top != full_top),
                "top_k_jaccard": len(removed_top & full_top) / len(removed_top | full_top),
                "maximum_absolute_model_score_change": float(np.max(np.abs(score_delta[:, item]))),
                "winner_runner_pairwise_change": float(
                    (removed_scores[full_winner, item] - removed_scores[runner_up, item])
                    - (full_scores[full_winner] - full_scores[runner_up])
                ),
            }
        )
    return pd.DataFrame(rows)


def leave_one_subject_influence(
    matrix: pd.DataFrame,
    subjects: Sequence[str] | Mapping[str, str],
) -> pd.DataFrame:
    frame = validate_binary_response_matrix(matrix)
    subject_map = normalize_subject_ids(frame.columns, subjects)
    full_scores = frame.mean(axis=1)
    full_ranks = full_scores.rank(ascending=False, method="average")
    full_winner = str(full_scores.idxmax())
    rows = []
    for subject in sorted(subject_map.unique()):
        keep = subject_map.index[~subject_map.eq(subject)]
        scores = frame.loc[:, keep].mean(axis=1)
        ranks = scores.rank(ascending=False, method="average")
        rows.append(
            {
                "held_out_subject": str(subject),
                "winner_changed": str(scores.idxmax()) != full_winner,
                "winner_without_subject": str(scores.idxmax()),
                "maximum_absolute_score_change": float((scores - full_scores).abs().max()),
                "maximum_absolute_rank_change": float((ranks - full_ranks).abs().max()),
                "rank_spearman": float(ranks.corr(full_ranks, method="spearman")),
            }
        )
    return pd.DataFrame(rows)


def crossfit_removal_evaluation(
    matrix: pd.DataFrame,
    *,
    removal_fraction: float = 0.05,
    seed: int = 2027,
) -> pd.DataFrame:
    """Discover item risk on one model fold and compare policies on the held-out fold."""

    frame = validate_binary_response_matrix(matrix)
    if not 0.0 < removal_fraction < 0.5:
        raise ValueError("removal_fraction must be in (0, 0.5)")
    rng = np.random.default_rng(seed)
    permutation = rng.permutation(frame.shape[0])
    split = max(2, frame.shape[0] // 2)
    discovery = frame.iloc[permutation[:split]]
    validation = frame.iloc[permutation[split:]]
    if validation.shape[0] < 2:
        raise ValueError("at least four models are required for cross-fitting")
    count = max(1, int(round(removal_fraction * frame.shape[1])))
    risk = -np.nan_to_num(item_discrimination_scores(discovery), nan=0.0)
    difficulty = frame.mean(axis=0).to_numpy(dtype=float)
    variance = frame.var(axis=0).to_numpy(dtype=float)
    suspicious = np.argsort(risk)[-count:]
    random = rng.choice(frame.shape[1], size=count, replace=False)
    high_difficulty = np.argsort(difficulty)[:count]
    high_variance = np.argsort(variance)[-count:]
    bins = pd.qcut(difficulty, q=10, labels=False, duplicates="drop")
    matched: list[int] = []
    for index in suspicious:
        candidates = np.flatnonzero(np.asarray(bins) == bins[index])
        candidates = np.asarray([candidate for candidate in candidates if candidate not in matched])
        matched.append(int(rng.choice(candidates)) if len(candidates) else int(index))
    policies = {
        "suspicious_crossfit": suspicious,
        "random": random,
        "matched_difficulty": np.asarray(matched),
        "high_difficulty": high_difficulty,
        "high_variance": high_variance,
    }
    baseline = validation.mean(axis=1)
    baseline_ranks = baseline.rank(ascending=False, method="average")
    rows = []
    for name, removed in policies.items():
        retained = np.ones(frame.shape[1], dtype=bool)
        retained[removed] = False
        scores = validation.iloc[:, retained].mean(axis=1)
        ranks = scores.rank(ascending=False, method="average")
        rows.append(
            {
                "policy": name,
                "discovery_models": int(discovery.shape[0]),
                "held_out_models": int(validation.shape[0]),
                "items_removed": int(len(removed)),
                "removal_fraction": float(len(removed) / frame.shape[1]),
                "held_out_rank_spearman": float(ranks.corr(baseline_ranks, method="spearman")),
                "held_out_maximum_rank_change": float((ranks - baseline_ranks).abs().max()),
                "held_out_maximum_score_change": float((scores - baseline).abs().max()),
                "held_out_winner_changed": str(scores.idxmax()) != str(baseline.idxmax()),
            }
        )
    return pd.DataFrame(rows)
