from __future__ import annotations


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
