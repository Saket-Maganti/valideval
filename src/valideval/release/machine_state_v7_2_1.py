from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CpuRunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    registered_runs: int = Field(ge=0)
    runtime_seconds: float = Field(ge=0)
    runtime_semantics: str
    monte_carlo_replicates: int = Field(ge=0)
    components: dict[str, Any]


class ValidationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tests: str
    coverage: str
    fuzz: str
    mutation_testing: str
    lint: str
    format: str
    mypy: str
    build: str
    notebooks: str
    secret_scan: str
    release: str


class FinalCpuMaxoutMachineState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "valideval.final-cpu-maxout-machine-state.v7.2.1"
    baseline_commit: str
    final_source_commit: str
    final_source_tag: str
    canonical_s1_source_ref: str
    metadata_commit: str
    git_clean: str
    ci: dict[str, Any]

    v7_2_1_closure_status: str
    runbook_provenance: str
    claim_policy_status: str
    claim_family_scope: list[str]
    critical_strata: dict[str, Any]
    v8_status: str

    cpu_runs: CpuRunSummary
    numerical_reproducibility: dict[str, str]

    architecture_status: str
    schema_status: str
    evidence_state_status: str
    importer_security: str
    resume_status: str
    oom_status: str

    validation: ValidationSummary

    s1_status: str
    s2_status: str
    s3_status: str
    s4_status: str

    remaining_cpu_work: list[str]
    remaining_gpu_work: list[str]
    remaining_human_work: list[str]
    exact_next_action: str


def validate_machine_state(payload: dict[str, Any]) -> FinalCpuMaxoutMachineState:
    return FinalCpuMaxoutMachineState.model_validate(payload)


def write_machine_state_schema(path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(FinalCpuMaxoutMachineState.model_json_schema(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination
