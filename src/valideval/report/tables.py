from __future__ import annotations

from valideval.schemas import DiagnosticResult


def diagnostic_summary_table(results: list[DiagnosticResult]) -> list[dict[str, str]]:
    return [
        {
            "diagnostic": result.diagnostic_name,
            "version": result.version,
            "warnings": str(len(result.warnings)),
        }
        for result in results
    ]
