from __future__ import annotations

from valideval.execution.errors import (
    GenerationOOM,
    ModelLoadOOM,
    OperationalFailureType,
    classify_operational_failure,
    retry_directive,
)
from valideval.execution.shards import worker_failure_is_retryable


class SourceMismatchError(ValueError):
    pass


class ChecksumError(ValueError):
    pass


def test_typed_ooms_are_distinct_and_bounded() -> None:
    assert classify_operational_failure(ModelLoadOOM("oom")) is OperationalFailureType.LOAD_OOM
    assert (
        classify_operational_failure(GenerationOOM("oom")) is OperationalFailureType.GENERATION_OOM
    )
    assert worker_failure_is_retryable(GenerationOOM("oom"), attempt=1)
    assert not worker_failure_is_retryable(GenerationOOM("oom"), attempt=3)


def test_integrity_failures_never_retry() -> None:
    for error, expected in (
        (SourceMismatchError("source mismatch"), OperationalFailureType.SOURCE_MISMATCH),
        (ChecksumError("checksum mismatch"), OperationalFailureType.CHECKSUM_FAILURE),
        (ValueError("configuration mismatch"), OperationalFailureType.CONFIG_FAILURE),
    ):
        assert classify_operational_failure(error) is expected
        directive = retry_directive(expected)
        assert not directive.retryable
        assert directive.maximum_retries == 0
        assert not worker_failure_is_retryable(error, attempt=1)


def test_parser_and_scorer_failures_block_without_retry() -> None:
    for error, expected in (
        (ValueError("parser extraction failed"), OperationalFailureType.PARSER_FAILURE),
        (ValueError("scoring failed"), OperationalFailureType.SCORER_FAILURE),
    ):
        assert classify_operational_failure(error) is expected
        assert retry_directive(expected).state_mutation.startswith("BLOCK")
