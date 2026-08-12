from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

CURRENT_PACKAGE_SCHEMA = "valideval.execution-package.v7.2.1"
CURRENT_EXECUTION_SCHEMA = "valideval.execution.v7.1"
CURRENT_PACKAGE_MEMBERS = (
    "run_manifest.json",
    "environment.json",
    "models.json",
    "benchmark_contract.json",
    "config_snapshot.yaml",
    "file_checksums.json",
    "shard_status.json",
    "failure_summary.csv",
    "predictions.jsonl",
    "matrix.csv",
)

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:+@/-]{0,255}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")


class BenchmarkId(str, Enum):
    MMLU = "mmlu"
    GSM8K = "gsm8k"
    BBH = "bbh"


class ClaimFamilyId(str, Enum):
    PRIMARY_PAIRWISE = "PRIMARY_PAIRWISE"
    TOP_K = "TOP_K"
    THRESHOLD_PASS = "THRESHOLD_PASS"
    ITEM_DIAGNOSTICS = "ITEM_DIAGNOSTICS"
    TRANSPORT = "TRANSPORT"
    REPAIR = "REPAIR"


@dataclass(frozen=True, slots=True)
class RunId:
    value: str

    def __post_init__(self) -> None:
        if not _SAFE_ID.fullmatch(self.value):
            raise ValueError(f"unsafe run identifier: {self.value!r}")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class SourceRef:
    value: str

    def __post_init__(self) -> None:
        if not _SAFE_ID.fullmatch(self.value):
            raise ValueError(f"unsafe source reference: {self.value!r}")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class SourceCommit:
    value: str

    def __post_init__(self) -> None:
        if not _COMMIT.fullmatch(self.value):
            raise ValueError("source commit must be a lowercase full Git SHA")

    def __str__(self) -> str:
        return self.value


def export_current_package_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": CURRENT_PACKAGE_SCHEMA,
        "title": "ValidEval current execution package",
        "description": (
            "V7.2.1 package envelope over the preserved V7.1 execution-record schema. "
            "Legacy compatibility is explicit rather than inferred."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": list(CURRENT_PACKAGE_MEMBERS),
        "properties": {
            member: {"type": "string", "description": "SHA-256-addressed package member"}
            for member in CURRENT_PACKAGE_MEMBERS
        },
    }
