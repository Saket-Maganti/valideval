from __future__ import annotations

import json
from pathlib import Path

from valideval.cli import main
from valideval.diagnostics.irt import IRTDiagnostic
from valideval.validation.flaw_generators import LABELS
from valideval.validation.materiality import classify_materiality, redundancy_materiality
from valideval.validation.multiplicity import benjamini_hochberg, bonferroni
from valideval.validation.synthetic_benchmark import (
    IRT_VALIDATION_MODEL_IDS,
    MODEL_ABILITIES,
    build_controlled_matrices,
    generate_synthetic_benchmark,
)
from valideval.validation.validation_report import write_summary_report
from valideval.validation.validation_runner import run_single_validation


def test_synthetic_generation_is_deterministic():
    left = generate_synthetic_benchmark(
        flaw_type="shortcut_signal",
        flaw_strength=0.5,
        seed=7,
        n_items=12,
    )
    right = generate_synthetic_benchmark(
        flaw_type="shortcut_signal",
        flaw_strength=0.5,
        seed=7,
        n_items=12,
    )

    assert [item.to_json_dict() for item in left.load_items()] == [
        item.to_json_dict() for item in right.load_items()
    ]


def test_flaw_strength_changes_intended_signal():
    clean = generate_synthetic_benchmark(
        flaw_type="label_imbalance",
        flaw_strength=0.0,
        seed=0,
        n_items=40,
    )
    severe = generate_synthetic_benchmark(
        flaw_type="label_imbalance",
        flaw_strength=1.0,
        seed=0,
        n_items=40,
    )

    clean_b = sum(_primary_answer(item) == "B" for item in clean.load_items())
    severe_b = sum(_primary_answer(item) == "B" for item in severe.load_items())

    assert clean_b == 10
    assert severe_b == 40


def test_shortcut_validation_reports_auc_and_clean_fpr(tmp_path: Path):
    result = run_single_validation(
        "shortcut",
        "shortcut_signal",
        strength_grid=[0.0, 1.0],
        seeds=[0],
        n_items=24,
        output_dir=tmp_path,
    )

    assert result["metrics"]["auc"] >= 0.85
    assert result["metrics"]["false_positive_rate"] <= 0.10
    assert (tmp_path / "shortcut_shortcut_signal.md").exists()


def test_answer_artifact_validation_recovers_length_artifact(tmp_path: Path):
    result = run_single_validation(
        "answer_distribution",
        "answer_length_artifact",
        strength_grid=[0.0, 1.0],
        seeds=[0],
        n_items=24,
        output_dir=tmp_path,
    )

    assert result["metrics"]["auc"] == 1.0
    assert result["credibility_status"] == "credible_under_synthetic_harness"


def test_redundancy_validation_recovers_duplicate_clusters(tmp_path: Path):
    result = run_single_validation(
        "redundancy",
        "redundancy",
        strength_grid=[0.0, 1.0],
        seeds=[0],
        n_items=24,
        output_dir=tmp_path,
    )

    assert result["metrics"]["auc"] >= 0.90
    assert result["materiality"]["status"] == "practically material"


def test_irt_warns_when_panel_is_too_small(tmp_path: Path):
    benchmark = generate_synthetic_benchmark(
        flaw_type="low_discrimination",
        flaw_strength=0.5,
        seed=0,
        n_items=16,
    )
    matrices = build_controlled_matrices(
        benchmark,
        variants=["full"],
        cache_root=tmp_path / "cache",
        model_ids=["clean_reasoner", "random_model"],
    )

    result = IRTDiagnostic().run(benchmark, matrices, config={"min_models_warn": 5})

    assert any("fewer than 5 models" in warning for warning in result.warnings)


