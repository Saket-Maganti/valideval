from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from valideval.config import load_yaml

NO_RUN_FORBIDDEN_ACTIONS = [
    "validation experiments",
    "synthetic generation",
    "model inference",
    "downloads",
    "metric recomputation",
    "threshold tuning",
    "MMLU-Redux reruns",
    "confirmatory cross-flaw / held-out runs",
    "real-panel ranking analysis",
]

MAX_OBSERVED_FIELD_PREVIEW = 50


def require_dry_run(
    *,
    dry_run: bool,
    execute: bool,
    execute_flag: str,
    action: str,
) -> None:
    if dry_run:
        return
    if execute:
        raise ValueError(
            f"{action} is intentionally not implemented in the no-run build. "
            f"{execute_flag} records future authorization only; implement execution in a "
            "separate approved evidence run."
        )
    raise ValueError(f"{action} requires --dry-run. No evidence computation was run.")


def path_status(
    path: str | Path | None, *, required: bool = True, kind: str = "file"
) -> dict[str, Any]:
    if path is None:
        return {
            "path": None,
            "required": required,
            "exists": False,
            "kind": kind,
            "status": "missing" if required else "not_supplied",
        }
    source = Path(path)
    exists = source.exists()
    kind_ok = source.is_file() if kind == "file" else source.is_dir()
    payload: dict[str, Any] = {
        "path": str(source),
        "required": required,
        "exists": exists,
        "kind": kind,
        "kind_ok": bool(exists and kind_ok),
        "status": "ok" if exists and kind_ok else "missing" if required else "not_available",
    }
    if exists and source.is_file():
        payload["suffix"] = source.suffix
        payload["size_bytes"] = source.stat().st_size
    return payload


def inspect_structured_schema(
    path: str | Path | None,
    *,
    required_fields: list[str] | None = None,
    accepted_id_fields: list[str] | None = None,
) -> dict[str, Any]:
    required_fields = required_fields or []
    accepted_id_fields = accepted_id_fields or []
    status = path_status(path, required=True, kind="file")
    if not status["exists"]:
        status.update(
            {
                "observed_fields": [],
                "observed_field_count": 0,
                "observed_fields_truncated": False,
                "required_fields": required_fields,
                "missing_required_fields": required_fields,
                "accepted_id_fields": accepted_id_fields,
                "accepted_id_field_present": False,
                "schema_status": "not_checked",
                "parse_status": "not_checked",
            }
        )
        return status

    source = Path(path or "")
    keys: list[str] = []
    parse_status = "ok"
    try:
        if source.suffix == ".csv":
            with source.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.reader(handle)
                keys = next(reader, [])
        elif source.suffix in {".jsonl", ".ndjson"}:
            with source.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        data = json.loads(line)
                        if not isinstance(data, dict):
                            raise ValueError(f"Expected JSON object records in {source}")
                        keys = sorted(data.keys())
                        break
        elif source.suffix == ".json":
            data = json.loads(source.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                keys = sorted(data.keys())
            elif isinstance(data, list) and data and isinstance(data[0], dict):
                keys = sorted(data[0].keys())
            else:
                parse_status = "unsupported_json_shape"
        else:
            parse_status = "unsupported_suffix"
    except (OSError, UnicodeDecodeError, csv.Error, json.JSONDecodeError, ValueError) as exc:
        status.update(
            {
                "observed_fields": [],
                "observed_field_count": 0,
                "observed_fields_truncated": False,
                "required_fields": required_fields,
                "missing_required_fields": required_fields,
                "accepted_id_fields": accepted_id_fields,
                "accepted_id_field_present": False,
                "schema_status": "blocked",
                "parse_status": "parse_error",
                "parse_error": f"{type(exc).__name__}: {exc}",
            }
        )
        return status

    missing = [field for field in required_fields if field not in keys]
    id_field_present = not accepted_id_fields or any(field in keys for field in accepted_id_fields)
    observed_field_count = len(keys)
    observed_fields = keys[:MAX_OBSERVED_FIELD_PREVIEW]
    status.update(
        {
            "observed_fields": observed_fields,
            "observed_field_count": observed_field_count,
            "observed_fields_truncated": observed_field_count > len(observed_fields),
            "required_fields": required_fields,
            "missing_required_fields": missing,
            "accepted_id_fields": accepted_id_fields,
            "accepted_id_field_present": id_field_present,
            "schema_status": "ok"
            if parse_status == "ok" and not missing and id_field_present
            else "blocked",
            "parse_status": parse_status,
        }
    )
    return status


def load_yaml_config(path: str | Path) -> dict[str, Any]:
    return load_yaml(path)


def write_manifest(path: str | Path, payload: dict[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def manifest_status(*checks: dict[str, Any]) -> str:
    blocked = any(check.get("status") == "missing" for check in checks)
    schema_blocked = any(check.get("schema_status") == "blocked" for check in checks)
    return "blocked" if blocked or schema_blocked else "dry_run_ready"
