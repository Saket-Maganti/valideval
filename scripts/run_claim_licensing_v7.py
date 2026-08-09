from __future__ import annotations

import argparse
import json
from pathlib import Path

from valideval.claims import ClaimEvidence, ClaimPolicy, ClaimType, license_claim
from valideval.claims.reporting import render_claim_table


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate every V7 claim-license state.")
    parser.add_argument("--output", type=Path, default=Path("results/v7/claims"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    policy = ClaimPolicy()
    examples = [
        (
            ClaimType.MODEL_A_OUTPERFORMS_MODEL_B,
            ClaimEvidence(
                confidence_lower=0.03,
                confidence_upper=0.07,
                effect_size=0.05,
                sample_size=500,
                decision_regret_upper=0.005,
                scope=("synthetic contract test",),
            ),
        ),
        (
            ClaimType.MODEL_IN_TOP_K,
            ClaimEvidence(
                simultaneous_rank_lower=1,
                simultaneous_rank_upper=3,
                requested_top_k=3,
                sample_size=500,
                decision_regret_upper=0.005,
            ),
        ),
        (
            ClaimType.ITEM_IS_SUSPICIOUS,
            ClaimEvidence(
                q_value=0.01,
                multiplicity_controlled=True,
                bootstrap_stability=0.9,
                effect_size=0.2,
                sample_size=500,
                external_validated=False,
            ),
        ),
        (
            ClaimType.DIAGNOSTIC_TRANSFERS,
            ClaimEvidence(
                confidence_lower=0.1,
                sample_size=500,
                exact_model_overlap=4,
                independent_model_families=3,
                transport_heterogeneity=0.8,
                transport_direction_consistent=False,
            ),
        ),
    ]
    results = [license_claim(claim, evidence, policy) for claim, evidence in examples]
    payload = {
        "status": "CLAIM_LICENSING_METHOD_READY",
        "policy": policy.to_dict(),
        "contract_examples_only": True,
        "results": [result.to_dict() for result in results],
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
