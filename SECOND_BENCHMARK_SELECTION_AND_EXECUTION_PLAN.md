# Second Benchmark Selection and Execution Plan

## 1. Executive Summary

No second-benchmark evidence was produced locally. GSM8K is the recommended next second-benchmark candidate because it has deterministic scoring and a clear construct, but the repository currently contains only scaffold/preflight configs, not a wide public-artifact panel. The execution path therefore routes through the Kaggle notebook package.

## 2. Candidate Comparison

| Candidate | Feasibility | Strength | Blocker |
|---|---|---|---|
| GPQA Diamond | local data exists | hard science QA construct | no validated wide model panel in this run |
| MMLU-Pro | plausible | harder MMLU-family stress test | no local artifact path present |
| TruthfulQA | scaffold exists | truthfulness construct | deterministic scoring/panel not present |
| GSM8K | scaffold exists | deterministic math reasoning | no local panel outputs present |
| BBH | config exists | broad reasoning | no local panel outputs present |
| ARC/HellaSwag | feasible in principle | common public tasks | no configs/panel selected here |

## 3. Recommended Benchmark

GSM8K is recommended as the next execution target because it has deterministic exact-match scoring and can be run with open local/Kaggle models.

## 4. Why Not Others

GPQA remains attractive but needs a validated wide panel. TruthfulQA requires careful deterministic scoring choices. MMLU-Pro/BBH/ARC/HellaSwag need additional import configs and panel outputs.

## 5. Required Panel

- At least 30 models for parity with the active MMLU panel-size gate, or an explicitly caveated pilot panel.
- Per-item predictions with deterministic `correct` values.
- No paid API dependency.

## 6. CPU Path

The local CPU path is scaffold-only for this run:

- `results/gsm8k/preflight.json`: dry-run ready
- `results/truthfulqa/preflight.json`: dry-run ready

No downloads, inference, or matrix creation were run.

## 7. Kaggle GPU Path If Needed

Use the Prompt 09 package:

- `kaggle/valideval_lm_eval_panel_runner.ipynb`
- `kaggle/panel_models_small.yaml`
- `kaggle/panel_tasks.yaml`
- `kaggle/IMPORT_KAGGLE_OUTPUTS.md`

## 8. Diagnostics To Run

After a second-benchmark matrix exists:

- panel-validity
- accuracy ranking
- subject/task subgroup instability where applicable
- proxy IRT/item diagnostics if panel shape supports them
- random and stratified resampling baselines

## 9. Baselines

Use random item bootstrap and task/subject-stratified bootstrap. Do not use naive difficulty as a model-ranking baseline.

## 10. Expected Paper Value

A successful second-benchmark panel would test whether the MMLU subject-instability finding generalizes beyond MMLU.

## 11. Risks

- Kaggle model availability and runtime.
- Scoring consistency for non-exact-match tasks.
- Small open models may produce limited variance or low absolute accuracy.

## 12. Final Decision

Recommended path: GSM8K via Kaggle open-model panel package.

Evidence state: `RESULT_REQUIRED`.
