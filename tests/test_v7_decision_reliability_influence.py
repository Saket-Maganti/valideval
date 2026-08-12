import numpy as np
import pandas as pd

from valideval.decision.fragility import item_removal_fragility, subject_weight_fragility
from valideval.decision.regret import compare_selection_rules
from valideval.decision.selective_ranking import selective_ranking
from valideval.influence import leave_one_item_influence, leave_one_subject_influence
from valideval.reliability import (
    benchmark_design_curve,
    estimate_variance_components,
    generalizability_coefficients,
)


def _matrix() -> pd.DataFrame:
    return pd.DataFrame(
        [[1, 1, 1, 0, 1, 0], [1, 1, 0, 0, 1, 0], [0, 1, 0, 1, 0, 1], [0, 0, 1, 1, 0, 1]],
        index=["a", "b", "c", "d"],
        columns=["s1::1", "s1::2", "s1::3", "s2::1", "s2::2", "s2::3"],
        dtype=float,
    )


def test_selective_ranking_supports_abstention() -> None:
    rng = np.random.default_rng(4)
    draws = pd.DataFrame(
        {
            "a": rng.normal(0.7, 0.01, 500),
            "b": rng.normal(0.6, 0.01, 500),
            "c": rng.normal(0.6, 0.01, 500),
        }
    )
    result = selective_ranking(draws, materiality_threshold=0.03)
    assert "A > B" in set(result["decision"])
    assert set(result["decision"]) <= {"A > B", "B > A", "A ~ B", "INSUFFICIENT_EVIDENCE"}


def test_claim_licensed_selection_can_abstain() -> None:
    draws = pd.DataFrame({"a": [0.51, 0.49, 0.5], "b": [0.49, 0.51, 0.5]})
    result = compare_selection_rules(draws, regret_bound=0.0)
    assert result.loc[result["rule"] == "claim_licensed", "status"].iloc[0] == "ABSTAIN"


def test_fragility_and_influence_are_finite() -> None:
    matrix = _matrix()
    scores = matrix.T.groupby(lambda value: value.split("::")[0]).mean().T
    assert subject_weight_fragility(scores)["winner"] == "a"
    assert item_removal_fragility(matrix)["winner"] == "a"
    assert len(leave_one_item_influence(matrix, top_k=2)) == matrix.shape[1]
    assert len(leave_one_subject_influence(matrix, ["s1"] * 3 + ["s2"] * 3)) == 2


def test_generalizability_curve_uses_all_design_facets() -> None:
    matrix = _matrix()
    components = estimate_variance_components(
        matrix,
        ["s1"] * 3 + ["s2"] * 3,
        {"a": "f1", "b": "f1", "c": "f2", "d": "f2"},
    )
    coefficients = generalizability_coefficients(components, items=100, subjects=10, families=4)
    assert all(0.0 <= value <= 1.0 for value in coefficients.values())
    curve = benchmark_design_curve(
        components,
        item_grid=(100,),
        subject_grid=(10,),
        family_grid=(4,),
        checkpoint_grid=(1, 2),
    )
    assert len(curve) == 2
