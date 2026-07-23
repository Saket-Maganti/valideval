from __future__ import annotations

import csv
import hashlib
import json
import shutil
import zipfile
from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path
from typing import Any

import pandas as pd

from valideval.diagnostics.panel_validity import write_panel_validity_report
from valideval.importers.wide_matrix import (
    build_matrix_from_wide_predictions,
    import_wide_predictions,
)
from valideval.psychometrics.irt_2pl import fit_irt_from_matrix
from valideval.real_panel.execution import (
    run_diagnostic_disagreement_audit,
    run_ranking_disagreement,
    run_real_panel_baselines,
    run_real_panel_ranking_audit,
    run_subject_instability_audit,
    subject_instability,
)

SUPPORTED_KAGGLE_BENCHMARKS = {"gsm8k", "bbh", "truthfulqa", "third_benchmark"}
PREDICTION_REQUIRED_FIELDS = ("benchmark", "model_id", "item_id", "prediction", "gold")
PREDICTION_STRICT_FIELDS = (*PREDICTION_REQUIRED_FIELDS, "correct")


def import_kaggle_outputs(
    *,
    input_dir: str | Path = "kaggle_outputs",
    output_root: str | Path = "data/external/kaggle_imported",
    cache_root: str | Path = "cache",
    results_root: str | Path = "results",
    strict: bool = False,
) -> dict[str, Any]:
    input_root = Path(input_dir)
    result_dir = Path(results_root) / "kaggle_import_v4"
    result_dir.mkdir(parents=True, exist_ok=True)
    zips = sorted(input_root.glob("**/*.zip")) if input_root.exists() else []
    if not zips:
        payload = {
            "schema_version": "v4",
            "status": "blocked_no_zips",
            "final_verdict": "KAGGLE_IMPORT_BLOCKED_NO_ZIPS",
            "input_dir": str(input_root),
            "zip_count": 0,
            "imports": [],
            "blocked_reason": "No Kaggle ZIP files were found under the input directory.",
        }
        _write_json(result_dir / "import_summary.json", payload)
        _write_text(result_dir / "blocked_report.md", _render_import_report(payload))
        return payload

    imports: list[dict[str, Any]] = []
    for zip_path in zips:
        imports.append(
            _import_single_zip(
                zip_path=zip_path,
                output_root=Path(output_root),
                cache_root=Path(cache_root),
                results_root=Path(results_root),
                strict=strict,
            )
        )

    payload = {
        "schema_version": "v4",
        "status": "ok",
        "final_verdict": "KAGGLE_IMPORTER_V4_IMPORTED_ZIPS",
        "input_dir": str(input_root),
        "zip_count": len(zips),
        "imports": imports,
    }
    _write_json(result_dir / "import_summary.json", payload)
    _write_text(result_dir / "import_summary.md", _render_import_report(payload))
    return payload


