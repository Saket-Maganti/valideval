from __future__ import annotations

from pathlib import Path
from typing import Any

from valideval.importers.leaderboard_details import import_published_details


def import_helm_details(
    input_path: str | Path,
    *,
    benchmark: str,
    output_path: str | Path,
    detail_format: str = "helm_jsonl",
    mapping_report: str | Path | None = None,
    include_text: bool = False,
) -> dict[str, Any]:
    return import_published_details(
        input_path,
        benchmark=benchmark,
        output_path=output_path,
        detail_format=detail_format,
        mapping_report=mapping_report,
        include_text=include_text,
    )
