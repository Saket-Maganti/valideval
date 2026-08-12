from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from valideval.execution.manifest import atomic_write_json, atomic_write_text
from valideval.scoring.bbh import parse_bbh_answer
from valideval.scoring.gsm8k import parse_gsm8k_answer
from valideval.scoring.mmlu import parse_mmlu_answer
from valideval.scoring.reference_v7_2_1 import (
    reference_bbh_parse,
    reference_gsm8k_parse,
    reference_mmlu_parse,
)


def extraction_fixtures() -> list[dict[str, Any]]:
    return [
        {"case": "mmlu_exact", "benchmark": "mmlu", "raw": " A ", "expected": "A"},
        {
            "case": "mmlu_prose",
            "benchmark": "mmlu",
            "raw": "Reasoning. Final answer: (C)",
            "expected": "C",
        },
        {
            "case": "mmlu_embedded_word",
            "benchmark": "mmlu",
            "raw": "The answer is complicated",
            "expected": None,
        },
        {
            "case": "mmlu_multiple",
            "benchmark": "mmlu",
            "raw": "Answer: A. Final answer: B",
            "expected": None,
        },
        {
            "case": "gsm_comma",
            "benchmark": "gsm8k",
            "raw": "Final answer: 1,234",
            "expected": "1234",
        },
        {
            "case": "gsm_decimal",
            "benchmark": "gsm8k",
            "raw": "#### 10.500",
            "expected": "10.5",
        },
        {
            "case": "gsm_fraction",
            "benchmark": "gsm8k",
            "raw": "Final answer: 2 / 4",
            "expected": "1/2",
        },
        {
            "case": "gsm_unicode_space",
            "benchmark": "gsm8k",
            "raw": "Final answer:\u00a0₹ 42",
            "expected": "42",
        },
        {
            "case": "gsm_multiple",
            "benchmark": "gsm8k",
            "raw": "Final answer: 2 and 3",
            "expected": None,
        },
        {
            "case": "bbh_choice",
            "benchmark": "bbh",
            "task": "causal_judgement",
            "kind": "MULTIPLE_CHOICE",
            "raw": "Final answer: (B)",
            "expected": "(B)",
        },
        {
            "case": "bbh_boolean",
            "benchmark": "bbh",
            "task": "boolean_expressions",
            "kind": "BOOLEAN",
            "raw": "Final answer: yes",
            "expected": "True",
        },
        {
            "case": "bbh_numeric",
            "benchmark": "bbh",
            "task": "object_counting",
            "kind": "NUMERIC",
            "raw": "Final answer: 007",
            "expected": "7",
        },
        {
            "case": "bbh_malformed",
            "benchmark": "bbh",
            "task": "causal_judgement",
            "kind": "MULTIPLE_CHOICE",
            "raw": "Final answer:",
            "expected": None,
        },
        {"case": "missing", "benchmark": "gsm8k", "raw": "", "expected": None},
    ]


def run_extraction_stress(output_root: str | Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for fixture in extraction_fixtures():
        benchmark = str(fixture["benchmark"])
        raw = str(fixture["raw"])
        if benchmark == "mmlu":
            production = parse_mmlu_answer(raw)
            reference = reference_mmlu_parse(raw)
        elif benchmark == "gsm8k":
            production = parse_gsm8k_answer(raw)
            reference = reference_gsm8k_parse(raw)
        else:
            production = parse_bbh_answer(raw, str(fixture["task"]))
            reference = reference_bbh_parse(raw, str(fixture["kind"]))
        expected = fixture["expected"]
        rows.append(
            {
                **fixture,
                "production_value": production.value,
                "production_status": production.status,
                "production_failure_type": production.failure_type,
                "reference_value": reference,
                "production_matches_expected": production.value == expected,
                "reference_matches_expected": reference == expected,
                "differential_agreement": production.value == reference,
                "incorrect_scoring_risk": production.value is not None
                and production.value != expected,
            }
        )
    frame = pd.DataFrame(rows)
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    atomic_write_text(
        output / "extraction_differential_fixtures.csv",
        frame.to_csv(index=False, lineterminator="\n"),
    )
    payload = {
        "schema_version": "valideval.extraction-stress.v7.2.1",
        "status": (
            "EXTRACTION_DIFFERENTIAL_PASS"
            if frame["production_matches_expected"].all()
            and frame["reference_matches_expected"].all()
            and frame["differential_agreement"].all()
            else "EXTRACTION_DIFFERENTIAL_FAIL"
        ),
        "fixture_count": int(len(frame)),
        "production_expected_agreement": float(frame["production_matches_expected"].mean()),
        "reference_expected_agreement": float(frame["reference_matches_expected"].mean()),
        "production_reference_agreement": float(frame["differential_agreement"].mean()),
        "incorrect_scoring_risk_rate": float(frame["incorrect_scoring_risk"].mean()),
        "evidence_class": "NON_EVIDENCE_FIXTURE",
    }
    atomic_write_json(output / "summary.json", payload)
    return payload
