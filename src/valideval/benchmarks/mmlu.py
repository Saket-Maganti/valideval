from __future__ import annotations

from pathlib import Path

from valideval.benchmarks.local_jsonl import LocalJSONLBenchmark
from valideval.schemas import ConstructSpec


class MMLULocalBenchmark(LocalJSONLBenchmark):
    """Load a user-provided MMLU JSONL export without downloading HF data."""

    benchmark_id = "mmlu"
    claimed_construct = "broad academic knowledge and problem solving"

    def __init__(self, path: str | Path):
        super().__init__(path)
        self.construct_spec = ConstructSpec(
            claimed_construct=self.claimed_construct,
            construct_tags=[
                "stem",
                "humanities",
                "social_sciences",
                "professional",
                "other",
            ],
            construct_critical_fields=["prompt", "choices"],
            expected_threats=[
                "subject imbalance",
                "answer-label priors",
                "contamination overlap",
                "low-discrimination items",
            ],
            description=(
                "Local MMLU JSONL export. Provide a validated export before reporting "
                "empirical results."
            ),
            metadata={"loader": "mmlu_local_jsonl", "status": "local_export_required"},
        )
