from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd

from valideval.diagnostics.dependency import audit_diagnostic_dependencies
from valideval.diagnostics.inference import infer_item_diagnostics


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V7 inferential item diagnostics.")
    parser.add_argument("--matrix", type=Path, default=Path("cache/mmlu/wide/matrix.csv"))
    parser.add_argument(
        "--families",
        type=Path,
        default=Path("configs/models/study_h_family_map_v5.csv"),
    )
    parser.add_argument("--bootstrap", type=int, default=500)
    parser.add_argument("--permutations", type=int, default=500)
    parser.add_argument("--output", type=Path, default=Path("results/v7/diagnostics"))
    args = parser.parse_args()
    started = time.perf_counter()
    matrix = pd.read_csv(args.matrix, index_col=0)
    families_frame = pd.read_csv(args.families)
    families = dict(zip(families_frame.model_id, families_frame.model_family, strict=True))
    subjects = {str(item): str(item).split("::", 1)[0] for item in matrix.columns}
    result = infer_item_diagnostics(
        matrix,
        subjects,
        model_families=families,
        n_bootstrap=args.bootstrap,
        n_permutations=args.permutations,
    )
    dependency = audit_diagnostic_dependencies(
        {
            "negative_discrimination": {
                "source_data": ["binary_response_matrix"],
                "formula": "negative leave-one-item response/ability correlation",
                "depends_on_accuracy": True,
            },
            "extreme_difficulty": {
                "source_data": ["binary_response_matrix"],
                "formula": "absolute distance from preregistered difficulty center",
                "depends_on_accuracy": True,
            },
            "legacy_accuracy_weight": {
                "source_data": ["binary_response_matrix"],
                "formula": "absolute distance from preregistered difficulty center",
                "depends_on_accuracy": True,
            },
            "external_issue_match": {
                "source_data": ["external_labels"],
                "formula": "held-out criterion match",
                "depends_on_external_labels": True,
            },
        }
    )
    args.output.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output / "item_inferential_diagnostics.csv", index=False)
    graph_path = args.output / "diagnostic_dependency_graph.json"
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_text(json.dumps(dependency, indent=2, sort_keys=True), encoding="utf-8")
    summary = {
        "status": "INFERENTIAL_DIAGNOSTICS_READY",
        "models": matrix.shape[0],
        "items": matrix.shape[1],
        "families": len(set(families.values())),
        "bootstrap": args.bootstrap,
        "permutations": args.permutations,
        "BH_flags": int((result["FDR_q_value"] <= 0.05).sum()),
        "BY_flags": int((result["BY_q_value"] <= 0.05).sum()),
        "stable_FDR_flags": int((result["claim_status"] == "STABLE_FDR_CONTROLLED_FLAG").sum()),
        "runtime_seconds": time.perf_counter() - started,
        "claim_boundary": (
            "Flags indicate evidence consistent with anti-discrimination under this imported "
            "panel and null; causes require independent validation."
        ),
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"{summary['status']}: {summary['runtime_seconds']:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
