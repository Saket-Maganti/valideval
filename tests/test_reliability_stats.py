from valideval.psychometrics.reliability_stats import (
    cohen_kappa,
    exact_agreement,
    spearman_correlation,
)


def test_agreement_statistics():
    a = [1, 1, 0, 0]
    b = [1, 0, 0, 0]

    assert exact_agreement(a, b) == 0.75
    assert round(cohen_kappa(a, b), 3) == 0.5


def test_spearman_handles_rank_order():
    assert spearman_correlation([1, 2, 3], [10, 20, 30]) == 1.0
    assert spearman_correlation([1, 2, 3], [30, 20, 10]) == -1.0
