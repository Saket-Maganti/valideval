from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.use("Agg")

TABLE_DIR = Path("paper/tables")
FIGURE_DIR = Path("paper/figures")


def load_json(path: str) -> dict[str, Any]:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def write_table(stem: str, rows: list[dict[str, Any]]) -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    frame.to_csv(TABLE_DIR / f"{stem}.csv", index=False)
    (TABLE_DIR / f"{stem}.tex").write_text(
        frame.to_latex(index=False, escape=True), encoding="utf-8"
    )


def save_figure(stem: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / f"{stem}.png", dpi=220)
    plt.savefig(FIGURE_DIR / f"{stem}.pdf")
    plt.close()


def build_tables() -> None:
    panel = load_json("results/mmlu/panel_validity/panel_validity.json")
    irt = load_json("results/mmlu/irt_proxy/fit_summary.json")
    irt_2pl = load_json("results/mmlu/irt_2pl/fit_summary.json")
    redux_schema = load_json("results/mmlu/redux_direct_alignment/schema_report.json")
    redux_metrics = load_json("results/mmlu/redux_validation/metrics.json")
    ranking = load_json("results/mmlu/ranking_disagreement/ranking_disagreement_summary.json")

    write_table(
        "evidence_state_summary",
        [
            {
                "evidence": "active_mmlu_panel",
                "state": "SUPPORTED",
                "artifact": "results/mmlu/panel_validity/panel_validity.json",
            },
            {
                "evidence": "three_model_mmlu_files",
                "state": "HISTORICAL_PROVENANCE_ONLY",
                "artifact": "LIMITED_REAL_MMLU_PANEL_VALIDITY_REPORT.md",
            },
            {
                "evidence": "proxy_irt",
                "state": "SUPPORTED_PROXY",
                "artifact": "results/mmlu/irt_proxy/fit_summary.json",
            },
            {
                "evidence": "full_2pl",
                "state": "RESULT_REQUIRED",
                "artifact": "results/mmlu/irt_2pl/fit_summary.json",
            },
            {
                "evidence": "mmlu_redux_direct_hash",
                "state": "BLOCKED_NOT_CONFIRMED",
                "artifact": "results/mmlu/redux_direct_alignment/schema_report.json",
            },
            {
                "evidence": "mmlu_redux_structural",
                "state": "WEAK_NEGATIVE",
                "artifact": "results/mmlu/redux_validation/metrics.json",
            },
            {
                "evidence": "real_panel_ranking_disagreement",
                "state": "ARTIFACT_BACKED",
                "artifact": "results/mmlu/ranking_disagreement/ranking_disagreement_summary.json",
            },
            {
                "evidence": "decoupled_synthetic_validation",
                "state": "RESULT_REQUIRED",
                "artifact": "DECOUPLED_SYNTHETIC_EXECUTION_REPORT.md",
            },
            {
                "evidence": "second_benchmark",
                "state": "RESULT_REQUIRED",
                "artifact": "SECOND_BENCHMARK_RUN_REPORT.md",
            },
            {
                "evidence": "neurips_readiness",
                "state": "BLOCKED",
                "artifact": "FINAL_SUBMISSION_GATE_AND_VENUE_STRATEGY.md",
            },
        ],
    )
    write_table(
        "panel_shapes",
        [
            {
                "panel": "active_helm_mmlu_wide",
                "models": panel.get("n_models", "[RESULT REQUIRED]"),
                "items": panel.get("n_items", "[RESULT REQUIRED]"),
                "missing_fraction": panel.get("missing_fraction", "[RESULT REQUIRED]"),
                "status": panel.get("status", "[RESULT REQUIRED]"),
            },
            {
                "panel": "legacy_three_model_mmlu",
                "models": 3,
                "items": "[HISTORICAL]",
                "missing_fraction": "[HISTORICAL]",
                "status": "historical_provenance_only",
            },
        ],
    )
    write_table(
        "mmlu_panel_validity",
        [
            {
                "status": panel.get("status", "[RESULT REQUIRED]"),
                "models": panel.get("n_models", "[RESULT REQUIRED]"),
                "items": panel.get("n_items", "[RESULT REQUIRED]"),
                "ability_spread": panel.get("ability_spread", "[RESULT REQUIRED]"),
                "near_chance_fraction": panel.get("near_chance_fraction", "[RESULT REQUIRED]"),
                "blockers": ",".join(panel.get("blockers", [])),
            }
        ],
    )
    item_summary = irt.get("item_parameter_summary", {})
    write_table(
        "mmlu_irt_summary",
        [
            {
                "layer": "proxy",
                "status": irt.get("status", "[RESULT REQUIRED]"),
                "negative_discrimination": item_summary.get(
                    "negative_discrimination_count", "[RESULT REQUIRED]"
                ),
                "near_zero_discrimination": item_summary.get(
                    "near_zero_discrimination_count", "[RESULT REQUIRED]"
                ),
                "extreme_difficulty": item_summary.get(
                    "extreme_difficulty_count", "[RESULT REQUIRED]"
                ),
                "full_parametric_2pl": irt.get("estimation_layers", {}).get(
                    "full_parametric_2pl", "[RESULT REQUIRED]"
                ),
            },
            {
                "layer": "2pl_proxy",
                "status": irt_2pl.get("status", "[RESULT REQUIRED]"),
                "negative_discrimination": item_summary.get(
                    "negative_discrimination_count", "[RESULT REQUIRED]"
                ),
                "near_zero_discrimination": item_summary.get(
                    "near_zero_discrimination_count", "[RESULT REQUIRED]"
                ),
                "extreme_difficulty": item_summary.get(
                    "extreme_difficulty_count", "[RESULT REQUIRED]"
                ),
                "full_parametric_2pl": irt_2pl.get("estimation_layers", {}).get(
                    "full_parametric_2pl", "[RESULT REQUIRED]"
                ),
            },
        ],
    )
    redux_diag = (redux_metrics.get("diagnostics") or {}).get("matrix_item_anomaly", {})
    write_table(
        "mmlu_redux_validation",
        [
            {
                "alignment": "direct_hash",
                "status": "BLOCKED_NOT_CONFIRMED",
                "direct_item_id_matches": redux_schema.get(
                    "direct_item_id_matches", "[RESULT REQUIRED]"
                ),
                "auroc": "[RESULT REQUIRED]",
                "auprc": "[RESULT REQUIRED]",
                "precision_at_10": "[RESULT REQUIRED]",
            },
            {
                "alignment": "structural_subject_numeric_index",
                "status": "WEAK_NEGATIVE",
                "direct_item_id_matches": 0,
                "auroc": redux_diag.get("auroc", "[RESULT REQUIRED]"),
                "auprc": redux_diag.get("auprc", "[RESULT REQUIRED]"),
                "precision_at_10": redux_diag.get("precision_at_k", "[RESULT REQUIRED]"),
            },
        ],
    )
    write_table(
        "ranking_disagreement",
        [
            {
                "analysis": "proxy_diagnostic_vs_accuracy",
                "spearman": ranking.get("rank_correlation", {}).get(
                    "spearman_accuracy_vs_diagnostic_weighted", "[RESULT REQUIRED]"
                ),
                "kendall": ranking.get("rank_correlation", {}).get(
                    "kendall_accuracy_vs_diagnostic_weighted", "[RESULT REQUIRED]"
                ),
                "max_abs_rank_delta": ranking.get(
                    "max_abs_diagnostic_rank_delta", "[RESULT REQUIRED]"
                ),
                "claim_state": "artifact_backed_proxy_only",
            },
            {
                "analysis": "subject_instability",
                "spearman": "[not applicable]",
                "kendall": "[not applicable]",
                "max_abs_rank_delta": ranking.get("max_subject_rank_range", "[RESULT REQUIRED]"),
                "claim_state": "artifact_backed_subject_sensitivity",
            },
        ],
    )
    baseline_path = Path("results/mmlu/real_panel_baselines/baseline_comparison.csv")
    if baseline_path.exists():
        baseline_path_frame = pd.read_csv(baseline_path)
        baseline_path_frame.to_csv(TABLE_DIR / "baseline_comparison.csv", index=False)
        (TABLE_DIR / "baseline_comparison.tex").write_text(
            baseline_path_frame.to_latex(index=False, escape=True), encoding="utf-8"
        )
    else:
        write_table("baseline_comparison", [{"baseline": "[RESULT REQUIRED]"}])
    write_table(
        "second_benchmark_summary",
        [
            {
                "benchmark": "gsm8k",
                "selection": "recommended_next",
                "run_status": "RESULT_REQUIRED",
                "artifact": "SECOND_BENCHMARK_RUN_REPORT.md",
            }
        ],
    )
    write_table(
        "claims_allowed_blocked",
        [
            {"claim": "active MMLU panel has 39 models", "state": "allowed"},
            {"claim": "panel-size blocker is cleared", "state": "allowed"},
            {"claim": "subject-level rank sensitivity under this panel", "state": "allowed"},
            {"claim": "MMLU error detection", "state": "blocked"},
            {"claim": "MMLU is valid or invalid", "state": "blocked"},
            {"claim": "direct/hash Redux alignment", "state": "blocked"},
            {"claim": "second-benchmark evidence", "state": "RESULT_REQUIRED"},
            {"claim": "NeurIPS-ready", "state": "blocked"},
        ],
    )


