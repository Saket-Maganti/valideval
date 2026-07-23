from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from valideval.benchmarks.base import Benchmark
from valideval.schemas import DiagnosticResult, ResponseMatrix

MatrixInput = ResponseMatrix | Mapping[str, ResponseMatrix]


class Diagnostic(Protocol):
    name: str
    version: str

    def run(
        self,
        benchmark: Benchmark,
        predictions: MatrixInput,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> DiagnosticResult: ...


def matrix_mapping(predictions: MatrixInput) -> dict[str, ResponseMatrix]:
    if isinstance(predictions, ResponseMatrix):
        variant = str(predictions.metadata.get("prompt_variant", "full"))
        return {variant: predictions}
    return dict(predictions)