def post_import_analysis(
    *,
    benchmark: str,
    matrix: str | Path,
    predictions: str | Path | None,
    output: str | Path,
    cache_root: str | Path = "cache",
    results_root: str | Path = "results",
    execute: bool = False,
    bootstrap: int = 100,
) -> dict[str, Any]:
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    matrix_path = Path(matrix)
    predictions_path = Path(predictions) if predictions else None

    if not execute:
        payload = {
            "schema_version": "v4",
            "status": "dry_run_only",
            "benchmark": benchmark,
            "matrix": str(matrix_path),
            "predictions": str(predictions_path) if predictions_path else None,
            "analyses_planned": _post_import_analysis_names(benchmark),
            "evidence_state": "RESULT_REQUIRED_UNTIL_EXECUTED_ON_IMPORTED_MATRIX",
        }
        _write_json(output_dir / "post_import_analysis_manifest.json", payload)
        _write_text(
            output_dir / "post_import_analysis_report.md", _render_post_import_report(payload)
        )
        return payload

    if not matrix_path.exists():
        raise FileNotFoundError(f"Matrix file does not exist: {matrix_path}")
    if predictions_path is not None and not predictions_path.exists():
        raise FileNotFoundError(f"Predictions file does not exist: {predictions_path}")

    artifacts: dict[str, Any] = {}
    panel = write_panel_validity_report(
        matrix_path,
        output_dir / "panel_validity",
        min_models=30,
        min_items=20,
    )
    artifacts["panel_validity"] = str(output_dir / "panel_validity" / "panel_validity.json")

    irt = fit_irt_from_matrix(matrix_path, output_dir / "irt_proxy", model="2pl")
    artifacts["irt_proxy"] = str(output_dir / "irt_proxy" / "fit_summary.json")

    ranking_audit = run_real_panel_ranking_audit(
        matrix=matrix_path,
        predictions=predictions_path,
        output=output_dir / "ranking_audit",
    )
    artifacts["ranking_audit"] = ranking_audit["artifacts"]

    diagnostic = run_diagnostic_disagreement_audit(
        matrix=matrix_path,
        predictions=predictions_path,
        output=output_dir / "diagnostic_disagreement",
        irt=output_dir / "irt_proxy",
    )
    artifacts["diagnostic_disagreement"] = diagnostic["artifacts"]

    subject = run_subject_instability_audit(
        matrix=matrix_path,
        predictions=predictions_path,
        output=output_dir / "subject_instability",
    )
    artifacts["subject_instability"] = subject["artifacts"]

    baselines = run_real_panel_baselines(
        matrix=matrix_path,
        output=output_dir / "baselines",
        bootstrap=bootstrap,
    )
    artifacts["baselines"] = baselines["artifacts"]

    materiality = run_ranking_disagreement(
        matrix=matrix_path,
        output=output_dir / "bootstrap_materiality",
        irt=output_dir / "irt_proxy",
        bootstrap=bootstrap,
    )
    artifacts["bootstrap_materiality"] = materiality["artifacts"]

    ablation_path = output_dir / "diagnostic_family_ablation.csv"
    _write_diagnostic_family_ablation(ablation_path, ranking_audit, diagnostic, subject)
    artifacts["diagnostic_family_ablation"] = str(ablation_path)

    cross_benchmark_prepared = None
    mmlu_matrix = Path(cache_root) / "mmlu" / "wide" / "matrix.csv"
    if benchmark == "gsm8k" and mmlu_matrix.exists():
        cross_benchmark_prepared = {
            "status": "prepared",
            "suggested_command": (
                "python3 -m valideval cross-benchmark-analysis "
                "--benchmarks mmlu,gsm8k --cache-root cache --results-root results "
                "--output results/cross_benchmark --execute"
            ),
            "mmlu_matrix": str(mmlu_matrix),
            "gsm8k_matrix": str(matrix_path),
        }
        _write_json(output_dir / "cross_benchmark_prepared.json", cross_benchmark_prepared)

    payload = {
        "schema_version": "v4",
        "status": "ok",
        "final_verdict": "POST_IMPORT_ROUTER_EXECUTED",
        "benchmark": benchmark,
        "matrix": str(matrix_path),
        "predictions": str(predictions_path) if predictions_path else None,
        "panel_status": panel["status"],
        "irt_status": irt["status"],
        "artifacts": artifacts,
        "cross_benchmark_prepared": cross_benchmark_prepared,
        "evidence_state": "ARTIFACT_BACKED_IMPORTED_BENCHMARK_ANALYSIS",
        "claim_limits": [
            "Do not claim benchmark invalidity from one diagnostic.",
            "Do not claim cross-benchmark evidence unless cross-benchmark-analysis has at least two matrices.",
            "Treat proxy IRT as proxy psychometrics, not full parametric 2PL.",
        ],
    }
    _write_json(output_dir / "post_import_analysis_manifest.json", payload)
    _write_text(output_dir / "post_import_analysis_report.md", _render_post_import_report(payload))
    return payload


