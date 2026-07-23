from __future__ import annotations

from typing import Any

from valideval.benchmarks.base import Benchmark
from valideval.schemas import DiagnosticResult

DIMENSION_STATUSES = {
    "strong",
    "moderate",
    "weak",
    "threatened",
    "unknown",
    "not applicable",
    "insufficient evidence",
}


def recommend_item(row: dict[str, Any]) -> str:
    if _truthy(row.get("coverage_critical")):
        return "coverage-critical keep"
    if _truthy(row.get("human_ambiguity_flag")) or _risk_is(row.get("temporal_risk"), "high"):
        return "human validate"
    if _truthy(row.get("negative_discrimination")):
        return "remove"
    if row.get("duplicate_cluster"):
        return "remove"
    discrimination = _float(row.get("discrimination"))
    if discrimination is not None and discrimination < 0.05:
        return "review"
    if (
        _float(row.get("shortcut_suspiciousness"))
        and _float(row["shortcut_suspiciousness"]) >= 0.50
    ):
        return "rewrite"
    if str(row.get("too_easy_hard") or "") in {"too_easy", "too_hard"}:
        return "review"
    if _float(row.get("scorer_instability")) and _float(row["scorer_instability"]) >= 0.20:
        return "human validate"
    if _float(row.get("provenance_missing")) and _float(row["provenance_missing"]) >= 0.70:
        return "review"
    return "keep"


def confidence_level(row: dict[str, Any]) -> str:
    observed = 0
    for field in [
        "difficulty",
        "discrimination",
        "shortcut_suspiciousness",
        "prompt_instability",
        "scorer_instability",
        "contamination_overlap",
        "temporal_risk",
        "provenance_missing",
    ]:
        value = row.get(field)
        observed += int(value not in {None, "", "unknown/unmeasured", "n/a"})
    if observed >= 6:
        return "high"
    if observed >= 3:
        return "medium"
    return "low"


def generate_misuse_warnings(
    benchmark: Benchmark,
    results: list[DiagnosticResult],
) -> list[str]:
    warnings = [
        f"Do not claim broad reasoning beyond the claimed construct: {benchmark.claimed_construct}.",
        "Do not treat the validity profile as a single scalar score.",
    ]
    if benchmark.construct_spec.metadata.get("artifact_scope") == "gpqa_fixture_dry_run":
        warnings.append(
            "Do not cite GPQA fixture dry-run artifacts as real GPQA Diamond benchmark findings."
        )
    by_name = _by_name(results)
    power = by_name.get("power")
    if power:
        points = power.summary_metrics.get("do_not_overinterpret_within_points")
        if points is not None:
            warnings.append(
                f"Do not overinterpret model differences within approximately {float(points):.2f} percentage points under this protocol."
            )
    saturation = by_name.get("saturation")
    if saturation:
        category = saturation.summary_metrics.get("saturation_category")
        if category in {"moderate", "severe"}:
            warnings.append(
                "Do not rank top models as meaningfully separated when the audited panel shows saturation evidence."
            )
    prompt = by_name.get("prompt_sensitivity")
    if prompt and prompt.summary_metrics.get("prompt_specific_ranking_flips"):
        warnings.append(
            "Do not compare model rankings across prompt templates without reporting prompt sensitivity."
        )
    extraction = by_name.get("extraction_robustness")
    if extraction and float(extraction.summary_metrics.get("strict_vs_lenient_score_shift") or 0.0):
        warnings.append("Do not compare across scorer or extractor configs without disclosure.")
    forensics = by_name.get("data_forensics")
    if forensics:
        overlap = _signal(forensics, "corpus_overlap")
        if overlap.get("status") in {"unavailable", "insufficient_corpus"}:
            warnings.append("Do not claim contamination-clean status from an unscanned corpus.")
        temporal = _signal(forensics, "temporal_validity")
        temporal_metrics = temporal.get("metrics", {})
        if temporal_metrics.get("items_with_temporal_warnings"):
            warnings.append(
                "Do not use time-sensitive items for current factuality claims without fresh verification."
            )
    else:
        warnings.append("Do not claim contamination-clean status without running data forensics.")
    return _dedupe(warnings)


