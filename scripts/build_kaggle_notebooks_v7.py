from __future__ import annotations

import hashlib
import json
from pathlib import Path

NOTEBOOKS = (
    ("01_s2_mmlu_t4x2.ipynb", "S2 pilot MMLU", ["configs/runs_v7/mmlu_s2_v7.yaml"]),
    ("02_s2_gsm8k_t4x2.ipynb", "S2 pilot GSM8K", ["configs/runs_v7/gsm8k_s2_v7.yaml"]),
    ("03_s2_bbh_t4x2.ipynb", "S2 pilot BBH", ["configs/runs_v7/bbh_s2_v7.yaml"]),
    ("04_s3_mmlu_t4x2.ipynb", "S3 scientific MMLU", ["configs/runs_v7/mmlu_s3_v7.yaml"]),
    ("05_s3_gsm8k_t4x2.ipynb", "S3 scientific GSM8K", ["configs/runs_v7/gsm8k_s3_v7.yaml"]),
    ("06_s3_bbh_t4x2.ipynb", "S3 scientific BBH", ["configs/runs_v7/bbh_s3_v7.yaml"]),
    ("07_s4_mmlu_t4x2.ipynb", "S4 maximum-ceiling MMLU", ["configs/runs_v7/mmlu_s4_v7.yaml"]),
    ("08_s4_gsm8k_t4x2.ipynb", "S4 maximum-ceiling GSM8K", ["configs/runs_v7/gsm8k_s4_v7.yaml"]),
    ("09_s4_bbh_t4x2.ipynb", "S4 maximum-ceiling BBH", ["configs/runs_v7/bbh_s4_v7.yaml"]),
    (
        "10_s5_robustness_t4x2.ipynb",
        "S5 prompt, scoring, and quantization robustness",
        [
            "configs/runs_v7/mmlu_s5_controlled_generation_v7.yaml",
            "configs/runs_v7/mmlu_s5_option_loglikelihood_v7.yaml",
            "configs/runs_v7/gsm8k_s5_alternate_prompt_parser_v7.yaml",
            "configs/runs_v7/bbh_s5_alternate_prompt_v7.yaml",
            "configs/runs_v7/mmlu_s5_quantization_fp16_v7.yaml",
            "configs/runs_v7/mmlu_s5_quantization_nf4_v7.yaml",
            "configs/runs_v7/gsm8k_s5_quantization_fp16_v7.yaml",
            "configs/runs_v7/gsm8k_s5_quantization_nf4_v7.yaml",
            "configs/runs_v7/bbh_s5_quantization_fp16_v7.yaml",
            "configs/runs_v7/bbh_s5_quantization_nf4_v7.yaml",
        ],
    ),
)


def _lines(source: str) -> list[str]:
    lines = source.strip().splitlines()
    return [f"{line}\n" for line in lines[:-1]] + [lines[-1]]


def _notebook(title: str, configs: list[str], requirements_hash: str) -> dict[str, object]:
    overview = f"""# ValidEval V7 — {title}

Frozen T4×2 execution notebook. `fixture` validates the exact production config and exercises
the packaged mock path, but is always `NON_EVIDENCE_FIXTURE`. Real runs require two visible T4s,
the final V7 source tag, exact dataset/model revisions, and unchanged file hashes."""
    setup = f"""
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("VALIDEVAL_REPOSITORY_ROOT", ".")).resolve()
MODE = os.environ.get("VALIDEVAL_EXECUTION_MODE", "fixture").strip()
OUTPUT_ROOT = Path(os.environ.get("VALIDEVAL_NOTEBOOK_OUTPUT_ROOT", "kaggle_v7_outputs"))
CONFIGS = {configs!r}
S4_ROUTE = os.environ.get("VALIDEVAL_S4_ROUTE", "maximum").strip().lower()
if S4_ROUTE == "fallback":
    CONFIGS = [config.replace("_s4_v7.yaml", "_s4_fallback_v7.yaml") for config in CONFIGS]
elif S4_ROUTE != "maximum":
    raise ValueError("VALIDEVAL_S4_ROUTE must be maximum or fallback")
REQUIREMENTS = ROOT / "requirements-kaggle-t4x2-v7.txt"
EXPECTED_REQUIREMENTS_SHA256 = {requirements_hash!r}
assert hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest() == EXPECTED_REQUIREMENTS_SHA256

if MODE != "fixture" and importlib.util.find_spec("valideval") is None:
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)], check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "--no-deps", str(ROOT)], check=True)

from valideval.execution.notebook_v7 import run_notebook_config_v7  # noqa: E402, I001

print(json.dumps({{"mode": MODE, "configs": CONFIGS, "output_root": str(OUTPUT_ROOT)}}, indent=2))
"""
    run = """
RESULTS = [
    run_notebook_config_v7(ROOT / config, mode=MODE, output_root=OUTPUT_ROOT)
    for config in CONFIGS
]
for result in RESULTS:
    if MODE == "fixture":
        assert result["evidence_class"] == "NON_EVIDENCE_FIXTURE"
        assert result["production_config_validated"] is True
print(json.dumps(RESULTS, indent=2, sort_keys=True))
"""
    handoff = """
print("Download every deterministic ZIP from:", OUTPUT_ROOT / "packages")
print("Local import command:")
print("python -m valideval ingest-and-analyze --input <downloaded-zip-or-directory>")
print("Resume by setting VALIDEVAL_EXECUTION_MODE=resume and rerunning this notebook.")
"""
    return {
        "cells": [
            {"cell_type": "markdown", "id": "overview", "metadata": {}, "source": _lines(overview)},
            {
                "cell_type": "code",
                "id": "setup",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": _lines(setup),
            },
            {
                "cell_type": "code",
                "id": "run",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": _lines(run),
            },
            {
                "cell_type": "code",
                "id": "handoff",
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
                "schema_version": "7.0",
                "required_source_ref": "valideval-v7.2.1-icml2027-kaggle-s1-ready",
                "requirements_sha256": requirements_hash,
                "hardware": "Kaggle T4x2",
                "fixture_evidence_class": "NON_EVIDENCE_FIXTURE",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "kaggle_v7"
    output.mkdir(parents=True, exist_ok=True)
    requirements_hash = hashlib.sha256(
        (root / "requirements-kaggle-t4x2-v7.txt").read_bytes()
    ).hexdigest()
    for filename, title, configs in NOTEBOOKS:
        path = output / filename
        path.write_text(
            json.dumps(_notebook(title, list(configs), requirements_hash), indent=1) + "\n",
            encoding="utf-8",
        )
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
