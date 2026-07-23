from __future__ import annotations

from valideval.validation.multiplicity import correct_p_values


def adjust_p_values(p_values: list[float], *, method: str = "bh") -> list[float]:
    return correct_p_values(p_values, method=method)