def cross_benchmark_analysis(
    *,
    benchmarks: Iterable[str],
    cache_root: str | Path = "cache",
    results_root: str | Path = "results",
    output: str | Path = "results/cross_benchmark",
    execute: bool = False,
) -> dict[str, Any]:
    benchmark_list = [name.strip() for name in benchmarks if name.strip()]
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    matrices = {
        benchmark: Path(cache_root) / benchmark / "wide" / "matrix.csv"
        for benchmark in benchmark_list
    }
    available = {benchmark: path for benchmark, path in matrices.items() if path.exists()}

    if not execute:
        payload = {
            "schema_version": "v4",
            "status": "dry_run_only",
            "benchmarks": benchmark_list,
            "available_matrices": {name: str(path) for name, path in available.items()},
            "analyses_planned": [
                "model_overlap",
                "ranking_correlations",
                "ability_correlations",
                "diagnostic_transfer",
                "instability_transfer",
                "materiality_transfer",
                "paper_tables",
            ],
        }
        _write_json(output_dir / "cross_benchmark_manifest.json", payload)
        _write_text(output_dir / "cross_benchmark_report.md", _render_cross_report(payload))
        return payload

    if len(available) < 2:
        payload = {
            "schema_version": "v4",
            "status": "blocked_need_second_matrix",
            "final_verdict": "CROSS_BENCHMARK_RUNNER_BLOCKED_NEED_SECOND_MATRIX",
            "benchmarks": benchmark_list,
            "available_matrices": {name: str(path) for name, path in available.items()},
            "blocked_reason": "At least two benchmark matrices are required.",
        }
        _write_json(output_dir / "cross_benchmark_manifest.json", payload)
        _write_text(output_dir / "blocked_report.md", _render_cross_report(payload))
        return payload

    frames = {name: _load_normalized_matrix(path) for name, path in available.items()}
    overlap_rows = _model_overlap_rows(frames)
    ranking_rows = _ranking_correlation_rows(frames)
    ability_rows = _ability_correlation_rows(frames, Path(results_root))
    instability_rows = _instability_transfer_rows(frames)
    diagnostic_rows = _diagnostic_transfer_rows(frames)
    materiality_rows = _materiality_transfer_rows(ranking_rows, instability_rows)

    _write_csv(output_dir / "model_overlap.csv", overlap_rows)
    _write_csv(output_dir / "ranking_correlations.csv", ranking_rows)
    _write_csv(output_dir / "ability_correlations.csv", ability_rows)
    _write_csv(output_dir / "diagnostic_transfer.csv", diagnostic_rows)
    _write_csv(output_dir / "instability_transfer.csv", instability_rows)
    _write_csv(output_dir / "materiality_transfer.csv", materiality_rows)

    paper_tables = _write_cross_benchmark_paper_tables(
        ranking_rows=ranking_rows,
        overlap_rows=overlap_rows,
    )
    figure_path = _write_cross_benchmark_svg(
        output_dir / "cross_benchmark_ranking_correlations.svg", ranking_rows
    )
    payload = {
        "schema_version": "v4",
        "status": "ok",
        "final_verdict": "CROSS_BENCHMARK_RUNNER_READY",
        "benchmarks": benchmark_list,
        "available_matrices": {name: str(path) for name, path in available.items()},
        "benchmark_count": len(available),
        "model_overlap": overlap_rows,
        "artifacts": {
            "model_overlap": str(output_dir / "model_overlap.csv"),
            "ranking_correlations": str(output_dir / "ranking_correlations.csv"),
            "ability_correlations": str(output_dir / "ability_correlations.csv"),
            "diagnostic_transfer": str(output_dir / "diagnostic_transfer.csv"),
            "instability_transfer": str(output_dir / "instability_transfer.csv"),
            "materiality_transfer": str(output_dir / "materiality_transfer.csv"),
            "figure": str(figure_path),
            "paper_tables": paper_tables,
        },
        "claim_limits": [
            "Correlations are protocol-scoped to overlapping model IDs.",
            "Cross-benchmark instability is not evidence of global benchmark invalidity.",
        ],
    }
    _write_json(output_dir / "cross_benchmark_manifest.json", payload)
    _write_text(output_dir / "cross_benchmark_report.md", _render_cross_report(payload))
    return payload


