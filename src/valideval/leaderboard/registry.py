from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from valideval.schemas import DiagnosticResult, utc_now

REGISTRY_FILES = ["audits.json", "benchmarks.json", "model_panels.json", "diagnostics.json"]


def ensure_registry(registry_root: str | Path = "registry") -> dict[str, Path]:
    root = Path(registry_root)
    root.mkdir(parents=True, exist_ok=True)
    defaults = {
        "audits.json": {"schema_version": "0.1", "audits": []},
        "benchmarks.json": {"schema_version": "0.1", "benchmarks": []},
        "model_panels.json": {"schema_version": "0.1", "model_panels": []},
        "diagnostics.json": {"schema_version": "0.1", "diagnostics": []},
    }
    paths = {}
    for name, payload in defaults.items():
        path = root / name
        if not path.exists():
            path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        paths[name] = path
    return paths


def validate_registry(registry_root: str | Path = "registry") -> dict[str, Any]:
    paths = ensure_registry(registry_root)
    errors = []
    payloads = {}
    for name, path in paths.items():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{name}: invalid JSON: {exc}")
            payload = {}
        payloads[name] = payload
        if "schema_version" not in payload:
            errors.append(f"{name}: missing schema_version")
    if "audits" not in payloads["audits.json"]:
        errors.append("audits.json: missing audits list")
    if "benchmarks" not in payloads["benchmarks.json"]:
        errors.append("benchmarks.json: missing benchmarks list")
    if "model_panels" not in payloads["model_panels.json"]:
        errors.append("model_panels.json: missing model_panels list")
    if "diagnostics" not in payloads["diagnostics.json"]:
        errors.append("diagnostics.json: missing diagnostics list")
    return {
        "valid": not errors,
        "errors": errors,
        "registry_root": str(Path(registry_root)),
        "counts": {
            "audits": len(payloads.get("audits.json", {}).get("audits", [])),
            "benchmarks": len(payloads.get("benchmarks.json", {}).get("benchmarks", [])),
            "model_panels": len(payloads.get("model_panels.json", {}).get("model_panels", [])),
            "diagnostics": len(payloads.get("diagnostics.json", {}).get("diagnostics", [])),
        },
    }


def list_audits(registry_root: str | Path = "registry") -> list[dict[str, Any]]:
    paths = ensure_registry(registry_root)
    payload = json.loads(paths["audits.json"].read_text(encoding="utf-8"))
    return payload.get("audits", [])


def add_audit_to_registry(
    *,
    benchmark_id: str,
    panel_id: str,
    results: list[DiagnosticResult],
    results_root: str | Path = "results",
    reportcards_root: str | Path = "reportcards",
    registry_root: str | Path = "registry",
    status: str = "complete",
) -> dict[str, Any]:
    paths = ensure_registry(registry_root)
    root = Path(results_root)
    manifest = _read_json(root / benchmark_id / "manifest.json")
    certificate = _read_json(root / benchmark_id / panel_id / "validity_certificate.json")
    audit_id = f"{benchmark_id}:{panel_id}:{manifest.get('item_text_hash', 'nohash')}"
    record = {
        "audit_id": audit_id,
        "benchmark_id": benchmark_id,
        "benchmark_hash": manifest.get("item_text_hash"),
        "benchmark_config_hash": manifest.get("benchmark_config_hash"),
        "panel_id": panel_id,
        "diagnostics": [result.diagnostic_name for result in results],
        "certificate_level": certificate.get("profile_level", "not issued"),
        "report_path": str(Path(reportcards_root) / f"{benchmark_id}_{panel_id}.md"),
        "certificate_path": str(root / benchmark_id / panel_id / "validity_certificate.json"),
        "ranking_views_path": str(root / benchmark_id / panel_id / "ranking_views.json"),
        "item_forensics_path": str(root / benchmark_id / panel_id / "item_forensics.csv"),
        "created_at": utc_now(),
        "status": status,
    }
    _upsert(paths["audits.json"], "audits", record, "audit_id")
    _upsert(
        paths["benchmarks.json"],
        "benchmarks",
        {
            "benchmark_id": benchmark_id,
            "latest_hash": manifest.get("item_text_hash"),
            "item_count": manifest.get("item_count"),
            "latest_audit_id": audit_id,
        },
        "benchmark_id",
    )
    _upsert(
        paths["model_panels.json"],
        "model_panels",
        {"panel_id": panel_id, "latest_audit_id": audit_id},
        "panel_id",
    )
    diagnostics_payload = {
        "schema_version": "0.1",
        "diagnostics": sorted(
            {
                diagnostic
                for audit in list_audits(registry_root)
                for diagnostic in audit.get("diagnostics", [])
            }
            | {result.diagnostic_name for result in results}
        ),
    }
    paths["diagnostics.json"].write_text(
        json.dumps(diagnostics_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return record


def _upsert(path: Path, key: str, record: dict[str, Any], id_field: str) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = [item for item in payload.get(key, []) if item.get(id_field) != record[id_field]]
    records.append(record)
    payload[key] = sorted(records, key=lambda item: str(item.get(id_field)))
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
