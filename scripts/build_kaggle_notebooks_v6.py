from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

NOTEBOOKS = (
    (
        "00_valideval_t4x2_environment_and_preflight.ipynb",
        "environment",
        "Environment and fail-closed preflight",
    ),
    (
        "01_valideval_common_panel_mmlu_t4x2.ipynb",
        "mmlu",
        "Controlled common-panel MMLU",
    ),
    (
        "02_valideval_common_panel_gsm8k_t4x2.ipynb",
        "gsm8k",
        "Controlled common-panel GSM8K",
    ),
    (
        "03_valideval_common_panel_bbh_t4x2.ipynb",
        "bbh",
        "Controlled common-panel BBH",
    ),
    (
        "04_valideval_t4x2_merge_validate_package.ipynb",
        "package",
        "Merge, validate, and package",
    ),
    (
        "05_valideval_optional_robustness_runs_t4x2.ipynb",
        "robustness",
        "Optional versioned robustness run",
    ),
)

EXECUTION_MODES = [
    "fixture",
    "smoke",
    "pilot",
    "minimum_scientific",
    "full_common_panel",
    "robustness",
    "resume",
    "validate_only",
    "package_only",
]


def _lines(source: str) -> list[str]:
    lines = source.strip().splitlines()
    return [f"{line}\n" for line in lines[:-1]] + [lines[-1]]


def _notebook(stage: str, title: str) -> dict[str, object]:
    markdown = f"""# ValidEval V6 — {title}

Canonical Kaggle T4×2 notebook for the frozen V6 S1 protocol. The real smoke is always
`ENGINEERING_ONLY`; fixture and mocked runs are always `NON_EVIDENCE_FIXTURE`. Run this
notebook top-to-bottom from the tagged source package. It delegates every execution,
resume, validation, and packaging operation to tested `valideval` package code."""
    setup = f"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

STAGE = {stage!r}
MODE = os.environ.get("VALIDEVAL_EXECUTION_MODE", "fixture").strip().lower()
OUTPUT_ROOT = Path(
    os.environ.get("VALIDEVAL_NOTEBOOK_OUTPUT_ROOT", "kaggle_max_ceiling_outputs")
)
INSTALL_SOURCE = os.environ.get("VALIDEVAL_INSTALL_SOURCE", "").strip()
if importlib.util.find_spec("valideval") is None or INSTALL_SOURCE:
    if not INSTALL_SOURCE:
        raise RuntimeError(
            "valideval is absent; set VALIDEVAL_INSTALL_SOURCE to the tagged source "
            "directory or wheel before running"
        )
    subprocess.run(
        [sys.executable, "-m", "pip", "install", INSTALL_SOURCE],
        check=True,
    )

valideval_package = __import__("valideval")
execution_package = __import__("valideval.execution", fromlist=["execution"])
__version__ = valideval_package.__version__
EXECUTION_MODES = execution_package.EXECUTION_MODES
run_notebook_stage = execution_package.run_notebook_stage

if MODE not in EXECUTION_MODES:
    raise ValueError(f"Unsupported execution mode: {{MODE}}")
CONFIG_BY_STAGE = {{
    "environment": "configs/runs/mmlu_s1_v6.yaml",
    "mmlu": "configs/runs/mmlu_s1_v6.yaml",
    "gsm8k": "configs/runs/gsm8k_s1_v6.yaml",
    "bbh": "configs/runs/bbh_s1_v6.yaml",
}}
CONFIG_PATH = os.environ.get(
    "VALIDEVAL_EXECUTION_CONFIG",
    CONFIG_BY_STAGE.get(STAGE, ""),
)
if MODE != "fixture" and STAGE in {{"mmlu", "gsm8k", "bbh"}}:
    os.environ["VALIDEVAL_EXECUTION_CONFIG"] = CONFIG_PATH

print(f"valideval={{__version__}}")
print(f"stage={{STAGE}} mode={{MODE}} config={{CONFIG_PATH or 'package-set'}}")
"""
    run = """
RESULT = run_notebook_stage(STAGE, mode=MODE, output_root=OUTPUT_ROOT)
if MODE == "fixture":
    assert RESULT["evidence_state"] == "NON_EVIDENCE_FIXTURE"

preflight = RESULT.get("preflight", {})
print(json.dumps({
    "status": RESULT["status"],
    "source_commit": RESULT.get("source_commit", preflight.get("source_commit")),
    "config_hash": RESULT.get("config_hash", preflight.get("config_hash")),
    "evidence_class": RESULT.get("evidence_class", RESULT.get("evidence_state")),
    "worker_status": RESULT.get("validation", RESULT.get("results")),
    "zip_path": RESULT.get("zip_path"),
}, indent=2, sort_keys=True))
"""
    handoff = """
EXPECTED_ZIPS = [
    OUTPUT_ROOT / "packages" / "valideval_v6_s1_mmlu_s1-v6-mmlu.zip",
    OUTPUT_ROOT / "packages" / "valideval_v6_s1_gsm8k_s1-v6-gsm8k.zip",
    OUTPUT_ROOT / "packages" / "valideval_v6_s1_bbh_s1-v6-bbh.zip",
]
print("Expected S1 ZIPs:")
for path in EXPECTED_ZIPS:
    print(path)
print("Local acceptance command:")
print(
    "python -m valideval accept-s1 "
    "--input-dir kaggle_outputs/v6 --output-root imported/v6"
)
print("Runtime recalibration command:")
print(
    "python -m valideval recalibrate-runtime "
    "--input-root imported/v6 "
    "--output results/planning/runtime_recalibration_v6.json"
)
"""
    return {
        "cells": [
            {
                "cell_type": "markdown",
                "id": f"{stage}-overview",
                "metadata": {},
                "source": _lines(markdown),
            },
            {
                "cell_type": "code",
                "id": f"{stage}-setup",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": _lines(setup),
            },
            {
                "cell_type": "code",
                "id": f"{stage}-run",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": _lines(run),
            },
            {
                "cell_type": "code",
                "id": f"{stage}-handoff",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": _lines(handoff),
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3"},
            "valideval": {
                "schema_version": "6.0",
                "stage": stage,
                "execution_modes": EXECUTION_MODES,
                "fixture_evidence_state": "NON_EVIDENCE_FIXTURE",
                "real_smoke_evidence_state": "ENGINEERING_ONLY",
                "required_source_ref": "valideval-v6-controlled-gpu-smoke-ready",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "kaggle_max_ceiling"
    paths: list[Path] = []
    for filename, stage, title in NOTEBOOKS:
        payload = _notebook(stage, title)
        path = root / filename
        path.write_text(
            json.dumps(payload, indent=1, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        paths.append(path)
        print(path)
    subprocess.run(
        [sys.executable, "-m", "ruff", "format", *(str(path) for path in paths)],
        check=True,
    )


if __name__ == "__main__":
    main()