def build_figures() -> None:
    ranking_path = Path("results/mmlu/ranking_disagreement/accuracy_ranking.csv")
    if ranking_path.exists():
        ranking = pd.read_csv(ranking_path).sort_values("accuracy")
        plt.figure(figsize=(7, 5))
        plt.barh(range(len(ranking)), ranking["accuracy"], color="#2F6F73")
        plt.yticks([])
        plt.xlabel("Accuracy")
        plt.ylabel("39 models")
        plt.title("MMLU panel ability spread")
        save_figure("panel_ability_spread")

    item_path = Path("results/mmlu/irt_proxy/item_parameters.csv")
    if item_path.exists():
        items = pd.read_csv(item_path)
        plt.figure(figsize=(6, 4))
        plt.hist(items["difficulty_proxy"].dropna(), bins=50, color="#5E7C40")
        plt.xlabel("Difficulty proxy")
        plt.ylabel("Items")
        plt.title("MMLU item difficulty distribution")
        save_figure("mmlu_item_difficulty_distribution")

        plt.figure(figsize=(6, 4))
        plt.hist(items["discrimination_proxy"].dropna(), bins=50, color="#8A5A44")
        plt.xlabel("Discrimination proxy")
        plt.ylabel("Items")
        plt.title("MMLU discrimination distribution")
        save_figure("mmlu_discrimination_distribution")

    redux_metrics = load_json("results/mmlu/redux_validation/metrics.json")
    redux_diag = (redux_metrics.get("diagnostics") or {}).get("matrix_item_anomaly", {})
    plt.figure(figsize=(6, 4))
    plt.axis("off")
    plt.text(
        0.02,
        0.68,
        "MMLU-Redux direct/hash curve: RESULT REQUIRED\n"
        f"Structural AUROC: {redux_diag.get('auroc', '[RESULT REQUIRED]')}\n"
        f"Structural AUPRC: {redux_diag.get('auprc', '[RESULT REQUIRED]')}\n"
        f"Precision@10: {redux_diag.get('precision_at_k', '[RESULT REQUIRED]')}",
        fontsize=11,
        va="top",
    )
    plt.title("MMLU-Redux validation status")
    save_figure("mmlu_redux_validation_pr_curve")

    instability_path = Path("results/mmlu/ranking_disagreement/subject_instability.csv")
    if instability_path.exists():
        instability = pd.read_csv(instability_path).head(20).iloc[::-1]
        plt.figure(figsize=(7, 5))
        plt.barh(instability["model_id"], instability["subject_rank_range"], color="#6C6AA5")
        plt.xlabel("Subject rank range")
        plt.title("Top MMLU subject rank instability")
        plt.tick_params(axis="y", labelsize=6)
        save_figure("mmlu_ranking_instability")

    subject_rankings_path = Path("results/mmlu/ranking_disagreement/subject_rankings.csv")
    if subject_rankings_path.exists():
        sr = pd.read_csv(subject_rankings_path)
        pivot = sr.pivot_table(index="subject", columns="model_id", values="subject_rank")
        plt.figure(figsize=(8, 7))
        plt.imshow(pivot.to_numpy(dtype=float), aspect="auto", cmap="viridis_r")
        plt.colorbar(label="Subject rank")
        plt.xlabel("Models")
        plt.ylabel("Subjects")
        plt.xticks([])
        plt.yticks([])
        plt.title("Diagnostic disagreement heatmap: subject ranks")
        save_figure("diagnostic_disagreement_heatmap")

    rank_shift_path = Path(
        "results/mmlu/ranking_disagreement/accuracy_vs_diagnostic_rank_shift.csv"
    )
    if rank_shift_path.exists():
        shift = pd.read_csv(rank_shift_path).sort_values("abs_rank_delta", ascending=False).head(20)
        plt.figure(figsize=(7, 5))
        plt.barh(
            shift["model_id"].iloc[::-1],
            shift["rank_delta_diagnostic_minus_accuracy"].iloc[::-1],
            color="#9A6B27",
        )
        plt.xlabel("Proxy diagnostic rank delta")
        plt.title("Proxy diagnostic vs accuracy rank shifts")
        plt.tick_params(axis="y", labelsize=6)
        save_figure("mmlu_diagnostic_disagreement")

    baseline_path = Path("results/mmlu/real_panel_baselines/baseline_comparison.csv")
    if baseline_path.exists():
        baseline = pd.read_csv(baseline_path)
        baseline = baseline[baseline["iterations"] > 0]
        plt.figure(figsize=(6, 4))
        plt.bar(baseline["baseline"], baseline["p95_max_abs_rank_delta"], color="#3F7F93")
        plt.ylabel("P95 max absolute rank delta")
        plt.xticks(rotation=15, ha="right")
        plt.title("MMLU baseline comparison")
        save_figure("baseline_comparison")
        plt.figure(figsize=(6, 4))
        plt.bar(baseline["baseline"], baseline["mean_top5_overlap"], color="#3F7F93")
        plt.ylim(0, 1.05)
        plt.ylabel("Mean top-5 overlap")
        plt.xticks(rotation=15, ha="right")
        plt.title("MMLU baseline top-5 stability")
        save_figure("mmlu_baseline_comparison")

    states = [
        ("39-model MMLU", "pass"),
        ("Proxy IRT", "proxy"),
        ("Redux direct/hash", "blocked"),
        ("Decoupled synth", "RESULT_REQUIRED"),
        ("Second benchmark", "RESULT_REQUIRED"),
        ("Submission gate", "blocked"),
    ]
    colors = {
        "pass": "#4B8A5A",
        "proxy": "#6C6AA5",
        "blocked": "#9A4D4D",
        "RESULT_REQUIRED": "#B4863A",
    }
    plt.figure(figsize=(9, 2.8))
    for idx, (label, state) in enumerate(states):
        plt.barh([0], [1], left=[idx], color=colors[state])
        plt.text(
            idx + 0.5, 0, f"{label}\n{state}", ha="center", va="center", fontsize=8, color="white"
        )
    plt.xlim(0, len(states))
    plt.ylim(-0.6, 0.6)
    plt.axis("off")
    plt.title("Evidence gate flow")
    save_figure("evidence_gate_flow")


def main() -> int:
    build_tables()
    build_figures()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
