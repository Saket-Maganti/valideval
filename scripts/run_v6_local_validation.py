from __future__ import annotations

import argparse
import json
import os
import platform
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run and record the V6 local closure chain.")
    parser.add_argument("--skip-clean-install", action="store_true")
    parser.add_argument("--stop-on-failure", action="store_true")
    return parser


def commands(*, clean_install: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if clean_install:
        rows.extend(
            [
                {"name": "clean_venv_create", "argv": ["python3", "-m", "venv", ".venv"]},
                {
                    "name": "clean_pip_upgrade",
                    "argv": [".venv/bin/python", "-m", "pip", "install", "--upgrade", "pip"],
                },
                {
                    "name": "clean_editable_install",
                    "argv": [".venv/bin/python", "-m", "pip", "install", "-e", ".[dev]"],
                },
                {
                    "name": "clean_environment_tests",
                    "argv": [".venv/bin/python", "-m", "pytest", "-q"],
                },
            ]
        )
    rows.extend(
        [
            {"name": "native_tests", "argv": [".venv-v5/bin/python", "-m", "pytest", "-q"]},
            {"name": "lint", "argv": [".venv-v5/bin/python", "-m", "ruff", "check", "."]},
            {
                "name": "format_check",
                "argv": [".venv-v5/bin/python", "-m", "ruff", "format", "--check", "."],
            },
            {
                "name": "type_check",
                "argv": [
                    ".venv-v5/bin/python",
                    "-m",
                    "mypy",
                    "src/valideval/execution/config.py",
                    "src/valideval/execution/datasets.py",
                    "src/valideval/execution/models.py",
                    "src/valideval/execution/prompts.py",
                    "src/valideval/execution/workers.py",
                    "src/valideval/execution/shards.py",
                    "src/valideval/execution/packaging.py",
                    "src/valideval/execution/runner.py",
                    "src/valideval/importers/s1_v6.py",
                    "src/valideval/planning/runtime_recalibration_v6.py",
                    "src/valideval/scoring",
                ],
            },
            {"name": "package_build", "argv": [".venv-v5/bin/python", "-m", "build"]},
            {
                "name": "doctor",
                "argv": [".venv-v5/bin/python", "-m", "valideval", "doctor"],
            },
            {
                "name": "cli_help",
                "argv": [".venv-v5/bin/python", "-m", "valideval", "--help"],
            },
            {
                "name": "v5_evidence_reproduction",
                "argv": [".venv-v5/bin/python", "scripts/reproduce_mmlu_evidence_v5.py"],
            },
            {
                "name": "paper_assets",
                "argv": [".venv-v5/bin/python", "scripts/build_paper_v5_assets.py"],
            },
            {
                "name": "paper_pdflatex_1",
                "argv": ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                "cwd": "paper/v5",
            },
            {"name": "paper_bibtex", "argv": ["bibtex", "main"], "cwd": "paper/v5"},
            {
                "name": "paper_pdflatex_2",
                "argv": ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                "cwd": "paper/v5",
            },
            {
                "name": "paper_pdflatex_3",
                "argv": ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                "cwd": "paper/v5",
            },
            {
                "name": "release_source_dry_run",
                "argv": [
                    ".venv-v5/bin/python",
                    "scripts/build_release_v5.py",
                    "--profile",
                    "source",
                ],
            },
        ]
    )
    return rows


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    records: list[dict[str, Any]] = []
    environment = os.environ.copy()
    environment.update(
        {
            "OPENBLAS_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "MPLCONFIGDIR": str(ROOT / ".matplotlib-v6"),
        }
    )
    started = datetime.now(timezone.utc)
    for spec in commands(clean_install=not args.skip_clean_install):
        command_started = datetime.now(timezone.utc)
        monotonic_started = time.monotonic()
        cwd = ROOT / spec.get("cwd", ".")
        try:
            completed = subprocess.run(
                spec["argv"],
                cwd=cwd,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            exit_code = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
        except FileNotFoundError as exc:
            exit_code = 127
            stdout = ""
            stderr = str(exc)
        record = {
            "name": spec["name"],
            "command": shlex.join(spec["argv"]),
            "cwd": str(cwd.relative_to(ROOT)) if cwd != ROOT else ".",
            "started_at": command_started.isoformat(),
            "duration_seconds": round(time.monotonic() - monotonic_started, 6),
            "exit_code": exit_code,
            "stdout_tail": stdout[-12000:],
            "stderr_tail": stderr[-12000:],
        }
        records.append(record)
        print(f"[{exit_code}] {record['name']} ({record['duration_seconds']}s)", flush=True)
        if exit_code and args.stop_on_failure:
            break
    payload = {
        "schema_version": "6.0",
        "started_at": started.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
        },
        "status": "PASS" if records and all(row["exit_code"] == 0 for row in records) else "FAIL",
        "passed": sum(row["exit_code"] == 0 for row in records),
        "failed": sum(row["exit_code"] != 0 for row in records),
        "skipped": 0,
        "commands": records,
    }
    output = ROOT / "results/v6_validation/command_ledger_v6.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output)
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
