from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from valideval.execution.manifest import atomic_write_json

SECRET_PATTERNS = (
    ("openai_key", re.compile(rb"sk-[A-Za-z0-9_-]{24,}")),
    ("huggingface_token", re.compile(rb"hf_[A-Za-z0-9]{24,}")),
    ("github_token", re.compile(rb"gh[opsu]_[A-Za-z0-9]{24,}")),
    ("aws_access_key", re.compile(rb"AKIA[0-9A-Z]{16}")),
    ("private_key", re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
)


def scan_repository(root: Path) -> dict:
    tracked = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=root, text=True, timeout=30
    ).split("\0")
    findings: list[dict[str, str]] = []
    scanned = 0
    env_files = []
    for relative in tracked:
        if not relative:
            continue
        path = root / relative
        if path.name.startswith(".env"):
            env_files.append(relative)
        if (
            not path.is_file()
            or path.stat().st_size > 10 * 1024**2
            or relative == "scripts/scan_repository_secrets.py"
        ):
            continue
        data = path.read_bytes()
        scanned += 1
        for name, pattern in SECRET_PATTERNS:
            if pattern.search(data):
                findings.append({"path": relative, "pattern": name})
    return {
        "schema_version": "valideval.secret-scan.v7.2.1",
        "status": "SECRET_SCAN_PASS" if not findings and not env_files else "SECRET_SCAN_FAIL",
        "scanned_tracked_files": scanned,
        "findings": findings,
        "tracked_env_files": env_files,
        "scope": "Tracked files up to 10 MiB; generated model caches and untracked user files excluded.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan tracked repository files for secret patterns."
    )
    parser.add_argument("--repository-root", default=".")
    parser.add_argument("--output", default="results/final_cpu_maxout/security/secret_scan.json")
    args = parser.parse_args()
    root = Path(args.repository_root).resolve()
    result = scan_repository(root)
    atomic_write_json(root / args.output, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "SECRET_SCAN_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
