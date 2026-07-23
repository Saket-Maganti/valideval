from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class MatrixBundle:
    frame: pd.DataFrame
    item_metadata: pd.DataFrame


def run_real_panel_ranking_audit(
    *,
    matrix: str | Path,
    predictions: str | Path | None,
    output: str | Path,
) -> dict[str, Any]:
    bundle = load_response_matrix(matrix)
    output_dir, json_path = _resolve_output(output, "real_panel_ranking_audit.json")
    output_dir.mkdir(parents=True, exist_ok=True)

    ranking = accuracy_ranking(bundle.frame)
    ranking_path = output_dir / "accuracy_ranking.csv"
    ranking.to_csv(ranking_path, index=False)

    ability_spread = float(ranking["accuracy"].max() - ranking["accuracy"].min())
    payload = {
        "schema_version": "0.1",
        "status": "ok",
        "analysis": "real_panel_ranking_audit",
        "evidence_state": "ARTIFACT_BACKED_REAL_PANEL_ANALYSIS",
        "matrix_path": str(matrix),
        "predictions_input": summarize_predictions(predictions),
        "panel_shape": panel_shape(bundle),
        "ability_spread": ability_spread,
        "top_models": ranking.head(10).to_dict(orient="records"),
        "artifacts": {
            "accuracy_ranking": str(ranking_path),
            "summary": str(output_dir / "real_panel_ranking_audit.md"),
        },
        "claim_limits": CLAIM_LIMITS,
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "real_panel_ranking_audit.md").write_text(
        render_ranking_audit(payload), encoding="utf-8"
    )
    return payload


def run_subject_instability_audit(
    *,
    matrix: str | Path,
    predictions: str | Path | None,
    output: str | Path,
) -> dict[str, Any]:
    bundle = load_response_matrix(matrix)
    output_dir, json_path = _resolve_output(output, "subject_instability_audit.json")
    output_dir.mkdir(parents=True, exist_ok=True)

    subject_rankings, instability, pairwise = subject_instability(
        bundle.frame, bundle.item_metadata
    )
    subject_rankings_path = output_dir / "subject_rankings.csv"
    instability_path = output_dir / "subject_instability.csv"
    pairwise_path = output_dir / "pairwise_subject_rank_flips.csv"
    subject_rankings.to_csv(subject_rankings_path, index=False)
    instability.to_csv(instability_path, index=False)
    pairwise.to_csv(pairwise_path, index=False)

    payload = {
        "schema_version": "0.1",
        "status": "ok",
        "analysis": "subject_instability_audit",
        "evidence_state": "ARTIFACT_BACKED_REAL_PANEL_ANALYSIS",
        "matrix_path": str(matrix),
        "predictions_input": summarize_predictions(predictions),
        "panel_shape": panel_shape(bundle),
        "subject_count": int(bundle.item_metadata["subject"].nunique()),
        "max_subject_rank_range": float(instability["subject_rank_range"].max())
        if not instability.empty
        else 0.0,
        "models_with_subject_rank_range_ge_3": int((instability["subject_rank_range"] >= 3).sum())
        if not instability.empty
        else 0,
        "top_instability": instability.head(10).to_dict(orient="records"),
        "artifacts": {
            "subject_rankings": str(subject_rankings_path),
            "subject_instability": str(instability_path),
            "pairwise_rank_flips": str(pairwise_path),
            "summary": str(output_dir / "subject_instability_audit.md"),
        },
        "claim_limits": CLAIM_LIMITS,
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "subject_instability_audit.md").write_text(
        render_subject_instability(payload), encoding="utf-8"
    )
    return payload


