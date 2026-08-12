from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path

from valideval.execution.manifest import sha256_file
from valideval.execution.notebook_v7_2 import run_notebook_stage_v7_2
from valideval.execution.packaging import validate_zip_archive
from valideval.importers.s1_v7_2 import accept_s1_v7_2


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the canonical offline V7.2 S1 transaction.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/v7_2/s1_mock_integration/summary.json"),
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="valideval-s1-v7-2-integration-") as temporary:
        work = Path(temporary)
        run_results = [
            run_notebook_stage_v7_2(
                benchmark,
                mode="fixture",
                output_root=work / "outputs",
                repository_root=root,
            )
            for benchmark in ("mmlu", "gsm8k", "bbh")
        ]
        packages = work / "outputs" / "packages"
        package_records = []
        for result in run_results:
            validation = validate_zip_archive(result["zip_path"])
            package_records.append(
                {
                    "benchmark_id": result["benchmark_id"],
                    "status": result["status"],
                    "evidence_class": result["evidence_class"],
                    "row_count": result["row_count"],
                    "zip_name": Path(result["zip_path"]).name,
                    "zip_sha256": sha256_file(result["zip_path"]),
                    "members": validation["members"],
                    "config_hash": result["config_hash"],
                }
            )
        import_root = work / "accepted"
        acceptance = accept_s1_v7_2(
            packages,
            repository_root=root,
            output_root=import_root,
            expected_source_commit=_head(root),
            allow_non_evidence_fixture=True,
        )
        accepted = acceptance["status"] == "S1_V7_2_ACCEPTED"
        payload = {
            "schema_version": "valideval.s1-mock-integration.v7.2",
            "status": (
                "S1_V7_2_END_TO_END_READY" if accepted else "S1_V7_2_END_TO_END_BLOCKED"
            ),
            "source_commit": _head(root),
            "fixture_only": True,
            "authorization_updated": False,
            "transaction": (
                "config -> runner -> scheduler -> canonical package -> ZIP -> V7 importer -> "
                "V7.2 acceptance"
            ),
            "packages": package_records,
            "acceptance": acceptance,
            "runtime_seconds": time.perf_counter() - started,
            "claim_boundary": (
                "This deterministic mock run proves integration readiness only. It is not an "
                "accepted real S1 and cannot support scientific claims or S2 authorization."
            ),
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"{payload['status']}: {payload['runtime_seconds']:.2f}s")
    return 0 if accepted else 2


def _head(root: Path) -> str:
    import subprocess

    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()


if __name__ == "__main__":
    raise SystemExit(main())
