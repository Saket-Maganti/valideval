from __future__ import annotations

import math
from dataclasses import dataclass

from scipy.stats import norm


@dataclass(frozen=True, slots=True)
class BinomialInterval:
    method: str
    successes: int
    trials: int
    confidence_level: float
    lower: float
    upper: float

    def to_dict(self) -> dict[str, float | int | str]:
        return {
            "method": self.method,
            "successes": self.successes,
            "trials": self.trials,
            "confidence_level": self.confidence_level,
            "lower": self.lower,
            "upper": self.upper,
        }


def wilson_interval(
    successes: int,
    trials: int,
    *,
    confidence_level: float = 0.95,
) -> BinomialInterval:
    """Two-sided Wilson score interval for a binomial proportion.

    This is the primary interval for rare false-license and error rates. In
    particular, zero observed events retain a positive upper risk bound.
    """

    if isinstance(successes, bool) or isinstance(trials, bool):
        raise TypeError("successes and trials must be integers, not booleans")
    if not isinstance(successes, int) or not isinstance(trials, int):
        raise TypeError("successes and trials must be integers")
    if trials <= 0 or successes < 0 or successes > trials:
        raise ValueError("require 0 <= successes <= trials and trials > 0")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must lie in (0, 1)")
    z = float(norm.ppf(0.5 + confidence_level / 2.0))
    proportion = successes / trials
    z2 = z * z
    denominator = 1.0 + z2 / trials
    center = (proportion + z2 / (2.0 * trials)) / denominator
    radius = (
        z
        * math.sqrt(proportion * (1.0 - proportion) / trials + z2 / (4.0 * trials * trials))
        / denominator
    )
    return BinomialInterval(
        method="WILSON_TWO_SIDED",
        successes=successes,
        trials=trials,
        confidence_level=confidence_level,
        lower=max(0.0, center - radius),
        upper=min(1.0, center + radius),
    )


def simultaneous_wilson_interval(
    successes: int,
    trials: int,
    *,
    family_size: int,
    family_confidence_level: float = 0.95,
) -> BinomialInterval:
    """Bonferroni-simultaneous Wilson interval for a prespecified safety family."""

    if family_size <= 0:
        raise ValueError("family_size must be positive")
    alpha = 1.0 - family_confidence_level
    return wilson_interval(
        successes,
        trials,
        confidence_level=1.0 - alpha / family_size,
    )


def monte_carlo_standard_error(successes: int, trials: int) -> float:
    if trials <= 0 or successes < 0 or successes > trials:
        raise ValueError("require 0 <= successes <= trials and trials > 0")
    proportion = successes / trials
    return math.sqrt(proportion * (1.0 - proportion) / trials)
