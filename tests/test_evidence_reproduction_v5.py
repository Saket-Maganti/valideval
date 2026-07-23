from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from valideval.evidence.reproduction import reproduce_helm_mmlu_panel
from valideval.evidence.status import EvidenceStatus


def test_evidence_status_is_non_ordinal_and_complete() -> None:
    assert {status.value for status in EvidenceStatus} == {
        "REPRODUCED",
        "VERIFIED_FROM_PRIMARY_ARTIFACT",
        "REPORTED_BUT_NOT_REPRODUCED",
        "INFERRED",
        "NON_EVIDENCE_FIXTURE",
        "PLANNED",
        "BLOCKED",
        "CONTRADICTED",
        "STALE",
        "RETIRED",
    }


def test_reproduction_reconstructs_fixture_without_promoting_it(tmp_path: Path) -> None:
    primary = tmp_path / "primary.jsonl"
    records = []
    for model_id, values in {"m1": [1, 0], "m2": [0, 1]}.items():
        for index, value in enumerate(values):
            records.append(
                {
                    "benchmark": "mmlu",
                    "subset": "fixture_subject",
                    "item_id": f"id{index}",
                    "model_id": model_id,
                    "prediction": "A" if value else "B",
                    "gold": "A",
                    "correct": bool(value),
                }
            )
    primary.write_text("".join(json.dumps(row) + "\n" for row in records), encoding="utf-8")
    matrix = pd.DataFrame(
        [[1.0, 0.0], [0.0, 1.0]],
        index=["m1", "m2"],
        columns=["fixture_subject::id0", "fixture_subject::id1"],
    )
    matrix.index.name = "model_id"
    matrix_path = tmp_path / "matrix.csv"
    matrix.to_csv(matrix_path)

    payload = reproduce_helm_mmlu_panel(primary, matrix_path, tmp_path / "output")

    assert payload["evidence_status"] == "REPRODUCED"
    assert payload["observed"]["row_count"] == 4
    assert payload["matrix_comparison"]["exact_values_equal"] is True
    assert (tmp_path / "output" / "predictions.normalized.v5.jsonl.gz").exists()
