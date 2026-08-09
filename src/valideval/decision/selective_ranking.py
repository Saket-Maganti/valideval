from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd


def selective_ranking(
    score_draws: pd.DataFrame,
    *,
    confidence_level: float = 0.95,
    materiality_threshold: float = 0.01,
) -> pd.DataFrame:
    """Return pairwise decisions that may abstain.

    ``score_draws`` has resampling replicates in rows and named models in columns.
    """

    if score_draws.shape[0] < 2 or score_draws.shape[1] < 2:
        raise ValueError("score_draws must contain at least two draws and two models")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be in (0, 1)")
    if materiality_threshold < 0.0:
        raise ValueError("materiality_threshold must be non-negative")
    alpha = 1.0 - confidence_level
    rows = []
    models = [str(column) for column in score_draws.columns]
    for left, model_a in enumerate(models):
        for model_b in models[left + 1 :]:
            difference = score_draws[model_a].to_numpy(dtype=float) - score_draws[model_b].to_numpy(
                dtype=float
            )
            lower, upper = np.quantile(difference, [alpha / 2.0, 1.0 - alpha / 2.0])
            if lower > materiality_threshold:
                decision = "A > B"
            elif upper < -materiality_threshold:
                decision = "B > A"
            elif lower >= -materiality_threshold and upper <= materiality_threshold:
                decision = "A ~ B"
            else:
                decision = "INSUFFICIENT_EVIDENCE"
            rows.append(
                {
                    "model_a": model_a,
                    "model_b": model_b,
                    "mean_difference": float(np.mean(difference)),
                    "confidence_lower": float(lower),
                    "confidence_upper": float(upper),
                    "materiality_threshold": materiality_threshold,
                    "decision": decision,
                }
            )
    return pd.DataFrame(rows)


def pairwise_confidence_graph(decisions: pd.DataFrame) -> dict[str, Sequence[dict[str, object]]]:
    required = {"model_a", "model_b", "decision", "confidence_lower", "confidence_upper"}
    if not required.issubset(decisions.columns):
        raise ValueError(f"decisions are missing {sorted(required - set(decisions.columns))}")
    nodes = sorted(set(decisions["model_a"]) | set(decisions["model_b"]))
    edges: list[dict[str, object]] = []
    abstentions: list[dict[str, object]] = []
    for row in decisions.to_dict(orient="records"):
        decision = str(row["decision"])
        if decision == "A > B":
            edges.append({"source": row["model_a"], "target": row["model_b"], **row})
        elif decision == "B > A":
            edges.append({"source": row["model_b"], "target": row["model_a"], **row})
        else:
            abstentions.append(row)
    return {
        "nodes": [{"model_id": model} for model in nodes],
        "directed_edges": edges,
        "abstentions": abstentions,
    }
