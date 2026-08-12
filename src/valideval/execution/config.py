from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from valideval.execution.manifest import canonical_json_bytes, sha256_bytes, sha256_file

if TYPE_CHECKING:
    from valideval.execution.config_v7 import RunConfigV7

V6_SCHEMA_VERSION = "6.0"
RUN_MODES = (
    "fixture",
    "smoke",
    "pilot",
    "minimum_scientific",
    "full_common_panel",
    "robustness",
    "resume",
    "validate_only",
    "package_only",
)
TERMINAL_STATES = (
    "RUN_COMPLETE",
    "RUN_COMPLETE_WITH_RECORDED_FAILURES",
    "RUN_INCOMPLETE_RETRYABLE",
    "RUN_INCOMPLETE_FATAL",
    "CONFIG_MISMATCH",
    "DATASET_RESOLUTION_FAILURE",
    "MODEL_RESOLUTION_FAILURE",
    "INSUFFICIENT_DISK",
    "INSUFFICIENT_GPU",
    "PACKAGE_VALIDATION_FAILURE",
)
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:+@-]{0,255}$")


class V6ConfigurationError(ValueError):
    """Raised when a V6 run configuration is incomplete or contradictory."""


class ExecutionOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    backend: Literal["transformers", "mock"] = "transformers"
    gpu_ids: list[str] = Field(default_factory=lambda: ["0", "1"])
    required_gpu_count: int = 2
    allow_single_gpu_fallback: bool = False
    use_processes: bool = True
    process_start_method: Literal["spawn", "forkserver"] = "spawn"
    max_retries: int = 1
    shard_count: int = 2
    batch_size: int = 1
    max_sequence_length: int = 4096
    allow_batch_size_fallback: bool = True
    allow_sequence_length_fallback: bool = False
    minimum_sequence_length: int = 512
    timeout_seconds: float = 900.0
    minimum_free_disk_gb: float = 2.0
    model_download_margin_gb: float = 2.0

    @field_validator("gpu_ids")
    @classmethod
    def _validate_gpu_ids(cls, value: list[str]) -> list[str]:
        normalized = [str(item).strip() for item in value if str(item).strip()]
        if len(set(normalized)) != len(normalized):
            raise ValueError("gpu_ids must be unique")
        return normalized

    @model_validator(mode="after")
    def _validate_options(self) -> ExecutionOptions:
        if self.required_gpu_count < 0:
            raise ValueError("required_gpu_count must be non-negative")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.shard_count <= 0 or self.batch_size <= 0 or self.max_sequence_length <= 0:
            raise ValueError("shard_count, batch_size, and max_sequence_length must be positive")
        if self.minimum_sequence_length <= 0:
            raise ValueError("minimum_sequence_length must be positive")
        if self.minimum_sequence_length > self.max_sequence_length:
            raise ValueError("minimum_sequence_length cannot exceed max_sequence_length")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.minimum_free_disk_gb < 0 or self.model_download_margin_gb < 0:
            raise ValueError("disk requirements must be non-negative")
        if self.backend == "transformers" and not self.gpu_ids:
            raise ValueError("transformers execution requires at least one configured GPU")
        return self


