from __future__ import annotations

import argparse
import json

from valideval.release.pre_gpu_bundle_v7_2_1 import build_pre_gpu_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the deterministic V7.2.1 pre-GPU bundle.")
    parser.add_argument("--repository-root", default=".")
    parser.add_argument("--output", default="dist/valideval-v7.2.1-pre-gpu-cpu-maxout.zip")
    args = parser.parse_args()
    result = build_pre_gpu_bundle(args.repository_root, output=args.output)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
