from __future__ import annotations

import inspect
from dataclasses import asdict

import pytest

from valideval.synthetic.contracts import (
    HIDDEN_SYNTHETIC_KEYS,
    FixedSyntheticReadout,
    ObservablePanelResponses,
    ObservableSyntheticItem,
    SyntheticBoundaryError,
    assert_public_synthetic_isolation,
    build_non_evidence_fixture,
)


def test_public_dataclasses_and_readout_api_exclude_hidden_truth() -> None:
    public_fields = set(ObservableSyntheticItem.__dataclass_fields__)
    response_fields = set(ObservablePanelResponses.__dataclass_fields__)
    signature = inspect.signature(FixedSyntheticReadout.score)

    assert HIDDEN_SYNTHETIC_KEYS.isdisjoint(public_fields)
    assert HIDDEN_SYNTHETIC_KEYS.isdisjoint(response_fields)
    assert list(signature.parameters) == ["self", "rows"]


def test_hidden_state_is_rejected_recursively() -> None:
    with pytest.raises(SyntheticBoundaryError, match="flaw_type"):
        ObservableSyntheticItem(
            item_id="neutral",
            prompt="p",
            choices=("A", "B"),
            public_metadata={"nested": {"flaw_type": "ambiguous"}},
        )
    with pytest.raises(SyntheticBoundaryError, match="private_seed"):
        assert_public_synthetic_isolation({"metadata": [{"private_seed": 42}]})


def test_fixture_truth_is_separate_and_public_inputs_pass_guards() -> None:
    public, truth, responses = build_non_evidence_fixture(seed=7, item_count=12, panel_size=4)

    assert len(public) == len(truth) == len(responses) == 12
    assert {row.item_id for row in public} == {row.item_id for row in truth}
    assert all(row.public_metadata["artifact_class"] == "NON_EVIDENCE_FIXTURE" for row in public)
    assert_public_synthetic_isolation([asdict(row) for row in public])
    assert_public_synthetic_isolation([asdict(row) for row in responses])
    scores = FixedSyntheticReadout().score(responses)
    assert set(scores) == {row.item_id for row in public}
    assert all(0.0 <= score <= 1.0 for score in scores.values())
