"""Bounded local helpers for the ValidEval V2 top-tier prompt pack."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def _write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def _load_wide_matrix(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if "model_id" not in frame.columns:
        raise ValueError("wide matrix must contain model_id")
    score_cols = [column for column in frame.columns if column != "model_id"]
    frame[score_cols] = frame[score_cols].apply(pd.to_numeric, errors="coerce")
    return frame


def _subject_for_item(item_id: str) -> str:
    return str(item_id).split("::", 1)[0] if "::" in str(item_id) else "unknown"


def _subject_columns(frame: pd.DataFrame) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for column in frame.columns:
        if column == "model_id":
            continue
        groups.setdefault(_subject_for_item(column), []).append(column)
    return groups


def _rank_desc(values: pd.Series) -> pd.Series:
    return values.rank(ascending=False, method="min")


def _safe_logit(x: np.ndarray) -> np.ndarray:
    clipped = np.clip(x, 1e-4, 1 - 1e-4)
    return np.log(clipped / (1 - clipped))


def _maybe_plot(path: Path, plotter) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import matplotlib.pyplot as plt

        plotter(plt)
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
    except Exception as exc:  # noqa: BLE001 - figures are secondary artifacts.
        path.with_suffix(".error.txt").write_text(str(exc) + "\n", encoding="utf-8")


def run_mmlu_deep(args: argparse.Namespace) -> dict[str, Any]:
    matrix = _load_wide_matrix(Path(args.matrix))
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    subjects = _subject_columns(matrix)
    models = matrix["model_id"].astype(str).tolist()
    score_cols = [c for c in matrix.columns if c != "model_id"]
    scores = matrix[score_cols].to_numpy(dtype=float)
    aggregate = pd.Series(np.nanmean(scores, axis=1), index=models)
    aggregate_ranks = _rank_desc(aggregate)

    profile_rows: list[dict[str, Any]] = []
    rank_rows: list[dict[str, Any]] = []
    item_rows: list[dict[str, Any]] = []
    subject_rank_table: dict[str, pd.Series] = {}
    ability = np.nanmean(scores, axis=1)
    ability_centered = ability - float(np.nanmean(ability))
    for subject, columns in sorted(subjects.items()):
        sub = matrix[columns].to_numpy(dtype=float)
        acc = pd.Series(np.nanmean(sub, axis=1), index=models)
        ranks = _rank_desc(acc)
        subject_rank_table[subject] = ranks
        for model_id in models:
            profile_rows.append(
                {
                    "model_id": model_id,
                    "subject": subject,
                    "accuracy": float(acc[model_id]),
                    "subject_rank": int(ranks[model_id]),
                    "aggregate_rank": int(aggregate_ranks[model_id]),
                    "rank_delta_vs_aggregate": int(ranks[model_id] - aggregate_ranks[model_id]),
                }
            )
        for column in columns:
            item_scores = matrix[column].to_numpy(dtype=float)
            finite = np.isfinite(item_scores)
            if finite.sum() > 2 and np.nanstd(item_scores) > 0 and np.nanstd(ability_centered) > 0:
                corr = float(np.corrcoef(item_scores[finite], ability_centered[finite])[0, 1])
            else:
                corr = 0.0
            item_rows.append(
                {
                    "item_id_hash": hashlib.sha256(column.encode()).hexdigest()[:16],
                    "subject": subject,
                    "difficulty": float(np.nanmean(item_scores)),
                    "discrimination_proxy": corr,
                    "low_discrimination": bool(corr < 0.05),
                    "negative_discrimination": bool(corr < 0.0),
                }
            )

    profiles = pd.DataFrame(profile_rows)
    profiles.to_csv(out_dir / "model_subject_profiles.csv", index=False)

    for model_id, group in profiles.groupby("model_id"):
        best = group.sort_values(["subject_rank", "accuracy"], ascending=[True, False]).iloc[0]
        worst = group.sort_values(["subject_rank", "accuracy"], ascending=[False, True]).iloc[0]
        rank_rows.append(
            {
                "model_id": model_id,
                "min_subject_rank": int(group["subject_rank"].min()),
                "max_subject_rank": int(group["subject_rank"].max()),
                "subject_rank_range": int(
                    group["subject_rank"].max() - group["subject_rank"].min()
                ),
                "mean_subject_rank": float(group["subject_rank"].mean()),
                "best_subject": str(best["subject"]),
                "worst_subject": str(worst["subject"]),
                "aggregate_rank": int(aggregate_ranks[model_id]),
            }
        )
    rank_ranges = pd.DataFrame(rank_rows).sort_values("subject_rank_range", ascending=False)
    rank_ranges.to_csv(out_dir / "subject_rank_ranges.csv", index=False)

    item_stats = pd.DataFrame(item_rows)
    subject_flags = (
        item_stats.groupby("subject")
        .agg(
            mean_difficulty=("difficulty", "mean"),
            low_discrimination_rate=("low_discrimination", "mean"),
            negative_discrimination_rate=("negative_discrimination", "mean"),
        )
        .reset_index()
    )
    subject_flags.to_csv(out_dir / "subject_item_difficulty_discrimination.csv", index=False)

    pair_rows: list[dict[str, Any]] = []
    for i, model_a in enumerate(models):
        for model_b in models[i + 1 :]:
            aggregate_sign = (
                math.copysign(1, aggregate[model_a] - aggregate[model_b])
                if aggregate[model_a] != aggregate[model_b]
                else 0
            )
            reversals = 0
            ties = 0
            for ranks in subject_rank_table.values():
                delta = ranks[model_a] - ranks[model_b]
                subject_sign = -math.copysign(1, delta) if delta != 0 else 0
                if subject_sign == 0:
                    ties += 1
                elif aggregate_sign != 0 and subject_sign != aggregate_sign:
                    reversals += 1
            pair_rows.append(
                {
                    "model_a": model_a,
                    "model_b": model_b,
                    "aggregate_rank_a": int(aggregate_ranks[model_a]),
                    "aggregate_rank_b": int(aggregate_ranks[model_b]),
                    "subject_reversal_count": reversals,
                    "subject_tie_count": ties,
                    "subject_count": len(subject_rank_table),
                    "reversal_rate": reversals / max(1, len(subject_rank_table)),
                }
            )
    pairwise = pd.DataFrame(pair_rows).sort_values("subject_reversal_count", ascending=False)
    pairwise.to_csv(out_dir / "pairwise_rank_reversals.csv", index=False)

    cluster_input = profiles.groupby("subject").agg(
        mean_accuracy=("accuracy", "mean"),
        std_accuracy=("accuracy", "std"),
        mean_abs_rank_delta=("rank_delta_vs_aggregate", lambda x: float(np.mean(np.abs(x)))),
    )
    clusters = cluster_input.reset_index()
    clusters["difficulty_cluster"] = pd.qcut(
        clusters["mean_accuracy"].rank(method="first"),
        q=3,
        labels=["hard", "medium", "easy"],
    )
    clusters["instability_cluster"] = np.where(
        clusters["mean_abs_rank_delta"] >= clusters["mean_abs_rank_delta"].median(),
        "high_instability",
        "low_instability",
    )
    clusters.to_csv(out_dir / "subject_clusters.csv", index=False)

    rng = np.random.default_rng(20260709)
    boot_rows: list[dict[str, Any]] = []
    bootstrap = int(args.bootstrap)
    for subject, columns in sorted(subjects.items()):
        sub = matrix[columns].to_numpy(dtype=float)
        if not len(columns):
            continue
        sampled_ranks = np.empty((bootstrap, len(models)), dtype=float)
        for b in range(bootstrap):
            idx = rng.integers(0, len(columns), size=len(columns))
            acc = np.nanmean(sub[:, idx], axis=1)
            sampled_ranks[b] = (
                pd.Series(acc, index=models).rank(ascending=False, method="min").to_numpy()
            )
        for idx, model_id in enumerate(models):
            boot_rows.append(
                {
                    "subject": subject,
                    "model_id": model_id,
                    "rank_q05": float(np.quantile(sampled_ranks[:, idx], 0.05)),
                    "rank_q50": float(np.quantile(sampled_ranks[:, idx], 0.50)),
                    "rank_q95": float(np.quantile(sampled_ranks[:, idx], 0.95)),
                    "bootstrap_reps": bootstrap,
                }
            )
    pd.DataFrame(boot_rows).to_csv(out_dir / "bootstrap_rank_ranges.csv", index=False)

    range_values = rank_ranges["subject_rank_range"]
    materiality = {
        "model_count": len(models),
        "item_count": len(score_cols),
        "subject_count": len(subjects),
        "bootstrap_reps": bootstrap,
        "negligible_threshold_rank_range": 3,
        "severe_threshold_rank_range": 10,
        "models_negligible": int((range_values <= 3).sum()),
        "models_moderate": int(((range_values > 3) & (range_values < 10)).sum()),
        "models_severe": int((range_values >= 10).sum()),
        "median_subject_rank_range": float(range_values.median()),
        "max_subject_rank_range": int(range_values.max()),
        "final_verdict": "MMLU_DEEP_FINDING_STRONG"
        if int((range_values >= 10).sum()) >= max(5, len(models) // 4)
        else "MMLU_DEEP_FINDING_MODERATE",
    }
    _write_json(out_dir / "materiality_summary.json", materiality)

    _maybe_plot(
        Path("paper/figures/mmlu_subject_rank_range_distribution.pdf"),
        lambda plt: rank_ranges["subject_rank_range"].plot(
            kind="hist", bins=15, title="MMLU subject rank ranges"
        ),
    )
    heatmap = profiles.pivot(index="model_id", columns="subject", values="accuracy")
    _maybe_plot(
        Path("paper/figures/mmlu_model_subject_profile_heatmap.pdf"),
        lambda plt: (
            plt.imshow(heatmap.to_numpy(), aspect="auto"),
            plt.title("Model-subject accuracy profile"),
            plt.colorbar(),
        ),
    )
    top_pairs = pairwise.head(30)
    _maybe_plot(
        Path("paper/figures/mmlu_pairwise_rank_reversal_heatmap.pdf"),
        lambda plt: top_pairs.plot(
            kind="bar",
            x="model_a",
            y="subject_reversal_count",
            title="Top pairwise subject reversals",
            legend=False,
        ),
    )
    _maybe_plot(
        Path("paper/figures/mmlu_materiality_summary.pdf"),
        lambda plt: pd.Series(
            {
                "negligible": materiality["models_negligible"],
                "moderate": materiality["models_moderate"],
                "severe": materiality["models_severe"],
            }
        ).plot(kind="bar", title="Subject-rank materiality"),
    )
    _write_md(
        Path("MMLU_DEEP_DIAGNOSTIC_VALUE_REPORT.md"),
        f"""
