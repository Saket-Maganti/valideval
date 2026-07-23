from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from valideval.execution.manifest import ConfigurationMismatchError

RESUME_IDENTITY_FIELDS = (
    "run_id",
    "config_hash",
    "source_commit",
    "model_revision",
    "dataset_revision",
    "prompt_hash",
    "scoring_version",
    "extraction_version",
    "shard_definition_hash",
)


def assert_exact_resume_identity(
    expected: Mapping[str, Any],
    observed: Mapping[str, Any],
) -> None:
    mismatches: list[str] = []
    for field in RESUME_IDENTITY_FIELDS:
        expected_value = expected.get(field)
        observed_value = observed.get(field)
        if expected_value is None or observed_value is None:
            mismatches.append(f"{field}: missing")
        elif expected_value != observed_value:
            mismatches.append(f"{field}: expected {expected_value!r}, observed {observed_value!r}")
    if mismatches:
        raise ConfigurationMismatchError(
            "refusing stale resume checkpoint; " + "; ".join(mismatches)
        )