def run_diagnostic_disagreement_audit(
    *,
    matrix: str | Path,
    predictions: str | Path | None,
    output: str | Path,
    irt: str | Path | None = None,
) -> dict[str, Any]:
    bundle = load_response_matrix(matrix)
    item_metrics = load_item_metrics(irt, bundle)
    output_dir, json_path = _resolve_output(output, "diagnostic_disagreement_audit.json")
    output_dir.mkdir(parents=True, exist_ok=True)

    disagreement = diagnostic_disagreement(bundle.frame, item_metrics)
    rank_shift_path = output_dir / "accuracy_vs_diagnostic_rank_shift.csv"
    subset_path = output_dir / "suspicious_subset_sensitivity.csv"
    disagreement["rank_shift"].to_csv(rank_shift_path, index=False)
    disagreement["subset_sensitivity"].to_csv(subset_path, index=False)

    payload = {
        "schema_version": "0.1",
        "status": "ok",
        "analysis": "diagnostic_disagreement_audit",
        "evidence_state": "ARTIFACT_BACKED_REAL_PANEL_ANALYSIS",
        "matrix_path": str(matrix),
        "predictions_input": summarize_predictions(predictions),
        "panel_shape": panel_shape(bundle),
        "diagnostic_source": item_metrics["source"],
        "diagnostic_source_is_irt_proxy": bool(item_metrics["source_is_irt_proxy"]),
        "rank_correlation": disagreement["rank_correlation"],
        "max_abs_rank_delta": disagreement["max_abs_rank_delta"],
        "models_with_abs_rank_delta_ge_3": disagreement["models_with_abs_rank_delta_ge_3"],
        "top_rank_shifts": disagreement["rank_shift"].head(10).to_dict(orient="records"),
        "artifacts": {
            "rank_shift": str(rank_shift_path),
            "suspicious_subset_sensitivity": str(subset_path),
            "summary": str(output_dir / "diagnostic_disagreement_audit.md"),
        },
        "claim_limits": CLAIM_LIMITS,
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "diagnostic_disagreement_audit.md").write_text(
        render_diagnostic_disagreement(payload), encoding="utf-8"
    )
    return payload


def run_ranking_disagreement(
    *,
    matrix: str | Path,
    output: str | Path,
    irt: str | Path | None = None,
    bootstrap: int = 1000,
    seed: int = 20260708,
) -> dict[str, Any]:
    bundle = load_response_matrix(matrix)
    item_metrics = load_item_metrics(irt, bundle)
    output_dir, json_path = _resolve_output(output, "ranking_disagreement_summary.json")
    output_dir.mkdir(parents=True, exist_ok=True)

    ranking = accuracy_ranking(bundle.frame)
    subject_rankings, instability, pairwise = subject_instability(
        bundle.frame, bundle.item_metadata
    )
    disagreement = diagnostic_disagreement(bundle.frame, item_metrics)
    baseline = compute_real_panel_baselines(
        bundle=bundle,
        output_dir=output_dir,
        bootstrap=bootstrap,
        seed=seed,
        write_artifacts=False,
    )
    materiality = materiality_thresholds(
        disagreement["rank_shift"], instability, baseline["iterations"]
    )

    paths = {
        "accuracy_ranking": output_dir / "accuracy_ranking.csv",
        "subject_rankings": output_dir / "subject_rankings.csv",
        "subject_instability": output_dir / "subject_instability.csv",
        "pairwise_rank_flips": output_dir / "pairwise_subject_rank_flips.csv",
        "rank_shift": output_dir / "accuracy_vs_diagnostic_rank_shift.csv",
        "subset_sensitivity": output_dir / "suspicious_subset_sensitivity.csv",
        "baseline_comparison": output_dir / "baseline_comparison.csv",
        "baseline_iterations": output_dir / "baseline_iterations.csv",
        "materiality": output_dir / "materiality_thresholds.csv",
    }
    ranking.to_csv(paths["accuracy_ranking"], index=False)
    subject_rankings.to_csv(paths["subject_rankings"], index=False)
    instability.to_csv(paths["subject_instability"], index=False)
    pairwise.to_csv(paths["pairwise_rank_flips"], index=False)
    disagreement["rank_shift"].to_csv(paths["rank_shift"], index=False)
    disagreement["subset_sensitivity"].to_csv(paths["subset_sensitivity"], index=False)
    baseline["comparison"].to_csv(paths["baseline_comparison"], index=False)
    baseline["iterations"].to_csv(paths["baseline_iterations"], index=False)
    materiality.to_csv(paths["materiality"], index=False)

    payload = {
        "schema_version": "0.1",
        "status": "ok",
        "analysis": "ranking_disagreement",
        "evidence_state": "ARTIFACT_BACKED_REAL_PANEL_ANALYSIS",
        "matrix_path": str(matrix),
        "panel_shape": panel_shape(bundle),
        "diagnostic_source": item_metrics["source"],
        "diagnostic_source_is_irt_proxy": bool(item_metrics["source_is_irt_proxy"]),
        "rank_correlation": disagreement["rank_correlation"],
        "max_abs_diagnostic_rank_delta": disagreement["max_abs_rank_delta"],
        "max_subject_rank_range": float(instability["subject_rank_range"].max())
        if not instability.empty
        else 0.0,
        "bootstrap": baseline["summary"],
        "materiality": materiality.to_dict(orient="records"),
        "artifacts": {key: str(path) for key, path in paths.items()}
        | {"summary": str(output_dir / "ranking_disagreement_summary.md")},
        "claim_limits": CLAIM_LIMITS,
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "ranking_disagreement_summary.md").write_text(
        render_ranking_disagreement(payload), encoding="utf-8"
    )
    return payload