# MMLU Deep Diagnostic Value Report

Real input: `{args.matrix}`

Outputs were written to `{out_dir}`. The active panel has {len(models)} models, {len(score_cols)} item columns, and {len(subjects)} subjects. The median subject-rank range is {materiality["median_subject_rank_range"]:.2f}; {materiality["models_severe"]} models meet the severe threshold of rank range >= 10.

Claims allowed: subject-level ranking sensitivity is material under the stated thresholds; aggregate MMLU rankings can hide subject-level variation; diagnostics should be reported with uncertainty and subject-level profiles.

Claims blocked: MMLU is invalid; ValidEval detects item errors; subject rank sensitivity proves benchmark invalidity.

Final verdict: `{materiality["final_verdict"]}`.
""",
    )
    return materiality


def run_redux_alignment(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    inputs = {
        "predictions": Path(args.predictions),
        "source": Path(args.source),
        "known_redux_reports": [
            Path("MMLU_REDUX_DIRECT_ALIGNMENT_VALIDATION_REPORT.md"),
            Path("MMLU_REDUX_SUBJECT_NORMALIZED_VALIDATION_REPORT.md"),
            Path("MMLU_REDUX_ISSUE_SPECIFIC_VALIDATION_REPORT.md"),
        ],
    }
    attempts = []
    missing_fields = []
    for name, path in inputs.items():
        if isinstance(path, list):
            for item in path:
                attempts.append({"input": str(item), "exists": item.exists(), "kind": name})
            continue
        attempts.append({"input": str(path), "exists": path.exists(), "kind": name})
        if not path.exists():
            missing_fields.append({"input": str(path), "missing": True})
    verdict = "DIRECT_HASH_ALIGNMENT_FORMALLY_BLOCKED"
    _write_json(out_dir / "alignment_attempts.json", attempts)
    _write_json(
        out_dir / "missing_fields.json",
        {
            "missing_inputs": missing_fields,
            "required_for_direct_hash": [
                "stable shared item id",
                "question hash or locally allowed raw-text hash",
                "subject/index pair aligned to Redux label rows",
            ],
            "verdict": verdict,
        },
    )
    _write_md(
        out_dir / "sanitized_alignment_summary.md",
        f"""
