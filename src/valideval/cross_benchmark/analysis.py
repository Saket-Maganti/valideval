from __future__ import annotations

import csv
import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from valideval.cross_benchmark.gates import (
    CROSS_BENCHMARK_EXPLORATORY_FAMILY_LEVEL_ONLY,
    CROSS_BENCHMARK_READY_EXACT_COMMON_PANEL,
    BenchmarkGateInput,
    CrossBenchmarkGateThresholds,
    evaluate_cross_benchmark_gate,
)
from valideval.execution.manifest import (
    NON_EVIDENCE_FIXTURE,
    atomic_write_json,
    atomic_write_text,
    sha256_file,
)
from valideval.stats.multiplicity import adjust_p_values

TRANSFER_STATES = frozenset(
    {
        "TRANSFER_SUPPORTED",
        "TRANSFER_PARTIAL",
        "TRANSFER_BENCHMARK_SPECIFIC",
        "TRANSFER_NOT_SUPPORTED",
        "UNDERPOWERED",
        "BLOCKED",
    }
)


class CrossBenchmarkAnalysisError(ValueError):
    """Raised when a matrix or preregistered analysis input is invalid."""


@dataclass(frozen=True, slots=True)
class CrossBenchmarkAnalysisConfig:
    top_k: int = 5
    bootstrap_iterations: int = 1_000
    permutation_iterations: int = 1_000
    random_seed: int = 0
    alpha: float = 0.05
    multiple_testing_method: str = "bh"
    minimum_models_for_inference: int = 8
    transfer_supported_spearman: float = 0.70
    transfer_partial_spearman: float = 0.40
    benchmark_specific_range: float = 0.35

    def __post_init__(self) -> None:
        if self.top_k <= 0:
            raise ValueError("top_k must be positive")
        if self.bootstrap_iterations < 0 or self.permutation_iterations < 0:
            raise ValueError("resampling iteration counts must be nonnegative")
        if not 0 < self.alpha < 1:
            raise ValueError("alpha must be in (0, 1)")
        if self.minimum_models_for_inference < 3:
            raise ValueError("minimum_models_for_inference must be at least 3")

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, Any] | None,
    ) -> CrossBenchmarkAnalysisConfig:
        if payload is None:
            return cls()
        known = set(cls.__dataclass_fields__)
        unknown = sorted(set(payload).difference(known))
        if unknown:
            raise ValueError(f"Unknown cross-benchmark analysis settings: {unknown}")
        return cls(**dict(payload))


