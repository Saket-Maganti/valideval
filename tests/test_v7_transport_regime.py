import pandas as pd

from valideval.measurement.regime_study import (
    evaluate_measurement_regime,
    simulate_measurement_regime,
)
from valideval.transport import analyze_transportability


def test_transport_supported_requires_heldout_exact_effects() -> None:
    frame = pd.DataFrame(
        {
            "estimand": ["score_transport"] * 3,
            "benchmark": ["mmlu", "gsm8k", "bbh"],
            "estimate": [0.4, 0.35, 0.45],
            "standard_error": [0.05] * 3,
            "exact_identity": [True] * 3,
            "held_out": [True] * 3,
            "independent_families": [6] * 3,
        }
    )
    assert analyze_transportability(frame)["overall_status"] == "TRANSFER_SUPPORTED"


def test_transport_blocks_identity_failure() -> None:
    frame = pd.DataFrame(
        {
            "estimand": ["score_transport"],
            "benchmark": ["mmlu"],
            "estimate": [0.4],
            "standard_error": [0.05],
            "exact_identity": [False],
            "held_out": [True],
            "independent_families": [6],
        }
    )
    assert analyze_transportability(frame)["overall_status"] == "BLOCKED"


def test_measurement_regime_is_deterministic() -> None:
    first = simulate_measurement_regime(
        model_count=12, family_count=3, item_count=80, subject_count=4, seed=8
    )
    second = simulate_measurement_regime(
        model_count=12, family_count=3, item_count=80, subject_count=4, seed=8
    )
    assert first[0].equals(second[0])
    result = evaluate_measurement_regime(*first, seed=9)
    assert result["regime"] in {"SUPPORTED", "CAUTION", "UNRELIABLE", "UNIDENTIFIABLE"}
