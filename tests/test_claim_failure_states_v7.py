import pytest

from valideval.claims import ClaimEvidence, ClaimPolicy, ClaimStatus, ClaimType, license_claim


@pytest.mark.parametrize(
    ("evidence", "status"),
    [
        (ClaimEvidence(identity_verified=False), ClaimStatus.BLOCKED_BY_IDENTITY),
        (ClaimEvidence(leakage_guard_passed=False), ClaimStatus.BLOCKED_BY_LEAKAGE),
        (ClaimEvidence(sample_size=10), ClaimStatus.UNDERPOWERED),
    ],
)
def test_global_failure_precedence(evidence: ClaimEvidence, status: ClaimStatus) -> None:
    assert license_claim(ClaimType.SUBJECT_IS_UNSTABLE, evidence).status is status


def test_by_sensitivity_can_block_bh_positive_item() -> None:
    result = license_claim(
        ClaimType.ITEM_IS_SUSPICIOUS,
        ClaimEvidence(
            q_value=0.01,
            by_q_value=0.2,
            multiplicity_controlled=True,
            bootstrap_stability=0.9,
            effect_size=0.2,
            sample_size=500,
            external_validated=True,
        ),
        ClaimPolicy(require_by_sensitivity=True),
    )
    assert result.status is ClaimStatus.BLOCKED_BY_MULTIPLICITY


def test_transport_checks_overlap_families_direction_and_heterogeneity() -> None:
    result = license_claim(
        ClaimType.DIAGNOSTIC_TRANSFERS,
        ClaimEvidence(
            confidence_lower=0.1,
            sample_size=500,
            exact_model_overlap=4,
            independent_model_families=8,
            transport_heterogeneity=0.1,
            transport_direction_consistent=True,
        ),
    )
    assert result.status is ClaimStatus.BLOCKED_BY_TRANSPORT
