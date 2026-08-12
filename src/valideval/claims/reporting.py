from __future__ import annotations

from collections.abc import Iterable

from valideval.claims.contracts import ClaimLicenseResult


def render_claim_table(results: Iterable[ClaimLicenseResult]) -> str:
    rows = ["| Claim | Status | Class | Scope |", "|---|---|---|---|"]
    for result in results:
        scope = ", ".join(result.scope) if result.scope else "predeclared population"
        rows.append(
            f"| {result.claim_type.value} | {result.status.value} | "
            f"{result.claim_class.value} | {scope} |"
        )
    return "\n".join(rows) + "\n"
