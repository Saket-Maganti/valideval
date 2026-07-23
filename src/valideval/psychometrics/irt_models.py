from __future__ import annotations

import math
from typing import Any

import numpy as np

from valideval.psychometrics.reliability_stats import pearson_correlation, spearman_correlation
from valideval.schemas import ResponseMatrix


def _logit(probability: float, eps: float = 1e-4) -> float:
    clipped = min(max(float(probability), eps), 1.0 - eps)
    return math.log(clipped / (1.0 - clipped))


def estimate_irt_proxy(matrix: ResponseMatrix) -> dict[str, Any]:
    frame = matrix.to_dataframe().astype(float)
    if frame.empty:
        raise ValueError("IRT proxy requires a non-empty response matrix.")

    total_scores = frame.mean(axis=1)
    abilities = {model_id: float(_logit(score)) for model_id, score in total_scores.items()}
    corrected_item_total = _corrected_item_total_correlations(frame, total_scores)
    anchor_items = _anchor_items(frame, corrected_item_total)
    anchor_set = set(anchor_items)
    anchor_sum = frame[anchor_items].sum(axis=1) if anchor_items else None
    min_anchor_count = _minimum_anchor_count(frame)
    total_sum = frame.sum(axis=1)

    item_stats: dict[str, dict[str, Any]] = {}
    for item_id in frame.columns:
        item_values = frame[item_id].astype(float)
        proportion_correct = float(item_values.mean())
        corrected_correlation = corrected_item_total[item_id]
        if (
            anchor_sum is not None
            and item_id in anchor_set
            and len(anchor_items) - 1 >= min_anchor_count
        ):
            ability_proxy = (anchor_sum - item_values) / (len(anchor_items) - 1)
        elif anchor_sum is not None and len(anchor_items) >= min_anchor_count:
            ability_proxy = anchor_sum / len(anchor_items)
        elif frame.shape[1] > 1:
            ability_proxy = (total_sum - item_values) / (frame.shape[1] - 1)
        else:
            ability_proxy = total_scores
        ability_pearson = pearson_correlation(item_values.tolist(), ability_proxy.tolist())
        ability_spearman = spearman_correlation(item_values.tolist(), ability_proxy.tolist())
        if math.isnan(ability_pearson):
            ability_pearson = corrected_correlation
        if math.isnan(ability_spearman):
            ability_spearman = ability_pearson
        if math.isnan(ability_spearman):
            ability_spearman = 0.0
        discrimination = float(ability_spearman)
        difficulty = float(-_logit(proportion_correct))
        information_proxy = float(
            max(discrimination, 0.0) * proportion_correct * (1.0 - proportion_correct)
        )
        label = _discrimination_label(
            discrimination,
            proportion_correct=proportion_correct,
            n_models=frame.shape[0],
            anchor_count=len(anchor_items),
        )
        item_stats[item_id] = {
            "proportion_correct": proportion_correct,
            "difficulty": difficulty,
            "discrimination": float(discrimination),
            "corrected_item_total_correlation": float(corrected_correlation),
            "ability_pearson_correlation": float(ability_pearson),
            "ability_spearman_correlation": float(ability_spearman),
            "information_proxy": information_proxy,
            "negative_discrimination": bool(discrimination < -0.05),
            "near_zero_discrimination": bool(abs(discrimination) < 0.05),
            "too_easy": bool(proportion_correct >= 0.95),
            "too_hard": bool(proportion_correct <= 0.05),
            "discrimination_label": label,
            "discrimination_basis": "anchor_oriented_spearman"
            if len(anchor_items) >= _minimum_anchor_count(frame)
            else "corrected_item_total_fallback",
        }

    raw_accuracy = total_scores.to_dict()
    ranking_correlation = spearman_correlation(
        list(raw_accuracy.values()), list(abilities.values())
    )

    return {
        "item_stats": item_stats,
        "model_abilities": abilities,
        "raw_accuracy": {key: float(value) for key, value in raw_accuracy.items()},
        "ranking_correlation_raw_vs_ability": float(ranking_correlation),
        "discrimination_estimation": {
            "primary": "spearman(item_correct, anchor_oriented_model_score)",
            "corrected_item_total_available": True,
            "anchor_item_count": len(anchor_items),
            "anchor_item_ids": anchor_items,
            "warning": (
                "Discrimination is a proxy correlation under the observed model panel, not a "
                "latent 2PL slope."
            ),
        },
    }


