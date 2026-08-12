from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    summaries = {
        "diagnostics": _json(root / "results/v7/diagnostics/summary.json"),
        "study_h": _json(root / "results/v7/study_h/summary.json"),
        "synthetic": _json(root / "results/v7/synthetic/confirmatory/summary.json"),
        "influence": _json(root / "results/v7/influence/mmlu_v7/summary.json"),
        "transport": _json(root / "results/v7/transport/summary.json"),
    }
    rows = [
        {
            "claim_id": "V7-C01",
            "claim": "The claim-licensing software implements the predeclared multidimensional gates.",
            "status": "METHOD_READY",
            "evidence": "contract and failure-state tests",
            "scope": "software/method contract",
            "blocked_by": "real-data validity evidence for substantive claims",
        },
        {
            "claim_id": "V7-C02",
            "claim": "Historical MMLU rankings vary across subjects under the declared Study H protocols.",
            "status": "SUPPORTED_WITH_LIMITATIONS",
            "evidence": f"Kendall W={summaries['study_h']['kendalls_w']:.6f}",
            "scope": "39 imported checkpoints, 57 MMLU subjects",
            "blocked_by": "controlled exact-model replication",
        },
        {
            "claim_id": "V7-C03",
            "claim": "Specific MMLU items are FDR-controlled negative-discrimination flags.",
            "status": "NOT_SUPPORTED",
            "evidence": f"stable flags={summaries['diagnostics']['stable_FDR_flags']}",
            "scope": "historical MMLU panel and permutation null",
            "blocked_by": "no discoveries; external labels unavailable",
        },
        {
            "claim_id": "V7-C04",
            "claim": "The frozen diagnostic readout detects the preregistered synthetic flaw grid.",
            "status": "FAILED_FROZEN_ACCEPTANCE_GATES",
            "evidence": (
                f"median AUPRC={summaries['synthetic']['median_AUPRC']:.6f}; "
                f"median FDR={summaries['synthetic']['median_FDR']:.6f}"
            ),
            "scope": "frozen synthetic generator/readout only",
            "blocked_by": "all three preregistered success criteria failed",
        },
        {
            "claim_id": "V7-C05",
            "claim": "Influential historical MMLU items change the benchmark winner.",
            "status": "NOT_OBSERVED",
            "evidence": f"winner-changing items={summaries['influence']['winner_changing_items']}",
            "scope": "historical MMLU matrix",
            "blocked_by": "no winner-changing deletion observed",
        },
        {
            "claim_id": "V7-C06",
            "claim": "Diagnostics transport across MMLU, GSM8K, and BBH.",
            "status": "BLOCKED",
            "evidence": summaries["transport"]["reason"],
            "scope": "none before controlled Study C",
            "blocked_by": "S1-S3 GPU outputs",
        },
        {
            "claim_id": "V7-C07",
            "claim": "Human reviewers confirm diagnostic precision or enrichment.",
            "status": "BLOCKED",
            "evidence": "protocol and power plan only; no labels",
            "scope": "none",
            "blocked_by": "H0/H1 annotation execution",
        },
        {
            "claim_id": "V7-C08",
            "claim": "A repair policy improves held-out decisions.",
            "status": "BLOCKED",
            "evidence": "cross-fit validation contract only",
            "scope": "none",
            "blocked_by": "held-out labels and controlled panels",
        },
    ]
    output = root / "results/v7/evidence"
    output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output / "claim_evidence_ledger_v7.csv", index=False)
    print(f"Wrote {len(rows)} evidence-ledger entries.")
    return 0


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
