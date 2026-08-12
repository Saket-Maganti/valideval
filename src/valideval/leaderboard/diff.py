from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from valideval.audit.ranking import compare_rankings
from valideval.schemas import utc_now


def diff_audits(
    old_path: str | Path,
    new_path: str | Path,
    *,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    old = _load_audit_bundle(Path(old_path))
    new = _load_audit_bundle(Path(new_path))
    payload = {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "old_path": str(old_path),
        "new_path": str(new_path),
        "item_count_change": _item_count(new) - _item_count(old),
        "diagnostics_coverage": {
            "old": sorted(old["diagnostics"]),
            "new": sorted(new["diagnostics"]),
            "added": sorted(new["diagnostics"] - old["diagnostics"]),
            "removed": sorted(old["diagnostics"] - new["diagnostics"]),
        },
        "certificate_change": {
            "old": old["certificate"].get("profile_level", "not issued"),
            "new": new["certificate"].get("profile_level", "not issued"),
        },
        "shortcut_change": _metric_change(old, new, "shortcut", "full_score"),
        "reliability_change": _metric_change(
            old,
            new,
            "reliability",
            "benchmark_level_reliability_estimate",
        ),
        "irt_change": _metric_change(
            old,
            new,
            "irt",
            "near_zero_discrimination_fraction",
        ),
        "ranking_change": _ranking_change(old, new),
        "warnings": _warning_changes(old, new),
        "interpretation": (
            "Audit diffs compare available artifacts. Changes are evidence about audit outputs, "
            "not proof that benchmark validity improved or declined."
        ),
    }
    if output_path is not None:
        Path(output_path).write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    return payload


def _load_audit_bundle(path: Path) -> dict[str, Any]:
    if path.is_file():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "diagnostics" in payload:
            return _bundle_from_json(payload)
    diagnostics = {}
    if path.is_dir():
        for file in sorted(path.glob("*.json")):
            payload = json.loads(file.read_text(encoding="utf-8"))
            if "diagnostic_name" in payload:
                diagnostics[payload["diagnostic_name"]] = payload
    certificate = _read_json(path / "validity_certificate.json") if path.is_dir() else {}
    ranking_views = _read_json(path / "ranking_views.json") if path.is_dir() else {}
    repair_diff = _read_json(path / "repair_diff.json") if path.is_dir() else {}
    return {
        "diagnostic_payloads": diagnostics,
        "diagnostics": set(diagnostics),
        "certificate": certificate,
        "ranking_views": ranking_views,
        "repair_diff": repair_diff,
    }


def _bundle_from_json(payload: dict[str, Any]) -> dict[str, Any]:
    diagnostics = {
        item.get("diagnostic_name", f"diagnostic_{index}"): item
        for index, item in enumerate(payload.get("diagnostics", []))
        if isinstance(item, dict)
    }
    return {
        "diagnostic_payloads": diagnostics,
        "diagnostics": set(diagnostics),
        "certificate": payload.get("certificate", {}),
        "ranking_views": payload.get("ranking_views", {}),
        "repair_diff": payload.get("repair_diff", {}),
    }


def _item_count(bundle: dict[str, Any]) -> int:
    irt = bundle["diagnostic_payloads"].get("irt", {})
    if "n_items" in irt.get("summary_metrics", {}):
        return int(irt["summary_metrics"]["n_items"])
    diff = bundle.get("repair_diff", {}).get("diff", {})
    return int(diff.get("original_item_count") or 0)


def _metric_change(
    old: dict[str, Any],
    new: dict[str, Any],
    diagnostic: str,
    metric: str,
) -> dict[str, Any]:
    old_value = (
        old["diagnostic_payloads"].get(diagnostic, {}).get("summary_metrics", {}).get(metric)
    )
    new_value = (
        new["diagnostic_payloads"].get(diagnostic, {}).get("summary_metrics", {}).get(metric)
    )
    return {
        "metric": metric,
        "old": old_value,
        "new": new_value,
        "delta": _delta(old_value, new_value),
    }


def _ranking_change(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    old_raw = (
        old.get("ranking_views", {}).get("views", {}).get("raw_accuracy", {}).get("ranking", [])
    )
    new_raw = (
        new.get("ranking_views", {}).get("views", {}).get("raw_accuracy", {}).get("ranking", [])
    )
    if not old_raw or not new_raw:
        return {"available": False, "reason": "Raw ranking views unavailable."}
    return {"available": True, **compare_rankings(old_raw, new_raw)}


def _warning_changes(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    old_warnings = {
        warning
        for payload in old["diagnostic_payloads"].values()
        for warning in payload.get("warnings", [])
    }
    new_warnings = {
        warning
        for payload in new["diagnostic_payloads"].values()
        for warning in payload.get("warnings", [])
    }
    return {
        "new": sorted(new_warnings - old_warnings),
        "resolved": sorted(old_warnings - new_warnings),
        "persisting": sorted(old_warnings & new_warnings),
    }


def _delta(old: Any, new: Any) -> float | None:
    try:
        return float(new) - float(old)
    except (TypeError, ValueError):
        return None


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