def build_author_checklist(
    benchmark: Benchmark,
    results: list[DiagnosticResult],
) -> list[dict[str, str]]:
    by_name = _by_name(results)
    manifest_like = any(result.diagnostic_name == "data_forensics" for result in results)
    provenance = _signal(by_name.get("data_forensics"), "provenance_completeness")
    provenance_fraction = provenance.get("metrics", {}).get("completeness_fraction")
    return [
        _check("Construct defined", bool(benchmark.claimed_construct), benchmark.claimed_construct),
        _check(
            "Construct-critical fields identified",
            bool(benchmark.construct_spec.construct_critical_fields),
            ", ".join(benchmark.construct_spec.construct_critical_fields),
        ),
        _check(
            "Sources documented",
            provenance_fraction is not None and float(provenance_fraction) > 0.0,
            f"provenance completeness={provenance_fraction}",
        ),
        _check("Contamination scan", "data_forensics" in by_name, "data_forensics"),
        _check("Duplicates checked", "data_forensics" in by_name, "data_forensics"),
        _check("Shortcut diagnostic", "shortcut" in by_name, "shortcut"),
        _check("IRT/item quality", "irt" in by_name, "irt"),
        _check("Reliability", "reliability" in by_name, "reliability"),
        _check("Scoring validation", "extraction_robustness" in by_name, "extraction_robustness"),
        _check("Human agreement", False, "not yet measured"),
        _check("Saturation", "saturation" in by_name, "saturation"),
        _check("Intended/non-intended use documented", False, "validity card recommended"),
        _check("Version/hash recorded", manifest_like, "results/{benchmark}/manifest.json"),
    ]


def build_claim_evidence_matrix(
    benchmark: Benchmark,
    results: list[DiagnosticResult],
) -> list[dict[str, str]]:
    by_name = _by_name(results)
    return [
        _claim(
            f"Scores provide evidence for {benchmark.claimed_construct}.",
            "Construct definition, shortcut checks, reliability, and item quality.",
            "shortcut, reliability, irt",
            _join_results(
                [by_name.get("shortcut"), by_name.get("reliability"), by_name.get("irt")]
            ),
            _joint_status(
                [
                    _status_shortcut(by_name.get("shortcut")),
                    _status_reliability(by_name.get("reliability")),
                    _status_item_quality(by_name.get("irt")),
                ]
            ),
        ),
        _claim(
            "Items discriminate between models under the audited panel.",
            "IRT/item-quality evidence.",
            "irt",
            _irt_result(by_name.get("irt")),
            _status_item_quality(by_name.get("irt")),
        ),
        _claim(
            "Scores are stable under prompt perturbations.",
            "Reliability and prompt-sensitivity diagnostics.",
            "reliability, prompt_sensitivity",
            _join_results([by_name.get("reliability"), by_name.get("prompt_sensitivity")]),
            _status_reliability(by_name.get("reliability")),
        ),
        _claim(
            "No high local contamination evidence was found in the supplied corpus.",
            "Corpus overlap and provenance diagnostics.",
            "data_forensics",
            _forensics_result(by_name.get("data_forensics"), "corpus_overlap"),
            _status_forensics_overlap(by_name.get("data_forensics")),
        ),
        _claim(
            "Small model gaps are interpretable.",
            "Power and saturation diagnostics.",
            "power, saturation",
            _join_results([by_name.get("power"), by_name.get("saturation")]),
            _status_gap_interpretability(by_name.get("power"), by_name.get("saturation")),
        ),
        _claim(
            "Scoring/extraction rules are robust enough for this protocol.",
            "Extraction robustness and ambiguity checks.",
            "extraction_robustness",
            _extraction_result(by_name.get("extraction_robustness")),
            _status_extraction(by_name.get("extraction_robustness")),
        ),
    ]


def _check(name: str, ok: bool, evidence: str) -> dict[str, str]:
    return {
        "check": name,
        "status": "complete" if ok else "needs_review",
        "evidence": evidence or "not available",
    }


def _claim(
    claim: str,
    evidence_needed: str,
    diagnostic: str,
    result: str,
    status: str,
) -> dict[str, str]:
    return {
        "claim": claim,
        "evidence_needed": evidence_needed,
        "diagnostic": diagnostic,
        "result": result,
        "status": status,
    }


