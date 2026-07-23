from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from valideval.diagnostics.panel_validity import evaluate_panel_validity, load_matrix_csv
from valideval.psychometrics.irt_models import (
    estimate_2pl_proxy,
    estimate_irt_proxy,
    estimate_rasch_1pl,
)
from valideval.schemas import ResponseMatrix


def fit_irt_from_matrix(
    matrix_path: str | Path,
    output_dir: str | Path,
    *,
    model: str = "2pl",
    chance: float = 0.25,
    min_models: int = 30,
    min_items: int = 20,
) -> dict[str, Any]:
    frame = load_matrix_csv(matrix_path)
    matrix = ResponseMatrix.from_dataframe(frame, metadata={"source_matrix": str(matrix_path)})
    panel = evaluate_panel_validity(
        frame,
        chance=chance,
        min_models=min_models,
        min_items=min_items,
    )
    proxy = estimate_irt_proxy(matrix)
    rasch = (
        estimate_rasch_1pl(matrix)
        if model in {"1pl", "2pl"}
        else {
            "available": False,
            "warnings": ["Rasch/1PL fit skipped because --model proxy was requested."],
        }
    )
    two_pl = (
        estimate_2pl_proxy(matrix)
        if model == "2pl"
        else {
            "available": False,
            "warnings": ["2PL proxy skipped because --model proxy was requested."],
            "item_slopes": {},
        }
    )
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    item_rows = []
    for item_id, stats in proxy["item_stats"].items():
        item_rows.append(
            {
                "item_id": item_id,
                "proportion_correct": stats.get("proportion_correct"),
                "difficulty_proxy": stats.get("difficulty"),
                "discrimination_proxy": stats.get("discrimination"),
                "rasch_difficulty": rasch.get("item_difficulties", {}).get(item_id),
                "two_pl_slope_proxy": two_pl.get("item_slopes", {}).get(item_id),
                "information_proxy": stats.get("information_proxy"),
                "negative_discrimination": stats.get("negative_discrimination"),
                "near_zero_discrimination": stats.get("near_zero_discrimination"),
                "too_easy": stats.get("too_easy"),
                "too_hard": stats.get("too_hard"),
                "discrimination_basis": stats.get("discrimination_basis"),
                "label": stats.get("discrimination_label"),
            }
        )
    model_rows = [
        {
            "model_id": model_id,
            "ability_proxy": ability,
            "rasch_ability": rasch.get("model_abilities", {}).get(model_id),
        }
        for model_id, ability in proxy["model_abilities"].items()
    ]
    pd.DataFrame(item_rows).to_csv(destination / "item_parameters.csv", index=False)
    pd.DataFrame(model_rows).to_csv(destination / "model_abilities.csv", index=False)
    flags = [
        {
            "benchmark": "wide_matrix",
            "subset": "default",
            "item_id": row["item_id"],
            "diagnostic": "irt_2pl_proxy",
            "score": max(0.0, 1.0 - abs(float(row["discrimination_proxy"] or 0.0))),
            "severity": "medium"
            if row["label"] in {"low_discrimination", "negative_discrimination"}
            else "low",
            "direction": "higher_is_more_suspicious",
            "evidence_summary": f"IRT proxy label: {row['label']}",
        }
        for row in item_rows
    ]
    (destination / "flags.jsonl").write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in flags) + ("\n" if flags else ""),
        encoding="utf-8",
    )
    payload = {
        "schema_version": "0.1",
        "status": "ok" if panel["status"] == "pass" else "proxy_only_blocked_panel",
        "requested_model": model,
        "matrix_path": str(matrix_path),
        "panel_validity": panel,
        "estimation_layers": {
            "proxy": True,
            "rasch_1pl": bool(rasch.get("available")),
            "two_pl_proxy": bool(two_pl.get("available")),
            "full_parametric_2pl": False,
        },
        "convergence": {
            "proxy": "closed_form_no_iteration",
            "rasch_1pl": {
                "available": bool(rasch.get("available")),
                "converged": rasch.get("converged"),
            },
            "two_pl_proxy": "proxy_slope_export_only"
            if two_pl.get("available")
            else "not_run_or_unavailable",
            "full_parametric_2pl": "not_run",
        },
        "item_parameter_summary": _item_parameter_summary(item_rows),
        "model_ability_summary": _numeric_summary([row["ability_proxy"] for row in model_rows]),
        "warnings": [
            *rasch.get("warnings", []),
            *two_pl.get("warnings", []),
            "No paid APIs or LLM generation are used. Full parametric 2PL is not claimed unless an external dependency is explicitly added and validated.",
        ],
        "artifacts": {
            "item_parameters": str(destination / "item_parameters.csv"),
            "model_abilities": str(destination / "model_abilities.csv"),
            "flags": str(destination / "flags.jsonl"),
            "summary": str(destination / "fit_summary.md"),
        },
    }
    (destination / "fit_summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (destination / "fit_summary.md").write_text(render_irt_summary(payload), encoding="utf-8")
    return payload


def render_irt_summary(payload: dict[str, Any]) -> str:
    panel = payload["panel_validity"]
    return (
        "\n".join(
            [
                "# Wide-Matrix IRT Fit Summary",
                "",
                f"- Status: `{payload['status']}`",
                f"- Requested model: `{payload['requested_model']}`",
                f"- Models: {panel['n_models']}",
                f"- Items: {panel['n_items']}",
                f"- Panel validity: `{panel['status']}`",
                "",
                "The default output is a proxy/Rasch/2PL-proxy report. Treat item-level claims as blocked unless panel validity passes.",
                "",
                "## Proxy Distributions",
                "",
                f"- Negative discrimination items: {payload['item_parameter_summary']['negative_discrimination_count']}",
                f"- Near-zero discrimination items: {payload['item_parameter_summary']['near_zero_discrimination_count']}",
                f"- Extreme difficulty items: {payload['item_parameter_summary']['extreme_difficulty_count']}",
                f"- Full parametric 2PL: `{payload['estimation_layers']['full_parametric_2pl']}`",
            ]
        )
        + "\n"
    )


def _item_parameter_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    difficulty = [row.get("difficulty_proxy") for row in rows]
    discrimination = [row.get("discrimination_proxy") for row in rows]
    return {
        "difficulty_proxy": _numeric_summary(difficulty),
        "discrimination_proxy": _numeric_summary(discrimination),
        "negative_discrimination_count": sum(
            1 for row in rows if bool(row.get("negative_discrimination"))
        ),
        "near_zero_discrimination_count": sum(
            1 for row in rows if bool(row.get("near_zero_discrimination"))
        ),
        "extreme_difficulty_count": sum(
            1 for row in rows if bool(row.get("too_easy")) or bool(row.get("too_hard"))
        ),
    }


def _numeric_summary(values: list[Any]) -> dict[str, Any]:
    series = pd.Series([float(value) for value in values if value is not None]).dropna()
    if series.empty:
        return {"n": 0}
    quantiles = series.quantile([0.1, 0.25, 0.5, 0.75, 0.9])
    return {
        "n": int(series.shape[0]),
        "mean": float(series.mean()),
        "std": float(series.std(ddof=0)),
        "min": float(series.min()),
        "p10": float(quantiles.loc[0.1]),
        "p25": float(quantiles.loc[0.25]),
        "median": float(quantiles.loc[0.5]),
        "p75": float(quantiles.loc[0.75]),
        "p90": float(quantiles.loc[0.9]),
        "max": float(series.max()),
    }