def run_cross_benchmark_analysis(
    matrices: Mapping[str, str | Path | pd.DataFrame],
    *,
    output_dir: str | Path,
    benchmark_metadata: Mapping[str, Mapping[str, Any]] | None = None,
    model_family_by_id: Mapping[str, str] | None = None,
    gate_thresholds: CrossBenchmarkGateThresholds | Mapping[str, Any] | None = None,
    analysis_config: CrossBenchmarkAnalysisConfig | Mapping[str, Any] | None = None,
    diagnostic_scores: Mapping[str, Mapping[str, Mapping[str, float]]] | None = None,
    score_reliabilities: Mapping[str, float] | None = None,
    execute: bool = True,
) -> dict[str, Any]:
    """Run fail-closed exact-panel or explicitly exploratory family analysis.

    ``matrices`` must be response matrices with exact model checkpoint IDs as
    the index (or a ``model_id`` column). Exact-model estimands are computed
    only after the V5 overlap gate passes and always use the intersection.
    """

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    config = (
        analysis_config
        if isinstance(analysis_config, CrossBenchmarkAnalysisConfig)
        else CrossBenchmarkAnalysisConfig.from_mapping(analysis_config)
    )
    thresholds = (
        gate_thresholds
        if isinstance(gate_thresholds, CrossBenchmarkGateThresholds)
        else CrossBenchmarkGateThresholds.from_mapping(gate_thresholds)
    )
    if len(matrices) < 2:
        raise CrossBenchmarkAnalysisError("At least two response matrices are required")
    frames = {
        benchmark_id: _load_response_matrix(value, benchmark_id)
        for benchmark_id, value in sorted(matrices.items())
    }
    metadata = benchmark_metadata or {}
    global_families = {str(key): str(value) for key, value in (model_family_by_id or {}).items()}
    gate_inputs = {
        benchmark_id: _build_gate_input(
            benchmark_id,
            frame,
            metadata.get(benchmark_id, {}),
            global_families,
        )
        for benchmark_id, frame in frames.items()
    }
    gate = evaluate_cross_benchmark_gate(gate_inputs, thresholds=thresholds)
    atomic_write_json(destination / "cross_benchmark_gate_v5.json", gate)

    preflight = {
        "schema_version": "valideval.cross_benchmark_analysis.v5",
        "status": "dry_run_only" if not execute else "gate_evaluated",
        "execute": execute,
        "gate": gate,
        "analysis_config": asdict(config),
        "estimands": [
            "exact_model_rank_transfer",
            "ability_transfer",
            "diagnostic_transfer",
            "construct_specialization",
            "ranking_decision_stability",
            "family_level_transfer_exploratory",
        ],
        "claim_limits": [
            "No universal transfer claim is permitted.",
            "Exact-model estimands use only exact checkpoint intersections.",
            "Family-level transfer is separately labeled exploratory.",
        ],
    }
    raw_claim_limits = preflight.get("claim_limits", [])
    claim_limits = (
        [str(value) for value in raw_claim_limits] if isinstance(raw_claim_limits, list) else []
    )
    if not execute:
        atomic_write_json(destination / "analysis_manifest_v5.json", preflight)
        return preflight

    gate_status = gate["status"]
    if gate_status not in {
        CROSS_BENCHMARK_READY_EXACT_COMMON_PANEL,
        CROSS_BENCHMARK_EXPLORATORY_FAMILY_LEVEL_ONLY,
    }:
        payload = {
            **preflight,
            "status": "blocked",
            "transfer_conclusion": "BLOCKED",
            "blocked_reason": gate["reasons"],
            "artifacts": {"gate": str(destination / "cross_benchmark_gate_v5.json")},
        }
        atomic_write_json(destination / "analysis_manifest_v5.json", payload)
        atomic_write_text(destination / "analysis_summary_v5.md", _render_summary(payload))
        return payload

    common_models = list(gate.get("exact_common_model_ids", []))
    family_map = dict(gate.get("exact_common_model_families", {}))
    if gate_status == CROSS_BENCHMARK_EXPLORATORY_FAMILY_LEVEL_ONLY:
        family_rows = _family_level_exploratory_rows(frames, gate_inputs, config)
        family_path = destination / "family_level_exploratory_transfer_v5.csv"
        _write_csv(family_path, family_rows)
        payload = {
            **preflight,
            "status": "exploratory_family_level_only",
            "transfer_conclusion": "UNDERPOWERED",
            "exact_model_analysis_executed": False,
            "family_level_analysis_executed": True,
            "artifacts": {
                "gate": str(destination / "cross_benchmark_gate_v5.json"),
                "family_level_exploratory": str(family_path),
            },
            "claim_limits": claim_limits
            + ["Family-level summaries do not identify exact-checkpoint transfer."],
        }
        atomic_write_json(destination / "analysis_manifest_v5.json", payload)
        atomic_write_text(destination / "analysis_summary_v5.md", _render_summary(payload))
        return payload

    if not common_models:
        raise CrossBenchmarkAnalysisError("Exact-ready gate returned an empty common panel")
    common_frames = {name: frame.loc[common_models] for name, frame in frames.items()}
    score_vectors = {name: frame.mean(axis=1, skipna=True) for name, frame in common_frames.items()}

    overlap_rows = _overlap_rows(frames, gate_inputs)
    rank_rows = _rank_transfer_rows(
        score_vectors,
        config,
        score_reliabilities=score_reliabilities or {},
    )
    _apply_multiple_testing(rank_rows, method=config.multiple_testing_method)
    family_rows = _family_deduplicated_rows(score_vectors, family_map, config)
    leave_one_family_out_rows = _leave_one_family_out_rows(
        score_vectors,
        family_map,
        config,
    )
    interaction = _interaction_summary(score_vectors)
    clustering_rows = _benchmark_clustering_rows(score_vectors)
    diagnostic_rows = _diagnostic_transfer_rows(
        diagnostic_scores or {},
        common_models,
        config,
    )
    condition_rows = _condition_sensitivity_rows(metadata, common_models, config)

    artifact_rows = {
        "overlap_audit": (destination / "overlap_audit_v5.csv", overlap_rows),
        "rank_transfer": (destination / "rank_transfer_v5.csv", rank_rows),
        "family_deduplicated_transfer": (
            destination / "family_deduplicated_transfer_v5.csv",
            family_rows,
        ),
        "leave_one_family_out": (
            destination / "leave_one_family_out_v5.csv",
            leave_one_family_out_rows,
        ),
        "benchmark_clustering": (
            destination / "benchmark_clustering_v5.csv",
            clustering_rows,
        ),
        "diagnostic_transfer": (
            destination / "diagnostic_transfer_v5.csv",
            diagnostic_rows,
        ),
        "condition_sensitivity": (
            destination / "condition_sensitivity_v5.csv",
            condition_rows,
        ),
    }
    for path, rows in artifact_rows.values():
        _write_csv(path, rows)
    interaction_path = destination / "model_benchmark_interaction_v5.json"
    atomic_write_json(interaction_path, interaction)

    evidence_state = gate.get("evidence_state", "ARTIFACT_GATED")
    conclusion = _transfer_conclusion(rank_rows, config, len(common_models))
    if evidence_state == NON_EVIDENCE_FIXTURE:
        conclusion = "UNDERPOWERED"
    payload = {
        **preflight,
        "status": "ok",
        "transfer_conclusion": conclusion,
        "exact_model_analysis_executed": True,
        "family_level_analysis_executed": True,
        "exact_common_model_ids": common_models,
        "exact_common_model_count": len(common_models),
        "evidence_state": evidence_state,
        "claim_state": (
            "NON_EVIDENCE_FIXTURE_ONLY"
            if evidence_state == NON_EVIDENCE_FIXTURE
            else "PROTOCOL_SCOPED_ARTIFACT_RESULT"
        ),
        "artifacts": {
            "gate": str(destination / "cross_benchmark_gate_v5.json"),
            **{name: str(path) for name, (path, _) in artifact_rows.items()},
            "model_benchmark_interaction": str(interaction_path),
        },
        "artifact_hashes": {name: sha256_file(path) for name, (path, _) in artifact_rows.items()}
        | {"model_benchmark_interaction": sha256_file(interaction_path)},
    }
    atomic_write_json(destination / "analysis_manifest_v5.json", payload)
    atomic_write_text(destination / "analysis_summary_v5.md", _render_summary(payload))
    return payload


