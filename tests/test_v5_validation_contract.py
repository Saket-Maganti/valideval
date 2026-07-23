from pathlib import Path


def test_machine_state_writer_names_every_required_gate() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "scripts/write_v5_machine_state.py").read_text(encoding="utf-8")
    for key in [
        "package_install",
        "tests",
        "lint",
        "format",
        "type_check",
        "package_build",
        "notebook_validation",
        "paper_build",
        "release_build",
        "primary_input_hashes",
        "reproduced_mmlu_metrics",
        "claim_status_counts",
        "leakage_gate",
        "model_identity_gate",
        "panel_power_gate",
        "notebook_gate",
        "importer_gate",
        "cross_benchmark_gate",
        "human_protocol_gate",
        "synthetic_protocol_gate",
        "paper_scaffold_gate",
        "remaining_blockers",
        "exact_next_commands",
    ]:
        assert f'"{key}"' in text