def _import_single_zip(
    *,
    zip_path: Path,
    output_root: Path,
    cache_root: Path,
    results_root: Path,
    strict: bool,
) -> dict[str, Any]:
    digest = _sha256(zip_path)
    benchmark = _detect_benchmark(zip_path)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    import_dir = _unique_dir(output_root / benchmark / f"import_{timestamp}_{digest[:12]}")
    import_dir.mkdir(parents=True, exist_ok=False)
    _safe_extract(zip_path, import_dir / "extracted")

    predictions_source = _find_file(import_dir / "extracted", "predictions.jsonl")
    if predictions_source is None:
        raise ValueError(f"{zip_path} does not contain predictions.jsonl")
    validation = _validate_prediction_schema(predictions_source, benchmark=benchmark, strict=strict)
    benchmark = validation["benchmark"]

    normalized_path = import_dir / "predictions.jsonl"
    matrix_path = import_dir / "matrix.csv"
    import_report_path = import_dir / "wide_import_report.md"
    matrix_report_path = import_dir / "matrix_report.md"
    import_summary = import_wide_predictions(
        predictions_source,
        normalized_path,
        benchmark=benchmark,
        source=f"kaggle_zip:{zip_path}",
        report_path=import_report_path,
    )
    matrix_summary = build_matrix_from_wide_predictions(
        normalized_path,
        matrix_path,
        report_path=matrix_report_path,
        allow_missing=False,
    )

    cache_predictions = cache_root / benchmark / "wide" / "predictions.jsonl"
    cache_matrix = cache_root / benchmark / "wide" / "matrix.csv"
    prediction_backup = _copy_current_artifact(normalized_path, cache_predictions)
    matrix_backup = _copy_current_artifact(matrix_path, cache_matrix)

    panel_output = results_root / benchmark / "panel_validity"
    panel = write_panel_validity_report(cache_matrix, panel_output, min_models=30, min_items=20)

    manifest = {
        "schema_version": "v4",
        "status": "imported",
        "zip_path": str(zip_path),
        "zip_sha256": digest,
        "benchmark": benchmark,
        "import_dir": str(import_dir),
        "normalized_predictions": str(normalized_path),
        "matrix": str(matrix_path),
        "cache_predictions": str(cache_predictions),
        "cache_matrix": str(cache_matrix),
        "cache_prediction_backup": str(prediction_backup) if prediction_backup else None,
        "cache_matrix_backup": str(matrix_backup) if matrix_backup else None,
        "schema_validation": validation,
        "wide_import": import_summary,
        "matrix_summary": matrix_summary,
        "panel_validity": {
            "status": panel["status"],
            "artifact": str(panel_output / "panel_validity.json"),
        },
    }
    _write_json(import_dir / "import_manifest.json", manifest)
    return manifest


def _detect_benchmark(zip_path: Path) -> str:
    path_tokens = {part.lower() for part in zip_path.parts}
    for token in ("gsm8k", "bbh", "truthfulqa"):
        if token in path_tokens or token in zip_path.name.lower():
            return token
    try:
        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            manifest_name = next(
                (name for name in names if Path(name).name == "manifest.json"), None
            )
            if manifest_name:
                manifest = json.loads(archive.read(manifest_name).decode("utf-8"))
                value = (
                    manifest.get("benchmark")
                    or manifest.get("benchmark_id")
                    or manifest.get("output_namespace")
                )
                if value:
                    return _normalize_benchmark_name(str(value))
            predictions_name = next(
                (name for name in names if Path(name).name == "predictions.jsonl"), None
            )
            if predictions_name:
                for line in archive.read(predictions_name).decode("utf-8").splitlines():
                    if line.strip():
                        return _normalize_benchmark_name(
                            str(json.loads(line).get("benchmark", "unknown"))
                        )
    except Exception:
        pass
    if "third_benchmark" in path_tokens or "third" in zip_path.name.lower():
        return "bbh"
    return "unknown"


def _normalize_benchmark_name(value: str) -> str:
    cleaned = value.strip().lower().replace("-", "_")
    if cleaned == "third_benchmark":
        return "bbh"
    return cleaned


