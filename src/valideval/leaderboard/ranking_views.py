from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from valideval.leaderboard.significance import ranking_significance
from valideval.schemas import DiagnosticResult, ResponseMatrix, utc_now

RANKING_VIEW_NAMES = [
    "raw_accuracy",
    "conservative_bootstrap_accuracy",
    "irt_latent_ability",
    "reliability_adjusted_score",
    "shortcut_penalized_view",
    "prompt_stable_ranking",
    "extraction_robust_ranking",
    "contamination_risk_aware_view",
    "saturation_aware_interpretation",
    "human_validated_subset_ranking",
]


def build_ranking_views(
    matrix: ResponseMatrix,
    results: list[DiagnosticResult],
    *,
    output_dir: str | Path | None = None,
    repair_diff_path: str | Path | None = None,
    n_boot: int = 500,
    seed: int = 0,
) -> dict[str, Any]:
    by_name = {result.diagnostic_name: result for result in results}
    frame = matrix.to_dataframe().astype(float)
    raw_scores = frame.mean(axis=1).to_dict()
    significance = ranking_significance(matrix, n_boot=n_boot, seed=seed)
    bootstrap_map = _bootstrap_model_cis(matrix, n_boot=n_boot, seed=seed)
    views = {
        "raw_accuracy": _view(
            raw_scores,
            assumptions=["Ranks models by mean cached full-condition accuracy."],
            cis=bootstrap_map,
        ),
        "conservative_bootstrap_accuracy": _view(
            {model_id: bootstrap_map[model_id]["lower"] for model_id in raw_scores},
            assumptions=[
                "Ranks models by lower bootstrap confidence bound of full-condition accuracy.",
                "A conservative view may demote high-variance estimates.",
            ],
            cis=bootstrap_map,
        ),
        "irt_latent_ability": _irt_view(raw_scores, by_name.get("irt")),
        "reliability_adjusted_score": _reliability_view(raw_scores, by_name.get("reliability")),
        "shortcut_penalized_view": _shortcut_view(raw_scores, by_name.get("shortcut")),
        "prompt_stable_ranking": _prompt_stable_view(raw_scores, by_name.get("prompt_sensitivity")),
        "extraction_robust_ranking": _extraction_view(
            raw_scores, by_name.get("extraction_robustness")
        ),
        "contamination_risk_aware_view": _contamination_view(
            raw_scores, by_name.get("data_forensics")
        ),
        "saturation_aware_interpretation": _saturation_view(raw_scores, by_name.get("saturation")),
        "human_validated_subset_ranking": _human_validated_view(raw_scores, repair_diff_path),
    }
    payload = {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "benchmark_id": matrix.metadata.get("benchmark_id"),
        "panel_id": matrix.metadata.get("panel_id"),
        "views": views,
        "significance": significance,
        "warnings": [
            "Ranking views are diagnostic-sensitive sensitivity analyses, not corrected or true leaderboards.",
            "Missing-evidence warnings should be reported with any ranking view.",
        ],
    }
    if output_dir is not None:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        (output / "ranking_views.json").write_text(
            json.dumps(_json_safe(payload), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        _write_ranking_csv(output / "ranking_views.csv", views)
        (output / "ranking_significance.json").write_text(
            json.dumps(_json_safe(significance), indent=2, sort_keys=True),
            encoding="utf-8",
        )
    return payload


def _view(
    scores: dict[str, float],
    *,
    assumptions: list[str],
    cis: dict[str, dict[str, float]] | None = None,
    warnings: list[str] | None = None,
    interpretation: str | None = None,
) -> dict[str, Any]:
    ranking = [
        {
            "rank": rank,
            "model_id": model_id,
            "score": float(score),
            "ci": (cis or {}).get(model_id),
        }
        for rank, (model_id, score) in enumerate(
            sorted(scores.items(), key=lambda pair: (pair[1], pair[0]), reverse=True),
            start=1,
        )
    ]
    return {
        "ranking": ranking,
        "assumptions": assumptions,
        "missing_evidence_warnings": warnings or [],
        "interpretation": interpretation
        or "Evidence is conditional on this diagnostic view and audited protocol.",
    }


def _irt_view(raw_scores: dict[str, float], result: DiagnosticResult | None) -> dict[str, Any]:
    if not result or not result.per_model_metrics:
        return _missing_view(raw_scores, "IRT diagnostic was not available.")
    scores = {
        model_id: float(metrics.get("latent_ability_proxy", raw_scores.get(model_id, 0.0)))
        for model_id, metrics in result.per_model_metrics.items()
    }
    cis = {
        model_id: metrics.get("ability_ci")
        for model_id, metrics in result.per_model_metrics.items()
        if isinstance(metrics.get("ability_ci"), dict)
    }
    return _view(
        scores,
        assumptions=[
            "Ranks models by IRT latent-ability proxy.",
            "Proxy/Rasch/2PL estimates are diagnostic aids, not ground truth.",
        ],
        cis=cis,
        warnings=result.warnings,
    )


def _reliability_view(
    raw_scores: dict[str, float],
    result: DiagnosticResult | None,
) -> dict[str, Any]:
    if not result or not result.per_model_metrics:
        return _missing_view(raw_scores, "Reliability diagnostic was not available.")
    scores = {}
    for model_id, raw_score in raw_scores.items():
        variance = result.per_model_metrics.get(model_id, {}).get("score_variance_across_variants")
        penalty = min(float(variance or 0.0), 1.0)
        scores[model_id] = raw_score * (1.0 - penalty)
    return _view(
        scores,
        assumptions=[
            "Scales raw accuracy by score variance across available prompt variants as a sensitivity analysis.",
            "Seed and scorer reliability remain separate evidence needs when unavailable.",
        ],
        warnings=result.warnings,
    )


def _shortcut_view(raw_scores: dict[str, float], result: DiagnosticResult | None) -> dict[str, Any]:
    if not result:
        return _missing_view(raw_scores, "Shortcut diagnostic was not available.")
    variant_scores = result.summary_metrics.get("variants", {})
    if not variant_scores:
        return _missing_view(raw_scores, "Shortcut diagnostic had no ablation variants.")
    max_retention = max(
        [float(metrics.get("shortcut_retention") or 0.0) for metrics in variant_scores.values()],
        default=0.0,
    )
    penalty = min(max(max_retention - 0.5, 0.0), 1.0)
    scores = {model_id: score * (1.0 - 0.25 * penalty) for model_id, score in raw_scores.items()}
    return _view(
        scores,
        assumptions=[
            "Applies a benchmark-level diagnostic-sensitive adjustment when ablated performance remains high.",
            "This is a sensitivity analysis ranking view, not proof that a model used shortcuts and not a true ranking.",
        ],
        warnings=result.warnings,
    )


def _prompt_stable_view(
    raw_scores: dict[str, float],
    result: DiagnosticResult | None,
) -> dict[str, Any]:
    if not result or not result.per_model_metrics:
        return _missing_view(raw_scores, "Prompt-sensitivity diagnostic was not available.")
    scores = {}
    for model_id, raw_score in raw_scores.items():
        metrics = result.per_model_metrics.get(model_id, {})
        variance = float(metrics.get("score_variance_across_prompt_templates") or 0.0)
        scores[model_id] = raw_score * (1.0 - min(variance, 1.0))
    return _view(
        scores,
        assumptions=[
            "Scales scores by prompt-template variance as a sensitivity analysis.",
            "Prompt templates are those implemented by the benchmark adapter.",
        ],
        warnings=result.warnings,
    )


def _extraction_view(
    raw_scores: dict[str, float],
    result: DiagnosticResult | None,
) -> dict[str, Any]:
    if not result:
        return _missing_view(raw_scores, "Extraction robustness diagnostic was not available.")
    per_model = result.per_model_metrics or {}
    strict_scores = {
        model_id: float(metrics.get("strict_score", raw_scores.get(model_id, 0.0)))
        for model_id, metrics in per_model.items()
    }
    if not strict_scores:
        strict_scores = raw_scores
    return _view(
        strict_scores,
        assumptions=[
            "Ranks by strict extraction score when cached raw outputs are available.",
            "Extractor disagreement is a scoring-validity signal, not a final truth.",
        ],
        warnings=result.warnings,
    )


def _contamination_view(
    raw_scores: dict[str, float],
    result: DiagnosticResult | None,
) -> dict[str, Any]:
    if not result:
        return _missing_view(raw_scores, "Data-forensics diagnostic was not available.")
    overlap = result.summary_metrics.get("signals", {}).get("corpus_overlap", {})
    risk = overlap.get("risk_level")
    penalty = {
        "no local evidence found": 0.0,
        "low local evidence": 0.03,
        "moderate local evidence": 0.08,
        "high local evidence": 0.15,
    }.get(risk, 0.0)
    scores = {model_id: score * (1.0 - penalty) for model_id, score in raw_scores.items()}
    warnings = list(result.warnings)
    if overlap.get("status") in {"unavailable", "insufficient_corpus"}:
        warnings.append(
            "Corpus overlap evidence is unavailable or insufficient; do not claim cleanliness."
        )
    return _view(
        scores,
        assumptions=[
            "Applies only benchmark-level local-overlap risk context.",
            "No local overlap is not proof of contamination cleanliness.",
        ],
        warnings=warnings,
    )


def _saturation_view(
    raw_scores: dict[str, float], result: DiagnosticResult | None
) -> dict[str, Any]:
    if not result:
        return _missing_view(raw_scores, "Saturation diagnostic was not available.")
    category = result.summary_metrics.get("saturation_category", "unknown")
    return _view(
        raw_scores,
        assumptions=[
            "Ranking order is raw accuracy, annotated with saturation evidence.",
            "When saturated, small top-model differences require extra caution.",
        ],
        warnings=result.warnings,
        interpretation=f"Saturation category under this panel: {category}.",
    )


def _human_validated_view(
    raw_scores: dict[str, float],
    repair_diff_path: str | Path | None,
) -> dict[str, Any]:
    warnings = ["Human-validated subset evidence was not available; falling back to raw accuracy."]
    if repair_diff_path and Path(repair_diff_path).exists():
        payload = json.loads(Path(repair_diff_path).read_text(encoding="utf-8"))
        selection = payload.get("selection", {})
        if selection.get("selected_item_ids"):
            warnings = [
                "Using repaired subset as an audit aid; this is not a human-validated subset unless human validation is documented."
            ]
    return _view(
        raw_scores,
        assumptions=[
            "Uses human-validated subset scores when documented.",
            "In the offline toy audit this view reports missing human-validation evidence.",
        ],
        warnings=warnings,
    )


def _missing_view(raw_scores: dict[str, float], reason: str) -> dict[str, Any]:
    return _view(
        raw_scores,
        assumptions=["Falls back to raw accuracy because required evidence is missing."],
        warnings=[reason],
    )


def _bootstrap_model_cis(
    matrix: ResponseMatrix,
    *,
    n_boot: int,
    seed: int,
) -> dict[str, dict[str, float]]:
    frame = matrix.to_dataframe().astype(float)
    rng = np.random.default_rng(seed)
    item_ids = list(frame.columns)
    output: dict[str, dict[str, float]] = {}
    for model_id in frame.index:
        values = []
        for _ in range(n_boot):
            sampled = rng.choice(item_ids, size=len(item_ids), replace=True).tolist()
            values.append(float(frame.loc[model_id, sampled].mean()))
        output[model_id] = {
            "estimate": float(frame.loc[model_id].mean()),
            "lower": float(np.quantile(values, 0.025)),
            "upper": float(np.quantile(values, 0.975)),
            "n": n_boot,
        }
    return output


def _write_ranking_csv(path: Path, views: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["view", "rank", "model_id", "score"])
        writer.writeheader()
        for view_name, view in views.items():
            for row in view["ranking"]:
                writer.writerow(
                    {
                        "view": view_name,
                        "rank": row["rank"],
                        "model_id": row["model_id"],
                        "score": row["score"],
                    }
                )


def _json_safe(value: Any) -> Any:
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, np.floating):
        item = float(value)
        return None if math.isnan(item) or math.isinf(item) else item
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value