def _status_shortcut(result: DiagnosticResult | None) -> str:
    if not result:
        return "unknown"
    if result.summary_metrics.get("high_retention_variants"):
        return "threatened"
    return "moderate"


def _status_reliability(result: DiagnosticResult | None) -> str:
    if not result:
        return "unknown"
    value = result.summary_metrics.get("benchmark_level_reliability_estimate")
    if value is None:
        return "unknown"
    value = float(value)
    if value >= 0.80:
        return "strong"
    if value >= 0.60:
        return "moderate"
    if value >= 0.40:
        return "weak"
    return "threatened"


def _status_item_quality(result: DiagnosticResult | None) -> str:
    if not result:
        return "unknown"
    near_zero = float(result.summary_metrics.get("near_zero_discrimination_fraction") or 0.0)
    negative = int(result.summary_metrics.get("negative_discrimination_items") or 0)
    if negative > 0:
        return "threatened"
    if near_zero < 0.10:
        return "strong"
    if near_zero < 0.30:
        return "moderate"
    if near_zero < 0.50:
        return "weak"
    return "threatened"


def _status_forensics_overlap(result: DiagnosticResult | None) -> str:
    if not result:
        return "unknown"
    overlap = _signal(result, "corpus_overlap")
    status = overlap.get("status")
    risk = overlap.get("risk_level")
    if status in {"unavailable", "insufficient_corpus"}:
        return "insufficient evidence"
    if risk == "no local evidence found":
        return "strong"
    if risk == "low local evidence":
        return "moderate"
    if risk == "moderate local evidence":
        return "weak"
    if risk == "high local evidence":
        return "threatened"
    return "unknown"


def _status_gap_interpretability(
    power: DiagnosticResult | None,
    saturation: DiagnosticResult | None,
) -> str:
    if not power:
        return "unknown"
    category = saturation.summary_metrics.get("saturation_category") if saturation else None
    if category in {"moderate", "severe"}:
        return "threatened"
    return "moderate"


def _status_extraction(result: DiagnosticResult | None) -> str:
    if not result:
        return "unknown"
    disagreement = float(result.summary_metrics.get("extraction_disagreement_rate") or 0.0)
    if disagreement <= 0.02:
        return "strong"
    if disagreement <= 0.10:
        return "moderate"
    if disagreement <= 0.20:
        return "weak"
    return "threatened"


def _joint_status(statuses: list[str]) -> str:
    if "threatened" in statuses:
        return "threatened"
    if "weak" in statuses:
        return "weak"
    if "unknown" in statuses:
        return "insufficient evidence"
    if all(status == "strong" for status in statuses):
        return "strong"
    return "moderate"


def _join_results(results: list[DiagnosticResult | None]) -> str:
    names = [result.diagnostic_name for result in results if result is not None]
    return ", ".join(names) if names else "not measured"


def _irt_result(result: DiagnosticResult | None) -> str:
    if not result:
        return "not measured"
    return (
        f"negative={result.summary_metrics.get('negative_discrimination_items')}, "
        f"near_zero_fraction={result.summary_metrics.get('near_zero_discrimination_fraction')}"
    )


def _forensics_result(result: DiagnosticResult | None, signal_name: str) -> str:
    if not result:
        return "not measured"
    signal = _signal(result, signal_name)
    return f"{signal.get('status', 'n/a')} / {signal.get('risk_level', 'n/a')}"


def _extraction_result(result: DiagnosticResult | None) -> str:
    if not result:
        return "not measured"
    return f"disagreement={result.summary_metrics.get('extraction_disagreement_rate')}"


def _by_name(results: list[DiagnosticResult]) -> dict[str, DiagnosticResult]:
    return {result.diagnostic_name: result for result in results}


def _signal(result: DiagnosticResult | None, name: str) -> dict[str, Any]:
    if not result:
        return {}
    signals = result.summary_metrics.get("signals", {})
    value = signals.get(name, {})
    return value if isinstance(value, dict) else {}


def _risk_is(value: Any, level: str) -> bool:
    return str(value or "").startswith(level)


def _float(value: Any) -> float | None:
    if value in {None, "", "n/a"}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    output = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output
