from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from valideval.execution.manifest import atomic_write_json


class AcceptedS2Summary(BaseModel):
    """Measured S2 inputs used to propose, never automatically authorize, S3."""

    model_config = ConfigDict(extra="forbid")

    status: str
    runtime_seconds_per_model: float = Field(gt=0)
    variance_estimate: float = Field(ge=0)
    model_failure_rate: float = Field(ge=0, le=1)
    family_coverage: int = Field(ge=1)
    extraction_reliability: float = Field(ge=0, le=1)
    primary_claim_power_floor: float = Field(ge=0, le=1)


def propose_s3_from_s2(
    s2_summary: dict[str, Any] | str | Path,
    *,
    output: str | Path | None = None,
) -> dict[str, Any]:
    """Return a fail-closed S3 proposal; it never grants execution authorization."""

    if isinstance(s2_summary, (str, Path)):
        payload = json.loads(Path(s2_summary).read_text(encoding="utf-8"))
    else:
        payload = dict(s2_summary)
    summary = AcceptedS2Summary.model_validate(payload)
    blockers: list[str] = []
    if summary.status != "S2_ACCEPTED":
        blockers.append("S2 summary is not accepted")
    if summary.extraction_reliability < 0.95:
        blockers.append("extraction reliability is below 0.95")
    if summary.model_failure_rate > 0.10:
        blockers.append("model failure rate exceeds 0.10")
    if summary.family_coverage < 5:
        blockers.append("fewer than five model families are represented")
    if summary.primary_claim_power_floor < 0.80:
        blockers.append("primary-claim planning power floor is below 0.80")
    result = {
        "schema_version": "valideval.s3-proposal.v7.2.1",
        "status": "S3_REDESIGN_REQUIRED" if blockers else "S3_PROPOSED",
        "execution_authorized": False,
        "measured_s2_inputs": summary.model_dump(mode="json"),
        "blockers": blockers,
        "claim_boundary": (
            "A proposal is not S3 authorization; a human must review scientific scope, compute, "
            "and claim hierarchy after accepted S2."
        ),
    }
    if output is not None:
        atomic_write_json(output, result)
    return result
