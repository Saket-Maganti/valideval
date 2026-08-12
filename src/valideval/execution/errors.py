from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FatalInferenceFailure(RuntimeError):
    """Inference cannot safely continue under the frozen execution contract."""


class RecoverableResourceFailure(RuntimeError):
    """A bounded, explicitly configured resource fallback may be attempted."""


class CudaResourceFailure(RecoverableResourceFailure):
    """CUDA resource exhaustion that must reach the scheduler."""


class ModelLoadOOM(CudaResourceFailure):
    """Out-of-memory failure while constructing the frozen model."""


class GenerationOOM(CudaResourceFailure):
    """Out-of-memory failure during generation or choice scoring."""


class OperationalFailureType(str, Enum):
    LOAD_OOM = "LOAD_OOM"
    GENERATION_OOM = "GENERATION_OOM"
    TIMEOUT = "TIMEOUT"
    CUDA_FAILURE = "CUDA_FAILURE"
    DOWNLOAD_FAILURE = "DOWNLOAD_FAILURE"
    DATASET_FAILURE = "DATASET_FAILURE"
    PARSER_FAILURE = "PARSER_FAILURE"
    SCORER_FAILURE = "SCORER_FAILURE"
    CHECKSUM_FAILURE = "CHECKSUM_FAILURE"
    CONFIG_FAILURE = "CONFIG_FAILURE"
    SOURCE_MISMATCH = "SOURCE_MISMATCH"
    GENERATION_FAILURE = "GENERATION_FAILURE"


@dataclass(frozen=True, slots=True)
class RetryDirective:
    failure_type: OperationalFailureType
    retryable: bool
    maximum_retries: int
    allowed_fallback: str | None
    state_mutation: str


_RETRY_POLICY: dict[OperationalFailureType, tuple[bool, int, str | None, str]] = {
    OperationalFailureType.LOAD_OOM: (True, 2, "REDUCE_BATCH_ONLY", "RECORD_RESOURCE_FALLBACK"),
    OperationalFailureType.GENERATION_OOM: (
        True,
        2,
        "REDUCE_BATCH_ONLY",
        "RECORD_RESOURCE_FALLBACK",
    ),
    OperationalFailureType.TIMEOUT: (True, 1, None, "RECORD_RETRY"),
    OperationalFailureType.CUDA_FAILURE: (True, 1, None, "RESTART_ISOLATED_WORKER"),
    OperationalFailureType.DOWNLOAD_FAILURE: (True, 2, None, "PRESERVE_PINNED_REVISION"),
    OperationalFailureType.DATASET_FAILURE: (True, 1, None, "PRESERVE_PINNED_REVISION"),
    OperationalFailureType.PARSER_FAILURE: (False, 0, None, "BLOCK_AND_INVALIDATE_SCORE"),
    OperationalFailureType.SCORER_FAILURE: (False, 0, None, "BLOCK_AND_INVALIDATE_SCORE"),
    OperationalFailureType.CHECKSUM_FAILURE: (False, 0, None, "REJECT_PACKAGE"),
    OperationalFailureType.CONFIG_FAILURE: (False, 0, None, "REJECT_RUN"),
    OperationalFailureType.SOURCE_MISMATCH: (False, 0, None, "REJECT_RUN"),
    OperationalFailureType.GENERATION_FAILURE: (False, 0, None, "RECORD_MODEL_FAILURE"),
}


def retry_directive(failure_type: OperationalFailureType | str) -> RetryDirective:
    resolved = OperationalFailureType(failure_type)
    retryable, maximum_retries, fallback, mutation = _RETRY_POLICY[resolved]
    return RetryDirective(resolved, retryable, maximum_retries, fallback, mutation)


def classify_operational_failure(error: BaseException) -> OperationalFailureType:
    """Classify operational failures without retrying deterministic integrity defects."""

    name = type(error).__name__.casefold()
    message = str(error).casefold()
    if isinstance(error, ModelLoadOOM):
        return OperationalFailureType.LOAD_OOM
    if isinstance(error, GenerationOOM):
        return OperationalFailureType.GENERATION_OOM
    if is_out_of_memory_error(error):
        return OperationalFailureType.GENERATION_OOM
    if isinstance(error, TimeoutError) or "timeout" in message or "timed out" in message:
        return OperationalFailureType.TIMEOUT
    if "source" in name and "mismatch" in name or "source mismatch" in message:
        return OperationalFailureType.SOURCE_MISMATCH
    if "checksum" in name or "checksum" in message or "digest" in message:
        return OperationalFailureType.CHECKSUM_FAILURE
    if "config" in name or "configuration" in message or "config mismatch" in message:
        return OperationalFailureType.CONFIG_FAILURE
    if "dataset" in name or "dataset" in message:
        return OperationalFailureType.DATASET_FAILURE
    if "download" in name or "download" in message or "connection" in message:
        return OperationalFailureType.DOWNLOAD_FAILURE
    if "parser" in name or "parse" in message or "extraction" in message:
        return OperationalFailureType.PARSER_FAILURE
    if "scorer" in name or "scoring" in message:
        return OperationalFailureType.SCORER_FAILURE
    if "cuda" in message:
        return OperationalFailureType.CUDA_FAILURE
    return OperationalFailureType.GENERATION_FAILURE


_OOM_MESSAGES = (
    "cuda out of memory",
    "cuda error: out of memory",
    "cublas_status_alloc_failed",
    "cuda oom",
    "out of memory on device",
)


def is_out_of_memory_error(error: BaseException) -> bool:
    if isinstance(error, MemoryError):
        return True
    qualified = f"{type(error).__module__}.{type(error).__name__}".lower()
    if qualified.endswith("torch.cuda.outofmemoryerror") or type(error).__name__ == (
        "OutOfMemoryError"
    ):
        return True
    message = str(error).casefold()
    return any(token in message for token in _OOM_MESSAGES)


def translate_model_load_error(error: BaseException) -> BaseException:
    if isinstance(error, RecoverableResourceFailure):
        return error
    if is_out_of_memory_error(error):
        return ModelLoadOOM(str(error) or type(error).__name__)
    return error


def translate_generation_error(error: BaseException) -> BaseException:
    if isinstance(error, RecoverableResourceFailure):
        return error
    if is_out_of_memory_error(error):
        return GenerationOOM(str(error) or type(error).__name__)
    return error
