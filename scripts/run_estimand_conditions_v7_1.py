from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import pandas as pd

from valideval.measurement.estimand_conditions_v7_1 import (
    compare_canonical_and_deduplicated,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare canonical and deduplicated estimands.")
    parser.add_argument("--matrix", type=Path, default=Path("cache/mmlu/wide/matrix.csv"))
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("results/freeze/study_c_v7/mmlu_scientific_full_v7.json"),
    )
    parser.add_argument("--bootstrap", type=int, default=200)
    parser.add_argument("--output", type=Path, default=Path("results/v7_1/estimand_conditions"))
    args = parser.parse_args()
    started = time.perf_counter()
    matrix = pd.read_csv(args.matrix, index_col=0)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    # HELM persists source-dataset row identifiers whose per-subject offsets include
    # non-test rows. The frozen manifest records zero-based test-split row indices.
    # Map them by within-subject source order, without inspecting model responses.
    columns_by_subject: dict[str, list[tuple[int, str]]] = {}
    for column in map(str, matrix.columns):
        subject, source_id = column.split("::", maxsplit=1)
        match = re.search(r"_id(\d+)$", source_id)
        if match is None:
            raise ValueError(f"cannot parse HELM source row identity: {column}")
        columns_by_subject.setdefault(subject, []).append((int(match.group(1)), column))
    ordered_columns = {
        subject: [column for _, column in sorted(rows)]
        for subject, rows in columns_by_subject.items()
    }
    subject_offsets: dict[str, int] = {}
    offset = 0
    for subject in sorted(ordered_columns):
        subject_offsets[subject] = offset
        offset += len(ordered_columns[subject])
    retained = [
        ordered_columns[str(item["subtask"])][
            int(item["row_index"]) - subject_offsets[str(item["subtask"])]
        ]
        for item in manifest["items"]
    ]
    summary, comparison = compare_canonical_and_deduplicated(
        matrix,
        retained,
        benchmark_id="mmlu",
        n_bootstrap=args.bootstrap,
    )
    args.output.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output / "mmlu_condition_summary.csv", index=False)
    artifacts = comparison.pop("artifacts")
    for condition, payload in artifacts.items():
        condition_dir = args.output / condition.lower()
        condition_dir.mkdir(parents=True, exist_ok=True)
        for name, frame in payload.items():
            frame.to_csv(condition_dir / f"{name}.csv", index=False)
    comparison.update(
        {
            "runtime_seconds": time.perf_counter() - started,
            "bbh_status": "BLOCKED_PENDING_EXACT_STUDY_C_RESPONSE_MATRIX",
            "bbh_reason": (
                "No cached exact-model BBH response matrix exists; no comparison was fabricated."
            ),
            "mmlu_identity_mapping": (
                "Frozen zero-based test-split row_index mapped to HELM source IDs by "
                "the canonical subject offset and within-subject numeric source order."
            ),
        }
    )
    (args.output / "summary.json").write_text(
        json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"{comparison['status']}: {comparison['runtime_seconds']:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