def run_real_panel_baselines(
    *,
    matrix: str | Path,
    output: str | Path,
    bootstrap: int = 1000,
    seed: int = 20260708,
) -> dict[str, Any]:
    bundle = load_response_matrix(matrix)
    output_dir, json_path = _resolve_output(output, "baseline_summary.json")
    output_dir.mkdir(parents=True, exist_ok=True)
    baseline = compute_real_panel_baselines(
        bundle=bundle,
        output_dir=output_dir,
        bootstrap=bootstrap,
        seed=seed,
        write_artifacts=True,
    )
    payload = {
        "schema_version": "0.1",
        "status": "ok",
        "analysis": "real_panel_baselines",
        "evidence_state": "ARTIFACT_BACKED_REAL_PANEL_ANALYSIS",
        "matrix_path": str(matrix),
        "panel_shape": panel_shape(bundle),
        "bootstrap": baseline["summary"],
        "baselines": baseline["comparison"].to_dict(orient="records"),
        "artifacts": {
            "comparison": str(output_dir / "baseline_comparison.csv"),
            "iterations": str(output_dir / "baseline_iterations.csv"),
            "summary": str(output_dir / "real_panel_baseline_comparison.md"),
        },
        "claim_limits": CLAIM_LIMITS,
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "real_panel_baseline_comparison.md").write_text(
        render_baseline_summary(payload), encoding="utf-8"
    )
    return payload


def load_response_matrix(matrix: str | Path) -> MatrixBundle:
    raw = pd.read_csv(matrix)
    if raw.empty:
        raise ValueError(f"Matrix is empty: {matrix}")

    if "model_id" in raw.columns:
        frame = raw.set_index("model_id")
    elif "model" in raw.columns:
        frame = raw.set_index("model")
        frame.index.name = "model_id"
    elif raw.columns[0] in {"item_id", "item", "question_id", "instance_id"}:
        frame = raw.set_index(raw.columns[0]).transpose()
        frame.index.name = "model_id"
    else:
        frame = raw.set_index(raw.columns[0])
        frame.index.name = "model_id"

    frame.index = frame.index.astype(str)
    frame.columns = frame.columns.astype(str)
    numeric = frame.apply(pd.to_numeric, errors="coerce")
    item_metadata = pd.DataFrame(
        [_split_item_column(column) for column in numeric.columns],
        columns=["column", "subject", "item_id"],
    )
    return MatrixBundle(frame=numeric, item_metadata=item_metadata)


def accuracy_ranking(frame: pd.DataFrame) -> pd.DataFrame:
    scores = frame.mean(axis=1, skipna=True)
    ranks = scores.rank(ascending=False, method="min")
    return (
        pd.DataFrame(
            {
                "model_id": scores.index,
                "accuracy": scores.to_numpy(dtype=float),
                "accuracy_rank": ranks.to_numpy(dtype=float),
            }
        )
        .sort_values(["accuracy_rank", "model_id"])
        .reset_index(drop=True)
    )


