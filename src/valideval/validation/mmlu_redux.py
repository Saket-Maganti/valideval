from __future__ import annotations

from pathlib import Path
from typing import Any

from valideval.validation.external_ground_truth import KNOWN_ISSUE_TYPES, import_ground_truth

MMLU_REDUX_ISSUE_TYPES = {
    *KNOWN_ISSUE_TYPES,
    "wrong_answer",
    "multiple_correct",
    "question_error",
    "label_error",
    "ambiguous_question",
    "obsolete",
}


def import_mmlu_redux_ground_truth(
    input_path: str | Path,
    output_path: str | Path,
    *,
    input_format: str = "auto",
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    return import_ground_truth(
        input_path,
        output_path,
        benchmark="mmlu",
        input_format=input_format,
        known_issue_types=MMLU_REDUX_ISSUE_TYPES,
        report_path=report_path,
    )
