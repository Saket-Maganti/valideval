from __future__ import annotations

import re
from datetime import date
from typing import Any

from valideval.forensics.report import risk_from_fraction, signal
from valideval.schemas import BenchmarkItem

RELATIVE_TIME_RE = re.compile(
    r"\b(today|current|currently|latest|recent|now|this year|last year|as of)\b",
    re.IGNORECASE,
)


def temporal_validity_report(items: list[BenchmarkItem]) -> dict[str, Any]:
    per_item = {}
    risky_items = []
    for item in items:
        metadata = item.metadata
        text = f"{item.prompt} {item.context or ''}"
        has_relative = bool(RELATIVE_TIME_RE.search(text))
        stale_label_risk = bool(
            metadata.get("time_sensitive") and not metadata.get("last_verified_date")
        )
        source_after_split = _after(metadata.get("source_date"), metadata.get("split_cutoff_date"))
        outdated_metadata = [
            field
            for field in ["answer_validity_date", "last_verified_date", "temporal_scope"]
            if metadata.get("time_sensitive") and not metadata.get(field)
        ]
        risk = has_relative or stale_label_risk or source_after_split or bool(outdated_metadata)
        if risk:
            risky_items.append(item.item_id)
        per_item[item.item_id] = {
            "has_relative_or_current_phrasing": has_relative,
            "time_sensitive": bool(metadata.get("time_sensitive", False)),
            "stale_label_risk": stale_label_risk,
            "source_after_split_risk": source_after_split,
            "outdated_entity_or_fact_metadata_missing": outdated_metadata,
            "web_verification": {
                "status": "unavailable",
                "reason": "No web verification tool is configured for offline toy audits.",
            },
        }
    fraction = len(risky_items) / len(items) if items else 0.0
    return signal(
        status="measured",
        risk_level=risk_from_fraction(fraction),
        metrics={
            "items_with_temporal_warnings": risky_items,
            "temporal_warning_rate": fraction,
            "per_item": per_item,
        },
        warnings=[
            "Temporal validity is based on item text and metadata only; web verification was not performed."
        ],
    )


def _after(left: Any, right: Any) -> bool:
    if not left or not right:
        return False
    try:
        return date.fromisoformat(str(left)) > date.fromisoformat(str(right))
    except ValueError:
        return str(left) > str(right)
