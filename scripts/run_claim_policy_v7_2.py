from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import yaml

from valideval.statistics.claim_policy_v7_2 import (
    POLICY_CONFIRMATION,
    POLICY_DEVELOPMENT,
    POLICY_VALIDATION,
    assert_split_isolation,
    build_scenario_registry,
    confirm_frozen_policy,
    evaluate_candidates,
    freeze_policy_payload,
    load_candidate_policies,
    pareto_frontier,
    policy_stability,
    select_primary_policy,
    split_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run disjoint V7.2 claim-policy calibration.")
    parser.add_argument(
        "--phase", choices=("select", "confirm", "all"), default="all"
    )
    parser.add_argument(
        "--scenarios",
        type=Path,
        default=Path("configs/statistics/claim_policy_v7_2_scenarios.yaml"),
    )
    parser.add_argument(
        "--candidates",
        type=Path,
        default=Path("configs/statistics/claim_policy_v7_2_candidates.yaml"),
    )
    parser.add_argument("--replicates", type=int, default=None)
    parser.add_argument("--output", type=Path, default=Path("results/v7_2/claim_policy"))
    args = parser.parse_args()
    started = time.perf_counter()

    registry = build_scenario_registry(
        args.scenarios, replicates_per_claim_family=args.replicates
    )
    assert_split_isolation(registry)
    args.output.mkdir(parents=True, exist_ok=True)
    registry.to_csv(args.output / "simulation_scenario_registry.csv", index=False)
    manifests = {
        split: split_manifest(registry, split)
        for split in (POLICY_DEVELOPMENT, POLICY_VALIDATION, POLICY_CONFIRMATION)
    }
    for split, manifest in manifests.items():
        (args.output / f"{split.lower()}_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    freeze_path = args.output / "claim_policy_v7_2_frozen.yaml"
    if args.phase in {"select", "all"}:
        candidates = load_candidate_policies(args.candidates)
        overall, cells = evaluate_candidates(registry, candidates)
        overall.to_csv(args.output / "candidate_policy_metrics.csv", index=False)
        cells.to_csv(args.output / "candidate_policy_metrics_by_cell.csv", index=False)
        frontier = pareto_frontier(overall, split=POLICY_VALIDATION)
        frontier.to_csv(args.output / "pareto_frontier_validation.csv", index=False)
        selected, selection = select_primary_policy(overall, candidates)
        frozen = freeze_policy_payload(
            selected,
            scenario_manifests=manifests,
            selection=selection,
        )
        freeze_path.write_text(yaml.safe_dump(frozen, sort_keys=True), encoding="utf-8")
        stability = policy_stability(registry, candidates, selected.policy_id)
        (args.output / "policy_stability.json").write_text(
            json.dumps(stability, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        summary = {
            "status": "CLAIM_POLICY_DEVELOPMENT_COMPLETE",
            "baseline": "V7_1_ULTRA_CONSERVATIVE_BASELINE",
            "baseline_false_license_rate": 0.0,
            "baseline_true_license_power": 0.0,
            "baseline_abstention_rate": 1.0,
            "selected": selection,
            "freeze_hash": frozen["freeze_hash"],
            "split_manifests": manifests,
            "stability": stability["status"],
            "confirmation_accessed": False,
            "runtime_seconds": time.perf_counter() - started,
        }
        (args.output / "development_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"{summary['status']}: {selected.policy_id} {frozen['freeze_hash']}")

    if args.phase in {"confirm", "all"}:
        if not freeze_path.is_file():
            raise FileNotFoundError(f"frozen policy missing: {freeze_path}")
        frozen = yaml.safe_load(freeze_path.read_text(encoding="utf-8"))
        cells, confirmation = confirm_frozen_policy(registry, frozen)
        cells.to_csv(args.output / "confirmation_metrics_by_cell.csv", index=False)
        confirmation["runtime_seconds"] = time.perf_counter() - started
        (args.output / "confirmation_summary.json").write_text(
            json.dumps(confirmation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(
            f"{confirmation['status']}: power={confirmation['true_license_power']:.4f} "
            f"false_license={confirmation['false_license_rate']:.4f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
