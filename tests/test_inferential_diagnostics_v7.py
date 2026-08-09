import numpy as np
import pandas as pd

from valideval.diagnostics.dependency import audit_diagnostic_dependencies
from valideval.diagnostics.inference import (
    diagnostic_agreement_taxonomy,
    empirical_bayes_shrinkage,
    infer_item_diagnostics,
)
from valideval.diagnostics.multiplicity import benjamini_hochberg, benjamini_yekutieli


def _matrix() -> pd.DataFrame:
    rng = np.random.default_rng(11)
    values = rng.binomial(1, np.linspace(0.2, 0.9, 10)[:, None], size=(10, 30)).astype(float)
    values[:, 0] = values[::-1, 1]
    return pd.DataFrame(
        values, index=[f"m{i}" for i in range(10)], columns=[f"s{i % 3}::i{i}" for i in range(30)]
    )


def test_multiplicity_adjustments_are_monotone_and_by_is_conservative() -> None:
    p = [0.001, 0.01, 0.04, 0.2]
    bh = benjamini_hochberg(p)
    by = benjamini_yekutieli(p)
    assert np.all(by >= bh)
    assert np.all((0 <= bh) & (bh <= 1))


def test_inferential_output_has_required_fields() -> None:
    matrix = _matrix()
    result = infer_item_diagnostics(
        matrix,
        [column.split("::")[0] for column in matrix.columns],
        n_bootstrap=20,
        n_permutations=20,
    )
    assert len(result) == matrix.shape[1]
    assert {"FDR_q_value", "BY_q_value", "bootstrap_stability", "claim_status"}.issubset(result)


def test_empirical_bayes_shrinkage_reduces_extremes() -> None:
    original = np.asarray([-3.0, 0.0, 3.0])
    shrunk = empirical_bayes_shrinkage(original, [2.0, 2.0, 2.0])
    assert np.max(np.abs(shrunk)) < np.max(np.abs(original))


def test_dependency_audit_retires_exact_duplicate() -> None:
    spec = {
        "a": {"source_data": ["matrix"], "formula": "mean", "depends_on_accuracy": True},
        "b": {"source_data": ["matrix"], "formula": "mean", "depends_on_accuracy": True},
    }
    audit = audit_diagnostic_dependencies(spec)
    assert audit["retired"] == ["b"]


def test_agreement_taxonomy() -> None:
    result = diagnostic_agreement_taxonomy(
        pd.DataFrame(
            [
                {
                    "item_id": "x",
                    "difficulty": True,
                    "discrimination": False,
                    "rank_material": False,
                    "forensic": False,
                }
            ]
        )
    )
    assert result.loc[0, "agreement_class"] == "DIFFICULTY_ONLY"
