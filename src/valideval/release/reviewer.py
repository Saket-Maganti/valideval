from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from valideval.schemas import utc_now

OVERCLAIM_PATTERNS = [
    (r"\bproves?\b", "Uses proof language for diagnostic evidence."),
    (r"\btrue ranking\b", "Implies a ranking is the true ordering."),
    (r"\bglobally (valid|invalid)\b", "Claims global benchmark validity/invalidity."),
    (r"\bbenchmark is worthless\b", "Uses unsupported dismissive benchmark language."),
    (r"\bproof of cleanliness\b", "Overstates contamination scan evidence."),
    (r"\bvalidity score\b", "Suggests validity is one scalar score."),
    (r"\btotal score\b", "Suggests a total score for benchmark health."),
]

REQUIRED_TOPICS = {
    "confidence_intervals": ["confidence interval", " ci", "bootstrap", "uncertainty"],
    "baselines": ["baseline", "dumb baseline"],
    "human_validation": ["human validation", "human agreement", "judge"],
    "contamination_scan": ["contamination", "forensics", "provenance", "overlap"],
    "preregistration": ["preregistration", "preregister", "selection criteria"],
    "multiple_comparison": ["multiple comparison", "multiplicity", "correction"],
    "benchmark_identity": ["benchmark", "toy_mcq", "valid benchmark"],
    "limitations": ["limitation", "missing evidence"],
    "reproduction": ["reproduction", "python3 -m valideval", "python -m valideval"],
    "negative_results": ["negative result", "missing diagnostics", "not run", "unavailable"],
}


def reviewer_risk_report(
    *,
    report: str | Path,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    path = Path(report)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    lower = text.lower()
    risks: list[dict[str, str]] = []
    if not path.exists():
        risks.append(
            {
                "risk": "missing_report",
                "severity": "high",
                "message": f"Report path does not exist: {path}",
            }
        )
    for pattern, message in OVERCLAIM_PATTERNS:
        if any(
            not _is_negated_context(lower, match.start()) for match in re.finditer(pattern, lower)
        ):
            risks.append({"risk": "overclaim", "severity": "high", "message": message})
    for topic, needles in REQUIRED_TOPICS.items():
        if not any(needle in lower for needle in needles):
            risks.append(
                {
                    "risk": f"missing_{topic}",
                    "severity": _severity_for_topic(topic),
                    "message": f"Report does not discuss {topic.replace('_', ' ')}.",
                }
            )
    scalar_match = re.search(r"validity\s*[:=]\s*\d+(\.\d+)?", lower)
    if scalar_match and not _is_negated_context(lower, scalar_match.start()):
        risks.append(
            {
                "risk": "scalar_validity_score",
                "severity": "high",
                "message": "Report appears to present validity as a numeric scalar.",
            }
        )
    payload = {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "report": str(path),
        "risk_count": len(risks),
        "high_risk_count": sum(1 for risk in risks if risk["severity"] == "high"),
        "risks": risks,
        "limitations": [
            "Reviewer-risk mode is a static text audit. It flags possible review risks and missing disclosures; it does not judge empirical correctness."
        ],
    }
    destination = Path(output_path) if output_path else path.with_suffix(".reviewer_risk.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    payload["output_path"] = str(destination)
    return payload


def _severity_for_topic(topic: str) -> str:
    if topic in {"limitations", "reproduction", "baselines", "contamination_scan"}:
        return "high"
    if topic in {"confidence_intervals", "human_validation", "benchmark_identity"}:
        return "moderate"
    return "low"


def _is_negated_context(text: str, start: int) -> bool:
    context = text[max(0, start - 80) : start]
    after_punctuation = re.split(r"[.;:!?]\s*", context)[-1]
    negation_cues = [
        "not ",
        "do not ",
        "does not ",
        "doesn't ",
        "no ",
        "never ",
        "avoid ",
        "must not ",
        "should not ",
        "is not ",
        "are not ",
    ]
    return any(cue in after_punctuation for cue in negation_cues)
