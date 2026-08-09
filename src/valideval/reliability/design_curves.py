from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas as pd

from valideval.reliability.generalizability import generalizability_coefficients


def benchmark_design_curve(
    components: Mapping[str, float | int | str],
    *,
    item_grid: Sequence[int] = (100, 250, 500, 1000, 2500, 5000, 10000, 15000),
    subject_grid: Sequence[int] = (5, 10, 20, 40, 57),
    family_grid: Sequence[int] = (3, 5, 8, 10, 15),
    checkpoint_grid: Sequence[int] = (1, 2, 3),
) -> pd.DataFrame:
    rows = []
    for items in item_grid:
        for subjects in subject_grid:
            for families in family_grid:
                for checkpoints in checkpoint_grid:
                    coefficients = generalizability_coefficients(
                        components,
                        items=int(items),
                        subjects=int(subjects),
                        families=int(families),
                        checkpoints_per_family=int(checkpoints),
                    )
                    rows.append(
                        {
                            "items": int(items),
                            "subjects": int(subjects),
                            "families": int(families),
                            "checkpoints_per_family": int(checkpoints),
                            **coefficients,
                        }
                    )
    return pd.DataFrame(rows)


def minimum_design(
    curve: pd.DataFrame,
    *,
    outcome: str,
    target: float,
) -> dict[str, float | int | str] | None:
    if outcome not in curve.columns:
        raise ValueError(f"unknown reliability outcome: {outcome}")
    eligible = curve[curve[outcome] >= target].copy()
    if eligible.empty:
        return None
    eligible["cost_proxy"] = (
        eligible["items"] * eligible["families"] * eligible["checkpoints_per_family"]
    )
    row = eligible.sort_values(
        ["cost_proxy", "subjects", "items", "families", "checkpoints_per_family"]
    ).iloc[0]
    return {
        "outcome": outcome,
        "target": float(target),
        "achieved": float(row[outcome]),
        "items": int(row["items"]),
        "subjects": int(row["subjects"]),
        "families": int(row["families"]),
        "checkpoints_per_family": int(row["checkpoints_per_family"]),
    }