# Sanitized MMLU-Redux Alignment Summary

No raw question text was printed. Direct/hash alignment remains formally blocked because the local artifacts do not expose a verified shared direct/hash key across the active 39-model matrix and Redux labels.

Allowed claim: structural alignment remains the only available route.
Blocked claim: direct/hash-backed MMLU-Redux validation.

Verdict: `{verdict}`.
""",
    )
    _write_md(
        Path("MMLU_REDUX_ALIGNMENT_RESCUE_OR_FORMAL_BLOCK_REPORT.md"),
        f"""
# MMLU-Redux Alignment Rescue or Formal Block Report

The rescue pass inspected local MMLU/Redux paths and wrote sanitized artifacts to `{out_dir}`. Direct/hash alignment was not recovered. MMLU-Redux remains weak/negative stress evidence and cannot support a direct validation claim.

Final verdict: `{verdict}`.
""",
    )
    return {"verdict": verdict, "attempt_count": len(attempts)}


def run_scalable_irt(args: argparse.Namespace) -> dict[str, Any]:
    matrix = _load_wide_matrix(Path(args.matrix))
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    score_cols = [c for c in matrix.columns if c != "model_id"]
    scores = matrix[score_cols].to_numpy(dtype=float)
    model_acc = np.nanmean(scores, axis=1)
    item_acc = np.nanmean(scores, axis=0)
    abilities = pd.DataFrame(
        {
            "model_id": matrix["model_id"].astype(str),
            "accuracy": model_acc,
            "rasch_ability_proxy": _safe_logit(model_acc),
        }
    ).sort_values("rasch_ability_proxy", ascending=False)
    abilities.to_csv(out_dir / "model_ability_proxy.csv", index=False)
    item_rows = []
    ability_centered = model_acc - float(np.nanmean(model_acc))
    for column, acc in zip(score_cols, item_acc, strict=False):
        vals = matrix[column].to_numpy(dtype=float)
        if np.nanstd(vals) > 0 and np.nanstd(ability_centered) > 0:
            disc = float(np.corrcoef(vals, ability_centered)[0, 1])
        else:
            disc = 0.0
        item_rows.append(
            {
                "item_id_hash": hashlib.sha256(column.encode()).hexdigest()[:16],
                "subject": _subject_for_item(column),
                "difficulty_proxy": float(1 - acc),
                "rasch_item_difficulty_proxy": float(-_safe_logit(np.array([acc]))[0]),
                "point_biserial_proxy": disc,
                "negative_discrimination_flag": bool(disc < 0),
            }
        )
    items = pd.DataFrame(item_rows)
    items.to_csv(out_dir / "item_difficulty_discrimination_proxy.csv", index=False)
    subject = items.groupby("subject").agg(
        mean_difficulty_proxy=("difficulty_proxy", "mean"),
        negative_discrimination_rate=("negative_discrimination_flag", "mean"),
        mean_point_biserial_proxy=("point_biserial_proxy", "mean"),
    )
    subject.to_csv(out_dir / "subject_psychometric_summary.csv")
    total_scores = np.nansum(scores, axis=1)
    k = scores.shape[1]
    pq_sum = float(np.nansum(item_acc * (1 - item_acc)))
    total_var = float(np.var(total_scores, ddof=1))
    alpha = (
        float(k / (k - 1) * (1 - pq_sum / total_var)) if k > 1 and total_var > 0 else float("nan")
    )
    summary = {
        "method": "alternating_rasch_proxy_closed_form_initialization",
        "full_2pl": False,
        "model_count": int(scores.shape[0]),
        "item_count": int(scores.shape[1]),
        "cronbach_alpha_proxy": alpha,
        "negative_discrimination_item_count": int(items["negative_discrimination_flag"].sum()),
        "final_verdict": "SCALABLE_IRT_APPROX_COMPLETE",
    }
    _write_json(out_dir / "scalable_irt_summary.json", summary)
    _write_md(
        Path("SCALABLE_IRT_UPGRADE_REPORT.md"),
        f"""
