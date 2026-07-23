from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from valideval.measurement.hierarchical_subject import validate_measurement_model_plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the V6 MMLU measurement-model closure.")
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--family-map", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/mmlu/measurement_model_closure_v6.json"),
    )
    parser.add_argument("--seed", type=int, default=2027)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    frame = pd.read_csv(args.matrix, index_col=0)
    subjects = {str(column): str(column).split("::", 1)[0] for column in frame.columns}
    if any("::" not in str(column) for column in frame.columns):
        raise ValueError("matrix columns must use subject::item_id identities")
    family_frame = pd.read_csv(args.family_map)
    families = dict(
        zip(
            family_frame["model_id"].astype(str),
            family_frame["model_family"].astype(str),
            strict=True,
        )
    )
    if set(frame.index.astype(str)) != set(families):
        raise ValueError("family map does not exactly cover the matrix models")
    result = validate_measurement_model_plan(
        frame,
        subjects,
        model_families=families,
        regularization_grid=(2.0, 10.0, 50.0),
        seed=args.seed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Measurement-model status: {result['status']}; output: {args.output}")
    return 0 if result["status"] == "MEASUREMENT_MODEL_PLAN_DEFENSIBLE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
