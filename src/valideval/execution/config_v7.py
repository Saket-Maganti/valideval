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

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:+@-]{0,255}$")
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
V7_2_CANONICAL_SOURCE_REF = "valideval-v7.2.1-icml2027-kaggle-s1-ready"


class RunConfigV7(BaseModel):
    """Frozen Study C execution contract.

    V7 intentionally does not relax :class:`RunConfigV6`.  Scientific runs use
    this separate schema so an old S1 smoke can never be relabelled by editing a
    single evidence field.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["7.0"]
    run_id: str
    study_id: str
    stage: Literal["S2", "S3", "S4", "S5"]
    evidence_class: Literal[
        "EXPLORATORY",
        "CONFIRMATORY",
        "ROBUSTNESS",
        "OPTIONAL_CEILING_EXTENSION",
        "NON_EVIDENCE_FIXTURE",
    ]
    mode: Literal[
        "fixture",
        "pilot",
        "minimum_scientific",
        "full_common_panel",
        "robustness",
        "resume",
        "validate_only",
        "package_only",
    ]
    benchmark_id: Literal["mmlu", "gsm8k", "bbh"]
    benchmark_contract: str
    benchmark_contract_sha256: str
    panel_config: str
    panel_config_sha256: str
    subset_manifest: str
    subset_manifest_sha256: str
    robustness_config: str | None = None
    robustness_config_sha256: str | None = None
    output_root: str = "kaggle_v7_outputs"
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
        "benchmark_contract_sha256",
        "panel_config_sha256",
        "subset_manifest_sha256",
    )
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        normalized = value.lower()
        if not _HEX_64.fullmatch(normalized):
            raise ValueError("expected a lowercase SHA-256 digest")
        return normalized

    @model_validator(mode="after")
    def _validate_scientific_boundary(self) -> RunConfigV7:
        if self.execution.backend == "mock":
            if self.evidence_class != "NON_EVIDENCE_FIXTURE" or self.mode not in {
                "fixture",
                "resume",
                "validate_only",
                "package_only",
            }:
                raise ValueError("mock execution must be a NON_EVIDENCE_FIXTURE")
            return self
        expected = {
            "S2": ("pilot", "EXPLORATORY"),
            "S3": ("minimum_scientific", "CONFIRMATORY"),
            "S4": ("full_common_panel", "CONFIRMATORY"),
            "S5": ("robustness", "ROBUSTNESS"),
        }
        if self.mode not in {"resume", "validate_only", "package_only"}:
            required_mode, required_evidence = expected[self.stage]
            if (self.mode, self.evidence_class) != (required_mode, required_evidence):
                raise ValueError(
                    f"{self.stage} requires mode={required_mode} and "
                    f"evidence_class={required_evidence}"
                )
        if self.required_source_ref != V7_2_CANONICAL_SOURCE_REF:
            raise ValueError("all future Study C runs must pin the canonical V7.2 source tag")
        if self.stage == "S5" and not (self.robustness_config and self.robustness_config_sha256):
            raise ValueError("S5 requires a hashed robustness_config")
        if bool(self.robustness_config) != bool(self.robustness_config_sha256):
            raise ValueError("robustness config path and hash must be supplied together")
        return self


def load_run_config_v7(
    path: str | Path,
    *,
    repository_root: str | Path | None = None,
) -> RunConfigV7:
    source = Path(path).resolve()
    try:
        config = RunConfigV7.model_validate(load_yaml_mapping(source))
    except Exception as exc:
        if isinstance(exc, V6ConfigurationError):
            raise
        raise V6ConfigurationError(f"invalid V7 run configuration {source}: {exc}") from exc
    root = Path(repository_root).resolve() if repository_root else discover_repository_root(source)
    for relative, digest, label in (
        (config.benchmark_contract, config.benchmark_contract_sha256, "benchmark contract"),
        (config.panel_config, config.panel_config_sha256, "panel config"),
        (config.subset_manifest, config.subset_manifest_sha256, "subset manifest"),
    ):
        verify_referenced_file(root / relative, digest, label=label)
    if config.robustness_config and config.robustness_config_sha256:
        verify_referenced_file(
            root / config.robustness_config,
            config.robustness_config_sha256,
            label="robustness config",
        )
    return config
