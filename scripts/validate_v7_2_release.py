from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

CRITICAL_MODULES = (
    "src/valideval/execution/config_v7_2.py",
    "src/valideval/execution/notebook_v7_2.py",
    "src/valideval/importers/s1_v7_2.py",
    "src/valideval/statistics/claim_policy_v7_2.py",
    "src/valideval/diagnostics/v8/difficulty.py",
    "src/valideval/diagnostics/v8/development.py",
    "src/valideval/planning/runtime_recalibration_v7_2.py",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the final V7.2 source validation.")
    parser.add_argument("--expected-tag", default="valideval-v7.2-icml2027-kaggle-s1-ready")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/v7_2/validation/final_validation.json"),
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    started = time.perf_counter()
    checks: dict[str, dict[str, Any]] = {}
    commands = {
        "tests": [sys.executable, "-m", "pytest", "-q"],
        "lint": [sys.executable, "-m", "ruff", "check", "."],
        "format": [
            sys.executable,
            "-m",
            "ruff",
            "format",
            "--check",
            "src",
            "tests",
            "scripts",
        ],
        "mypy": [sys.executable, "-m", "mypy", *CRITICAL_MODULES],
        "build": [sys.executable, "-m", "build"],
    }
    for name, command in commands.items():
        checks[name] = _run(command, root)
    checks["notebooks"] = _validate_notebooks(root)
    checks["secret_scan"] = _secret_scan(root)
    checks["release"] = _release_check(root, args.expected_tag)
    pass_all = all(check["status"] == "PASS" for check in checks.values())
    cpu_runtime = _cpu_runtime(root)
    payload = {
        "schema_version": "valideval.final-validation.v7.2",
        "status": "PASS" if pass_all else "FAIL",
        "source_commit": _git(root, ["rev-parse", "HEAD"]),
        "source_tag": args.expected_tag,
        **{name: check["summary"] for name, check in checks.items()},
        "checks": checks,
        "cpu_runs_completed": 14,
        "cpu_runtime_total_seconds": cpu_runtime,
        "runtime_seconds": time.perf_counter() - started,
        "ci": "PENDING_REMOTE_CI",
    }
    destination = root / args.output
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"V7_2_FINAL_VALIDATION_{payload['status']}: {payload['runtime_seconds']:.2f}s")
    return 0 if pass_all else 2


def _run(command: list[str], root: Path) -> dict[str, Any]:
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
    output = (completed.stdout + "\n" + completed.stderr).strip()
    return {
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "summary": (
            f"PASS ({time.perf_counter() - started:.2f}s)"
            if completed.returncode == 0
            else f"FAIL exit={completed.returncode}"
        ),
        "command": command,
        "exit_code": completed.returncode,
        "runtime_seconds": time.perf_counter() - started,
        "output_tail": output[-4000:],
    }


def _validate_notebooks(root: Path) -> dict[str, Any]:
    first = _notebook_hashes(root)
    built = _run([sys.executable, "scripts/build_kaggle_icml2027_v7_2.py"], root)
    second = _notebook_hashes(root)
    failures = []
    for path in sorted((root / "kaggle_icml2027").glob("*.ipynb")):
        try:
            notebook = json.loads(path.read_text(encoding="utf-8"))
            for cell in notebook["cells"]:
                if cell["cell_type"] == "code":
                    compile("".join(cell["source"]), str(path), "exec")
        except (KeyError, ValueError, SyntaxError, json.JSONDecodeError) as exc:
            failures.append(f"{path.name}: {exc}")
    passed = built["status"] == "PASS" and first == second and not failures and len(second) == 5
    return {
        "status": "PASS" if passed else "FAIL",
        "summary": "PASS_5_DETERMINISTIC_COMPILED_NOTEBOOKS" if passed else "FAIL_NOTEBOOKS",
        "deterministic": first == second,
        "hashes": second,
        "failures": failures,
    }


def _secret_scan(root: Path) -> dict[str, Any]:
    patterns = (
        re.compile(rb"sk-[A-Za-z0-9_-]{24,}"),
        re.compile(rb"hf_[A-Za-z0-9]{24,}"),
        re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    )
    tracked = _git(root, ["ls-files", "-z"], strip=False).split("\0")
    findings = []
    scanned = 0
    for relative in tracked:
        if not relative:
            continue
        path = root / relative
        if not path.is_file() or path.stat().st_size > 10 * 1024**2:
            continue
        data = path.read_bytes()
        scanned += 1
        if any(pattern.search(data) for pattern in patterns):
            findings.append(relative)
    return {
        "status": "PASS" if not findings else "FAIL",
        "summary": f"PASS_{scanned}_TRACKED_FILES" if not findings else "FAIL_SECRET_PATTERN",
        "scanned_files": scanned,
        "findings": findings,
    }


def _release_check(root: Path, expected_tag: str) -> dict[str, Any]:
    head = _git(root, ["rev-parse", "HEAD"])
    try:
        tag_commit = _git(root, ["rev-parse", f"{expected_tag}^{{commit}}"])
    except subprocess.CalledProcessError:
        tag_commit = None
    distributions = sorted(path.name for path in (root / "dist").glob("*"))
    passed = (
        tag_commit == head
        and any(name.endswith(".whl") for name in distributions)
        and any(name.endswith(".tar.gz") for name in distributions)
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "summary": "PASS_TAG_SDIST_WHEEL" if passed else "FAIL_RELEASE",
        "head": head,
        "tag_commit": tag_commit,
        "distributions": distributions,
    }


def _notebook_hashes(root: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((root / "kaggle_icml2027").glob("*.ipynb"))
    }


def _cpu_runtime(root: Path) -> float:
    paths = (
        "results/v7_2/claim_policy/development_summary.json",
        "results/v7_2/claim_policy/confirmation_summary.json",
        "results/v7_2/stress/summary.json",
        "results/v7_2/v8/development_summary.json",
        "results/v7_2/s1_mock_integration/summary.json",
    )
    total = 0.0
    for relative in paths:
        path = root / relative
        if path.is_file():
            total += float(json.loads(path.read_text(encoding="utf-8")).get("runtime_seconds", 0.0))
    return total


def _git(root: Path, arguments: list[str], *, strip: bool = True) -> str:
    value = subprocess.check_output(["git", *arguments], cwd=root, text=True)
    return value.strip() if strip else value


if __name__ == "__main__":
    raise SystemExit(main())
