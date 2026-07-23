from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

PACKAGE_FILES = [
    "kaggle/valideval_lm_eval_panel_runner.ipynb",
    "kaggle/README_KAGGLE_PANEL_RUN.md",
    "kaggle/kaggle_requirements.txt",
    "kaggle/panel_models_small.yaml",
    "kaggle/panel_models_medium.yaml",
    "kaggle/panel_tasks.yaml",
    "kaggle/IMPORT_KAGGLE_OUTPUTS.md",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_package(output: Path) -> dict[str, object]:
    missing = [path for path in PACKAGE_FILES if not Path(path).exists()]
    if missing:
        raise FileNotFoundError(f"Missing Kaggle package files: {missing}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in PACKAGE_FILES:
            archive.write(name, name)
    payload = {
        "package": str(output),
        "size_bytes": output.stat().st_size,
        "sha256": sha256(output),
        "files": PACKAGE_FILES,
        "evidence_state": "KAGGLE_NOTEBOOK_PACKAGE_ONLY_RESULT_REQUIRED",
    }
    manifest = output.with_suffix(".manifest.json")
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Package ValidEval Kaggle notebook assets.")
    parser.add_argument(
        "--output",
        default="kaggle/valideval_kaggle_panel_package.zip",
        help="Destination ZIP path.",
    )
    args = parser.parse_args()
    payload = build_package(Path(args.output))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
