from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from valideval.claims import (
    ClaimEvidence,
    ClaimPolicy,
    ClaimType,
    InferentialUnit,
    RankIntervalType,
    license_claim,
)
from valideval.claims.reporting import render_claim_table


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate every V7 claim-license state.")
    parser.add_argument("--output", type=Path, default=Path("results/v7_1/claims"))
    args = parser.parse_args()
    started = time.perf_counter()
    args.output.mkdir(parents=True, exist_ok=True)
    policy = ClaimPolicy()
    examples = [
        (
            ClaimType.MODEL_A_OUTPERFORMS_MODEL_B,
            ClaimEvidence(
                confidence_lower=0.03,
                confidence_upper=0.07,
                effect_size=0.05,
                estimand_unit=InferentialUnit.ITEM,
                raw_n=500,
                effective_n=500,
                independence_unit=InferentialUnit.ITEM,
                dependence_structure="paired items",
                decision_regret_upper=0.005,
                scope=("synthetic contract test",),
            ),
        ),
        (
            ClaimType.MODEL_IN_TOP_K,
            ClaimEvidence(
                simultaneous_rank_lower=1,
                simultaneous_rank_upper=3,
                rank_interval_type=RankIntervalType.BOOTSTRAP_MAX_DEVIATION_SIMULTANEOUS,
                requested_top_k=3,
                estimand_unit=InferentialUnit.ITEM,
                raw_n=500,
                effective_n=500,
                independence_unit=InferentialUnit.ITEM,
                dependence_structure="joint item bootstrap",
                decision_regret_upper=0.005,
            ),
        ),
        (
            ClaimType.ITEM_IS_SUSPICIOUS,
            ClaimEvidence(
                q_value=0.01,
                multiplicity_controlled=True,
                hypothesis_family_id="ITEM_DIAGNOSTICS",
                multiplicity_scope="ALL_ITEMS",
                bootstrap_stability=0.9,
                effect_size=0.2,
                estimand_unit=InferentialUnit.MODEL_FAMILY,
                raw_n=500,
                effective_n=10,
                independence_unit=InferentialUnit.MODEL_FAMILY,
                dependence_structure="family clustered",
                external_validated=False,
            ),
        ),
        (
            ClaimType.DIAGNOSTIC_TRANSFERS,
            ClaimEvidence(
                confidence_lower=0.1,
                estimand_unit=InferentialUnit.BENCHMARK,
                raw_n=3,
                effective_n=3,
                independence_unit=InferentialUnit.BENCHMARK,
                dependence_structure="held-out benchmark folds",
                exact_model_overlap=4,
                independent_model_families=3,
                transport_heterogeneity=0.8,
                transport_direction_consistent=False,
            ),
        ),
    ]
    results = [license_claim(claim, evidence, policy) for claim, evidence in examples]
    payload = {
        "status": "CLAIM_SEMANTICS_READY",
        "policy": policy.to_dict(),
        "contract_examples_only": True,
        "results": [result.to_dict() for result in results],
        "runtime_seconds": time.perf_counter() - started,
    }
    (args.output / "claim_licensing_validation.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    (args.output / "claim_licensing_validation.md").write_text(
        "# V7 Claim-Licensing Contract Validation\n\n"
        "These deterministic cases validate gate behavior; they are not benchmark findings.\n\n"
        + render_claim_table(results),
        encoding="utf-8",
    )
    print(f"{payload['status']}: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
