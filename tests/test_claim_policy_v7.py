import pytest

from valideval.claims import ClaimPolicy


def test_policy_roundtrip() -> None:
    policy = ClaimPolicy.from_dict({"fdr_level": 0.1, "minimum_sample_size": 20})
    assert policy.to_dict()["fdr_level"] == 0.1


def test_policy_rejects_unknown_fields() -> None:
    with pytest.raises(ValueError, match="unknown"):
        ClaimPolicy.from_dict({"magic": 1})


@pytest.mark.parametrize(
    "payload",
    [
        {"fdr_level": 0.0},
        {"confidence_level": 1.0},
        {"effect_size_threshold": -0.1},
        {"minimum_sample_size": 0},
    ],
)
def test_policy_validates_bounds(payload: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        ClaimPolicy.from_dict(payload)
