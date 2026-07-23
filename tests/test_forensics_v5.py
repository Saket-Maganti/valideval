from pathlib import Path

from valideval.release.forensics_v5 import classify_artifact


def test_v5_artifact_taxonomy_is_fail_closed() -> None:
    assert classify_artifact(Path("src/valideval/cli.py")) == "SOURCE"
    assert classify_artifact(Path("tests/test_cli.py")) == "TEST"
    assert classify_artifact(Path("data/external/mmlu/raw.jsonl")) == "RAW_INPUT"
    assert classify_artifact(Path("results/mmlu/result.json")) == "DERIVED_EVIDENCE"
    assert classify_artifact(Path("cache/mmlu/matrix.csv")) == "NORMALIZED_INPUT"
    assert classify_artifact(Path("unknown.bin")) == "UNKNOWN"
