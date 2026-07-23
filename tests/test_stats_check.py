from __future__ import annotations

import json
from pathlib import Path

from valideval.stats.check import run_stats_check
from valideval.stats.effect_sizes import cohens_d
from valideval.stats.multiplicity import adjust_p_values


def test_stats_helpers_and_check(tmp_path: Path):
    assert adjust_p_values([0.01, 0.2], method="bh")[0] <= 0.02
    assert cohens_d([1, 2, 3], [1, 1, 1]) is not None

    results = tmp_path / "results"
    results.mkdir()
    (results / "diagnostic.json").write_text(
        json.dumps({"summary_metrics": {"auc": 0.8, "p_value": 0.01}}),
        encoding="utf-8",
    )
    payload = run_stats_check(results, tmp_path / "stats")
    assert payload["status"] == "ok"
    assert (tmp_path / "stats" / "stats_check.md").exists()
