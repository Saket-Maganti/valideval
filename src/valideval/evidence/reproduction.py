from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reproduce_helm_mmlu_panel(
    primary_path: str | Path,
    existing_matrix_path: str | Path,
    output_dir: str | Path,
    *,
    irt_proxy_path: str | Path | None = None,
) -> dict[str, Any]:
    """Reconstruct the public HELM-derived MMLU panel from the earliest local artifact.

    The function writes a deterministic compressed normalized long table and a newly
    reconstructed matrix. It never mutates the primary input or the active cache.
    """

    primary = Path(primary_path)
    existing_matrix = Path(existing_matrix_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    by_model: dict[str, dict[str, float]] = defaultdict(dict)
    row_fingerprints: dict[tuple[str, str], tuple[bool, str, str]] = {}
    item_subject: dict[str, str] = {}
    item_gold: dict[str, str] = {}
    model_row_counts: Counter[str] = Counter()
    item_model_counts: Counter[str] = Counter()
    subjects: set[str] = set()
    duplicate_rows = 0
    contradictory_duplicates = 0
    invalid_correctness = 0
    identity_conflicts = 0
    row_count = 0
    canonical_digest = hashlib.sha256()

    normalized_path = destination / "predictions.normalized.v5.jsonl.gz"
    with (
        primary.open("r", encoding="utf-8") as source,
        normalized_path.open("wb") as raw_output,
        gzip.GzipFile(fileobj=raw_output, mode="wb", mtime=0) as compressed,
        io.TextIOWrapper(compressed, encoding="utf-8", newline="\n") as normalized_output,
    ):
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            row_count += 1
            model_id = str(record.get("model_id", ""))
            subset = str(record.get("subset", ""))
            item_id = str(record.get("item_id", ""))
            prediction = str(record.get("prediction", ""))
            gold = str(record.get("gold", ""))
            correct_raw = record.get("correct")
            if not isinstance(correct_raw, (bool, int, float)) or float(correct_raw) not in (
                0.0,
                1.0,
            ):
                invalid_correctness += 1
                continue
            correct = bool(correct_raw)
            if not model_id or not subset or not item_id:
                raise ValueError(f"Missing identity field at primary row {line_number}.")

            item_key = f"{subset}::{item_id}"
            row_key = (model_id, item_key)
            fingerprint = (correct, prediction, gold)
            previous = row_fingerprints.get(row_key)
            if previous is not None:
                duplicate_rows += 1
                if previous != fingerprint:
                    contradictory_duplicates += 1
                continue
            row_fingerprints[row_key] = fingerprint

            if item_key in item_subject and item_subject[item_key] != subset:
                identity_conflicts += 1
            if item_key in item_gold and item_gold[item_key] != gold:
                identity_conflicts += 1
            item_subject[item_key] = subset
            item_gold[item_key] = gold
            subjects.add(subset)
            model_row_counts[model_id] += 1
            item_model_counts[item_key] += 1
            by_model[model_id][item_key] = float(correct)

            normalized = {
                "benchmark": "mmlu",
                "correct": correct,
                "gold": gold,
                "item_id": item_id,
                "model_id": model_id,
                "prediction": prediction,
                "subset": subset,
            }
            encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
            canonical_digest.update(encoded.encode("utf-8"))
            canonical_digest.update(b"\n")
            normalized_output.write(encoded + "\n")

    frame = pd.DataFrame.from_dict(by_model, orient="index", dtype=float)
    frame.index.name = "model_id"
    frame = frame.sort_index().sort_index(axis=1)
    reconstructed_matrix = destination / "matrix.reconstructed.v5.csv"
    frame.to_csv(reconstructed_matrix)

    active = pd.read_csv(existing_matrix, index_col=0).astype(float)
    active.index = active.index.astype(str)
    active = active.sort_index().sort_index(axis=1)
    same_labels = frame.index.equals(active.index) and frame.columns.equals(active.columns)
    max_abs_difference = None
    matrix_equal = False
    if same_labels and frame.shape == active.shape:
        delta = np.abs(frame.to_numpy(dtype=float) - active.to_numpy(dtype=float))
        max_abs_difference = float(np.nanmax(delta)) if delta.size else 0.0
        matrix_equal = bool(np.array_equal(frame.to_numpy(), active.to_numpy(), equal_nan=True))

    model_accuracy = frame.mean(axis=1)
    model_ranks = model_accuracy.rank(ascending=False, method="min")
    model_table = pd.DataFrame(
        {
            "model_id": frame.index,
            "accuracy": model_accuracy.to_numpy(dtype=float),
            "aggregate_rank": model_ranks.to_numpy(dtype=float),
            "row_count": [model_row_counts[str(model)] for model in frame.index],
        }
    ).sort_values(["aggregate_rank", "model_id"])
    model_table.to_csv(destination / "model_accuracies_v5.csv", index=False)

    subject_rows: list[dict[str, Any]] = []
    subject_rank_columns: dict[str, pd.Series] = {}
    for subject in sorted(subjects):
        columns = [column for column in frame.columns if column.startswith(f"{subject}::")]
        accuracy = frame[columns].mean(axis=1)
        ranks = accuracy.rank(ascending=False, method="min")
        subject_rank_columns[subject] = ranks
        for model_id in frame.index:
            subject_rows.append(
                {
                    "subject": subject,
                    "model_id": model_id,
                    "item_count": len(columns),
                    "accuracy": float(accuracy.loc[model_id]),
                    "subject_rank": float(ranks.loc[model_id]),
                    "aggregate_rank": float(model_ranks.loc[model_id]),
                }
            )
    subject_table = pd.DataFrame(subject_rows)
    subject_table.to_csv(destination / "subject_accuracies_and_ranks_v5.csv", index=False)
    subject_rank_frame = pd.DataFrame(subject_rank_columns)
    rank_ranges = pd.DataFrame(
        {
            "model_id": subject_rank_frame.index,
            "minimum_subject_rank": subject_rank_frame.min(axis=1),
            "maximum_subject_rank": subject_rank_frame.max(axis=1),
            "subject_rank_range": subject_rank_frame.max(axis=1) - subject_rank_frame.min(axis=1),
            "normalized_subject_rank_range": (
                (subject_rank_frame.max(axis=1) - subject_rank_frame.min(axis=1))
                / max(frame.shape[0] - 1, 1)
            ),
        }
    ).reset_index(drop=True)
    rank_ranges = rank_ranges.sort_values(
        ["subject_rank_range", "model_id"], ascending=[False, True]
    )
    rank_ranges.to_csv(destination / "subject_rank_ranges_v5.csv", index=False)

    weighted = _diagnostic_weighted_ranking(frame, irt_proxy_path)
    weighted["table"].to_csv(destination / "diagnostic_weighted_ranking_v5.csv", index=False)

    expected_models = frame.shape[0]
    partial_items = sum(count != expected_models for count in item_model_counts.values())
    expected_items = frame.shape[1]
    partial_models = sum(count != expected_items for count in model_row_counts.values())
    observed = {
        "row_count": row_count,
        "unique_rows": len(row_fingerprints),
        "model_count": int(frame.shape[0]),
        "item_count": int(frame.shape[1]),
        "subject_count": len(subjects),
        "matrix_cells": int(frame.shape[0] * frame.shape[1]),
        "missing_cells": int(frame.isna().sum().sum()),
        "missing_fraction": float(frame.isna().sum().sum() / max(frame.size, 1)),
        "duplicate_rows": duplicate_rows,
        "contradictory_duplicates": contradictory_duplicates,
        "invalid_correctness_values": invalid_correctness,
        "identity_conflicts": identity_conflicts,
        "partial_model_coverage": partial_models,
        "partial_item_coverage": partial_items,
        "ability_spread": float(model_accuracy.max() - model_accuracy.min()),
        "median_subject_rank_range": float(rank_ranges["subject_rank_range"].median()),
        "maximum_subject_rank_range": float(rank_ranges["subject_rank_range"].max()),
        "models_rank_range_ge_3": int((rank_ranges["subject_rank_range"] >= 3).sum()),
        "models_rank_range_ge_10_exploratory": int((rank_ranges["subject_rank_range"] >= 10).sum()),
        "diagnostic_weighted_spearman": weighted["spearman"],
        "diagnostic_weighted_kendall": weighted["kendall"],
        "diagnostic_weighted_max_abs_rank_delta": weighted["max_abs_rank_delta"],
    }
    verification = {
        "schema_version": "5.0",
        "evidence_status": "REPRODUCED" if matrix_equal else "CONTRADICTED",
        "source_description": "public HELM-derived MMLU response panel",
        "primary_input": str(primary),
        "active_matrix": str(existing_matrix),
        "reconstructed_normalized_long": str(normalized_path),
        "reconstructed_matrix": str(reconstructed_matrix),
        "hashes": {
            "primary_sha256": sha256_file(primary),
            "normalized_long_gzip_sha256": sha256_file(normalized_path),
            "normalized_canonical_rows_sha256": canonical_digest.hexdigest(),
            "active_matrix_sha256": sha256_file(existing_matrix),
            "reconstructed_matrix_sha256": sha256_file(reconstructed_matrix),
        },
        "matrix_comparison": {
            "same_labels": same_labels,
            "exact_values_equal": matrix_equal,
            "max_absolute_difference": max_abs_difference,
            "numeric_tolerance": 0.0,
        },
        "observed": observed,
        "claim_limits": [
            "The panel was imported from public HELM outputs; it was not executed by ValidEval.",
            "Raw subject rank ranges are descriptive and do not by themselves establish materiality.",
            "Proxy diagnostic weighting is not a full 2PL model.",
            "No benchmark-global validity conclusion follows from this reproduction.",
        ],
    }
    (destination / "mmlu_reproduction_v5.json").write_text(
        json.dumps(verification, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_comparison_table(destination / "reported_vs_reproduced_v5.csv", observed)
    return verification


def _diagnostic_weighted_ranking(
    frame: pd.DataFrame, irt_proxy_path: str | Path | None
) -> dict[str, Any]:
    full_accuracy = frame.mean(axis=1)
    full_rank = full_accuracy.rank(ascending=False, method="min")
    weights = pd.Series(1.0, index=frame.columns, dtype=float)
    if irt_proxy_path is not None and Path(irt_proxy_path).exists():
        metrics = pd.read_csv(irt_proxy_path)
        if {"item_id", "discrimination_proxy"}.issubset(metrics.columns):
            metric_map = metrics.set_index(metrics["item_id"].astype(str))["discrimination_proxy"]
            values = []
            for item_id in frame.columns:
                raw = metric_map.get(item_id, np.nan)
                value = float(raw) if pd.notna(raw) else 1.0
                values.append(max(value, 0.0))
            weights = pd.Series(values, index=frame.columns, dtype=float)
    if float(weights.sum()) <= 0:
        weights[:] = 1.0
    weighted_accuracy = frame.mul(weights, axis=1).sum(axis=1) / float(weights.sum())
    weighted_rank = weighted_accuracy.rank(ascending=False, method="min")
    table = pd.DataFrame(
        {
            "model_id": frame.index,
            "accuracy": full_accuracy.to_numpy(dtype=float),
            "accuracy_rank": full_rank.to_numpy(dtype=float),
            "diagnostic_weighted_score": weighted_accuracy.to_numpy(dtype=float),
            "diagnostic_weighted_rank": weighted_rank.to_numpy(dtype=float),
            "rank_delta": (weighted_rank - full_rank).to_numpy(dtype=float),
        }
    )
    return {
        "table": table,
        "spearman": _safe_rank_correlation(full_rank, weighted_rank, method="spearman"),
        "kendall": _safe_rank_correlation(full_rank, weighted_rank, method="kendall"),
        "max_abs_rank_delta": float((weighted_rank - full_rank).abs().max()),
    }


def _safe_rank_correlation(left: pd.Series, right: pd.Series, *, method: str) -> float | None:
    if left.nunique() < 2 or right.nunique() < 2:
        return None
    statistic = (
        stats.spearmanr(left, right).statistic
        if method == "spearman"
        else stats.kendalltau(left, right).statistic
    )
    return float(statistic) if np.isfinite(statistic) else None


def _write_comparison_table(path: Path, observed: dict[str, Any]) -> None:
    reported = {
        "row_count": 547638,
        "model_count": 39,
        "item_count": 14042,
        "subject_count": 57,
        "missing_cells": 0,
        "ability_spread": 0.5801880074063523,
        "median_subject_rank_range": 19.0,
        "maximum_subject_rank_range": 30.0,
        "diagnostic_weighted_spearman": 0.9979757085020243,
        "diagnostic_weighted_kendall": 0.9784075573549258,
        "diagnostic_weighted_max_abs_rank_delta": 2.0,
    }
    tolerances = {
        "ability_spread": 1e-12,
        "diagnostic_weighted_spearman": 1e-12,
        "diagnostic_weighted_kendall": 1e-12,
    }
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["metric", "reported", "observed", "tolerance", "status"],
        )
        writer.writeheader()
        for metric, reported_value in reported.items():
            observed_value = observed.get(metric)
            tolerance = tolerances.get(metric, 0.0)
            matches = (
                observed_value is not None
                and abs(float(observed_value) - reported_value) <= tolerance
            )
            writer.writerow(
                {
                    "metric": metric,
                    "reported": reported_value,
                    "observed": observed_value,
                    "tolerance": tolerance,
                    "status": "REPRODUCED" if matches else "CONTRADICTED",
                }
            )
