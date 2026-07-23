from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from valideval.statistics.rank_materiality import analyze_rank_materiality


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run artifact-derived, null-calibrated MMLU rank materiality analysis."
    )
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument(
        "--subject-map",
        type=Path,
        help=(
            "Optional CSV mapping item IDs to subjects. If omitted, every matrix column must "
            "use the canonical 'subject::item_id' form."
        ),
    )
    parser.add_argument("--subject-delimiter", default="::")
    parser.add_argument("--item-column", default="item_id")
    parser.add_argument("--subject-column", default="subject")
    parser.add_argument("--bootstrap", type=int, default=500)
    parser.add_argument("--null-simulations", type=int, default=500)
    parser.add_argument(
        "--null-method",
        choices=(
            "additive",
            "binomial_subject_size",
            "empirical_bayes_additive",
            "model_margin_permutation",
        ),
        default="additive",
    )
    parser.add_argument("--model-family-map", type=Path)
    parser.add_argument("--model-column", default="model_id")
    parser.add_argument("--family-column", default="model_family")
    parser.add_argument("--practical-effect-threshold", type=float, default=0.01)
    parser.add_argument("--seed", type=int, default=2027)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/mmlu/rank_materiality_v5"),
    )
    return parser


def _load_subject_map(path: Path, item_column: str, subject_column: str) -> dict[str, str]:
    frame = pd.read_csv(path)
    required = {item_column, subject_column}
    if not required.issubset(frame.columns):
        raise ValueError(f"subject map must contain columns {sorted(required)}")
    if frame[item_column].duplicated().any():
        raise ValueError("subject map contains duplicate item identifiers")
    return dict(zip(frame[item_column].astype(str), frame[subject_column].astype(str), strict=True))


def _load_family_map(path: Path, model_column: str, family_column: str) -> dict[str, str]:
    frame = pd.read_csv(path)
    required = {model_column, family_column}
    if not required.issubset(frame.columns):
        raise ValueError(f"model family map must contain columns {sorted(required)}")
    if frame[model_column].duplicated().any():
        raise ValueError("model family map contains duplicate model identifiers")
    return dict(zip(frame[model_column].astype(str), frame[family_column].astype(str), strict=True))


def _derive_subject_map(item_ids: pd.Index, delimiter: str) -> dict[str, str]:
    if not delimiter:
        raise ValueError("subject delimiter must be non-empty")
    mapping: dict[str, str] = {}
    malformed: list[str] = []
    for raw_item_id in item_ids:
        item_id = str(raw_item_id)
        if delimiter not in item_id:
            malformed.append(item_id)
            continue
        subject, remainder = item_id.split(delimiter, 1)
        if not subject.strip() or not remainder.strip():
            malformed.append(item_id)
            continue
        mapping[item_id] = subject.strip()
    if malformed:
        examples = ", ".join(repr(item_id) for item_id in malformed[:3])
        raise ValueError(
            f"cannot derive subjects: {len(malformed)} item ID(s) do not match "
            f"'subject{delimiter}item_id'; examples: {examples}"
        )
    return mapping


def _write_records(output: Path, name: str, payload: dict[str, Any]) -> None:
    records = payload.get(name, [])
    pd.DataFrame(records).to_csv(output / f"{name}.csv", index=False)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    matrix = pd.read_csv(args.matrix, index_col=0)
    matrix.columns = matrix.columns.astype(str)
    subjects = (
        _load_subject_map(args.subject_map, args.item_column, args.subject_column)
        if args.subject_map
        else _derive_subject_map(matrix.columns, args.subject_delimiter)
    )
    model_families = (
        _load_family_map(args.model_family_map, args.model_column, args.family_column)
        if args.model_family_map
        else None
    )
    result = analyze_rank_materiality(
        matrix,
        subjects,
        n_bootstrap=args.bootstrap,
        n_null_simulations=args.null_simulations,
        null_method=args.null_method,
        seed=args.seed,
        model_families=model_families,
        practical_effect_threshold=args.practical_effect_threshold,
    )
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "rank_materiality_summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    for name in (
        "model_rank_materiality",
        "rank_confidence_sets",
        "pairwise_outranking_probabilities",
        "top_k_membership_probabilities",
        "subject_rank_correlations",
        "top_k_jaccard_stability",
        "leave_one_subject_out_sensitivity",
        "benchmark_composition_rank_confidence",
        "effect_size_filtered_reversals",
        "null_simulations",
    ):
        _write_records(args.output, name, result)
    print(f"Rank-materiality status: {result['status']}; output: {args.output}")
    return 0 if result["status"] == "REPRODUCED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
