from __future__ import annotations

from copy import deepcopy
from typing import Any

POLICIES: dict[str, dict[str, Any]] = {
    "REMOVE_CONFIRMED_ISSUES": {
        "description": "Remove only independently confirmed item issues.",
        "v7_validation_required": True,
        "confirmed_only": True,
    },
    "DOWNWEIGHT_UNCERTAIN_ITEMS": {
        "description": "Downweight uncertain items using cross-fitted risk estimates.",
        "v7_validation_required": True,
        "cross_fitted_weights": True,
    },
    "ABSTAIN_ON_DISPUTED_ITEMS": {
        "description": "Exclude disputed items from claims while preserving them for audit.",
        "v7_validation_required": True,
        "adjudication_required": True,
    },
    "REWEIGHT_FOR_RELIABILITY": {
        "description": "Use held-out reliability weights with a matched random baseline.",
        "v7_validation_required": True,
        "held_out_reliability": True,
    },
    "conservative": {
        "description": (
            "Remove clear local item-quality threats while preserving coverage-critical items."
        ),
        "keep_coverage_critical": True,
        "remove_negative_discrimination": True,
        "min_discrimination": 0.05,
        "remove_duplicates": True,
        "max_shortcut_suspiciousness": 0.50,
        "remove_overlap_levels": {"high local evidence"},
        "max_prompt_instability": 0.40,
    },
    "stable": {
        "description": (
            "Prefer prompt/scorer-stable items and remove duplicates, preserving coverage-critical items."
        ),
        "keep_coverage_critical": True,
        "remove_negative_discrimination": True,
        "min_discrimination": 0.0,
        "remove_duplicates": True,
        "max_shortcut_suspiciousness": 0.75,
        "remove_overlap_levels": {"high local evidence"},
        "max_prompt_instability": 0.20,
        "max_scorer_instability": 0.10,
    },
    "low_contamination_risk": {
        "description": (
            "Prefer items with no high local corpus-overlap evidence while preserving coverage-critical items."
        ),
        "keep_coverage_critical": True,
        "remove_negative_discrimination": False,
        "min_discrimination": None,
        "remove_duplicates": True,
        "max_shortcut_suspiciousness": 0.90,
        "remove_overlap_levels": {"moderate local evidence", "high local evidence"},
        "max_prompt_instability": None,
    },
    "high_information": {
        "description": (
            "Keep higher-discrimination items first, then preserve coverage-critical items."
        ),
        "keep_coverage_critical": True,
        "remove_negative_discrimination": True,
        "min_discrimination": 0.0,
        "remove_duplicates": True,
        "max_shortcut_suspiciousness": 1.0,
        "remove_overlap_levels": set(),
        "max_prompt_instability": None,
        "target_fraction": 0.75,
    },
}


def get_policy(name: str) -> dict[str, Any]:
    if name not in POLICIES:
        raise ValueError(f"Unknown repair policy: {name}")
    return deepcopy(POLICIES[name])


def policy_names() -> list[str]:
    return sorted(POLICIES)
