from __future__ import annotations

from valideval.schemas import DiagnosticResult, ValidityProfile


def build_validity_profile(
    benchmark_id: str, diagnostics: list[DiagnosticResult]
) -> ValidityProfile:
    diagnostic_map = {result.diagnostic_name: result for result in diagnostics}
    interpretation = [
        "Validity is represented as a multidimensional profile, not a single score.",
        "Diagnostics identify evidence consistent with specific measurement threats under the configured protocol.",
    ]
    limitations = [
        "Offline toy diagnostics do not establish empirical claims about real production benchmarks.",
        "IRT estimates are proxy estimates when model panels are small.",
    ]
    recommended_actions = [
        "Inspect items flagged by multiple diagnostics.",
        "Validate construct tags and prompt variants with human benchmark authors.",
    ]
    return ValidityProfile(
        benchmark_id=benchmark_id,
        diagnostics=diagnostic_map,
        interpretation=interpretation,
        limitations=limitations,
        recommended_actions=recommended_actions,
    )