def _validate_prediction_schema(path: Path, *, benchmark: str, strict: bool) -> dict[str, Any]:
    rows = _read_jsonl(path)
    errors: list[str] = []
    keys = PREDICTION_STRICT_FIELDS if strict else PREDICTION_REQUIRED_FIELDS
    duplicate_keys: Counter[tuple[str, str]] = Counter()
    benchmarks: Counter[str] = Counter()
    missing_predictions = 0
    non_bool_correct = 0
    unstable_item_ids = 0
    for index, row in enumerate(rows, start=1):
        for key in keys:
            if key not in row or row[key] in (None, ""):
                errors.append(f"row {index}: missing required field {key}")
        item_id = row.get("item_id")
        model_id = row.get("model_id")
        if not isinstance(item_id, str) or not item_id.strip():
            unstable_item_ids += 1
        if row.get("prediction") in (None, ""):
            missing_predictions += 1
        if strict and "correct" in row and not _is_bool_like(row["correct"]):
            non_bool_correct += 1
        if item_id is not None and model_id is not None:
            duplicate_keys[(str(model_id), str(item_id))] += 1
        if row.get("benchmark"):
            benchmarks[_normalize_benchmark_name(str(row["benchmark"]))] += 1
    duplicate_count = sum(count - 1 for count in duplicate_keys.values() if count > 1)
    if duplicate_count:
        errors.append(f"duplicate model/item rows: {duplicate_count}")
    if missing_predictions:
        errors.append(f"missing predictions: {missing_predictions}")
    if non_bool_correct:
        errors.append(f"non-boolean correctness values: {non_bool_correct}")
    if unstable_item_ids:
        errors.append(f"unstable item ids: {unstable_item_ids}")
    if errors:
        raise ValueError(
            f"Kaggle prediction schema validation failed for {path}: {'; '.join(errors[:8])}"
        )
    detected_benchmark = benchmarks.most_common(1)[0][0] if benchmarks else benchmark
    if detected_benchmark == "unknown":
        detected_benchmark = benchmark
    return {
        "status": "pass",
        "source": str(path),
        "strict": strict,
        "benchmark": detected_benchmark,
        "row_count": len(rows),
        "model_count": len({str(row.get("model_id")) for row in rows}),
        "item_count": len({str(row.get("item_id")) for row in rows}),
        "duplicate_model_item_rows": duplicate_count,
        "missing_prediction_count": missing_predictions,
        "correctness_field_checked": strict,
        "stable_item_id_check": "pass",
    }


def _post_import_analysis_names(benchmark: str) -> list[str]:
    names = [
        "panel_validity",
        "ranking_audit",
        "diagnostic_disagreement",
        "baselines",
        "scalable_irt_proxy",
        "bootstrap_materiality",
        "diagnostic_family_ablation",
    ]
    if benchmark == "gsm8k":
        names.append("cross_benchmark_preparation_if_mmlu_exists")
    return names


def _write_diagnostic_family_ablation(
    path: Path,
    ranking_audit: dict[str, Any],
    diagnostic: dict[str, Any],
    subject: dict[str, Any],
) -> None:
    rows = [
        {
            "family": "accuracy_only",
            "metric": "ability_spread",
            "value": ranking_audit.get("ability_spread"),
            "claim_state": "artifact_backed",
        },
        {
            "family": "diagnostic_weighted",
            "metric": "max_abs_rank_delta",
            "value": diagnostic.get("max_abs_rank_delta"),
            "claim_state": "proxy_diagnostic",
        },
        {
            "family": "subject_instability",
            "metric": "max_subject_rank_range",
            "value": subject.get("max_subject_rank_range"),
            "claim_state": "artifact_backed",
        },
    ]
    _write_csv(path, rows)


