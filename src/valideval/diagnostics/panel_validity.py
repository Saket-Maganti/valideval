from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from valideval.schemas import ResponseMatrix


def load_matrix_csv(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path, index_col=0).astype(float)


def evaluate_minimum_matrix_adequacy(
    matrix: ResponseMatrix | pd.DataFrame,
    *,
    chance: float = 0.25,
    min_models: int = 30,
    min_items: int = 20,
    max_missing_fraction: float = 0.10,
    min_ability_spread: float = 0.20,
    near_chance_tolerance: float = 0.05,
) -> dict[str, Any]:
    frame = matrix.to_dataframe() if isinstance(matrix, ResponseMatrix) else matrix
    frame = frame.astype(float)
    n_models, n_items = frame.shape
    missing_fraction = float(frame.isna().sum().sum() / max(n_models * n_items, 1))
    model_accuracy = frame.mean(axis=1, skipna=True)
    item_accuracy = frame.mean(axis=0, skipna=True)
    ability_spread = float(model_accuracy.max() - model_accuracy.min()) if n_models else 0.0
    accuracy_std = float(model_accuracy.std(ddof=0)) if n_models else 0.0
    near_chance_fraction = (
        float((model_accuracy.sub(chance).abs() <= near_chance_tolerance).mean())
        if n_models
        else 1.0
    )
    blockers: list[str] = []
    warnings: list[str] = []
    if n_models < min_models:
        blockers.append(f"model_count_below_{min_models}")
    if n_items < min_items:
        blockers.append(f"item_count_below_{min_items}")
    if missing_fraction > max_missing_fraction:
        blockers.append("missingness_too_high")
    if ability_spread < min_ability_spread:
        blockers.append("ability_spread_too_narrow")
    if near_chance_fraction >= 0.80:
        blockers.append("panel_clustered_near_chance")
    if float(item_accuracy.std(ddof=0)) < 0.03 and n_items:
        warnings.append("Item difficulty variance is very low under this panel.")

    suitability = {
        "exploratory_item_analysis": not blockers,
        "irt_item_discrimination": False,
        "ranking_uncertainty": n_models >= max(10, min_models // 2)
        and ability_spread >= min_ability_spread / 2
        and missing_fraction <= max_missing_fraction,
        "protocol_demo_only": bool(blockers),
    }
    status = "pass" if not blockers else "blocked"
    return {
        "schema_version": "0.2",
        "diagnostic_name": "minimum_matrix_adequacy",
        "legacy_alias": "panel_validity",
        "status": status,
        "n_models": int(n_models),
        "n_items": int(n_items),
        "chance": float(chance),
        "missing_fraction": missing_fraction,
        "model_accuracy": _series_summary(model_accuracy),
        "item_accuracy": _series_summary(item_accuracy),
        "ability_spread": ability_spread,
        "accuracy_std": accuracy_std,
        "near_chance_fraction": near_chance_fraction,
        "blockers": blockers,
        "warnings": warnings,
        "suitability": suitability,
        "psychometric_validity_established": False,
        "deprecated_fields": {
            "suitability.irt_item_discrimination": (
                "Retained as fail-closed compatibility metadata; use "
                "suitability.exploratory_item_analysis."
            )
        },
        "interpretation": (
            "Passing this gate permits exploratory matrix analysis; it does not validate "
            "psychometric assumptions or establish construct validity."
            if status == "pass"
            else "The matrix does not meet the configured minimum adequacy checks. Dependent "
            "item-discrimination or ranking analyses must remain blocked or fixture-only."
        ),
    }


def evaluate_panel_validity(
    matrix: ResponseMatrix | pd.DataFrame,
    *,
    chance: float = 0.25,
    min_models: int = 30,
    min_items: int = 20,
    max_missing_fraction: float = 0.10,
    min_ability_spread: float = 0.20,
    near_chance_tolerance: float = 0.05,
) -> dict[str, Any]:
    """Compatibility alias for :func:`evaluate_minimum_matrix_adequacy`.

    The historical function name is retained for callers and stored artifacts. Its
    result is a feasibility gate only and must not be interpreted as evidence that
    psychometric assumptions or benchmark validity have been established.
    """

    return evaluate_minimum_matrix_adequacy(
        matrix,
        chance=chance,
        min_models=min_models,
        min_items=min_items,
        max_missing_fraction=max_missing_fraction,
        min_ability_spread=min_ability_spread,
        near_chance_tolerance=near_chance_tolerance,
    )


def write_panel_validity_report(
    matrix_path: str | Path,
    output_dir: str | Path,
    *,
    chance: float = 0.25,
    min_models: int = 30,
    min_items: int = 20,
) -> dict[str, Any]:
    frame = load_matrix_csv(matrix_path)
    payload = evaluate_panel_validity(
        frame,
        chance=chance,
        min_models=min_models,
        min_items=min_items,
    )
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "panel_validity.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (destination / "panel_validity.md").write_text(_render_panel_report(payload), encoding="utf-8")
    return payload


def write_minimum_matrix_adequacy_report(
    matrix_path: str | Path,
    output_dir: str | Path,
    *,
    chance: float = 0.25,
    min_models: int = 30,
    min_items: int = 20,
) -> dict[str, Any]:
    """Canonical writer while retaining legacy artifact filenames for compatibility."""

    return write_panel_validity_report(
        matrix_path,
        output_dir,
        chance=chance,
        min_models=min_models,
        min_items=min_items,
    )


def _series_summary(series: pd.Series) -> dict[str, Any]:
    values = series.dropna().astype(float)
    if values.empty:
        return {"n": 0, "mean": None, "std": None, "min": None, "max": None}
    return {
        "n": int(values.shape[0]),
        "mean": float(values.mean()),
        "std": float(values.std(ddof=0)),
        "min": float(values.min()),
        "max": float(values.max()),
        "p10": float(values.quantile(0.10)),
        "p90": float(values.quantile(0.90)),
    }


def _render_panel_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Minimum Matrix Adequacy Report",
        "",
        "Legacy compatibility alias: `panel_validity`.",
        "",
        f"- Status: `{payload['status']}`",
        f"- Models: {payload['n_models']}",
        f"- Items: {payload['n_items']}",
        f"- Ability spread: {payload['ability_spread']:.3f}",
        f"- Near-chance model fraction: {payload['near_chance_fraction']:.3f}",
        f"- Missing fraction: {payload['missing_fraction']:.3f}",
        "- Psychometric validity established: `false`",
        f"- Interpretation: {payload['interpretation']}",
    ]
    if payload["blockers"]:
        lines.extend(["", "## Blockers", *[f"- `{blocker}`" for blocker in payload["blockers"]]])
    if payload["warnings"]:
        lines.extend(["", "## Warnings", *[f"- {warning}" for warning in payload["warnings"]]])
    return "\n".join(lines) + "\n"