def _corrected_item_total_correlations(
    frame: Any,
    total_scores: Any,
) -> dict[str, float]:
    correlations: dict[str, float] = {}
    total_sum = frame.sum(axis=1)
    for item_id in frame.columns:
        item_values = frame[item_id].astype(float)
        if frame.shape[1] > 1:
            total_without_item = (total_sum - item_values) / (frame.shape[1] - 1)
        else:
            total_without_item = total_scores
        correlation = pearson_correlation(item_values.tolist(), total_without_item.tolist())
        correlations[item_id] = 0.0 if math.isnan(correlation) else float(correlation)
    return correlations


def _minimum_anchor_count(frame: Any) -> int:
    return min(5, max(2, frame.shape[1] // 4))


def _anchor_items(frame: Any, corrected_item_total: dict[str, float]) -> list[str]:
    candidates = []
    for item_id in frame.columns:
        proportion_correct = float(frame[item_id].mean())
        if 0.05 < proportion_correct < 0.95 and corrected_item_total.get(item_id, 0.0) > 0.05:
            candidates.append(item_id)
    if len(candidates) >= _minimum_anchor_count(frame):
        return candidates
    relaxed = [item_id for item_id in frame.columns if corrected_item_total.get(item_id, 0.0) > 0.0]
    return relaxed if len(relaxed) >= _minimum_anchor_count(frame) else []


def _anchor_ability_proxy(
    frame: Any,
    *,
    item_id: str,
    anchor_items: list[str],
    fallback_scores: Any,
) -> Any:
    anchor_columns = [candidate for candidate in anchor_items if candidate != item_id]
    if len(anchor_columns) >= _minimum_anchor_count(frame):
        return frame[anchor_columns].mean(axis=1)
    if frame.shape[1] > 1:
        return frame.drop(columns=[item_id]).mean(axis=1)
    return fallback_scores


def _discrimination_label(
    discrimination: float,
    *,
    proportion_correct: float,
    n_models: int,
    anchor_count: int,
) -> str:
    if n_models < 5:
        return "insufficient_panel"
    if anchor_count == 0:
        return "unstable_estimate"
    if proportion_correct <= 0.05 or proportion_correct >= 0.95:
        return "unstable_estimate"
    if discrimination < -0.05:
        return "negative_discrimination"
    if abs(discrimination) < 0.05:
        return "low_discrimination"
    return "positive_discrimination"


def estimate_rasch_1pl(matrix: ResponseMatrix, *, max_iter: int = 200) -> dict[str, Any]:
    frame = matrix.to_dataframe().astype(float)
    warnings: list[str] = []
    if frame.shape[0] < 4 or frame.shape[1] < 6:
        return {
            "available": False,
            "warnings": ["Rasch/1PL fit skipped because the matrix is too small."],
        }
    try:
        from scipy.optimize import minimize
    except Exception:
        return {
            "available": False,
            "warnings": ["Rasch/1PL fit skipped because scipy.optimize is unavailable."],
        }

    values = frame.to_numpy(dtype=float)
    n_models, n_items = values.shape
    parameter_count = n_models + n_items - 1
    if parameter_count > 2000:
        return {
            "available": False,
            "warnings": [
                "Rasch/1PL fit skipped because the local BFGS implementation is too large for "
                f"this matrix ({parameter_count} free parameters). Proxy item diagnostics remain "
                "available; full Rasch evidence is RESULT_REQUIRED."
            ],
        }

    def unpack(params: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        ability = params[:n_models]
        difficulty_free = params[n_models:]
        difficulty = np.concatenate([difficulty_free, [-float(np.sum(difficulty_free))]])
        return ability, difficulty

    def objective(params: np.ndarray) -> float:
        ability, difficulty = unpack(params)
        logits = ability[:, None] - difficulty[None, :]
        probabilities = 1.0 / (1.0 + np.exp(-np.clip(logits, -30, 30)))
        eps = 1e-8
        nll = -np.sum(
            values * np.log(probabilities + eps)
            + (1.0 - values) * np.log(1.0 - probabilities + eps)
        )
        ridge = 0.01 * float(np.sum(params**2))
        return float(nll + ridge)

    proxy = estimate_irt_proxy(matrix)
    start_ability = np.array(
        [proxy["model_abilities"][model_id] for model_id in frame.index], dtype=float
    )
    start_difficulty = np.array(
        [proxy["item_stats"][item_id]["difficulty"] for item_id in frame.columns[:-1]],
        dtype=float,
    )
    start = np.concatenate([start_ability, start_difficulty])
    result = minimize(objective, start, method="BFGS", options={"maxiter": max_iter})
    if not result.success:
        warnings.append(f"Rasch/1PL optimization did not fully converge: {result.message}")
    ability, difficulty = unpack(np.asarray(result.x, dtype=float))
    return {
        "available": True,
        "converged": bool(result.success),
        "objective": float(result.fun),
        "model_abilities": {
            model_id: float(value) for model_id, value in zip(frame.index, ability, strict=True)
        },
        "item_difficulties": {
            item_id: float(value) for item_id, value in zip(frame.columns, difficulty, strict=True)
        },
        "warnings": warnings,
    }


def estimate_2pl_proxy(matrix: ResponseMatrix) -> dict[str, Any]:
    frame = matrix.to_dataframe().astype(float)
    proxy = estimate_irt_proxy(matrix)
    if frame.shape[0] < 8 or frame.shape[1] < 10:
        return {
            "available": False,
            "warnings": ["2PL proxy flagged as insufficient-data; reporting proxy slopes only."],
            "item_slopes": {
                item_id: max(float(stats["discrimination"]), 0.0)
                for item_id, stats in proxy["item_stats"].items()
            },
        }
    return {
        "available": True,
        "warnings": [
            "2PL values are proxy slopes from item-total discrimination, not a full parametric 2PL fit."
        ],
        "item_slopes": {
            item_id: max(float(stats["discrimination"]), 0.0)
            for item_id, stats in proxy["item_stats"].items()
        },
    }


def bootstrap_irt_uncertainty(
    matrix: ResponseMatrix,
    *,
    n_boot: int = 100,
    seed: int = 0,
) -> dict[str, Any]:
    frame = matrix.to_dataframe().astype(float)
    rng = np.random.default_rng(seed)
    if frame.empty or n_boot <= 0:
        return {"item_difficulty_ci": {}, "item_discrimination_ci": {}, "ability_ci": {}}

    ability_samples: dict[str, list[float]] = {model_id: [] for model_id in frame.index}
    difficulty_samples: dict[str, list[float]] = {item_id: [] for item_id in frame.columns}
    discrimination_samples: dict[str, list[float]] = {item_id: [] for item_id in frame.columns}
    item_ids = list(frame.columns)
    for _ in range(n_boot):
        sampled_items = rng.choice(item_ids, size=len(item_ids), replace=True).tolist()
        sampled = frame[sampled_items]
        sampled.columns = [f"{item_id}__{idx}" for idx, item_id in enumerate(sampled_items)]
        sample_matrix = ResponseMatrix.from_dataframe(
            sampled,
            metadata={"prompt_variant": matrix.metadata.get("prompt_variant", "full")},
        )
        estimates = estimate_irt_proxy(sample_matrix)
        for model_id, ability in estimates["model_abilities"].items():
            ability_samples[model_id].append(float(ability))
        for sampled_column, stats in estimates["item_stats"].items():
            original_item_id = sampled_column.split("__", 1)[0]
            difficulty_samples[original_item_id].append(float(stats["difficulty"]))
            discrimination_samples[original_item_id].append(float(stats["discrimination"]))

    return {
        "ability_ci": {
            model_id: _sample_ci(values) for model_id, values in ability_samples.items()
        },
        "item_difficulty_ci": {
            item_id: _sample_ci(values) for item_id, values in difficulty_samples.items()
        },
        "item_discrimination_ci": {
            item_id: _sample_ci(values) for item_id, values in discrimination_samples.items()
        },
    }


def select_high_information_subset(
    item_stats: dict[str, dict[str, float | bool]],
    k: int,
) -> list[str]:
    scored = sorted(
        item_stats.items(),
        key=lambda pair: (
            float(pair[1].get("information_proxy", 0.0)),
            float(pair[1].get("discrimination", 0.0)),
        ),
        reverse=True,
    )
    return [item_id for item_id, _ in scored[:k]]


def _sample_ci(values: list[float], alpha: float = 0.05) -> dict[str, float | int]:
    if not values:
        return {"estimate": float("nan"), "lower": float("nan"), "upper": float("nan"), "n": 0}
    lower, upper = np.quantile(values, [alpha / 2.0, 1.0 - alpha / 2.0])
    return {
        "estimate": float(np.mean(values)),
        "lower": float(lower),
        "upper": float(upper),
        "n": len(values),
    }


def simulate_1pl(
    abilities: np.ndarray,
    difficulties: np.ndarray,
    *,
    seed: int = 0,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    logits = abilities[:, None] - difficulties[None, :]
    probabilities = 1.0 / (1.0 + np.exp(-logits))
    return (rng.random(size=probabilities.shape) < probabilities).astype(float)
