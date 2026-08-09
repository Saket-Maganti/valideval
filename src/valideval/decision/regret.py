from __future__ import annotations

import numpy as np
import pandas as pd


def expected_decision_regret(
    score_draws: pd.DataFrame,
    selected_model: str,
    *,
    confidence_level: float = 0.95,
) -> dict[str, float | str]:
    if selected_model not in score_draws.columns:
        raise ValueError(f"selected model is absent: {selected_model}")
    values = score_draws.to_numpy(dtype=float)
    selected = score_draws[selected_model].to_numpy(dtype=float)
    regret = np.max(values, axis=1) - selected
    alpha = 1.0 - confidence_level
    return {
        "selected_model": selected_model,
        "expected_regret": float(np.mean(regret)),
        "regret_lower": float(np.quantile(regret, alpha / 2.0)),
        "regret_upper": float(np.quantile(regret, 1.0 - alpha / 2.0)),
        "probability_optimal": float(np.mean(regret <= 1e-12)),
    }


def compare_selection_rules(
    score_draws: pd.DataFrame,
    *,
    confidence_level: float = 0.95,
    regret_bound: float = 0.01,
) -> pd.DataFrame:
    means = score_draws.mean(axis=0)
    alpha = 1.0 - confidence_level
    lower = score_draws.quantile(alpha / 2.0, axis=0)
    naive = str(means.idxmax())
    uncertainty_aware = str(lower.idxmax())
    candidates = []
    for model in score_draws.columns:
        summary = expected_decision_regret(
            score_draws, str(model), confidence_level=confidence_level
        )
        if float(summary["regret_upper"]) <= regret_bound:
            candidates.append((float(summary["expected_regret"]), str(model)))
    licensed = min(candidates)[1] if candidates else None
    rows: list[dict[str, object]] = []
    for rule, model in (
        ("naive_leaderboard", naive),
        ("uncertainty_aware", uncertainty_aware),
        ("claim_licensed", licensed),
    ):
        if model is None:
            rows.append(
                {
                    "rule": rule,
                    "selected_model": None,
                    "status": "ABSTAIN",
                    "expected_regret": None,
                    "regret_upper": None,
                }
            )
            continue
        summary = expected_decision_regret(score_draws, model, confidence_level=confidence_level)
        row: dict[str, object] = {"rule": rule, "status": "SELECT"}
        row.update(summary)
        rows.append(row)
    return pd.DataFrame(rows)
