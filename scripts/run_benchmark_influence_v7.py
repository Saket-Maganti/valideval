from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd

from valideval.influence import (
    crossfit_removal_evaluation,
    leave_one_item_influence,
    leave_one_subject_influence,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact/scalable V7 benchmark influence.")
    parser.add_argument("--matrix", type=Path, default=Path("cache/mmlu/wide/matrix.csv"))
    parser.add_argument(
        "--families", type=Path, default=Path("configs/models/study_h_family_map_v5.csv")
    )
    parser.add_argument("--output", type=Path, default=Path("results/v7_1/influence/mmlu"))
    args = parser.parse_args()
    started = time.perf_counter()
    matrix = pd.read_csv(args.matrix, index_col=0)
    family_frame = pd.read_csv(args.families)
    families = dict(zip(family_frame.model_id, family_frame.model_family, strict=True))
    subjects = {str(item): str(item).split("::", 1)[0] for item in matrix.columns}
    item = leave_one_item_influence(matrix)
    subject = leave_one_subject_influence(matrix, subjects)
    crossfit = crossfit_removal_evaluation(matrix, model_families=families)
    args.output.mkdir(parents=True, exist_ok=True)
    item.to_csv(args.output / "exact_leave_one_item_influence.csv", index=False)
    subject.to_csv(args.output / "leave_one_subject_influence.csv", index=False)
    crossfit.to_csv(args.output / "crossfit_removal_evaluation.csv", index=False)
    summary = {
        "status": "FAMILY_GROUPED_CROSSFIT_READY",
        "items": len(item),
        "winner_changing_items": int(item["winner_changed"].sum()),
        "top5_changing_items": int(item["top_k_changed"].sum()),
        "winner_changing_subjects": int(subject["winner_changed"].sum()),
        "runtime_seconds": time.perf_counter() - started,
        "claim_boundary": (
            "Influence measures sensitivity to deletion, not evidence that an influential item "
            "is flawed or should be removed."
        ),
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"{summary['status']}: {summary['runtime_seconds']:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