def _load_normalized_matrix(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if "model_id" in frame.columns:
        frame = frame.set_index("model_id")
    else:
        frame = frame.set_index(frame.columns[0])
    frame.index = frame.index.map(_normalize_model_id)
    frame = frame.groupby(frame.index).mean(numeric_only=True)
    return frame.apply(pd.to_numeric, errors="coerce")


def _model_overlap_rows(frames: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for left, right in combinations(sorted(frames), 2):
        left_models = set(frames[left].index)
        right_models = set(frames[right].index)
        overlap = sorted(left_models & right_models)
        rows.append(
            {
                "benchmark_a": left,
                "benchmark_b": right,
                "models_a": len(left_models),
                "models_b": len(right_models),
                "overlap_models": len(overlap),
                "overlap_model_ids": ";".join(overlap),
            }
        )
    return rows


def _ranking_correlation_rows(frames: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for left, right in combinations(sorted(frames), 2):
        left_scores = frames[left].mean(axis=1, skipna=True)
        right_scores = frames[right].mean(axis=1, skipna=True)
        shared = sorted(set(left_scores.index) & set(right_scores.index))
        row: dict[str, Any] = {
            "benchmark_a": left,
            "benchmark_b": right,
            "overlap_models": len(shared),
        }
        if len(shared) >= 2:
            row["spearman_accuracy"] = _corr(
                left_scores.loc[shared], right_scores.loc[shared], "spearman"
            )
            row["kendall_accuracy"] = _corr(
                left_scores.loc[shared], right_scores.loc[shared], "kendall"
            )
        else:
            row["spearman_accuracy"] = None
            row["kendall_accuracy"] = None
        rows.append(row)
    return rows


def _ability_correlation_rows(
    frames: dict[str, pd.DataFrame], results_root: Path
) -> list[dict[str, Any]]:
    abilities = {
        benchmark: _load_ability_series(benchmark, frame, results_root)
        for benchmark, frame in frames.items()
    }
    rows: list[dict[str, Any]] = []
    for left, right in combinations(sorted(abilities), 2):
        shared = sorted(set(abilities[left].index) & set(abilities[right].index))
        rows.append(
            {
                "benchmark_a": left,
                "benchmark_b": right,
                "overlap_models": len(shared),
                "spearman_ability": _corr(
                    abilities[left].loc[shared], abilities[right].loc[shared], "spearman"
                )
                if len(shared) >= 2
                else None,
                "ability_source_a": abilities[left].attrs.get("source", "matrix_accuracy_proxy"),
                "ability_source_b": abilities[right].attrs.get("source", "matrix_accuracy_proxy"),
            }
        )
    return rows


def _load_ability_series(benchmark: str, frame: pd.DataFrame, results_root: Path) -> pd.Series:
    candidates = [
        results_root / benchmark / "irt_proxy" / "model_abilities.csv",
        results_root / benchmark / "post_import" / "irt_proxy" / "model_abilities.csv",
        results_root / benchmark / "model_abilities.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            ability = pd.read_csv(candidate)
            if {"model_id", "ability_proxy"}.issubset(ability.columns):
                series = pd.Series(
                    ability["ability_proxy"].astype(float).to_numpy(),
                    index=ability["model_id"].map(_normalize_model_id),
                )
                series.attrs["source"] = str(candidate)
                return series
    series = frame.mean(axis=1, skipna=True)
    series.attrs["source"] = "matrix_accuracy_proxy"
    return series


def _instability_transfer_rows(frames: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    instabilities = {}
    for benchmark, frame in frames.items():
        bundle = load_response_matrix_from_frame(frame)
        _, instability, _ = subject_instability(bundle["frame"], bundle["item_metadata"])
        if instability.empty:
            instabilities[benchmark] = pd.Series(dtype=float)
        else:
            instabilities[benchmark] = pd.Series(
                instability["subject_rank_range"].astype(float).to_numpy(),
                index=instability["model_id"].map(_normalize_model_id),
            )
    rows: list[dict[str, Any]] = []
    for left, right in combinations(sorted(instabilities), 2):
        shared = sorted(set(instabilities[left].index) & set(instabilities[right].index))
        rows.append(
            {
                "benchmark_a": left,
                "benchmark_b": right,
                "overlap_models": len(shared),
                "spearman_subject_instability": _corr(
                    instabilities[left].loc[shared],
                    instabilities[right].loc[shared],
                    "spearman",
                )
                if len(shared) >= 2
                else None,
            }
        )
    return rows


def _diagnostic_transfer_rows(frames: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    item_disagreement = {
        benchmark: (
            frame.mean(axis=0, skipna=True) * (1.0 - frame.mean(axis=0, skipna=True))
        ).mean()
        for benchmark, frame in frames.items()
    }
    for left, right in combinations(sorted(frames), 2):
        rows.append(
            {
                "benchmark_a": left,
                "benchmark_b": right,
                "diagnostic": "mean_item_disagreement_proxy",
                "value_a": float(item_disagreement[left]),
                "value_b": float(item_disagreement[right]),
                "absolute_delta": float(abs(item_disagreement[left] - item_disagreement[right])),
                "claim_state": "proxy_transfer_summary",
            }
        )
    return rows


def _materiality_transfer_rows(
    ranking_rows: list[dict[str, Any]],
    instability_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    instability_by_pair = {
        (row["benchmark_a"], row["benchmark_b"]): row.get("spearman_subject_instability")
        for row in instability_rows
    }
    rows = []
    for row in ranking_rows:
        key = (row["benchmark_a"], row["benchmark_b"])
        rows.append(
            {
                "benchmark_a": row["benchmark_a"],
                "benchmark_b": row["benchmark_b"],
                "overlap_models": row["overlap_models"],
                "ranking_spearman": row.get("spearman_accuracy"),
                "instability_spearman": instability_by_pair.get(key),
                "materiality_note": "interpret only with overlapping models and imported artifact manifests",
            }
        )
    return rows


def load_response_matrix_from_frame(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    temp = frame.copy()
    temp.index.name = "model_id"
    item_metadata = pd.DataFrame(
        [_split_item_column(column) for column in temp.columns],
        columns=["column", "subject", "item_id"],
    )
    return {"frame": temp, "item_metadata": item_metadata}


def _write_cross_benchmark_paper_tables(
    *,
    ranking_rows: list[dict[str, Any]],
    overlap_rows: list[dict[str, Any]],
) -> list[str]:
    table_dir = Path("paper") / "tables"
    if not table_dir.exists():
        return []
    ranking_path = table_dir / "cross_benchmark_ranking_correlations.csv"
    overlap_path = table_dir / "cross_benchmark_model_overlap.csv"
    _write_csv(ranking_path, ranking_rows)
    _write_csv(overlap_path, overlap_rows)
    return [str(ranking_path), str(overlap_path)]


def _write_cross_benchmark_svg(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    bars = []
    for idx, row in enumerate(rows):
        value = row.get("spearman_accuracy")
        value = 0.0 if value is None else max(min(float(value), 1.0), -1.0)
        width = int((value + 1.0) * 100)
        y = 30 + idx * 34
        label = f"{row['benchmark_a']} vs {row['benchmark_b']}: {value:.3f}"
        bars.append(f'<text x="10" y="{y}" font-size="12">{label}</text>')
        bars.append(f'<rect x="180" y="{y - 12}" width="{width}" height="16" fill="#4C78A8"/>')
    height = max(80, 40 + len(rows) * 34)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="{height}" '
        f'viewBox="0 0 420 {height}">' + "".join(bars) + "</svg>\n"
    )
    path.write_text(svg, encoding="utf-8")
    return path


def _safe_extract(zip_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(zip_path) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise ValueError(f"Corrupt ZIP member in {zip_path}: {bad_member}")
        root = destination.resolve()
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if not str(target).startswith(str(root)):
                raise ValueError(f"Unsafe ZIP path: {member.filename}")
        archive.extractall(destination)


def _find_file(root: Path, name: str) -> Path | None:
    matches = sorted(path for path in root.rglob(name) if path.is_file())
    return matches[0] if matches else None


def _copy_current_artifact(source: Path, destination: Path) -> Path | None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    if destination.exists() and _sha256(destination) != _sha256(source):
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup = destination.with_name(f"{destination.name}.backup_{timestamp}")
        backup = _unique_file(backup)
        shutil.copy2(destination, backup)
    shutil.copy2(source, destination)
    return backup


def _unique_dir(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 10_000):
        candidate = path.with_name(f"{path.name}_v{index:04d}")
        if not candidate.exists():
            return candidate
    raise FileExistsError(f"Could not allocate unique directory for {path}")


def _unique_file(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 10_000):
        candidate = path.with_name(f"{path.name}.v{index:04d}")
        if not candidate.exists():
            return candidate
    raise FileExistsError(f"Could not allocate unique file for {path}")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
    if not rows:
        raise ValueError(f"Prediction file has zero rows: {path}")
    return rows


def _is_bool_like(value: Any) -> bool:
    if isinstance(value, bool):
        return True
    if isinstance(value, int | float):
        return value in {0, 1}
    if isinstance(value, str):
        return value.strip().lower() in {"true", "false", "1", "0", "yes", "no"}
    return False


def _normalize_model_id(value: Any) -> str:
    return str(value).strip().lower().replace(" ", "_")


def _split_item_column(column: str) -> tuple[str, str, str]:
    if "::" in str(column):
        subject, item_id = str(column).split("::", 1)
    else:
        subject, item_id = "default", str(column)
    return str(column), subject, item_id


def _corr(left: pd.Series, right: pd.Series, method: str) -> float | None:
    if len(left) < 2 or len(right) < 2:
        return None
    value = left.astype(float).corr(right.astype(float), method=method)
    if pd.isna(value):
        return None
    return float(value)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _render_import_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Kaggle Output Import V4 Report",
        "",
        f"- Status: `{payload['status']}`",
        f"- Final verdict: `{payload['final_verdict']}`",
        f"- ZIP count: {payload['zip_count']}",
    ]
    if payload.get("blocked_reason"):
        lines.append(f"- Blocked reason: {payload['blocked_reason']}")
    for record in payload.get("imports", []):
        lines.extend(
            [
                "",
                f"## `{record['benchmark']}`",
                f"- ZIP SHA256: `{record['zip_sha256']}`",
                f"- Import directory: `{record['import_dir']}`",
                f"- Cache matrix: `{record['cache_matrix']}`",
                f"- Panel-validity status: `{record['panel_validity']['status']}`",
            ]
        )
    return "\n".join(lines) + "\n"


def _render_post_import_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Post-Import Analysis Router V4 Report",
        "",
        f"- Status: `{payload['status']}`",
        f"- Benchmark: `{payload['benchmark']}`",
        f"- Matrix: `{payload['matrix']}`",
    ]
    if payload["status"] == "dry_run_only":
        lines.append("- Evidence state: `RESULT_REQUIRED_UNTIL_EXECUTED_ON_IMPORTED_MATRIX`")
        lines.extend([f"- Planned: `{name}`" for name in payload["analyses_planned"]])
    else:
        lines.extend(
            [
                f"- Final verdict: `{payload['final_verdict']}`",
                f"- Panel status: `{payload['panel_status']}`",
                f"- IRT status: `{payload['irt_status']}`",
                "- Claim boundary: imported analyses are benchmark/protocol-scoped.",
            ]
        )
    return "\n".join(lines) + "\n"


def _render_cross_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Cross-Benchmark Analysis V4 Report",
        "",
        f"- Status: `{payload['status']}`",
    ]
    if "final_verdict" in payload:
        lines.append(f"- Final verdict: `{payload['final_verdict']}`")
    lines.append(f"- Available matrices: {len(payload.get('available_matrices', {}))}")
    if payload.get("blocked_reason"):
        lines.append(f"- Blocked reason: {payload['blocked_reason']}")
    if payload.get("model_overlap"):
        lines.append("")
        lines.append("## Model Overlap")
        for row in payload["model_overlap"]:
            lines.append(
                f"- `{row['benchmark_a']}` vs `{row['benchmark_b']}`: {row['overlap_models']} overlapping models"
            )
    return "\n".join(lines) + "\n"
