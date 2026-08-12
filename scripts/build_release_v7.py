from __future__ import annotations

import argparse
import json
from pathlib import Path

from valideval.release.v5 import build_deterministic_zip, plan_release, write_release_audit

PROFILES = {
    "source": "configs/release/source_release_v7.txt",
    "cpu": "configs/release/cpu_reproduction_release_v7.txt",
    "evidence": "configs/release/derived_evidence_release_v7.txt",
    "reviewer": "configs/release/anonymous_reviewer_release_v7.txt",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an allowlisted deterministic V7 release.")
    parser.add_argument("--profile", choices=sorted(PROFILES), required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    audit = Path(f"results/v7/release/{args.profile}_release_audit.md")
    plan = plan_release(args.root, PROFILES[args.profile], excluded_paths={audit.as_posix()})
    write_release_audit(plan, audit)
    built = None
    if args.build:
        built = build_deterministic_zip(
            args.root,
            plan,
            Path(f"bundles/v7/valideval_v7_{args.profile}.zip"),
        )
    print(
        json.dumps(
            {
                "profile": args.profile,
                "status": plan["status"],
                "included_count": plan["included_count"],
                "excluded_count": plan["excluded_count"],
                "build": built,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
