"""No-run statistical planning scaffolds."""

from valideval.statistics.rank_inference_v7_1 import (
    MARGINAL_METHOD,
    SIMULTANEOUS_METHOD,
    marginal_rank_intervals,
    pairwise_multiplicity_analysis,
    prespecified_pair_test,
    simulate_simultaneous_rank_coverage,
    simultaneous_rank_confidence_sets,
)

__all__ = [
    "MARGINAL_METHOD",
    "SIMULTANEOUS_METHOD",
    "marginal_rank_intervals",
    "pairwise_multiplicity_analysis",
    "prespecified_pair_test",
    "simulate_simultaneous_rank_coverage",
    "simultaneous_rank_confidence_sets",
]