analyze_cross_benchmark = run_cross_benchmark_analysis


def _load_response_matrix(
    value: str | Path | pd.DataFrame,
    benchmark_id: str,
) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        frame = value.copy()
    else:
        path = Path(value)
        if not path.is_file():
            raise FileNotFoundError(f"{benchmark_id} matrix does not exist: {path}")
        try:
            frame = pd.read_csv(path)
        except pd.errors.ParserError as exc:
            raise CrossBenchmarkAnalysisError(f"{benchmark_id} matrix is malformed: {exc}") from exc
    if "model_id" in frame.columns:
        frame = frame.set_index("model_id")
    elif isinstance(frame.index, pd.RangeIndex):
        first_column = str(frame.columns[0]) if len(frame.columns) else ""
        if first_column.lower().startswith("unnamed"):
            frame = frame.set_index(frame.columns[0])
        else:
            raise CrossBenchmarkAnalysisError(
                f"{benchmark_id} matrix requires exact model IDs as index or model_id column"
            )
    frame.index = frame.index.map(str)
    frame.index.name = "model_id"
    if frame.index.has_duplicates:
        duplicates = sorted(frame.index[frame.index.duplicated()].unique())
        raise CrossBenchmarkAnalysisError(
            f"{benchmark_id} matrix has duplicate model IDs: {duplicates}"
        )
    if frame.columns.duplicated().any():
        raise CrossBenchmarkAnalysisError(f"{benchmark_id} matrix has duplicate item columns")
    if frame.empty or frame.shape[1] == 0:
        raise CrossBenchmarkAnalysisError(f"{benchmark_id} matrix is empty")
    numeric = frame.apply(pd.to_numeric, errors="coerce")
    introduced_missing = numeric.isna() & ~frame.isna()
    if introduced_missing.any().any():
        raise CrossBenchmarkAnalysisError(
            f"{benchmark_id} matrix contains nonnumeric response values"
        )
    observed = numeric.to_numpy(dtype=float)
    finite = observed[np.isfinite(observed)]
    if finite.size and not np.isin(finite, [0.0, 1.0]).all():
        raise CrossBenchmarkAnalysisError(
            f"{benchmark_id} matrix responses must be binary 0/1 or missing"
        )
    return numeric.sort_index()


