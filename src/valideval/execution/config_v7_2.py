from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from valideval.execution.config import (
    ExecutionOptions,
    V6ConfigurationError,
    discover_repository_root,
    load_yaml_mapping,
    verify_referenced_file,
)

V7_2_CANONICAL_SOURCE_REF = "valideval-v7.2-icml2027-kaggle-s1-ready"
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:+@-]{0,255}$")
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")


class RunConfigV72(BaseModel):
    """Native V7.2 engineering-smoke contract for the canonical S1 bridge."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["7.2"]
    run_id: str
    study_id: Literal["study-c-s1-v7-2"]
    stage: Literal["S1"]
    evidence_class: Literal["ENGINEERING_ONLY", "NON_EVIDENCE_FIXTURE"]
    mode: Literal["fixture", "smoke", "resume", "validate_only", "package_only"]
    benchmark_id: Literal["mmlu", "gsm8k", "bbh"]
    benchmark_contract: str
    benchmark_contract_sha256: str
    panel_config: str
    panel_config_sha256: str
    subset_manifest: str
    subset_manifest_sha256: str
    output_root: str = "kaggle_icml2027_outputs"
    required_source_ref: str
    expected_source_commit: str | None = None
    allow_source_commit_from_environment: bool = True
    execution: ExecutionOptions = Field(default_factory=ExecutionOptions)

    @field_validator("run_id", "study_id", "benchmark_id")
    @classmethod
    def _validate_id(cls, value: str) -> str:
        if not _SAFE_ID.fullmatch(value):
            raise ValueError(f"unsafe identifier: {value!r}")
        return value

    @field_validator(
        "benchmark_contract_sha256", "panel_config_sha256", "subset_manifest_sha256"
    )
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        normalized = value.lower()
        if not _HEX_64.fullmatch(normalized):
            raise ValueError("expected a lowercase SHA-256 digest")
        return normalized

    @model_validator(mode="after")
    def _validate_smoke_boundary(self) -> RunConfigV72:
        if self.required_source_ref != V7_2_CANONICAL_SOURCE_REF:
            raise ValueError("S1 V7.2 must pin the canonical V7.2 source tag")
        if self.execution.backend == "mock":
            if self.evidence_class != "NON_EVIDENCE_FIXTURE" or self.mode not in {
                "fixture",
                "resume",
                "validate_only",
                "package_only",
            }:
                raise ValueError("mock S1 must be a NON_EVIDENCE_FIXTURE")
        elif self.mode not in {"resume", "validate_only", "package_only"}:
            if self.mode != "smoke" or self.evidence_class != "ENGINEERING_ONLY":
                raise ValueError("production S1 V7.2 must be an ENGINEERING_ONLY smoke")
        if self.execution.required_gpu_count != 2 and self.execution.backend == "transformers":
            raise ValueError("production S1 V7.2 requires T4 x 2")
        return self


def load_run_config_v7_2(
    path: str | Path, *, repository_root: str | Path | None = None
) -> RunConfigV72:
    source = Path(path).resolve()
    try:
        config = RunConfigV72.model_validate(load_yaml_mapping(source))
    except Exception as exc:
        if isinstance(exc, V6ConfigurationError):
            raise
        raise V6ConfigurationError(f"invalid V7.2 run configuration {source}: {exc}") from exc
    root = Path(repository_root).resolve() if repository_root else discover_repository_root(source)
    for relative, digest, label in (
        (config.benchmark_contract, config.benchmark_contract_sha256, "benchmark contract"),
        (config.panel_config, config.panel_config_sha256, "panel config"),
        (config.subset_manifest, config.subset_manifest_sha256, "subset manifest"),
    ):
        verify_referenced_file(root / relative, digest, label=label)
    return config
