from __future__ import annotations

import csv
import json
from pathlib import Path

from valideval.leakage.audit_v5 import build_leakage_audit_v5


def test_build_leakage_audit_is_fail_closed_and_machine_readable(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "leakage"
    payload = build_leakage_audit_v5(root, output)

    assert payload["gate"] == "LEAKAGE_GUARDS_PARTIAL"
    assert payload["output_is_empirical_evidence"] is False
    assert payload["p0_open_paths"]
    loaded = json.loads((output / "leakage_checks_v5.json").read_text(encoding="utf-8"))
    assert loaded["checks"]["benchmark_split_overlap"]["status"] == "BLOCKED"
    with (output / "cross_benchmark_overlap_candidates_v5.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        assert csv.DictReader(handle).fieldnames == [
            "left_dataset",
            "left_item_id",
            "right_dataset",
            "right_item_id",
            "match_type",
            "similarity",
            "question_hash",
            "option_aware_hash",
            "option_set_hash",
            "manual_review_required",
        ]
