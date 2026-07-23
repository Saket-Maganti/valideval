from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


def _to_jsonable(record: Any) -> dict[str, Any]:
    if isinstance(record, BaseModel):
        return record.model_dump(mode="json")
    return dict(record)


def write_jsonl(path: str | Path, records: Iterable[Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(_to_jsonable(record), sort_keys=True) + "\n")


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    records: list[dict[str, Any]] = []
    with source.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                records.append(json.loads(stripped))
    return records


def read_jsonl_as(path: str | Path, model: type[T]) -> list[T]:
    return [model(**record) for record in read_jsonl(path)]
