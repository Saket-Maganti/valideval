import json
from pathlib import Path

import numpy as np
import pandas as pd

from valideval.forensics.benchmark_v7 import analyze_mcq_answer_positions
from valideval.human.planning_v7 import annotation_power_plan
from valideval.human.protocol_v7 import stratified_candidate_sample
from valideval.validation.confirmatory_v7 import (
    fixed_confirmatory_readout,
    generate_confirmatory_matrix,
    run_confirmatory_validation,
)


def test_confirmatory_detector_cannot_receive_sealed_truth() -> None:
    matrix, sealed = generate_confirmatory_matrix(
        flaw_class="MISSINGNESS",
        severity=0.8,
        prevalence=0.2,
        model_count=12,
        family_count=3,
        item_count=50,
        subject_count=5,
        dependence=0.3,
        seed=3,
    )
    scores = fixed_confirmatory_readout(matrix)
    assert len(scores) == len(sealed)
    assert scores[sealed["sealed_is_flawed"]].mean() > scores[~sealed["sealed_is_flawed"]].mean()


def test_confirmatory_run_uses_clean_threshold() -> None:
    results, summary = run_confirmatory_validation(
        {
            "seeds": [1],
            "flaw_classes": ["NO_FLAW", "MISSINGNESS"],
            "severities": [0.5],
            "prevalences": [0.2],
            "model_count": 10,
            "family_count": 2,
            "item_count": 40,
            "subject_count": 4,
            "dependence": 0.2,
            "target_fdr": 0.05,
        }
    )
    assert len(results) == 2
    assert summary["status"] == "SYNTHETIC_CONFIRMATORY_COMPLETE"


def test_human_power_intervals_narrow_with_sample_size() -> None:
    result = annotation_power_plan((50, 500))
    widths = result["precision_ci_upper"] - result["precision_ci_lower"]
    assert widths.iloc[1] < widths.iloc[0]


def test_human_stratified_sample_is_balanced_and_disjoint() -> None:
    candidates = pd.DataFrame(
        {
            "item_id": [f"item_{index}" for index in range(80)],
            "diagnostic_score": np.linspace(0.0, 1.0, 80),
            "subject": [f"s{index % 4}" for index in range(80)],
            "benchmark": ["mmlu" if index % 2 else "bbh" for index in range(80)],
        }
    )
    result = stratified_candidate_sample(candidates, per_stratum=5, seed=9)
    assert len(result) == 20
    assert result["item_id"].is_unique
    assert set(result["diagnostic_stratum"]) == {
        "high_diagnostic",
        "medium_diagnostic",
        "low_diagnostic",
        "random_control",
    }


def test_answer_position_forensics(tmp_path: Path) -> None:
    path = tmp_path / "predictions.jsonl"
    rows = [
        {
            "item_id": "mmlu_math_id1",
            "gold": "A",
            "prediction": "A",
            "correct": True,
            "subset": "math",
            "model_id": "m1",
        },
        {
            "item_id": "mmlu_math_id1",
            "gold": "A",
            "prediction": "B",
            "correct": False,
            "subset": "math",
            "model_id": "m2",
        },
        {
            "item_id": "mmlu_math_id2",
            "gold": "B",
            "prediction": "B",
            "correct": True,
            "subset": "math",
            "model_id": "m1",
        },
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    result = analyze_mcq_answer_positions(path)
    assert result["status"] == "REPRODUCED"
    assert result["unique_items"] == 2
