from __future__ import annotations

import argparse
import json
from pathlib import Path

from valideval.release.v5 import build_deterministic_zip, plan_release, write_release_audit

PROFILES = {
    "source": (
        "configs/release/source_release_v5.txt",
        "dist/valideval_v5_source.zip",
        "reports/v5/VALID_EVAL_V5_SOURCE_RELEASE_AUDIT.md",
    ),
    "evidence": (
        "configs/release/evidence_release_v5.txt",
        "dist/valideval_v5_evidence.zip",
        "reports/v5/VALID_EVAL_V5_EVIDENCE_RELEASE_AUDIT.md",
    ),
    "reviewer": (
        "configs/release/reviewer_packet_v5.txt",
        "dist/valideval_v5_reviewer_packet.zip",
        "reports/v5/VALID_EVAL_V5_REVIEWER_PACKET_AUDIT.md",
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan or build an allowlisted V5 release.")
    parser.add_argument("--profile", choices=sorted(PROFILES), default="source")
    parser.add_argument("--root", default=".")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    allowlist, default_output, report = PROFILES[args.profile]
    plan = plan_release(args.root, allowlist, excluded_paths={report})
    write_release_audit(plan, report)
    payload: dict[str, object] = {"plan": plan, "build": None}
    if args.build:
        payload["build"] = build_deterministic_zip(
            args.root,
            plan,
            Path(args.output or default_output),
        )
    print(
        json.dumps(
            {
                "profile": args.profile,
                "status": plan["status"],
                "included_count": plan["included_count"],
                "excluded_count": plan["excluded_count"],
                "build": payload["build"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
