from __future__ import annotations

from pathlib import Path
from typing import Any

from valideval.no_run_preflight import inspect_structured_schema

LOGPROB_REQUIRED_FIELDS = [
    "benchmark",
    "item_id",
    "model_id",
    "selected_answer",
    "gold_answer",
    "correct",
    "logprob_selected",
    "logprob_gold",
    "option_logprobs",
    "source",
    "metadata",
]


def inspect_logprob_schema(path: str | Path) -> dict[str, Any]:
    return inspect_structured_schema(
        path,
        required_fields=LOGPROB_REQUIRED_FIELDS,
        accepted_id_fields=["item_id"],
    )
