from __future__ import annotations

import pytest

from valideval.statistics.rare_events import (
    monte_carlo_standard_error,
    simultaneous_wilson_interval,
    wilson_interval,
)


@pytest.mark.parametrize(
    ("successes", "trials", "expected_lower", "expected_upper"),
    [
        (0, 1, 0.0, 0.7934506856),
        (0, 5, 0.0, 0.4344824648),
        (0, 10, 0.0, 0.2775327999),
        (0, 100, 0.0, 0.0369934982),
        (1, 10, 0.0178762131, 0.4041500268),
        (1, 100, 0.0017674321, 0.0544861962),
        (5, 100, 0.0215436792, 0.1117504692),
    ],
)
def test_wilson_interval_matches_trusted_values(
    successes: int,
    trials: int,
    expected_lower: float,
    expected_upper: float,
) -> None:
    interval = wilson_interval(successes, trials)
    assert interval.lower == pytest.approx(expected_lower, abs=1e-10)
    assert interval.upper == pytest.approx(expected_upper, abs=1e-10)


def test_zero_events_never_means_zero_upper_risk() -> None:
    assert wilson_interval(0, 100).upper > 0.0


def test_simultaneous_interval_is_at_least_as_conservative() -> None:
    marginal = wilson_interval(1, 100)
    simultaneous = simultaneous_wilson_interval(1, 100, family_size=12)
    assert simultaneous.upper >= marginal.upper
    assert simultaneous.lower <= marginal.lower


def test_monte_carlo_standard_error_boundaries() -> None:
    assert monte_carlo_standard_error(0, 100) == 0.0
    assert monte_carlo_standard_error(50, 100) == pytest.approx(0.05)