def test_negative_discrimination_generator_has_anti_ability_ground_truth(tmp_path: Path):
    benchmark = generate_synthetic_benchmark(
        flaw_type="negative_discrimination",
        flaw_strength=1.0,
        seed=3,
        n_items=80,
    )
    matrices = build_controlled_matrices(
        benchmark,
        variants=["full"],
        cache_root=tmp_path / "cache",
        model_ids=IRT_VALIDATION_MODEL_IDS,
    )
    frame = matrices["full"].to_dataframe()
    flawed_ids = [item.item_id for item in benchmark.load_items() if item.metadata.get("is_flawed")]
    clean_ids = [
        item.item_id for item in benchmark.load_items() if not item.metadata.get("is_flawed")
    ]
    ordered_models = sorted(IRT_VALIDATION_MODEL_IDS, key=lambda model: MODEL_ABILITIES[model])
    low_models = ordered_models[:4]
    high_models = ordered_models[-4:]

    assert flawed_ids
    assert clean_ids
    assert frame.loc[low_models, flawed_ids].mean().mean() > 0.80
    assert frame.loc[high_models, flawed_ids].mean().mean() < 0.20
    assert (
        frame.loc[high_models, clean_ids].mean().mean()
        > frame.loc[low_models, clean_ids].mean().mean()
    )


def test_negative_discrimination_validation_recovers_known_items(tmp_path: Path):
    result = run_single_validation(
        "irt",
        "negative_discrimination",
        strength_grid=[0.0, 1.0],
        seeds=[0],
        n_items=48,
        output_dir=tmp_path,
    )

    assert result["metrics"]["auc"] >= 0.85
    assert result["credibility_status"] == "credible_under_synthetic_harness"


def test_reliability_validation_detects_format_fragility(tmp_path: Path):
    result = run_single_validation(
        "reliability",
        "prompt_format_fragility",
        strength_grid=[0.0, 1.0],
        seeds=[0],
        n_items=24,
        output_dir=tmp_path,
    )

    assert result["metrics"]["auc"] >= 0.95
    assert result["credibility_status"] == "credible_under_synthetic_harness"


def test_extraction_validation_detects_ambiguous_formats(tmp_path: Path):
    result = run_single_validation(
        "extraction_robustness",
        "extraction_ambiguity",
        strength_grid=[0.0, 1.0],
        seeds=[0],
        n_items=24,
        output_dir=tmp_path,
    )

    assert result["metrics"]["auc"] == 1.0
    assert result["multiplicity"]["corrected_item_flags"]


def test_multiplicity_and_materiality_helpers():
    p_values = [0.001, 0.01, 0.2, 0.8]
    bh = benjamini_hochberg(p_values)
    bonf = bonferroni(p_values)

    assert bh[0] <= bonf[0]
    assert bh[1] <= bonf[1]
    assert classify_materiality(diagnostic="shortcut", effect_size=0.8) == ("practically material")
    redundancy = redundancy_materiality(raw_item_count=100, effective_item_count=70)
    assert redundancy["status"] == "practically material"


def test_validation_report_and_cli_smoke(tmp_path: Path):
    result = run_single_validation(
        "saturation",
        "too_easy_saturation",
        strength_grid=[0.0, 1.0],
        seeds=[0],
        n_items=24,
        output_dir=tmp_path,
    )
    paths = write_summary_report([result], tmp_path)

    assert Path(paths["json"]).exists()
    assert Path(paths["markdown"]).exists()
    assert json.loads(Path(paths["json"]).read_text(encoding="utf-8"))["n_experiments"] == 1
    assert (
        main(
            [
                "validate-diagnostics",
                "--diagnostic",
                "shortcut",
                "--flaw",
                "shortcut_signal",
                "--output-dir",
                str(tmp_path / "cli"),
                "--n-items",
                "16",
                "--strength-grid",
                "0",
                "1",
                "--seeds",
                "0",
            ]
        )
        == 0
    )
    assert main(["validation-summary", "--report-dir", str(tmp_path / "cli")]) == 0


def _primary_answer(item) -> str:
    answer = item.answer[0] if isinstance(item.answer, list) else item.answer
    answer = str(answer).upper()
    assert answer in LABELS
    return answer