def subject_instability(
    frame: pd.DataFrame,
    item_metadata: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    full_scores = frame.mean(axis=1, skipna=True)
    full_ranks = full_scores.rank(ascending=False, method="min")
    subject_rows: list[dict[str, Any]] = []
    pairwise_counts: dict[tuple[str, str], int] = {}

    for subject, rows in item_metadata.groupby("subject", sort=True):
        columns = rows["column"].tolist()
        if not columns:
            continue
        scores = frame[columns].mean(axis=1, skipna=True)
        ranks = scores.rank(ascending=False, method="min")
        for model_id in frame.index:
            subject_rows.append(
                {
                    "subject": subject,
                    "model_id": model_id,
                    "subject_accuracy": float(scores.loc[model_id]),
                    "subject_rank": float(ranks.loc[model_id]),
                    "full_accuracy": float(full_scores.loc[model_id]),
                    "full_rank": float(full_ranks.loc[model_id]),
                    "rank_delta_vs_full": float(ranks.loc[model_id] - full_ranks.loc[model_id]),
                    "n_items": int(len(columns)),
                }
            )
        _count_pairwise_flips(pairwise_counts, full_ranks, ranks)

    subject_rankings = pd.DataFrame(subject_rows)
    if subject_rankings.empty:
        instability = pd.DataFrame(
            columns=[
                "model_id",
                "full_rank",
                "best_subject_rank",
                "worst_subject_rank",
                "subject_rank_range",
                "subject_rank_std",
                "mean_abs_delta_vs_full",
                "max_abs_delta_vs_full",
            ]
        )
    else:
        grouped = subject_rankings.groupby("model_id")
        instability = pd.DataFrame(
            {
                "model_id": grouped["subject_rank"].min().index,
                "full_rank": grouped["full_rank"].first().to_numpy(dtype=float),
                "best_subject_rank": grouped["subject_rank"].min().to_numpy(dtype=float),
                "worst_subject_rank": grouped["subject_rank"].max().to_numpy(dtype=float),
                "subject_rank_range": (
                    grouped["subject_rank"].max() - grouped["subject_rank"].min()
                ).to_numpy(dtype=float),
                "subject_rank_std": grouped["subject_rank"]
                .std(ddof=0)
                .fillna(0)
                .to_numpy(dtype=float),
                "mean_abs_delta_vs_full": grouped["rank_delta_vs_full"]
                .apply(lambda values: values.abs().mean())
                .to_numpy(dtype=float),
                "max_abs_delta_vs_full": grouped["rank_delta_vs_full"]
                .apply(lambda values: values.abs().max())
                .to_numpy(dtype=float),
            }
        ).sort_values(
            ["subject_rank_range", "max_abs_delta_vs_full", "model_id"],
            ascending=[False, False, True],
        )
    pairwise = pd.DataFrame(
        [
            {
                "model_a": model_a,
                "model_b": model_b,
                "subject_flip_count_vs_full": count,
            }
            for (model_a, model_b), count in pairwise_counts.items()
        ],
        columns=["model_a", "model_b", "subject_flip_count_vs_full"],
    )
    if not pairwise.empty:
        pairwise = pairwise.sort_values(
            ["subject_flip_count_vs_full", "model_a", "model_b"], ascending=[False, True, True]
        )
    return subject_rankings, instability.reset_index(drop=True), pairwise.reset_index(drop=True)


def diagnostic_disagreement(
    frame: pd.DataFrame,
    item_metrics: dict[str, Any],
) -> dict[str, Any]:
    full_scores = frame.mean(axis=1, skipna=True)
    full_ranks = full_scores.rank(ascending=False, method="min")
    weights = pd.Series(item_metrics["weights"], index=frame.columns, dtype=float)
    weight_sum = float(weights.sum())
    if weight_sum <= 0:
        weighted_scores = full_scores.copy()
    else:
        weighted_scores = frame.mul(weights, axis=1).sum(axis=1, skipna=True) / weight_sum
    weighted_ranks = weighted_scores.rank(ascending=False, method="min")

    suspicious_columns = [
        column
        for column, suspicious in zip(frame.columns, item_metrics["suspicious"], strict=False)
        if bool(suspicious)
    ]
    clean_columns = [column for column in frame.columns if column not in set(suspicious_columns)]
    suspicious_scores = (
        frame[suspicious_columns].mean(axis=1, skipna=True)
        if suspicious_columns
        else pd.Series(np.nan, index=frame.index)
    )
    clean_scores = (
        frame[clean_columns].mean(axis=1, skipna=True)
        if clean_columns
        else pd.Series(np.nan, index=frame.index)
    )

    rank_shift = pd.DataFrame(
        {
            "model_id": frame.index,
            "accuracy": full_scores.to_numpy(dtype=float),
            "accuracy_rank": full_ranks.to_numpy(dtype=float),
            "diagnostic_weighted_score": weighted_scores.to_numpy(dtype=float),
            "diagnostic_weighted_rank": weighted_ranks.to_numpy(dtype=float),
            "rank_delta_diagnostic_minus_accuracy": (weighted_ranks - full_ranks).to_numpy(
                dtype=float
            ),
            "abs_rank_delta": (weighted_ranks - full_ranks).abs().to_numpy(dtype=float),
        }
    ).sort_values(["abs_rank_delta", "model_id"], ascending=[False, True])

    subset_sensitivity = pd.DataFrame(
        {
            "model_id": frame.index,
            "accuracy_all_items": full_scores.to_numpy(dtype=float),
            "accuracy_suspicious_items": suspicious_scores.to_numpy(dtype=float),
            "accuracy_proxy_clean_items": clean_scores.to_numpy(dtype=float),
            "suspicious_minus_clean_accuracy": (suspicious_scores - clean_scores).to_numpy(
                dtype=float
            ),
            "n_suspicious_items": int(len(suspicious_columns)),
            "n_proxy_clean_items": int(len(clean_columns)),
        }
    ).sort_values(["suspicious_minus_clean_accuracy", "model_id"], ascending=[True, True])

    return {
        "rank_shift": rank_shift.reset_index(drop=True),
        "subset_sensitivity": subset_sensitivity.reset_index(drop=True),
        "rank_correlation": {
            "spearman_accuracy_vs_diagnostic_weighted": _corr(
                full_ranks, weighted_ranks, method="spearman"
            ),
            "kendall_accuracy_vs_diagnostic_weighted": _corr(
                full_ranks, weighted_ranks, method="kendall"
            ),
        },
        "max_abs_rank_delta": float(rank_shift["abs_rank_delta"].max())
        if not rank_shift.empty
        else 0.0,
        "models_with_abs_rank_delta_ge_3": int((rank_shift["abs_rank_delta"] >= 3).sum())
        if not rank_shift.empty
        else 0,
    }


def compute_real_panel_baselines(
    *,
    bundle: MatrixBundle,
    output_dir: str | Path,
    bootstrap: int,
    seed: int,
    write_artifacts: bool,
) -> dict[str, Any]:
    frame = bundle.frame
    rng = np.random.default_rng(seed)
    values = frame.to_numpy(dtype=float)
    n_models, n_items = values.shape
    full_scores = np.nanmean(values, axis=1)
    full_ranks = _rank_desc(full_scores)
    top5 = set(np.argsort(full_scores)[::-1][: min(5, n_models)].tolist())
    subject_groups = [
        group.index.to_numpy(dtype=int)
        for _, group in bundle.item_metadata.reset_index().groupby("subject", sort=True)
    ]

    rows: list[dict[str, Any]] = []
    for iteration in range(int(bootstrap)):
        random_indices = rng.integers(0, n_items, size=n_items)
        random_scores = np.nanmean(values[:, random_indices], axis=1)
        rows.append(
            _baseline_iteration_row(
                baseline="random_item_bootstrap",
                iteration=iteration,
                scores=random_scores,
                full_scores=full_scores,
                full_ranks=full_ranks,
                top5=top5,
            )
        )

        stratified_indices = np.concatenate(
            [
                rng.choice(group, size=len(group), replace=True)
                for group in subject_groups
                if len(group)
            ]
        )
        stratified_scores = np.nanmean(values[:, stratified_indices], axis=1)
        rows.append(
            _baseline_iteration_row(
                baseline="subject_stratified_bootstrap",
                iteration=iteration,
                scores=stratified_scores,
                full_scores=full_scores,
                full_ranks=full_ranks,
                top5=top5,
            )
        )

    iterations = pd.DataFrame(rows)
    comparison = (
        iterations.groupby("baseline")
        .agg(
            iterations=("iteration", "count"),
            mean_spearman_vs_full=("spearman_vs_full", "mean"),
            p05_spearman_vs_full=("spearman_vs_full", lambda x: float(x.quantile(0.05))),
            p50_spearman_vs_full=("spearman_vs_full", "median"),
            p95_spearman_vs_full=("spearman_vs_full", lambda x: float(x.quantile(0.95))),
            mean_top5_overlap=("top5_overlap", "mean"),
            p05_top5_overlap=("top5_overlap", lambda x: float(x.quantile(0.05))),
            mean_max_abs_rank_delta=("max_abs_rank_delta", "mean"),
            p95_max_abs_rank_delta=("max_abs_rank_delta", lambda x: float(x.quantile(0.95))),
            top1_match_rate=("top1_match", "mean"),
        )
        .reset_index()
    )
    comparison = pd.concat(
        [
            comparison,
            pd.DataFrame(
                [
                    {
                        "baseline": "naive_difficulty_only",
                        "iterations": 0,
                        "mean_spearman_vs_full": np.nan,
                        "p05_spearman_vs_full": np.nan,
                        "p50_spearman_vs_full": np.nan,
                        "p95_spearman_vs_full": np.nan,
                        "mean_top5_overlap": np.nan,
                        "p05_top5_overlap": np.nan,
                        "mean_max_abs_rank_delta": np.nan,
                        "p95_max_abs_rank_delta": np.nan,
                        "top1_match_rate": np.nan,
                        "note": "Item difficulty alone is not a model ranking baseline.",
                    },
                    {
                        "baseline": "naive_model_disagreement",
                        "iterations": 0,
                        "mean_spearman_vs_full": np.nan,
                        "p05_spearman_vs_full": np.nan,
                        "p50_spearman_vs_full": np.nan,
                        "p95_spearman_vs_full": np.nan,
                        "mean_top5_overlap": np.nan,
                        "p05_top5_overlap": np.nan,
                        "mean_max_abs_rank_delta": np.nan,
                        "p95_max_abs_rank_delta": np.nan,
                        "top1_match_rate": np.nan,
                        "note": "Model disagreement is reported as an item diagnostic, not an external label.",
                    },
                ]
            ),
        ],
        ignore_index=True,
    )
    if write_artifacts:
        destination = Path(output_dir)
        comparison.to_csv(destination / "baseline_comparison.csv", index=False)
        iterations.to_csv(destination / "baseline_iterations.csv", index=False)

    summary = {
        "bootstrap_iterations_per_resampling_baseline": int(bootstrap),
        "seed": int(seed),
        "n_models": int(n_models),
        "n_items": int(n_items),
        "top_k_for_overlap": int(min(5, n_models)),
    }
    return {"comparison": comparison, "iterations": iterations, "summary": summary}


def materiality_thresholds(
    rank_shift: pd.DataFrame,
    instability: pd.DataFrame,
    baseline_iterations: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    for threshold in [1, 3, 5, 10]:
        rows.append(
            {
                "threshold": f"absolute_rank_delta_ge_{threshold}",
                "diagnostic_models": int((rank_shift["abs_rank_delta"] >= threshold).sum())
                if not rank_shift.empty
                else 0,
                "subject_instability_models": int(
                    (instability["subject_rank_range"] >= threshold).sum()
                )
                if not instability.empty
                else 0,
                "bootstrap_iteration_rate_random": _threshold_rate(
                    baseline_iterations,
                    "random_item_bootstrap",
                    threshold,
                ),
                "bootstrap_iteration_rate_subject_stratified": _threshold_rate(
                    baseline_iterations,
                    "subject_stratified_bootstrap",
                    threshold,
                ),
            }
        )
    return pd.DataFrame(rows)


def load_item_metrics(irt: str | Path | None, bundle: MatrixBundle) -> dict[str, Any]:
    metric_path = resolve_item_metric_path(irt)
    if metric_path is None:
        return derived_item_metrics(bundle)

    metrics = pd.read_csv(metric_path)
    if "item_id" not in metrics.columns:
        return derived_item_metrics(bundle)
    metrics["item_id"] = metrics["item_id"].astype(str)
    by_full = metrics.set_index("item_id", drop=False)
    plain = metrics.assign(_plain_item_id=metrics["item_id"].map(_plain_item_id)).set_index(
        "_plain_item_id",
        drop=False,
    )

    weights: list[float] = []
    suspicious: list[bool] = []
    matched = 0
    for _, row in bundle.item_metadata.iterrows():
        metric_row = None
        if row["column"] in by_full.index:
            metric_row = by_full.loc[row["column"]]
        elif row["item_id"] in plain.index:
            metric_row = plain.loc[row["item_id"]]
        if isinstance(metric_row, pd.DataFrame):
            metric_row = metric_row.iloc[0]
        if metric_row is None:
            weights.append(1.0)
            suspicious.append(False)
            continue
        matched += 1
        discrimination = _float_or_none(metric_row.get("discrimination_proxy"))
        information = _float_or_none(metric_row.get("information_proxy"))
        weights.append(max(discrimination or 0.0, 0.0) or max(information or 0.0, 0.0))
        suspicious.append(
            any(
                _as_bool(metric_row.get(field))
                for field in [
                    "negative_discrimination",
                    "near_zero_discrimination",
                    "too_easy",
                    "too_hard",
                ]
            )
        )
    if float(np.nansum(weights)) <= 0:
        weights = [1.0 for _ in weights]
    return {
        "source": str(metric_path),
        "source_is_irt_proxy": True,
        "matched_items": matched,
        "weights": weights,
        "suspicious": suspicious,
    }


def resolve_item_metric_path(irt: str | Path | None) -> Path | None:
    candidates: list[Path] = []
    if irt is not None:
        path = Path(irt)
        candidates.append(path / "item_parameters.csv" if path.is_dir() else path)
    candidates.extend(
        [
            Path("results/mmlu/irt_proxy/item_parameters.csv"),
            Path("results/mmlu/irt/item_parameters.csv"),
            Path("results/mmlu/irt_2pl/item_parameters.csv"),
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def derived_item_metrics(bundle: MatrixBundle) -> dict[str, Any]:
    item_accuracy = bundle.frame.mean(axis=0, skipna=True)
    disagreement = item_accuracy * (1.0 - item_accuracy)
    suspicious = (
        (item_accuracy <= 0.05)
        | (item_accuracy >= 0.95)
        | (disagreement <= disagreement.quantile(0.1))
    )
    weights = disagreement.fillna(0.0).to_numpy(dtype=float).tolist()
    if float(np.nansum(weights)) <= 0:
        weights = [1.0 for _ in weights]
    return {
        "source": "derived_from_matrix_item_difficulty_and_disagreement",
        "source_is_irt_proxy": False,
        "matched_items": int(bundle.frame.shape[1]),
        "weights": weights,
        "suspicious": suspicious.fillna(False).to_numpy(dtype=bool).tolist(),
    }


def summarize_predictions(predictions: str | Path | None) -> dict[str, Any]:
    if predictions is None:
        return {"path": None, "exists": False}
    path = Path(predictions)
    payload: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "sample_keys": [],
    }
    if not path.exists():
        return payload
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                break
            payload["sample_keys"] = sorted(row.keys())
            break
    return payload


def panel_shape(bundle: MatrixBundle) -> dict[str, Any]:
    return {
        "models": int(bundle.frame.shape[0]),
        "items": int(bundle.frame.shape[1]),
        "subjects": int(bundle.item_metadata["subject"].nunique()),
        "missing_fraction": float(bundle.frame.isna().sum().sum() / max(bundle.frame.size, 1)),
    }


def render_ranking_audit(payload: dict[str, Any]) -> str:
    return (
        "\n".join(
            [
                "# Real-Panel Ranking Audit",
                "",
                f"- Status: `{payload['status']}`",
                f"- Evidence state: `{payload['evidence_state']}`",
                f"- Models: {payload['panel_shape']['models']}",
                f"- Items: {payload['panel_shape']['items']}",
                f"- Ability spread: {payload['ability_spread']:.4f}",
                "",
                "This is an accuracy-ranking artifact on the active cached response matrix. It does not validate item-error detection or benchmark validity.",
            ]
        )
        + "\n"
    )


def render_subject_instability(payload: dict[str, Any]) -> str:
    return (
        "\n".join(
            [
                "# Subject Instability Audit",
                "",
                f"- Status: `{payload['status']}`",
                f"- Subjects: {payload['subject_count']}",
                f"- Max subject rank range: {payload['max_subject_rank_range']:.1f}",
                f"- Models with subject rank range >= 3: {payload['models_with_subject_rank_range_ge_3']}",
                "",
                "Subject-level rank changes are diagnostic sensitivity evidence only; they are not evidence that MMLU is valid or invalid.",
            ]
        )
        + "\n"
    )


def render_diagnostic_disagreement(payload: dict[str, Any]) -> str:
    return (
        "\n".join(
            [
                "# Diagnostic Disagreement Audit",
                "",
                f"- Status: `{payload['status']}`",
                f"- Diagnostic source: `{payload['diagnostic_source']}`",
                f"- IRT proxy source: `{payload['diagnostic_source_is_irt_proxy']}`",
                f"- Max absolute rank delta: {payload['max_abs_rank_delta']:.1f}",
                f"- Models with absolute rank delta >= 3: {payload['models_with_abs_rank_delta_ge_3']}",
                "",
                "These are proxy diagnostic disagreements, not externally validated error-detection results.",
            ]
        )
        + "\n"
    )


def render_ranking_disagreement(payload: dict[str, Any]) -> str:
    return (
        "\n".join(
            [
                "# Ranking Disagreement Summary",
                "",
                f"- Status: `{payload['status']}`",
                f"- Diagnostic source: `{payload['diagnostic_source']}`",
                f"- Max diagnostic rank delta: {payload['max_abs_diagnostic_rank_delta']:.1f}",
                f"- Max subject rank range: {payload['max_subject_rank_range']:.1f}",
                f"- Bootstrap iterations: {payload['bootstrap']['bootstrap_iterations_per_resampling_baseline']}",
                "",
                "The artifact supports cautious discussion of ranking sensitivity under this protocol. It does not establish a true model ranking.",
            ]
        )
        + "\n"
    )


def render_baseline_summary(payload: dict[str, Any]) -> str:
    return (
        "\n".join(
            [
                "# Real-Panel Baseline Comparison",
                "",
                f"- Status: `{payload['status']}`",
                f"- Bootstrap iterations: {payload['bootstrap']['bootstrap_iterations_per_resampling_baseline']}",
                f"- Models: {payload['panel_shape']['models']}",
                f"- Items: {payload['panel_shape']['items']}",
                "",
                "Random and subject-stratified baselines quantify sensitivity to item sampling. They are not external validation labels.",
            ]
        )
        + "\n"
    )


def _resolve_output(output: str | Path, default_name: str) -> tuple[Path, Path]:
    path = Path(output)
    if path.suffix:
        return path.parent, path
    return path, path / default_name


def _split_item_column(column: str) -> tuple[str, str, str]:
    if "::" in column:
        subject, item_id = column.split("::", 1)
    else:
        subject, item_id = "unknown", column
    return column, subject, item_id


def _plain_item_id(item_id: str) -> str:
    return item_id.split("::", 1)[1] if "::" in item_id else item_id


def _count_pairwise_flips(
    counts: dict[tuple[str, str], int],
    full_ranks: pd.Series,
    subject_ranks: pd.Series,
) -> None:
    models = list(full_ranks.index)
    for i, model_a in enumerate(models):
        for model_b in models[i + 1 :]:
            full_order = np.sign(float(full_ranks.loc[model_a] - full_ranks.loc[model_b]))
            subject_order = np.sign(float(subject_ranks.loc[model_a] - subject_ranks.loc[model_b]))
            if full_order != 0 and subject_order != 0 and full_order != subject_order:
                key = tuple(sorted((model_a, model_b)))
                counts[key] = counts.get(key, 0) + 1


def _rank_desc(scores: np.ndarray) -> np.ndarray:
    series = pd.Series(scores)
    return series.rank(ascending=False, method="min").to_numpy(dtype=float)


def _baseline_iteration_row(
    *,
    baseline: str,
    iteration: int,
    scores: np.ndarray,
    full_scores: np.ndarray,
    full_ranks: np.ndarray,
    top5: set[int],
) -> dict[str, Any]:
    ranks = _rank_desc(scores)
    top = set(np.argsort(scores)[::-1][: len(top5)].tolist())
    return {
        "baseline": baseline,
        "iteration": int(iteration),
        "spearman_vs_full": float(
            pd.Series(scores).corr(pd.Series(full_scores), method="spearman")
        ),
        "kendall_vs_full": float(pd.Series(scores).corr(pd.Series(full_scores), method="kendall")),
        "top5_overlap": float(len(top & top5) / max(len(top5), 1)),
        "top1_match": float(int(np.argmax(scores) == np.argmax(full_scores))),
        "max_abs_rank_delta": float(np.nanmax(np.abs(ranks - full_ranks))),
        "mean_abs_rank_delta": float(np.nanmean(np.abs(ranks - full_ranks))),
    }


def _threshold_rate(iterations: pd.DataFrame, baseline: str, threshold: int) -> float:
    subset = iterations[iterations["baseline"] == baseline]
    if subset.empty:
        return float("nan")
    return float((subset["max_abs_rank_delta"] >= threshold).mean())


def _corr(left: pd.Series, right: pd.Series, *, method: str) -> float | None:
    value = left.corr(right, method=method)
    if pd.isna(value):
        return None
    return float(value)


def _float_or_none(value: Any) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


CLAIM_LIMITS = [
    "Do not claim MMLU error detection without direct/hash external validation.",
    "Do not claim MMLU is valid or invalid.",
    "Do not treat proxy IRT or derived disagreement as full 2PL.",
    "Do not treat ranking sensitivity as the true model ranking.",
]
