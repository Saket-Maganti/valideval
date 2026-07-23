from __future__ import annotations

from typing import Any

SIGNAL_STATUSES = {"measured", "unavailable", "not_implemented", "insufficient_corpus"}
RISK_LEVELS = {
    "no local evidence found",
    "low local evidence",
    "moderate local evidence",
    "high local evidence",
    "unknown/unmeasured",
    "insufficient corpus",
}


def signal(
    *,
    status: str,
    risk_level: str,
    metrics: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    limitations: list[str] | None = None,
) -> dict[str, Any]:
    if status not in SIGNAL_STATUSES:
        raise ValueError(f"Unknown forensics signal status: {status}")
    if risk_level not in RISK_LEVELS:
        raise ValueError(f"Unknown forensics risk level: {risk_level}")
    return {
        "status": status,
        "risk_level": risk_level,
        "metrics": metrics or {},
        "warnings": warnings or [],
        "limitations": limitations or [],
    }


def risk_from_fraction(fraction: float | None, *, insufficient: bool = False) -> str:
    if insufficient:
        return "insufficient corpus"
    if fraction is None:
        return "unknown/unmeasured"
    if fraction <= 0.0:
        return "no local evidence found"
    if fraction < 0.05:
        return "low local evidence"
    if fraction < 0.20:
        return "moderate local evidence"
    return "high local evidence"


def status_for_corpus(n_docs: int) -> str:
    return "measured" if n_docs > 0 else "insufficient_corpus"
