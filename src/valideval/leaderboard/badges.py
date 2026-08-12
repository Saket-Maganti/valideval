from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from valideval.schemas import DiagnosticResult, utc_now

BADGE_STATUSES = {"strong", "moderate", "weak", "threatened", "unknown", "insufficient evidence"}


def health_badges(
    results: list[DiagnosticResult],
    *,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    by_name = {result.diagnostic_name: result for result in results}
    badges = {
        "shortcut_resistance": _shortcut_badge(by_name.get("shortcut")),
        "reliability": _reliability_badge(by_name.get("reliability")),
        "item_quality": _item_quality_badge(by_name.get("irt")),
        "scoring_stability": _scoring_badge(by_name.get("extraction_robustness")),
        "saturation": _saturation_badge(by_name.get("saturation")),
        "contamination_risk": _contamination_badge(by_name.get("data_forensics")),
        "coverage": _coverage_badge(by_name.get("coverage")),
    }
    payload = {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "badges": badges,
        "warnings": [
            "Badges are per-dimension evidence summaries, not a total validity score.",
        ],
    }
    if output_dir is not None:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        (output / "health_badges.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    return payload


def _badge(status: str, evidence: str) -> dict[str, str]:
    if status not in BADGE_STATUSES:
        status = "unknown"
    return {"status": status, "evidence": evidence}


def _shortcut_badge(result: DiagnosticResult | None) -> dict[str, str]:
    if not result:
        return _badge("unknown", "Shortcut diagnostic not run.")
    high = result.summary_metrics.get("high_retention_variants", [])
    if high:
        return _badge("threatened", f"High-retention variants: {', '.join(high)}.")
    return _badge("moderate", "No high-retention variants reported under this protocol.")


def _reliability_badge(result: DiagnosticResult | None) -> dict[str, str]:
    if not result:
        return _badge("unknown", "Reliability diagnostic not run.")
    value = result.summary_metrics.get("benchmark_level_reliability_estimate")
    if value is None:
        return _badge("unknown", "Reliability estimate unavailable.")
    value = float(value)
    if value >= 0.80:
        return _badge("strong", f"Reliability estimate {value:.3f}.")
    if value >= 0.60:
        return _badge("moderate", f"Reliability estimate {value:.3f}.")
    if value >= 0.40:
        return _badge("weak", f"Reliability estimate {value:.3f}.")
    return _badge("threatened", f"Reliability estimate {value:.3f}.")


def _item_quality_badge(result: DiagnosticResult | None) -> dict[str, str]:
    if not result:
        return _badge("unknown", "IRT/item-quality diagnostic not run.")
    negative = int(result.summary_metrics.get("negative_discrimination_items") or 0)
    near_zero = float(result.summary_metrics.get("near_zero_discrimination_fraction") or 0.0)
    if negative:
        return _badge("threatened", f"{negative} negative-discrimination items.")
    if near_zero < 0.10:
        return _badge("strong", f"Near-zero discrimination fraction {near_zero:.3f}.")
    if near_zero < 0.30:
        return _badge("moderate", f"Near-zero discrimination fraction {near_zero:.3f}.")
    if near_zero < 0.50:
        return _badge("weak", f"Near-zero discrimination fraction {near_zero:.3f}.")
    return _badge("threatened", f"Near-zero discrimination fraction {near_zero:.3f}.")


def _scoring_badge(result: DiagnosticResult | None) -> dict[str, str]:
    if not result:
        return _badge("unknown", "Extraction robustness diagnostic not run.")
    disagreement = float(result.summary_metrics.get("extraction_disagreement_rate") or 0.0)
    if disagreement <= 0.02:
        return _badge("strong", f"Extractor disagreement rate {disagreement:.3f}.")
    if disagreement <= 0.10:
        return _badge("moderate", f"Extractor disagreement rate {disagreement:.3f}.")
    if disagreement <= 0.20:
        return _badge("weak", f"Extractor disagreement rate {disagreement:.3f}.")
    return _badge("threatened", f"Extractor disagreement rate {disagreement:.3f}.")


def _saturation_badge(result: DiagnosticResult | None) -> dict[str, str]:
    if not result:
        return _badge("unknown", "Saturation diagnostic not run.")
    category = result.summary_metrics.get("saturation_category", "unknown")
    mapping = {
        "not saturated": "strong",
        "mild": "moderate",
        "moderate": "weak",
        "severe": "threatened",
        "insufficient evidence": "insufficient evidence",
    }
    return _badge(mapping.get(category, "unknown"), f"Saturation category: {category}.")


def _contamination_badge(result: DiagnosticResult | None) -> dict[str, str]:
    if not result:
        return _badge("unknown", "Data-forensics diagnostic not run.")
    overlap = result.summary_metrics.get("signals", {}).get("corpus_overlap", {})
    status = overlap.get("status")
    risk = overlap.get("risk_level")
    if status in {"unavailable", "insufficient_corpus"}:
        return _badge(
            "insufficient evidence", "Local corpus overlap was unavailable or insufficient."
        )
    mapping = {
        "no local evidence found": "strong",
        "low local evidence": "moderate",
        "moderate local evidence": "weak",
        "high local evidence": "threatened",
    }
    return _badge(mapping.get(risk, "unknown"), f"Corpus overlap risk: {risk}.")


def _coverage_badge(result: DiagnosticResult | None) -> dict[str, str]:
    if not result:
        return _badge("unknown", "Coverage diagnostic not run.")
    missing = result.summary_metrics.get("missing_expected_tags", [])
    if missing:
        return _badge("weak", f"Missing expected tags: {', '.join(missing)}.")
    return _badge("moderate", "Tag coverage metadata present under this protocol.")
