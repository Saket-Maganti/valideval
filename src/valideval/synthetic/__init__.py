"""V5 confirmatory-synthetic contracts.

Legacy synthetic validation remains in :mod:`valideval.validation`; this package provides a
separate, preregistered generator/detector boundary for future confirmatory work.
"""

from valideval.synthetic.confirmatory import (
    REQUIRED_EXPERIMENTS,
    load_confirmatory_config,
    run_confirmatory_synthetic_v5,
    validate_confirmatory_config,
)
from valideval.synthetic.contracts import (
    FixedSyntheticReadout,
    HiddenSyntheticTruth,
    ObservablePanelResponses,
    ObservableSyntheticItem,
    SyntheticBoundaryError,
    assert_public_synthetic_isolation,
    build_non_evidence_fixture,
)

__all__ = [
    "FixedSyntheticReadout",
    "HiddenSyntheticTruth",
    "ObservablePanelResponses",
    "ObservableSyntheticItem",
    "REQUIRED_EXPERIMENTS",
    "SyntheticBoundaryError",
    "assert_public_synthetic_isolation",
    "build_non_evidence_fixture",
    "load_confirmatory_config",
    "run_confirmatory_synthetic_v5",
    "validate_confirmatory_config",
]
