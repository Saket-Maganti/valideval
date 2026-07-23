from __future__ import annotations

from typing import Any

from pydantic import Field

from valideval.schemas import JsonModel


class WidePredictionRow(JsonModel):
    schema_version: str = "0.1"
    benchmark: str
    subset: str = "default"
    item_id: str
    model_id: str
    prediction: str
    gold: str
    correct: bool | None = None
    source: str = "local"
    source_file: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ImportIssue(JsonModel):
    row_number: int | None = None
    field: str | None = None
    message: str
    severity: str = "error"


class ImportSummary(JsonModel):
    schema_version: str = "0.1"
    status: str
    input_path: str
    output_path: str
    rows_read: int
    rows_written: int
    duplicate_count: int = 0
    missing_field_count: int = 0
    model_count: int = 0
    item_count: int = 0
    subsets: list[str] = Field(default_factory=list)
    discarded_text_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[ImportIssue] = Field(default_factory=list)
