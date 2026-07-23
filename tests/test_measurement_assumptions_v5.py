from __future__ import annotations

import numpy as np
import pandas as pd

from valideval.measurement.hierarchical_subject import check_measurement_assumptions


def test_measurement_assumptions_do_not_claim_psychometric_validity():
    rng = np.random.default_rng(2)
    abilities = np.linspace(0.15, 0.85, 10)
    values = np.vstack([rng.binomial(1, probability, 60) for probability in abilities])
    frame = pd.DataFrame(
        values,
        index=[f"m{index}" for index in range(10)],
        columns=[f"i{index}" for index in range(60)],
    )
    result = check_measurement_assumptions(frame, ["a"] * 30 + ["b"] * 30)
    assert result["status"] == "pass"
    assert result["psychometric_validity_established"] is False
    assert result["full_parametric_2pl_identified"] is False


def test_measurement_assumptions_block_family_concentration():
    rng = np.random.default_rng(6)
    abilities = np.linspace(0.1, 0.9, 10)
    frame = pd.DataFrame(
        np.vstack([rng.binomial(1, probability, 60) for probability in abilities]),
        index=[f"m{index}" for index in range(10)],
        columns=[f"i{index}" for index in range(60)],
    )
    families = {f"m{index}": "dominant" if index < 8 else f"other{index}" for index in range(10)}
    result = check_measurement_assumptions(frame, ["a"] * 30 + ["b"] * 30, model_families=families)
    assert result["status"] == "blocked"
    assert "model_family_concentration_too_high" in result["blockers"]
