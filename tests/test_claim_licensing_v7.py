from valideval.claims import ClaimEvidence, ClaimPolicy, ClaimStatus, ClaimType, license_claim


def test_pairwise_claim_uses_lower_bound_not_point_estimate() -> None:
    result = license_claim(
        ClaimType.MODEL_A_OUTPERFORMS_MODEL_B,
        ClaimEvidence(
            point_estimate=0.08,
            confidence_lower=0.03,
            confidence_upper=0.12,
            effect_size=0.08,
            sample_size=500,
            decision_regret_upper=0.005,
        ),
        ClaimPolicy(effect_size_threshold=0.02),
    )
    assert result.status is ClaimStatus.LICENSED
    assert result.licensed


def test_pairwise_claim_abstains_when_interval_crosses_materiality() -> None:
    result = license_claim(
        "MODEL_A_OUTPERFORMS_MODEL_B",
        ClaimEvidence(
            point_estimate=0.08,
            confidence_lower=0.01,
            sample_size=500,
            decision_regret_upper=0.005,
        ),
        ClaimPolicy(effect_size_threshold=0.02),
    )
    assert result.status is ClaimStatus.BLOCKED_BY_UNCERTAINTY


def test_top_k_requires_simultaneous_rank_set() -> None:
    result = license_claim(
        ClaimType.MODEL_IN_TOP_K,
        ClaimEvidence(
            simultaneous_rank_lower=1,
            simultaneous_rank_upper=3,
            requested_top_k=3,
            sample_size=500,
            decision_regret_upper=0.005,
            scope=("MMLU", "exact panel"),
        ),
    )
    assert result.status is ClaimStatus.LICENSED_WITH_SCOPE


def test_suspicious_item_requires_external_validation() -> None:
    result = license_claim(
        ClaimType.ITEM_IS_SUSPICIOUS,
        ClaimEvidence(
            q_value=0.01,
            multiplicity_controlled=True,
            bootstrap_stability=0.95,
            effect_size=0.2,
            sample_size=500,
        ),
    )
    assert result.status is ClaimStatus.BLOCKED_BY_EXTERNAL_VALIDATION
