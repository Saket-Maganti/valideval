#!/usr/bin/env python3
"""Validate and privately import V5 blinded human annotations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from valideval.human.importer_v5 import HumanLabelImportError, import_human_labels_v5


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--blinded-tasks", type=Path, required=True)
    parser.add_argument("--private-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--minimum-annotators", type=int)
    parser.add_argument("--minimum-rationale-characters", type=int, default=0)
    parser.add_argument("--minimum-control-match-rate", type=float, default=0.8)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = import_human_labels_v5(
            args.annotations,
            blinded_tasks_path=args.blinded_tasks,
            private_manifest_path=args.private_manifest,
            output_dir=args.output_dir,
            minimum_annotators=args.minimum_annotators,
            minimum_rationale_characters=args.minimum_rationale_characters,
            minimum_control_match_rate=args.minimum_control_match_rate,
        )
    except HumanLabelImportError as exc:
        print(json.dumps({"status": "IMPORT_BLOCKED", "error": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
