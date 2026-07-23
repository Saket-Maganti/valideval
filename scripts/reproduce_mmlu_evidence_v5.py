from __future__ import annotations

import argparse
import json

from valideval.evidence.reproduction import reproduce_helm_mmlu_panel


def main() -> int:
    parser = argparse.ArgumentParser(description="Reproduce the public HELM-derived MMLU panel.")
    parser.add_argument(
        "--primary",
        default="data/external/mmlu/prediction_details_wide.jsonl",
    )
    parser.add_argument("--matrix", default="cache/mmlu/wide/matrix.csv")
    parser.add_argument("--irt-proxy", default="results/mmlu/irt_proxy/item_parameters.csv")
    parser.add_argument("--output", default="results/evidence/mmlu_reproduction_v5")
    args = parser.parse_args()
    payload = reproduce_helm_mmlu_panel(
        args.primary,
        args.matrix,
        args.output,
        irt_proxy_path=args.irt_proxy,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["evidence_status"] == "REPRODUCED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
