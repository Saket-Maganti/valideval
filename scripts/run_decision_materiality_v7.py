from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd

from valideval.decision import (
    compare_selection_rules,
    item_removal_fragility,
    pairwise_confidence_graph,
    selective_ranking,
    subject_weight_fragility,
)
from valideval.statistics.rank_nulls import subject_accuracy_matrix
from valideval.statistics.study_h_v7 import nested_subject_item_bootstrap


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V7 decision materiality analysis.")
    parser.add_argument("--matrix", type=Path, default=Path("cache/mmlu/wide/matrix.csv"))
    parser.add_argument(
        "--score-draws",
        type=Path,
        default=Path("results/mmlu/study_h_v7/nested_bootstrap_score_draws.csv"),
    )
    parser.add_argument("--bootstrap", type=int, default=500)
    parser.add_argument("--output", type=Path, default=Path("results/decision/materiality_v7"))
    args = parser.parse_args()
    started = time.perf_counter()
    matrix = pd.read_csv(args.matrix, index_col=0)
    subjects = {str(item): str(item).split("::", 1)[0] for item in matrix.columns}
    if args.score_draws.is_file():
        score_draws = pd.read_csv(args.score_draws)
    else:
        score_draws = nested_subject_item_bootstrap(
            matrix, subjects, n_bootstrap=args.bootstrap, seed=2027
        )
    decisions = selective_ranking(score_draws, materiality_threshold=0.01)
    rules = compare_selection_rules(score_draws, regret_bound=0.01)
    subject_scores = subject_accuracy_matrix(matrix, subjects)
    subject_fragility = subject_weight_fragility(subject_scores)
    item_fragility = item_removal_fragility(matrix, difficulty=matrix.mean(axis=0))
    graph = pairwise_confidence_graph(decisions)
    args.output.mkdir(parents=True, exist_ok=True)
    decisions.to_csv(args.output / "selective_pairwise_ranking.csv", index=False)
    rules.to_csv(args.output / "selection_rule_regret.csv", index=False)
    (args.output / "pairwise_confidence_graph.json").write_text(
        json.dumps(graph, indent=2, sort_keys=True), encoding="utf-8"
    )
    summary = {
        "status": "DECISION_MATERIALITY_READY",
        "pairwise_decisions": decisions["decision"].value_counts().to_dict(),
        "subject_weight_fragility": subject_fragility,
        "item_removal_fragility": item_fragility,
        "runtime_seconds": time.perf_counter() - started,
        "claim_boundary": (
            "Decision fragility is conditional on the fixed historical panel and registered "
            "materiality threshold; it is not a globally optimal deployment policy."
        ),
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"{summary['status']}: {summary['runtime_seconds']:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
