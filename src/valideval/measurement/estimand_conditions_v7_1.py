from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd

from valideval.decision.regret import compare_selection_rules
from valideval.decision.selective_ranking import selective_ranking
from valideval.statistics.rank_inference_v7_1 import simultaneous_rank_confidence_sets


def item_bootstrap_draws(
    matrix: pd.DataFrame,
    *,
    n_bootstrap: int = 500,
    seed: int = 2027,
) -> pd.DataFrame:
    if matrix.shape[0] < 2 or matrix.shape[1] < 2 or n_bootstrap < 2:
        raise ValueError("matrix and bootstrap count are too small")
    values = matrix.to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    draws = np.empty((n_bootstrap, matrix.shape[0]), dtype=float)
    for replicate in range(n_bootstrap):
        sampled = rng.integers(0, matrix.shape[1], size=matrix.shape[1])
        draws[replicate] = np.nanmean(values[:, sampled], axis=1)
    return pd.DataFrame(draws, columns=matrix.index.astype(str))


def compare_canonical_and_deduplicated(
    canonical: pd.DataFrame,
    retained_item_ids: Sequence[str],
    *,
    benchmark_id: str,
    n_bootstrap: int = 500,
    seed: int = 2027,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    retained = list(map(str, retained_item_ids))
    if len(retained) != len(set(retained)):
        raise ValueError("retained_item_ids contains duplicates")
    missing = sorted(set(retained) - set(map(str, canonical.columns)))
    if missing:
        raise ValueError(
            f"deduplicated item identities are missing from canonical matrix: {missing[:5]}"
        )
    conditions = {
        "CANONICAL": canonical,
        "DEDUPLICATED_VALIDITY_ANALYSIS": canonical.loc[:, retained],
    }
    summaries = []
    artifacts: dict[str, Any] = {}
    for offset, (condition, matrix) in enumerate(conditions.items()):
        draws = item_bootstrap_draws(matrix, n_bootstrap=n_bootstrap, seed=seed + offset)
        means = matrix.mean(axis=1)
        ranks = means.rank(ascending=False, method="average")
        pairwise = selective_ranking(draws)
        rank_sets = simultaneous_rank_confidence_sets(
            draws,
            observed_scores=means,
            resampling_unit="item_bootstrap_joint_model_draws",
        )
        regret = compare_selection_rules(draws)
        top_five = sorted(ranks.index[ranks <= 5].astype(str))
        summaries.append(
            {
                "benchmark_id": benchmark_id,
                "condition": condition,
                "item_count": matrix.shape[1],
                "model_count": matrix.shape[0],
                "winner": str(means.idxmax()),
                "winner_accuracy": float(means.max()),
                "top_5": "|".join(top_five),
                "directional_pairwise_decisions": int(
                    pairwise["decision"].isin(["A > B", "B > A"]).sum()
                ),
                "pairwise_abstentions": int(pairwise["decision"].eq("INSUFFICIENT_EVIDENCE").sum()),
                "simultaneous_top_5_licenses": int(
                    (rank_sets["simultaneous_rank_upper"] <= 5).sum()
                ),
                "claim_licensed_selection_status": str(
                    regret.loc[regret["rule"] == "claim_licensed", "status"].iloc[0]
                ),
            }
        )
        artifacts[condition] = {
            "scores": means.rename("accuracy").rename_axis("model_id").reset_index(),
            "pairwise": pairwise,
            "rank_sets": rank_sets,
            "decision_regret": regret,
        }
    summary_frame = pd.DataFrame(summaries)
    canonical_row = summary_frame.loc[summary_frame["condition"] == "CANONICAL"].iloc[0]
    deduplicated_row = summary_frame.loc[
        summary_frame["condition"] == "DEDUPLICATED_VALIDITY_ANALYSIS"
    ].iloc[0]
    comparison = {
        "status": "CANONICAL_AND_DEDUPLICATED_ESTIMANDS_READY",
        "benchmark_id": benchmark_id,
        "winner_changed": bool(canonical_row["winner"] != deduplicated_row["winner"]),
        "top_5_changed": bool(canonical_row["top_5"] != deduplicated_row["top_5"]),
        "directional_pairwise_decision_count_changed": bool(
            canonical_row["directional_pairwise_decisions"]
            != deduplicated_row["directional_pairwise_decisions"]
        ),
        "rank_interval_type": "BOOTSTRAP_MAX_DEVIATION_SIMULTANEOUS",
        "claim_boundary": (
            "The deduplicated condition is a validity-analysis estimand and is never labeled "
            f"canonical {benchmark_id}."
        ),
        "artifacts": artifacts,
    }
    return summary_frame, comparison
