from __future__ import annotations

from valideval.schemas import BenchmarkItem, ConstructSpec, ScoreResult


class UnavailableBenchmark:
    def __init__(self, benchmark_id: str):
        self.benchmark_id = benchmark_id
        self.claimed_construct = f"{benchmark_id} construct"
        self.construct_spec = ConstructSpec(
            claimed_construct=self.claimed_construct,
            construct_critical_fields=["prompt"],
            expected_threats=[
                "loader not implemented",
                "requires explicit dataset access and scoring validation",
            ],
            description=(
                "This adapter is a placeholder. Provide a local JSONL export or implement a "
                "validated loader before reporting empirical results."
            ),
        )

    def load_items(self) -> list[BenchmarkItem]:
        raise NotImplementedError(
            f"{self.benchmark_id} is scaffolded but not implemented. "
            "Use --benchmark toy_mcq for the offline demo or --benchmark local_jsonl "
            "with --local-path for a user-provided export."
        )

    def render_prompt(self, item: BenchmarkItem, variant: str = "full") -> str:
        raise NotImplementedError("Placeholder benchmarks cannot render prompts.")

    def score_prediction(self, item: BenchmarkItem, prediction: str) -> ScoreResult:
        raise NotImplementedError("Placeholder benchmarks cannot score predictions.")

    def available_prompt_variants(self) -> list[str]:
        return ["full"]


def unavailable_benchmark(benchmark_id: str) -> UnavailableBenchmark:
    known = {"mmlu", "gsm8k", "bbh", "truthfulqa", "causalagentbench"}
    if benchmark_id not in known:
        raise ValueError(f"Unknown benchmark: {benchmark_id}")
    return UnavailableBenchmark(benchmark_id)