def _build_gate_input(
    benchmark_id: str,
    frame: pd.DataFrame,
    metadata: Mapping[str, Any],
    global_families: Mapping[str, str],
) -> BenchmarkGateInput:
    local_families = metadata.get("model_family_by_id", global_families)
    if not isinstance(local_families, Mapping):
        raise CrossBenchmarkAnalysisError(
            f"{benchmark_id}: model_family_by_id metadata must be a mapping"
        )
    nonmissing = int(frame.notna().to_numpy().sum())
    total = int(frame.shape[0] * frame.shape[1])
    frame_models = set(frame.index)
    family_mapping = {
        str(key): str(value) for key, value in local_families.items() if str(key) in frame_models
    }
    integrity_value = metadata.get("data_integrity", "pass")
    if integrity_value is True:
        integrity = "pass"
    elif integrity_value is False:
        integrity = "fail"
    else:
        integrity = str(integrity_value)
    if frame.notna().sum(axis=1).eq(0).any():
        integrity = "fail_no_usable_rows_for_one_or_more_models"
    return BenchmarkGateInput(
        benchmark_id=benchmark_id,
        model_ids=frozenset(frame.index),
        model_family_by_id=family_mapping,
        config_class=str(metadata.get("config_class", "")),
        usable_items=int(metadata.get("usable_items", frame.notna().any(axis=0).sum())),
        extraction_reliability=float(
            metadata.get("extraction_reliability", nonmissing / total if total else 0.0)
        ),
        data_integrity=integrity,
        evidence_state=str(metadata.get("evidence_state", "RESULT_REQUIRED")),
        study_id=str(metadata["study_id"]) if metadata.get("study_id") is not None else None,
    )


