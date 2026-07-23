from __future__ import annotations

import fnmatch
import hashlib
import json
import stat
import zipfile
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FORBIDDEN_PARTS = {
    ".git",
    ".ipynb_checkpoints",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
}
FORBIDDEN_NAMES = {".DS_Store", ".env"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".sqlite", ".db", ".zip"}


def load_allowlist(path: str | Path) -> list[str]:
    patterns = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if value and not value.startswith("#"):
            patterns.append(value)
    if not patterns:
        raise ValueError(f"Release allowlist is empty: {path}")
    return patterns


def plan_release(
    root: str | Path,
    allowlist_path: str | Path,
    *,
    maximum_file_bytes: int = 100 * 1024 * 1024,
    excluded_paths: Iterable[str] = (),
) -> dict[str, Any]:
    repository = Path(root).resolve()
    patterns = load_allowlist(allowlist_path)
    explicit_exclusions = {Path(value).as_posix().removeprefix("./") for value in excluded_paths}
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []
    matched_paths: set[str] = set()
    for path in sorted(repository.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(repository)
        relative_value = relative.as_posix()
        if not any(fnmatch.fnmatch(relative_value, pattern) for pattern in patterns):
            continue
        if relative_value in matched_paths:
            continue
        matched_paths.add(relative_value)
        if relative_value in explicit_exclusions:
            excluded.append(
                {
                    "path": relative_value,
                    "reason": "generated audit is excluded from its own release plan",
                }
            )
            continue
        reason = _exclusion_reason(relative, path, maximum_file_bytes)
        if reason:
            excluded.append({"path": relative_value, "reason": reason})
            continue
        included.append(
            {
                "path": relative_value,
                "size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    if not included:
        raise ValueError("Release allowlist matched no safe files.")
    manifest_hash = hashlib.sha256(
        "".join(f"{row['path']}:{row['sha256']}\n" for row in included).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": "5.0",
        "status": "RELEASE_DRY_RUN_SAFE"
        if not excluded
        else "RELEASE_DRY_RUN_SAFE_WITH_EXCLUSIONS",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository_root": str(repository),
        "allowlist": str(allowlist_path),
        "included_count": len(included),
        "included_bytes": sum(row["size_bytes"] for row in included),
        "excluded_count": len(excluded),
        "included": included,
        "excluded": excluded,
        "manifest_sha256": manifest_hash,
    }


def build_deterministic_zip(
    root: str | Path,
    plan: dict[str, Any],
    output_path: str | Path,
) -> dict[str, Any]:
    repository = Path(root).resolve()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_payload = {
        key: value
        for key, value in plan.items()
        if key not in {"generated_at", "repository_root", "allowlist"}
    }
    manifest_bytes = (json.dumps(manifest_payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for row in plan["included"]:
            path = repository / row["path"]
            info = zipfile.ZipInfo(row["path"], date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(
                info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9
            )
        manifest_info = zipfile.ZipInfo("V5_RELEASE_MANIFEST.json", date_time=(1980, 1, 1, 0, 0, 0))
        manifest_info.compress_type = zipfile.ZIP_DEFLATED
        manifest_info.external_attr = (stat.S_IFREG | 0o644) << 16
        archive.writestr(
            manifest_info, manifest_bytes, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9
        )
    return {
        "status": "RELEASE_BUILT",
        "path": str(output),
        "sha256": _sha256(output),
        "size_bytes": output.stat().st_size,
        "member_count": len(plan["included"]) + 1,
        "manifest_sha256": plan["manifest_sha256"],
    }


def write_release_audit(plan: dict[str, Any], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# ValidEval V5 Release Allowlist Audit",
        "",
        f"- Status: `{plan['status']}`",
        f"- Included files: `{plan['included_count']}`",
        f"- Included bytes: `{plan['included_bytes']}`",
        f"- Excluded matched files: `{plan['excluded_count']}`",
        f"- Manifest SHA-256: `{plan['manifest_sha256']}`",
        "",
        "The plan is allowlist-only. Raw benchmark inputs, caches, generated model outputs, secrets, compiled files, and nested archives are excluded.",
        "",
        "## Explicit exclusions",
        "",
    ]
    if plan["excluded"]:
        lines.extend(f"- `{row['path']}`: {row['reason']}" for row in plan["excluded"])
    else:
        lines.append("- None among allowlist matches.")
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _exclusion_reason(relative: Path, path: Path, maximum_file_bytes: int) -> str | None:
    if any(part in FORBIDDEN_PARTS for part in relative.parts):
        return "forbidden cache or repository metadata path"
    if relative.name in FORBIDDEN_NAMES:
        return "forbidden metadata or secret filename"
    if relative.suffix.lower() in FORBIDDEN_SUFFIXES:
        return "forbidden compiled, database, or nested archive suffix"
    if path.is_symlink():
        return "symlinks are not included"
    if path.stat().st_size > maximum_file_bytes:
        return "file exceeds release size ceiling"
    if relative.parts and relative.parts[0] in {"cache", "data", "local_outputs", "kaggle_outputs"}:
        return "raw or cached input boundary"
    return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
