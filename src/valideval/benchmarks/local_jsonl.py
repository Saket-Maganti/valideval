from __future__ import annotations

from pathlib import Path

from valideval.io.jsonl import read_jsonl_as
from valideval.schemas import BenchmarkItem, ConstructSpec, ScoreResult
from valideval.scoring import exact_match_score, score_mcq


class LocalJSONLBenchmark:
    benchmark_id = "local_jsonl"
    claimed_construct = "user-provided local benchmark"

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.construct_spec = ConstructSpec(
            claimed_construct=self.claimed_construct,
            construct_tags=[],
            construct_critical_fields=["prompt"],
            expected_threats=["format artifacts", "coverage gaps", "scoring mismatch"],
            description="Local JSONL benchmark loaded from BenchmarkItem-compatible records.",
        )

    def load_items(self) -> list[BenchmarkItem]:
        if not self.path.exists():
            raise FileNotFoundError(f"Local benchmark file does not exist: {self.path}")
        return read_jsonl_as(self.path, BenchmarkItem)

    def render_prompt(self, item: BenchmarkItem, variant: str = "full") -> str:
        if variant != "full":
            raise ValueError("LocalJSONLBenchmark currently supports only the 'full' variant.")
        choices = "\n".join(item.choices or [])
        parts = []
        if item.context:
            parts.append(f"Context:\n{item.context}")
        parts.append(f"Question:\n{item.prompt}")
        if choices:
            parts.append(f"Choices:\n{choices}")
            parts.append("Answer with only the letter A, B, C, or D.")
        return "\n\n".join(parts)

    def score_prediction(self, item: BenchmarkItem, prediction: str) -> ScoreResult:
        if item.choices:
            return score_mcq(item, prediction)
        return exact_match_score(item.answer, prediction)

    def available_prompt_variants(self) -> list[str]:
        return ["full"]
