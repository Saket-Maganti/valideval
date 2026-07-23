from __future__ import annotations

from pathlib import Path
from typing import Protocol

from valideval.schemas import BenchmarkItem, ConstructSpec, ScoreResult


class Benchmark(Protocol):
    benchmark_id: str
    claimed_construct: str
    construct_spec: ConstructSpec

    def load_items(self) -> list[BenchmarkItem]: ...

    def render_prompt(self, item: BenchmarkItem, variant: str = "full") -> str: ...

    def score_prediction(self, item: BenchmarkItem, prediction: str) -> ScoreResult: ...

    def available_prompt_variants(self) -> list[str]: ...


def get_benchmark(benchmark_id: str, *, local_path: str | Path | None = None) -> Benchmark:
    if benchmark_id == "toy_mcq":
        from valideval.benchmarks.toy import ToyMCQBenchmark

        return ToyMCQBenchmark()
    if benchmark_id == "gpqa_diamond_tiny_fixture":
        from valideval.benchmarks.gpqa import GPQADiamondJSONLBenchmark

        return GPQADiamondJSONLBenchmark(
            Path("examples/gpqa_diamond_tiny_fixture.jsonl"),
            benchmark_id="gpqa_diamond_tiny_fixture",
            artifact_scope="gpqa_fixture_dry_run",
        )
    if benchmark_id == "gpqa_diamond":
        if local_path is None:
            raise ValueError(
                "gpqa_diamond requires --local-path pointing to a local GPQA Diamond JSONL export. "
                "ValidEval does not download or redistribute GPQA data."
            )
        from valideval.benchmarks.gpqa import GPQADiamondJSONLBenchmark

        return GPQADiamondJSONLBenchmark(local_path)
    if benchmark_id == "local_jsonl":
        if local_path is None:
            raise ValueError("local_jsonl benchmark requires --local-path.")
        from valideval.benchmarks.local_jsonl import LocalJSONLBenchmark

        return LocalJSONLBenchmark(local_path)
    if benchmark_id == "mmlu":
        if local_path is None:
            raise ValueError(
                "mmlu requires --local-path pointing to a validated local MMLU JSONL export."
            )
        from valideval.benchmarks.mmlu import MMLULocalBenchmark

        return MMLULocalBenchmark(local_path)

    from valideval.benchmarks.hf_loader import unavailable_benchmark

    return unavailable_benchmark(benchmark_id)