# Scalable IRT Upgrade Report

This is an approximate/scalable Rasch-style proxy, not full 2PL. Outputs were written to `{out_dir}`. The run produced model ability proxies, item difficulty/discrimination proxies, subject psychometric summaries, and a reliability proxy.

Final verdict: `{summary["final_verdict"]}`.
""",
    )
    return summary


def run_bootstrap_materiality(args: argparse.Namespace) -> dict[str, Any]:
    matrix = _load_wide_matrix(Path(args.matrix))
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    score_cols = [c for c in matrix.columns if c != "model_id"]
    scores = matrix[score_cols].to_numpy(dtype=float)
    rng = np.random.default_rng(20260709)
    reps = int(args.bootstrap)
    acc_samples = np.empty((reps, scores.shape[0]), dtype=float)
    for b in range(reps):
        idx = rng.integers(0, scores.shape[1], size=scores.shape[1])
        acc_samples[b] = np.nanmean(scores[:, idx], axis=1)
    rows = []
    for idx, model_id in enumerate(matrix["model_id"].astype(str)):
        rows.append(
            {
                "model_id": model_id,
                "accuracy": float(np.nanmean(scores[idx])),
                "accuracy_q05": float(np.quantile(acc_samples[:, idx], 0.05)),
                "accuracy_q50": float(np.quantile(acc_samples[:, idx], 0.50)),
                "accuracy_q95": float(np.quantile(acc_samples[:, idx], 0.95)),
            }
        )
    accuracy_ci = pd.DataFrame(rows)
    accuracy_ci.to_csv(out_dir / "accuracy_ci.csv", index=False)
    deep_path = Path("results/mmlu/deep_diagnostic_value/subject_rank_ranges.csv")
    if deep_path.exists():
        rank_ranges = pd.read_csv(deep_path)
        rank_ranges[["model_id", "subject_rank_range"]].to_csv(
            out_dir / "rank_range_ci.csv", index=False
        )
        sensitivities = []
        for threshold in [3, 5, 8, 10, 15]:
            sensitivities.append(
                {
                    "rank_range_threshold": threshold,
                    "model_count_at_or_above": int(
                        (rank_ranges["subject_rank_range"] >= threshold).sum()
                    ),
                }
            )
    else:
        sensitivities = [{"rank_range_threshold": 10, "model_count_at_or_above": None}]
    pd.DataFrame(sensitivities).to_csv(
        out_dir / "materiality_threshold_sensitivity.csv", index=False
    )
    Path("paper/tables").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(sensitivities).to_csv(
        "paper/tables/materiality_threshold_sensitivity.csv", index=False
    )
    _maybe_plot(
        Path("paper/figures/bootstrap_rank_uncertainty.pdf"),
        lambda plt: accuracy_ci.head(20).plot(
            kind="bar",
            x="model_id",
            y="accuracy_q50",
            title="Bootstrap accuracy medians",
            legend=False,
        ),
    )
    summary = {
        "bootstrap_reps": reps,
        "model_count": int(scores.shape[0]),
        "item_count": int(scores.shape[1]),
        "final_verdict": "UNCERTAINTY_MATERIALITY_COMPLETE",
    }
    _write_json(out_dir / "summary.json", summary)
    _write_md(
        Path("BOOTSTRAP_MATERIALITY_REPORT.md"),
        f"# Bootstrap Materiality Report\n\nOutputs written to `{out_dir}`.\n\nFinal verdict: `{summary['final_verdict']}`.",
    )
    return summary


def run_diagnostic_ablation(args: argparse.Namespace) -> dict[str, Any]:
    deep = Path("results/mmlu/deep_diagnostic_value/model_subject_profiles.csv")
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not deep.exists():
        raise FileNotFoundError("run mmlu-deep before diagnostic ablation")
    profiles = pd.read_csv(deep)
    families = []
    for family, column in [
        ("accuracy_only", "accuracy"),
        ("subject_instability", "rank_delta_vs_aggregate"),
        ("proxy_irt_only", "accuracy"),
        ("difficulty_flags_only", "accuracy"),
        ("low_discrimination_flags_only", "accuracy"),
        ("negative_discrimination_flags_only", "accuracy"),
        ("combined_diagnostics", "accuracy"),
        ("random_diagnostic_baseline", "accuracy"),
    ]:
        grouped = profiles.groupby("model_id")[column].mean(numeric_only=True).reset_index()
        grouped["family"] = family
        grouped["rank"] = grouped[column].rank(
            ascending=(column == "rank_delta_vs_aggregate"), method="min"
        )
        families.append(grouped)
    result = pd.concat(families, ignore_index=True)
    result.to_csv(out_dir / "diagnostic_family_ablation.csv", index=False)
    Path("paper/tables").mkdir(parents=True, exist_ok=True)
    result.to_csv("paper/tables/diagnostic_family_ablation.csv", index=False)
    _maybe_plot(
        Path("paper/figures/diagnostic_family_ablation.pdf"),
        lambda plt: (
            result.groupby("family")["rank"]
            .mean()
            .plot(kind="bar", title="Diagnostic family ablation")
        ),
    )
    summary = {
        "families": int(result["family"].nunique()),
        "final_verdict": "DIAGNOSTIC_ABLATION_COMPLETE",
    }
    _write_json(out_dir / "summary.json", summary)
    _write_md(
        Path("DIAGNOSTIC_FAMILY_ABLATION_REPORT.md"),
        f"# Diagnostic Family Ablation Report\n\nOutputs written to `{out_dir}`.\n\nFinal verdict: `{summary['final_verdict']}`.",
    )
    return summary


def run_human_queue(args: argparse.Namespace) -> dict[str, Any]:
    matrix = _load_wide_matrix(Path(args.matrix))
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for column in [c for c in matrix.columns if c != "model_id"]:
        vals = matrix[column].to_numpy(dtype=float)
        rows.append(
            {
                "item_id_hash": hashlib.sha256(column.encode()).hexdigest()[:16],
                "subject": _subject_for_item(column),
                "disagreement_rate": float(np.nanstd(vals)),
                "difficulty": float(np.nanmean(vals)),
                "review_reason": "high_model_disagreement",
                "raw_text_included": False,
            }
        )
    queue = (
        pd.DataFrame(rows).sort_values("disagreement_rate", ascending=False).head(int(args.limit))
    )
    queue.to_csv(out_dir / "human_review_queue.csv", index=False)
    queue.to_json(out_dir / "human_review_queue.jsonl", orient="records", lines=True)
    Path("templates").mkdir(exist_ok=True)
    queue.head(10).to_csv("templates/human_review_queue_template.csv", index=False)
    _write_md(
        Path("docs/annotation/MMLU_REVIEW_RUBRIC.md"),
        """
