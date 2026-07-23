#!/usr/bin/env python3
"""Build or preflight a V5 blinded human-review packet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from valideval.human.protocol_v5 import build_blinded_human_packet, load_human_queue

DEFAULT_CONFIG = Path("configs/human/human_validation_v5.yaml")


def _config(path: Path) -> dict[str, object]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("human protocol config must be a mapping")
    if value.get("claim_state") != "RESULT_REQUIRED":
        raise ValueError("human protocol must remain RESULT_REQUIRED before labels are collected")
    return value


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, help="Candidate queue in CSV, JSON, or JSONL.")
    parser.add_argument(
        "--controls",
        type=Path,
        help="Required positive and negative control rows in CSV, JSON, or JSONL.",
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--packet-dir", type=Path, default=Path("results/human_v5/public_packet"))
    parser.add_argument("--audit-dir", type=Path, default=Path("results/human_v5_private"))
    parser.add_argument("--sample-size", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--minimum-annotators", type=int)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the protocol/configuration without reading a queue or writing a packet.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = _config(args.config)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "HUMAN_PROTOCOL_READY",
                    "mode": "dry-run",
                    "config": str(args.config),
                    "packet_written": False,
                    "labels_created": False,
                    "claim_state": "RESULT_REQUIRED",
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.candidates is None:
        raise SystemExit("--candidates is required unless --dry-run is used")
    if args.controls is None:
        raise SystemExit("--controls is required for a real packet build")
    sampling = config.get("sampling") if isinstance(config.get("sampling"), dict) else {}
    pilot = config.get("pilot") if isinstance(config.get("pilot"), dict) else {}
    result = build_blinded_human_packet(
        load_human_queue(args.candidates),
        control_rows=load_human_queue(args.controls),
        packet_dir=args.packet_dir,
        audit_dir=args.audit_dir,
        sample_size=args.sample_size,
        seed=args.seed
        if args.seed is not None
        else int(sampling.get("randomization_seed", 20260715)),
        minimum_annotators=(
            args.minimum_annotators
            if args.minimum_annotators is not None
            else int(pilot.get("minimum_annotators_per_task", 2))
        ),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