def _overlap_rows(
    frames: Mapping[str, pd.DataFrame],
    gate_inputs: Mapping[str, BenchmarkGateInput],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for left, right in combinations(sorted(frames), 2):
        common = sorted(set(frames[left].index).intersection(frames[right].index))
        families = {
            gate_inputs[left].model_family_by_id[model]
            for model in common
            if model in gate_inputs[left].model_family_by_id
        }
        rows.append(
            {
                "benchmark_a": left,
                "benchmark_b": right,
                "models_a": len(frames[left]),
                "models_b": len(frames[right]),
                "exact_common_models": len(common),
                "independent_common_families": len(families),
                "exact_common_model_ids": "|".join(common),
            }
        )
    return rows


def _rank_transfer_rows(
    score_vectors: Mapping[str, pd.Series],
    config: CrossBenchmarkAnalysisConfig,
    *,
    score_reliabilities: Mapping[str, float],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pair_index, (left, right) in enumerate(combinations(sorted(score_vectors), 2)):
        paired = pd.concat(
            [score_vectors[left].rename("left"), score_vectors[right].rename("right")],
            axis=1,
            join="inner",
        ).dropna()
        x = paired["left"].to_numpy(dtype=float)
        y = paired["right"].to_numpy(dtype=float)
        spearman = _safe_correlation(stats.spearmanr, x, y)
        kendall = _safe_correlation(stats.kendalltau, x, y)
        ci_lower, ci_upper = _bootstrap_spearman_ci(
            x,
            y,
            iterations=config.bootstrap_iterations,
            seed=config.random_seed + pair_index,
            alpha=config.alpha,
        )
        permutation_p = _permutation_p_value(
            x,
            y,
            observed=spearman,
            iterations=config.permutation_iterations,
            seed=config.random_seed + 10_000 + pair_index,
        )
        reliability_a = score_reliabilities.get(left)
        reliability_b = score_reliabilities.get(right)
        attenuation_corrected = _attenuation_correct(
            spearman,
            reliability_a,
            reliability_b,
        )
        pair_agreement, comparable_pairs = _pairwise_order_agreement(x, y)
        top_k = min(config.top_k, len(paired))
        top_left = _top_k_ids(paired["left"], top_k)
        top_right = _top_k_ids(paired["right"], top_k)
        overlap = len(set(top_left).intersection(top_right))
        union = len(set(top_left).union(top_right))
        rows.append(
            {
                "benchmark_a": left,
                "benchmark_b": right,
                "exact_common_models": len(paired),
                "spearman": spearman,
                "spearman_ci_lower": ci_lower,
                "spearman_ci_upper": ci_upper,
                "kendall_tau": kendall,
                "permutation_p_value": permutation_p,
                "attenuation_corrected_spearman": attenuation_corrected,
                "score_reliability_a": reliability_a,
                "score_reliability_b": reliability_b,
                "pairwise_order_agreement": pair_agreement,
                "comparable_model_pairs": comparable_pairs,
                "top_k": top_k,
                "top_k_overlap_count": overlap,
                "top_k_jaccard": overlap / union if union else None,
                "effect_size": spearman,
            }
        )
    return rows


def _family_deduplicated_rows(
    score_vectors: Mapping[str, pd.Series],
    family_map: Mapping[str, str],
    config: CrossBenchmarkAnalysisConfig,
) -> list[dict[str, Any]]:
    family_scores = {
        benchmark: pd.DataFrame(
            {
                "score": vector,
                "family": [family_map[model_id] for model_id in vector.index],
            }
        )
        .groupby("family", sort=True)["score"]
        .mean()
        for benchmark, vector in score_vectors.items()
    }
    rows: list[dict[str, Any]] = []
    for left, right in combinations(sorted(family_scores), 2):
        paired = pd.concat(
            [family_scores[left].rename("left"), family_scores[right].rename("right")],
            axis=1,
            join="inner",
        ).dropna()
        x = paired["left"].to_numpy(dtype=float)
        y = paired["right"].to_numpy(dtype=float)
        rows.append(
            {
                "benchmark_a": left,
                "benchmark_b": right,
                "common_families": len(paired),
                "family_spearman": _safe_correlation(stats.spearmanr, x, y),
                "family_kendall_tau": _safe_correlation(stats.kendalltau, x, y),
                "minimum_models_for_inference": config.minimum_models_for_inference,
                "analysis_scope": "family_deduplicated",
            }
        )
    return rows


def _leave_one_family_out_rows(
    score_vectors: Mapping[str, pd.Series],
    family_map: Mapping[str, str],
    config: CrossBenchmarkAnalysisConfig,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    families = sorted(set(family_map.values()))
    for left, right in combinations(sorted(score_vectors), 2):
        for family in families:
            keep = [model for model in score_vectors[left].index if family_map[model] != family]
            paired = pd.concat(
                [
                    score_vectors[left].loc[keep].rename("left"),
                    score_vectors[right].loc[keep].rename("right"),
                ],
                axis=1,
                join="inner",
            ).dropna()
            rows.append(
                {
                    "benchmark_a": left,
                    "benchmark_b": right,
                    "excluded_family": family,
                    "remaining_models": len(paired),
                    "spearman": _safe_correlation(
                        stats.spearmanr,
                        paired["left"].to_numpy(dtype=float),
                        paired["right"].to_numpy(dtype=float),
                    ),
                    "underpowered": len(paired) < config.minimum_models_for_inference,
                }
            )
    return rows


def _interaction_summary(score_vectors: Mapping[str, pd.Series]) -> dict[str, Any]:
    frame = pd.DataFrame(score_vectors).sort_index()
    values = frame.to_numpy(dtype=float)
    grand = float(np.nanmean(values))
    model_effect = np.nanmean(values, axis=1, keepdims=True) - grand
    benchmark_effect = np.nanmean(values, axis=0, keepdims=True) - grand
    residual = values - grand - model_effect - benchmark_effect
    total_variance = float(np.nanvar(values, ddof=1)) if values.size > 1 else 0.0
    interaction_variance = float(np.nanvar(residual, ddof=1)) if values.size > 1 else 0.0
    return {
        "schema_version": "valideval.model_benchmark_interaction.v5",
        "status": "ok",
        "model_count": frame.shape[0],
        "benchmark_count": frame.shape[1],
        "grand_mean_accuracy": grand,
        "total_variance": total_variance,
        "model_by_benchmark_interaction_variance": interaction_variance,
        "interaction_variance_fraction": (
            interaction_variance / total_variance if total_variance > 0 else None
        ),
        "interpretation": "descriptive_interaction_effect_not_universal_transfer",
    }


def _benchmark_clustering_rows(
    score_vectors: Mapping[str, pd.Series],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for left, right in combinations(sorted(score_vectors), 2):
        paired = pd.concat(
            [score_vectors[left].rename("left"), score_vectors[right].rename("right")],
            axis=1,
            join="inner",
        ).dropna()
        correlation = _safe_correlation(
            stats.spearmanr,
            paired["left"].to_numpy(dtype=float),
            paired["right"].to_numpy(dtype=float),
        )
        rows.append(
            {
                "benchmark_a": left,
                "benchmark_b": right,
                "spearman_similarity": correlation,
                "rank_distance": 1.0 - correlation if correlation is not None else None,
                "method": "pairwise_spearman_distance",
            }
        )
    return rows


def _diagnostic_transfer_rows(
    diagnostic_scores: Mapping[str, Mapping[str, Mapping[str, float]]],
    common_models: Sequence[str],
    config: CrossBenchmarkAnalysisConfig,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for left, right in combinations(sorted(diagnostic_scores), 2):
        common_diagnostics = sorted(
            set(diagnostic_scores[left]).intersection(diagnostic_scores[right])
        )
        for diagnostic in common_diagnostics:
            left_scores = diagnostic_scores[left][diagnostic]
            right_scores = diagnostic_scores[right][diagnostic]
            usable = [
                model for model in common_models if model in left_scores and model in right_scores
            ]
            x = np.array([float(left_scores[model]) for model in usable], dtype=float)
            y = np.array([float(right_scores[model]) for model in usable], dtype=float)
            rows.append(
                {
                    "benchmark_a": left,
                    "benchmark_b": right,
                    "diagnostic_family": diagnostic,
                    "exact_common_models": len(usable),
                    "spearman": _safe_correlation(stats.spearmanr, x, y),
                    "underpowered": len(usable) < config.minimum_models_for_inference,
                }
            )
    return rows


def _condition_sensitivity_rows(
    metadata: Mapping[str, Mapping[str, Any]],
    common_models: Sequence[str],
    config: CrossBenchmarkAnalysisConfig,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for benchmark_id, payload in sorted(metadata.items()):
        condition_scores = payload.get("condition_scores", {})
        if not isinstance(condition_scores, Mapping):
            continue
        for left, right in combinations(sorted(condition_scores), 2):
            left_scores = condition_scores[left]
            right_scores = condition_scores[right]
            if not isinstance(left_scores, Mapping) or not isinstance(right_scores, Mapping):
                continue
            usable = [
                model for model in common_models if model in left_scores and model in right_scores
            ]
            x = np.array([float(left_scores[model]) for model in usable], dtype=float)
            y = np.array([float(right_scores[model]) for model in usable], dtype=float)
            rows.append(
                {
                    "benchmark_id": benchmark_id,
                    "condition_a": left,
                    "condition_b": right,
                    "exact_common_models": len(usable),
                    "spearman": _safe_correlation(stats.spearmanr, x, y),
                    "underpowered": len(usable) < config.minimum_models_for_inference,
                }
            )
    return rows


def _family_level_exploratory_rows(
    frames: Mapping[str, pd.DataFrame],
    gate_inputs: Mapping[str, BenchmarkGateInput],
    config: CrossBenchmarkAnalysisConfig,
) -> list[dict[str, Any]]:
    family_scores: dict[str, pd.Series] = {}
    for benchmark_id, frame in frames.items():
        scores = frame.mean(axis=1, skipna=True)
        mapping = gate_inputs[benchmark_id].model_family_by_id
        family_scores[benchmark_id] = (
            pd.DataFrame({"score": scores, "family": [mapping[model] for model in scores.index]})
            .groupby("family", sort=True)["score"]
            .mean()
        )
    rows: list[dict[str, Any]] = []
    for left, right in combinations(sorted(family_scores), 2):
        paired = pd.concat(
            [family_scores[left].rename("left"), family_scores[right].rename("right")],
            axis=1,
            join="inner",
        ).dropna()
        rows.append(
            {
                "benchmark_a": left,
                "benchmark_b": right,
                "common_families": len(paired),
                "family_spearman": _safe_correlation(
                    stats.spearmanr,
                    paired["left"].to_numpy(dtype=float),
                    paired["right"].to_numpy(dtype=float),
                ),
                "underpowered": len(paired) < config.minimum_models_for_inference,
                "analysis_scope": "EXPLORATORY_FAMILY_LEVEL_ONLY",
            }
        )
    return rows


def _safe_correlation(function: Any, x: np.ndarray, y: np.ndarray) -> float | None:
    if len(x) < 2 or len(y) < 2 or np.all(x == x[0]) or np.all(y == y[0]):
        return None
    result = function(x, y)
    value = result.statistic if hasattr(result, "statistic") else result[0]
    return float(value) if np.isfinite(value) else None


def _bootstrap_spearman_ci(
    x: np.ndarray,
    y: np.ndarray,
    *,
    iterations: int,
    seed: int,
    alpha: float,
) -> tuple[float | None, float | None]:
    if len(x) < 3 or iterations <= 0:
        return None, None
    rng = np.random.default_rng(seed)
    values: list[float] = []
    for _ in range(iterations):
        indices = rng.integers(0, len(x), size=len(x))
        value = _safe_correlation(stats.spearmanr, x[indices], y[indices])
        if value is not None:
            values.append(value)
    if not values:
        return None, None
    lower, upper = np.quantile(values, [alpha / 2, 1 - alpha / 2])
    return float(lower), float(upper)


def _permutation_p_value(
    x: np.ndarray,
    y: np.ndarray,
    *,
    observed: float | None,
    iterations: int,
    seed: int,
) -> float | None:
    if observed is None or len(x) < 3 or iterations <= 0:
        return None
    rng = np.random.default_rng(seed)
    extreme = 0
    valid = 0
    for _ in range(iterations):
        value = _safe_correlation(stats.spearmanr, x, rng.permutation(y))
        if value is not None:
            valid += 1
            extreme += abs(value) >= abs(observed)
    return (extreme + 1) / (valid + 1) if valid else None


def _attenuation_correct(
    correlation: float | None,
    reliability_a: float | None,
    reliability_b: float | None,
) -> float | None:
    if correlation is None or reliability_a is None or reliability_b is None:
        return None
    if not 0 < reliability_a <= 1 or not 0 < reliability_b <= 1:
        return None
    value = correlation / math.sqrt(reliability_a * reliability_b)
    return float(np.clip(value, -1.0, 1.0))


def _pairwise_order_agreement(x: np.ndarray, y: np.ndarray) -> tuple[float | None, int]:
    agreements = 0
    comparable = 0
    for left, right in combinations(range(len(x)), 2):
        x_delta = x[left] - x[right]
        y_delta = y[left] - y[right]
        if x_delta == 0 or y_delta == 0:
            continue
        comparable += 1
        agreements += (x_delta > 0) == (y_delta > 0)
    return (agreements / comparable if comparable else None), comparable


def _top_k_ids(scores: pd.Series, top_k: int) -> list[str]:
    ordered = sorted(
        ((str(model_id), float(value)) for model_id, value in scores.items()),
        key=lambda item: (-item[1], item[0]),
    )
    return [model_id for model_id, _ in ordered[:top_k]]


def _apply_multiple_testing(rows: list[dict[str, Any]], *, method: str) -> None:
    indices = [
        index for index, row in enumerate(rows) if row.get("permutation_p_value") is not None
    ]
    adjusted = adjust_p_values(
        [float(rows[index]["permutation_p_value"]) for index in indices],
        method=method,
    )
    for row in rows:
        row["adjusted_p_value"] = None
        row["multiple_testing_method"] = method
    for index, value in zip(indices, adjusted, strict=True):
        rows[index]["adjusted_p_value"] = float(value)


def _transfer_conclusion(
    rank_rows: Sequence[Mapping[str, Any]],
    config: CrossBenchmarkAnalysisConfig,
    model_count: int,
) -> str:
    if model_count < config.minimum_models_for_inference:
        return "UNDERPOWERED"
    correlations = [float(row["spearman"]) for row in rank_rows if row.get("spearman") is not None]
    if not correlations:
        return "BLOCKED"
    median = float(np.median(correlations))
    if (
        len(correlations) > 1
        and max(correlations) - min(correlations) >= config.benchmark_specific_range
    ):
        return "TRANSFER_BENCHMARK_SPECIFIC"
    if median >= config.transfer_supported_spearman:
        return "TRANSFER_SUPPORTED"
    if median >= config.transfer_partial_spearman:
        return "TRANSFER_PARTIAL"
    return "TRANSFER_NOT_SUPPORTED"


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        atomic_write_text(path, "status\nNOT_AVAILABLE\n")
        return
    fieldnames = sorted({str(key) for row in rows for key in row})
    buffer: list[str] = []
    string_io = _ListWriter(buffer)
    writer = csv.DictWriter(string_io, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _csv_value(row.get(key)) for key in fieldnames})
    atomic_write_text(path, "".join(buffer))


class _ListWriter:
    def __init__(self, target: list[str]) -> None:
        self.target = target

    def write(self, value: str) -> int:
        self.target.append(value)
        return len(value)


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float) and not math.isfinite(value):
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    return value


def _render_summary(payload: Mapping[str, Any]) -> str:
    conclusion = payload.get("transfer_conclusion", "BLOCKED")
    status = payload.get("status", "blocked")
    lines = [
        "# ValidEval V5 Cross-Benchmark Analysis",
        "",
        f"- Status: `{status}`",
        f"- Transfer conclusion: `{conclusion}`",
        f"- Gate: `{payload.get('gate', {}).get('status', 'UNKNOWN')}`",
        f"- Evidence state: `{payload.get('evidence_state', payload.get('gate', {}).get('evidence_state', 'ARTIFACT_GATED'))}`",
        "",
        "The conclusion is protocol-scoped. It does not establish universal model-ability transfer or global benchmark validity.",
    ]
    blocked = payload.get("blocked_reason")
    if blocked:
        lines.extend(["", "Blocked reasons:"])
        lines.extend(f"- {reason}" for reason in blocked)
    return "\n".join(lines) + "\n"