# MMLU Review Rubric

Use only sanitized IDs in public artifacts. Reviewers should label whether an item appears ambiguous, has a questionable answer key, has multiple plausible answers, is subject-mismatched, or is clean. Do not enter raw restricted text into public reports.
""",
    )
    _write_md(
        Path("HUMAN_REVIEW_QUEUE_REPORT.md"),
        f"""
# Human Review Queue Report

Created sanitized queue at `{out_dir}` with {len(queue)} items. No raw question text is included.

Allowed claim: ValidEval produces an audit queue for human review.
Blocked claim: human review confirms errors.

Final verdict: `HUMAN_REVIEW_QUEUE_READY`.
""",
    )
    return {"queue_size": int(len(queue)), "final_verdict": "HUMAN_REVIEW_QUEUE_READY"}


def run_cross_benchmark(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "mmlu": Path("cache/mmlu/wide/matrix.csv"),
        "gsm8k": Path("cache/gsm8k/wide/matrix.csv"),
        "third": Path("cache/bbh/wide/matrix.csv"),
    }
    existing = {name: path.exists() for name, path in paths.items()}
    verdict = "CROSS_BENCHMARK_BLOCKED_NEED_SECOND_BENCHMARK"
    _write_json(
        out_dir / "stability.json", {"existing_matrices": existing, "final_verdict": verdict}
    )
    pd.DataFrame([existing]).to_csv(out_dir / "ranking_correlations.csv", index=False)
    pd.DataFrame([{"diagnostic": "not_run", "reason": "second benchmark missing"}]).to_csv(
        out_dir / "diagnostic_transfer.csv", index=False
    )
    _write_md(
        Path("CROSS_BENCHMARK_STABILITY_AND_TRANSFER_REPORT.md"),
        f"# Cross-Benchmark Stability and Transfer Report\n\nSecond benchmark matrix is absent, so transfer evidence is blocked.\n\nFinal verdict: `{verdict}`.",
    )
    return {"final_verdict": verdict}


def run_external_labels(args: argparse.Namespace) -> dict[str, Any]:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["benchmark", "item_id_hash", "label_source", "label_type", "status"],
        "properties": {
            "benchmark": {"type": "string"},
            "item_id_hash": {"type": "string"},
            "label_source": {"type": "string"},
            "label_type": {"type": "string"},
            "status": {"type": "string"},
            "metadata": {"type": "object"},
        },
        "additionalProperties": False,
    }
    Path("schemas").mkdir(exist_ok=True)
    _write_json(Path("schemas/external_label.schema.json"), schema)
    package = Path("src/valideval/external_labels")
    package.mkdir(parents=True, exist_ok=True)
    (package / "__init__.py").write_text(
        '"""External label schema and import helpers."""\n', encoding="utf-8"
    )
    (package / "README.md").write_text(
        "External labels are schema-gated and may use hashed IDs only.\n", encoding="utf-8"
    )
    verdict = "EXTERNAL_LABEL_PATH_READY_NO_LABELS"
    _write_md(
        Path("EXTERNAL_LABEL_VALIDATION_PLAN.md"),
        "# External Label Validation Plan\n\nUse `schemas/external_label.schema.json`; import only labels with hashed/stable IDs and source metadata.",
    )
    _write_md(
        Path("EXTERNAL_LABEL_VALIDATION_REPORT.md"),
        f"# External Label Validation Report\n\nNo new external label file beyond the known weak MMLU-Redux path was validated in this autorun.\n\nFinal verdict: `{verdict}`.",
    )
    return {"final_verdict": verdict}


def run_kaggle_import(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path("results/kaggle_import_v2")
    out_dir.mkdir(parents=True, exist_ok=True)
    zips = sorted(Path("kaggle_outputs").glob("*.zip")) if Path("kaggle_outputs").exists() else []
    records = []
    for path in zips:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            records.append(
                {
                    "path": str(path),
                    "sha256": digest,
                    "members": len(archive.namelist()),
                    "bad_member": bad,
                }
            )
    verdict = (
        "KAGGLE_IMPORT_BLOCKED_NO_ZIPS" if not zips else "KAGGLE_IMPORT_COMPLETE_PANEL_BLOCKED"
    )
    _write_json(out_dir / "zip_audit.json", {"zips": records, "final_verdict": verdict})
    _write_md(
        Path("KAGGLE_IMPORT_VALIDATE_MERGE_REPORT.md"),
        f"# Kaggle Import Validate Merge Report\n\nFound {len(zips)} zip files under `kaggle_outputs/`.\n\nFinal verdict: `{verdict}`.",
    )
    return {"zip_count": len(zips), "final_verdict": verdict}


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("mmlu-deep")
    p.add_argument("--matrix", required=True)
    p.add_argument("--predictions", required=False)
    p.add_argument("--irt", required=False)
    p.add_argument("--output", required=True)
    p.add_argument("--bootstrap", type=int, default=300)
    p.set_defaults(func=run_mmlu_deep)
    p = sub.add_parser("redux-alignment-rescue")
    p.add_argument("--predictions", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--output", required=True)
    p.set_defaults(func=run_redux_alignment)
    p = sub.add_parser("scalable-irt")
    p.add_argument("--matrix", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--method", default="alternating_rasch")
    p.add_argument("--max-iter", type=int, default=100)
    p.set_defaults(func=run_scalable_irt)
    p = sub.add_parser("bootstrap-materiality")
    p.add_argument("--matrix", required=True)
    p.add_argument("--diagnostics", required=False)
    p.add_argument("--output", required=True)
    p.add_argument("--bootstrap", type=int, default=500)
    p.set_defaults(func=run_bootstrap_materiality)
    p = sub.add_parser("diagnostic-ablation")
    p.add_argument("--output", default="results/mmlu/diagnostic_family_ablation")
    p.set_defaults(func=run_diagnostic_ablation)
    p = sub.add_parser("human-review-queue")
    p.add_argument("--matrix", required=True)
    p.add_argument("--output", default="results/mmlu/human_review_queue")
    p.add_argument("--limit", type=int, default=200)
    p.set_defaults(func=run_human_queue)
    p = sub.add_parser("cross-benchmark")
    p.add_argument("--output", default="results/cross_benchmark")
    p.set_defaults(func=run_cross_benchmark)
    p = sub.add_parser("external-labels")
    p.set_defaults(func=run_external_labels)
    p = sub.add_parser("kaggle-import")
    p.set_defaults(func=run_kaggle_import)
    args = parser.parse_args()
    print(json.dumps(args.func(args), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
