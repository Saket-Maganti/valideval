from __future__ import annotations

from pathlib import Path
from typing import Any

from valideval.no_run_preflight import inspect_structured_schema

TRUTHFULQA_REQUIRED_FIELDS = ["item_id", "question"]


def inspect_truthfulqa_schema(path: str | Path) -> dict[str, Any]:
    return inspect_structured_schema(
        path,
        required_fields=TRUTHFULQA_REQUIRED_FIELDS,
        accepted_id_fields=["item_id", "question_id"],
    )
