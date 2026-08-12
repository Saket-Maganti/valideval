from __future__ import annotations

import hashlib
import json
from pathlib import Path

NOTEBOOKS = (
    ("00_v7_2_t4x2_preflight.ipynb", "preflight", "T4×2 environment and preflight"),
    ("01_v7_2_s1_mmlu.ipynb", "mmlu", "MMLU S1 engineering smoke"),
    ("02_v7_2_s1_gsm8k.ipynb", "gsm8k", "GSM8K S1 engineering smoke"),
    ("03_v7_2_s1_bbh.ipynb", "bbh", "BBH S1 engineering smoke"),
    (
        "04_v7_2_s1_validate_package.ipynb",
        "validate_package",
        "validate and transactionally accept the three packages",
    ),
)


def _lines(source: str) -> list[str]:
    lines = source.strip().splitlines()
    return [f"{line}\n" for line in lines[:-1]] + [lines[-1]]


def _notebook(stage: str, title: str, requirements_hash: str) -> dict[str, object]:
    overview = f"""# ValidEval V7.2 — {title}

Canonical pre-Kaggle S1 notebook. It delegates all inference, resume, validation, import, and
packaging to tested package code. Real outputs are `ENGINEERING_ONLY`; local fixture outputs are
always `NON_EVIDENCE_FIXTURE` and cannot advance S1 acceptance or scientific claims."""
    setup = f"""
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("VALIDEVAL_REPOSITORY_ROOT", ".")).resolve()
STAGE = {stage!r}
MODE = os.environ.get("VALIDEVAL_EXECUTION_MODE", "fixture").strip().lower()
OUTPUT_ROOT = Path(os.environ.get("VALIDEVAL_NOTEBOOK_OUTPUT_ROOT", "kaggle_icml2027_outputs")).resolve()
REQUIREMENTS = ROOT / "requirements-kaggle-t4x2-v7.txt"
EXPECTED_REQUIREMENTS_SHA256 = {requirements_hash!r}
assert hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest() == EXPECTED_REQUIREMENTS_SHA256
if MODE != "fixture" and importlib.util.find_spec("valideval") is None:
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)], check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "--no-deps", str(ROOT)], check=True)

from valideval.execution.notebook_v7_2 import run_notebook_stage_v7_2  # noqa: E402, I001

print(json.dumps({{"stage": STAGE, "mode": MODE, "output_root": str(OUTPUT_ROOT)}}, indent=2))
"""
    run = """
RESULT = run_notebook_stage_v7_2(
    STAGE,
    mode=MODE,
    output_root=OUTPUT_ROOT,
    repository_root=ROOT,
)
print(json.dumps(RESULT, indent=2, sort_keys=True))
"""
    handoff = """
EXPECTED_ZIPS = [
    OUTPUT_ROOT / "packages" / "valideval_v7_2_s1_mmlu_s1-v7-2-mmlu.zip",
    OUTPUT_ROOT / "packages" / "valideval_v7_2_s1_gsm8k_s1-v7-2-gsm8k.zip",
    OUTPUT_ROOT / "packages" / "valideval_v7_2_s1_bbh_s1-v7-2-bbh.zip",
]
print("Expected ZIP paths:")
for path in EXPECTED_ZIPS:
    print(path)
print("Resume: set VALIDEVAL_EXECUTION_MODE=resume and rerun the benchmark notebook.")
print("Exact local import/acceptance command:")
print("python -m valideval accept-s1-v7-2 --input-dir kaggle_icml2027_outputs/packages --output-root imported/v7_2/s1")
print("Post-acceptance recalibration command:")
print("python -m valideval recalibrate-study-c-after-s1 --input-root imported/v7_2/s1")
"""
    return {
        "cells": [
            {
                "cell_type": "markdown",
                "id": f"{stage}-overview",
                "metadata": {},
                "source": _lines(overview),
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
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3"},
            "valideval": {
                "schema_version": "7.2",
                "stage": stage,
                "required_source_ref": "valideval-v7.2-icml2027-kaggle-s1-ready",
                "requirements_sha256": requirements_hash,
                "hardware": "Kaggle T4x2",
                "real_evidence_class": "ENGINEERING_ONLY",
                "fixture_evidence_class": "NON_EVIDENCE_FIXTURE",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "kaggle_icml2027"
    output.mkdir(parents=True, exist_ok=True)
    requirements_hash = hashlib.sha256(
        (root / "requirements-kaggle-t4x2-v7.txt").read_bytes()
    ).hexdigest()
    for filename, stage, title in NOTEBOOKS:
        path = output / filename
        path.write_text(
            json.dumps(_notebook(stage, title, requirements_hash), indent=1) + "\n",
            encoding="utf-8",
        )
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
