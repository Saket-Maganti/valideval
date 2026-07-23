from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from valideval.forensics.provenance import stable_hash
from valideval.release.environment import capture_environment
from valideval.release.paper_assets import generate_paper_assets
from valideval.schemas import utc_now

EXPECTED_RESULT_FILES = [
    "validity_card.json",
    "validity_card.md",
    "validity_certificate.json",
    "validity_certificate.md",
    "item_forensics.csv",
    "repair_report.md",
    "repair_diff.json",
    "ranking_views.json",
    "ranking_flips.json",
    "ranking_significance.json",
]


def build_reproducibility_bundle(
    *,
    benchmark: str,
    panel: str,
    output_dir: str | Path = "bundles",
    results_root: str | Path = "results",
    reportcards_root: str | Path = "reportcards",
    configs: list[str | Path] | None = None,
    seed: int = 0,
) -> dict[str, Any]:
    root = Path(output_dir) / f"{benchmark}_{panel}_bundle"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    result_dir = Path(results_root) / benchmark / panel
    copied: list[str] = []
    missing: list[str] = []
    for name in EXPECTED_RESULT_FILES:
        _copy_if_exists(result_dir / name, root / "results" / name, copied, missing)
    for path in (
        sorted(result_dir.glob("*.json"))
        + sorted(result_dir.glob("*.csv"))
        + sorted(result_dir.glob("*.md"))
    ):
        _copy_if_exists(path, root / "results" / path.name, copied, missing=None)
    _copy_if_exists(
        Path(results_root) / benchmark / "manifest.json",
        root / "results" / "manifest.json",
        copied,
        missing,
    )
    report_base = f"{benchmark}_{panel}"
    _copy_if_exists(
        Path(reportcards_root) / f"{report_base}.md",
        root / "reportcards" / f"{report_base}.md",
        copied,
        missing,
    )
    _copy_if_exists(
        Path(reportcards_root) / f"{report_base}.manifest.json",
        root / "reportcards" / f"{report_base}.manifest.json",
        copied,
        missing=None,
    )
    for config in configs or ["configs/default.yaml"]:
        _copy_if_exists(Path(config), root / "configs" / Path(config).name, copied, missing)
    paper_assets = generate_paper_assets(
        benchmark=benchmark,
        panel=panel,
        results_root=results_root,
        paper_dir=root / "paper_assets",
    )
    for path in [
        *paper_assets["figures"].values(),
        *paper_assets["tables"].values(),
        paper_assets["assets_manifest"],
    ]:
        copied.append(str(Path(path).relative_to(root)))
    env = capture_environment(
        command=f"python -m valideval bundle --benchmark {benchmark} --panel {panel}",
        config_paths=configs or ["configs/default.yaml"],
        seed=seed,
    )
    environment_path = root / "environment.json"
    environment_path.write_text(json.dumps(env, indent=2, sort_keys=True), encoding="utf-8")
    copied.append("environment.json")
    commands_path = root / "reproduction_commands.txt"
    commands_path.write_text(
        "\n".join(
            [
                f"python3 -m valideval matrices --benchmark {benchmark} --panel {panel}",
                f"python3 -m valideval audit --benchmark {benchmark} --panel {panel} --diagnostics all-core",
                f"python3 -m valideval report --benchmark {benchmark} --panel {panel}",
                f"python3 -m valideval bundle --benchmark {benchmark} --panel {panel}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    copied.append("reproduction_commands.txt")
    readme_path = root / "README.md"
    readme_path.write_text(_bundle_readme(benchmark, panel, missing), encoding="utf-8")
    copied.append("README.md")
    manifest = {
        "schema_version": "0.1",
        "created_at": utc_now(),
        "benchmark": benchmark,
        "panel": panel,
        "files": _file_hashes(root, copied),
        "missing_expected_artifacts": sorted(set(missing)),
        "reproduction_commands": commands_path.read_text(encoding="utf-8").splitlines(),
        "limitations": [
            "The bundle records available local artifacts and hashes; missing artifacts are disclosed rather than synthesized."
        ],
    }
    manifest_path = root / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "bundle_dir": str(root),
        "bundle_manifest": str(manifest_path),
        "environment_json": str(environment_path),
        "missing_expected_artifacts": sorted(set(missing)),
        "file_count": len(manifest["files"]),
    }


def verify_bundle(bundle_path: str | Path) -> dict[str, Any]:
    root = Path(bundle_path)
    manifest_path = root / "bundle_manifest.json"
    errors: list[str] = []
    warnings: list[str] = []
    if not manifest_path.exists():
        return {
            "bundle_dir": str(root),
            "valid": False,
            "errors": ["Missing bundle_manifest.json"],
            "warnings": [],
        }
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for relative, expected_hash in manifest.get("files", {}).items():
        path = root / relative
        if not path.exists():
            errors.append(f"Missing bundled file: {relative}")
            continue
        actual = _file_hash(path)
        if actual != expected_hash:
            errors.append(f"Hash mismatch for {relative}")
    for required in ["README.md", "environment.json", "reproduction_commands.txt"]:
        if not (root / required).exists():
            errors.append(f"Missing required bundle file: {required}")
    if manifest.get("missing_expected_artifacts"):
        warnings.append(
            "Bundle disclosed missing expected artifacts: "
            + ", ".join(manifest["missing_expected_artifacts"])
        )
    commands = root / "reproduction_commands.txt"
    if commands.exists() and "python" not in commands.read_text(encoding="utf-8"):
        errors.append("Reproduction commands file does not contain runnable python commands.")
    return {
        "bundle_dir": str(root),
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "checked_files": len(manifest.get("files", {})),
    }


def _copy_if_exists(
    source: Path,
    destination: Path,
    copied: list[str],
    missing: list[str] | None,
) -> None:
    if not source.exists():
        if missing is not None:
            missing.append(str(source))
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != destination.resolve():
        shutil.copy2(source, destination)
    relative_root = destination.parents[1] if len(destination.parents) > 1 else destination.parent
    try:
        copied.append(str(destination.relative_to(relative_root)))
    except ValueError:
        copied.append(str(destination))


def _file_hashes(root: Path, relative_paths: list[str]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative in sorted(set(relative_paths)):
        path = root / relative
        if path.exists() and path.is_file():
            hashes[relative] = _file_hash(path)
    return hashes


def _file_hash(path: Path) -> str:
    return stable_hash(path.read_bytes().hex())


def _bundle_readme(benchmark: str, panel: str, missing: list[str]) -> str:
    missing_block = "\n".join(f"- {item}" for item in sorted(set(missing))) or "- None."
    return "\n".join(
        [
            f"# ValidEval Reproducibility Bundle: {benchmark}/{panel}",
            "",
            "This bundle contains local audit artifacts, hashes, environment metadata, and reproduction commands.",
            "",
            "## Interpretation",
            "",
            "Artifacts are evidence under the recorded protocol. They are not a global proof of benchmark validity or invalidity.",
            "",
            "## Missing Expected Artifacts",
            "",
            missing_block,
            "",
            "## Verify",
            "",
            "```bash",
            "python3 -m valideval verify-bundle .",
            "```",
            "",
        ]
    )
