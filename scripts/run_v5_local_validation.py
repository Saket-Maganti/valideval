from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _commands(*, clean_environment: bool) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    if clean_environment:
        commands.extend(
            [
                {
                    "name": "clean_venv_create",
                    "argv": ["python3", "-m", "venv", "--clear", ".venv-v5"],
                },
                {
                    "name": "clean_venv_pip_upgrade",
                    "argv": [".venv-v5/bin/python", "-m", "pip", "install", "--upgrade", "pip"],
                },
                {
                    "name": "clean_editable_install",
                    "argv": [
                        ".venv-v5/bin/python",
                        "-m",
                        "pip",
                        "install",
                        "-e",
                        ".[dev]",
                    ],
                },
                {
                    "name": "clean_environment_tests",
                    "argv": [".venv-v5/bin/python", "-m", "pytest", "-q"],
                },
            ]
        )
    commands.extend(
        [
            {"name": "full_tests", "argv": ["python3", "-m", "pytest", "-q"]},
            {"name": "lint", "argv": ["python3", "-m", "ruff", "check", "."]},
            {
                "name": "format_check",
                "argv": ["python3", "-m", "ruff", "format", "--check", "."],
            },
            {
                "name": "type_check",
                "argv": [
                    "python3",
                    "-m",
                    "mypy",
                    "src/valideval/evidence",
                    "src/valideval/execution",
                    "src/valideval/importers/kaggle_v5.py",
                    "src/valideval/importers/post_import_v5.py",
                    "src/valideval/cross_benchmark",
                    "src/valideval/planning",
                    "src/valideval/statistics/rank_materiality.py",
                    "src/valideval/statistics/rank_nulls.py",
                    "src/valideval/measurement",
                    "src/valideval/leakage",
                    "src/valideval/synthetic",
                    "src/valideval/external_labels",
                    "src/valideval/human",
                ],
            },
            {"name": "package_build", "argv": ["python3", "-m", "build"]},
            {"name": "cli_help", "argv": ["python3", "-m", "valideval", "--help"]},
            {"name": "cli_doctor", "argv": ["python3", "-m", "valideval", "doctor", "--help"]},
            {
                "name": "mmlu_reproduction",
                "argv": ["python3", "scripts/reproduce_mmlu_evidence_v5.py"],
            },
            {
                "name": "claim_ledger",
                "argv": ["python3", "scripts/build_claim_evidence_ledger_v5.py"],
            },
            {
                "name": "leakage_audit",
                "argv": ["python3", "scripts/build_leakage_audit_v5.py"],
            },
            {
                "name": "redux_identity_resolution",
                "argv": ["python3", "scripts/resolve_mmlu_redux_v5.py"],
            },
            {
                "name": "panel_power_planner",
                "argv": ["python3", "scripts/build_common_panel_plan_v5.py"],
            },
            {
                "name": "runtime_planner",
                "argv": ["python3", "scripts/estimate_execution_runtime_v5.py"],
            },
            {
                "name": "rank_materiality",
                "argv": [
                    "python3",
                    "scripts/run_mmlu_rank_materiality_v5.py",
                    "--matrix",
                    "cache/mmlu/wide/matrix.csv",
                    "--model-family-map",
                    "configs/models/study_h_family_map_v5.csv",
                    "--bootstrap",
                    "500",
                    "--null-simulations",
                    "500",
                    "--output",
                    "results/mmlu/rank_materiality_v5",
                ],
            },
            {
                "name": "cross_benchmark_preflight",
                "argv": ["python3", "scripts/run_cross_benchmark_v5.py"],
            },
            {
                "name": "human_protocol_dry_run",
                "argv": ["python3", "scripts/build_blinded_human_packet_v5.py", "--dry-run"],
            },
            {
                "name": "synthetic_fixture",
                "argv": [
                    "python3",
                    "scripts/run_confirmatory_synthetic_v5.py",
                    "--mode",
                    "fixture",
                ],
            },
            {
                "name": "paper_assets",
                "argv": ["python3", "scripts/build_paper_v5_assets.py"],
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
                "name": "source_release_dry_run",
                "argv": ["python3", "scripts/build_release_v5.py", "--profile", "source"],
            },
            {
                "name": "evidence_release_dry_run",
                "argv": ["python3", "scripts/build_release_v5.py", "--profile", "evidence"],
            },
            {
                "name": "reviewer_release_build",
                "argv": [
                    "python3",
                    "scripts/build_release_v5.py",
                    "--profile",
                    "reviewer",
                    "--build",
                ],
            },
            {
                "name": "repository_forensics",
                "argv": ["python3", "scripts/build_repository_forensics_v5.py"],
            },
        ]
    )
    return commands


def run_validation(*, clean_environment: bool, stop_on_failure: bool) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    environment = os.environ.copy()
    environment.update(
        {
            "OPENBLAS_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "MPLCONFIGDIR": str(ROOT / ".matplotlib-v5"),
        }
    )
    started = datetime.now(timezone.utc)
    for spec in _commands(clean_environment=clean_environment):
        cwd = ROOT / spec.get("cwd", ".")
        command_started = datetime.now(timezone.utc)
        monotonic_started = time.monotonic()
        try:
            result = subprocess.run(
                spec["argv"],
                cwd=cwd,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            exit_code = result.returncode
            stdout = result.stdout
            stderr = result.stderr
        except FileNotFoundError as error:
            exit_code = 127
            stdout = ""
            stderr = str(error)
        record = {
            "name": spec["name"],
            "command": shlex.join(spec["argv"]),
            "cwd": str(cwd.relative_to(ROOT)) if cwd != ROOT else ".",
            "started_at": command_started.isoformat(),
            "duration_seconds": round(time.monotonic() - monotonic_started, 6),
            "exit_code": exit_code,
            "stdout_tail": stdout[-8000:],
            "stderr_tail": stderr[-8000:],
        }
        records.append(record)
        print(f"[{exit_code}] {record['name']}: {record['command']}", flush=True)
        if exit_code and stop_on_failure:
            break
    payload = {
        "schema_version": "5.0",
        "started_at": started.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "clean_environment_requested": clean_environment,
        "status": "PASS"
        if records and all(record["exit_code"] == 0 for record in records)
        else "FAIL",
        "command_count": len(records),
        "passed": sum(record["exit_code"] == 0 for record in records),
        "failed": sum(record["exit_code"] != 0 for record in records),
        "commands": records,
    }
    output = ROOT / "results/v5_validation"
    output.mkdir(parents=True, exist_ok=True)
    (output / "command_ledger_v5.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / "command_ledger_v5.md").write_text(_render_markdown(payload), encoding="utf-8")
    return payload


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# ValidEval V5 Local Validation Command Ledger",
        "",
        f"- Status: `{payload['status']}`",
        f"- Commands: `{payload['command_count']}`",
        f"- Passed: `{payload['passed']}`",
        f"- Failed: `{payload['failed']}`",
        "",
        "| Command ID | Exit | Duration (s) | Exact command |",
        "|---|---:|---:|---|",
    ]
    for record in payload["commands"]:
        command = record["command"].replace("|", r"\|")
        lines.append(
            f"| `{record['name']}` | {record['exit_code']} | {record['duration_seconds']:.3f} | `{command}` |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the complete local-safe V5 validation chain.")
    parser.add_argument("--skip-clean-environment", action="store_true")
    parser.add_argument("--stop-on-failure", action="store_true")
    args = parser.parse_args()
    payload = run_validation(
        clean_environment=not args.skip_clean_environment,
        stop_on_failure=args.stop_on_failure,
    )
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
