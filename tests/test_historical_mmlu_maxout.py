from __future__ import annotations

import pandas as pd

from valideval.statistics.historical_mmlu_maxout import historical_weighting_summary


def test_weighting_summary_is_tie_deterministic() -> None:
    matrix = pd.DataFrame(
        {
            "subject_a::0": [1, 1, 0],
            "subject_a::1": [1, 0, 1],
            "subject_b::0": [0, 1, 1],
            "subject_c::0": [1, 0, 0],
        },
        index=["model_a", "model_b", "model_c"],
    )
    families = {"model_a": "f1", "model_b": "f2", "model_c": "f3"}
    rows, summary = historical_weighting_summary(matrix, families)
    assert set(rows["estimand"]) == {
        "CANONICAL_ITEM_WEIGHTED",
        "BALANCED_SUBJECT_WEIGHTED",
        "TRIMMED_SUBJECT_WEIGHTED",
    }
    assert summary["estimands"]["CANONICAL_ITEM_WEIGHTED"]["winner"] == "model_a"
    assert rows.groupby("estimand")["rank"].min().eq(1.0).all()