class RunConfigV6(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["6.0"]
    run_id: str
    study_id: str
    evidence_class: Literal["ENGINEERING_ONLY", "NON_EVIDENCE_FIXTURE"]
    mode: Literal[
        "fixture",
        "smoke",
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
    output_root: str = "kaggle_max_ceiling_outputs"
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
        if not re.fullmatch(r"[0-9a-f]{64}", normalized):
            raise ValueError("expected a lowercase SHA-256 digest")
        return normalized

    @model_validator(mode="after")
    def _validate_evidence_boundary(self) -> RunConfigV6:
        if self.execution.backend == "mock" and self.evidence_class != "NON_EVIDENCE_FIXTURE":
            raise ValueError("mock execution must be labeled NON_EVIDENCE_FIXTURE")
        if self.mode == "fixture" and self.evidence_class != "NON_EVIDENCE_FIXTURE":
            raise ValueError("fixture execution must be labeled NON_EVIDENCE_FIXTURE")
        if self.mode == "smoke" and self.execution.backend == "transformers":
            if self.evidence_class != "ENGINEERING_ONLY":
                raise ValueError("the controlled S1 smoke is ENGINEERING_ONLY")
        return self


def load_yaml_mapping(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    try:
        payload = yaml.safe_load(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise V6ConfigurationError(f"configuration file does not exist: {source}") from exc
    if not isinstance(payload, dict):
        raise V6ConfigurationError(f"configuration must contain a mapping: {source}")
    return payload


def load_run_config(
    path: str | Path, *, repository_root: str | Path | None = None
) -> RunConfigV6 | RunConfigV7:
    source = Path(path).resolve()
    raw = load_yaml_mapping(source)
    if str(raw.get("schema_version")) == "7.0":
        from valideval.execution.config_v7 import load_run_config_v7

        return load_run_config_v7(source, repository_root=repository_root)
    try:
        config = RunConfigV6.model_validate(raw)
    except Exception as exc:
        if isinstance(exc, V6ConfigurationError):
            raise
        raise V6ConfigurationError(f"invalid V6 run configuration {source}: {exc}") from exc
    root = Path(repository_root).resolve() if repository_root else discover_repository_root(source)
    verify_referenced_file(
        root / config.benchmark_contract,
        config.benchmark_contract_sha256,
        label="benchmark contract",
    )
    verify_referenced_file(
        root / config.panel_config,
        config.panel_config_sha256,
        label="panel config",
    )
    verify_referenced_file(
        root / config.subset_manifest,
        config.subset_manifest_sha256,
        label="subset manifest",
    )
    return config


def discover_repository_root(start: str | Path) -> Path:
    candidate = Path(start).resolve()
    if candidate.is_file():
        candidate = candidate.parent
    for parent in (candidate, *candidate.parents):
        if (parent / "pyproject.toml").is_file() and (parent / "src/valideval").is_dir():
            return parent
    raise V6ConfigurationError(f"could not locate repository root from {start}")


def verify_referenced_file(path: Path, expected_sha256: str, *, label: str) -> None:
    if not path.is_file():
        raise V6ConfigurationError(f"{label} is missing: {path}")
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise V6ConfigurationError(
            f"{label} hash mismatch for {path}: expected {expected_sha256}, got {actual}"
        )


def semantic_config_hash(config: BaseModel | dict[str, Any]) -> str:
    payload = config.model_dump(mode="json") if isinstance(config, BaseModel) else dict(config)
    if payload.get("mode") in {"resume", "validate_only", "package_only"}:
        execution = payload.get("execution", {})
        if (
            payload.get("schema_version") == "7.0"
            and isinstance(execution, dict)
            and execution.get("backend") == "mock"
        ):
            payload["mode"] = "fixture"
        elif payload.get("schema_version") == "7.0":
            payload["mode"] = {
                "S2": "pilot",
                "S3": "minimum_scientific",
                "S4": "full_common_panel",
                "S5": "robustness",
            }[str(payload["stage"])]
        else:
            payload["mode"] = "smoke"
    return sha256_bytes(canonical_json_bytes(payload))


def resolve_source_commit(
    repository_root: str | Path,
    *,
    required_source_ref: str,
    expected_source_commit: str | None,
    allow_environment: bool,
) -> str:
    root = Path(repository_root)
    environment_commit = os.environ.get("VALIDEVAL_SOURCE_COMMIT", "").strip()
    head = _git_output(root, "rev-parse", "HEAD")
    resolved_ref = _git_output(root, "rev-parse", f"{required_source_ref}^{{commit}}")

    expected = expected_source_commit
    if expected is None and resolved_ref is not None:
        expected = resolved_ref
    actual = head
    if actual is None and allow_environment and environment_commit:
        actual = environment_commit
    if expected is None and allow_environment and environment_commit:
        expected = environment_commit
    if expected is None:
        raise V6ConfigurationError(
            f"cannot resolve required source ref {required_source_ref!r}; "
            "attach a tagged source checkout or set VALIDEVAL_SOURCE_COMMIT"
        )
    if actual is None:
        raise V6ConfigurationError(
            "cannot determine source commit; attach .git metadata or set VALIDEVAL_SOURCE_COMMIT"
        )
    if actual != expected:
        raise V6ConfigurationError(
            f"source commit mismatch: expected {expected} from {required_source_ref}, got {actual}"
        )
    return actual


def _git_output(root: Path, *arguments: str) -> str | None:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    value = completed.stdout.strip()
    return value or None
