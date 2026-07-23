from __future__ import annotations

from copy import deepcopy
from typing import Any

POLICIES: dict[str, dict[str, Any]] = {
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
