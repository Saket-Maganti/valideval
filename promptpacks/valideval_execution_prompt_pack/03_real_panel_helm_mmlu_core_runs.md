# Prompt 03 — Real HELM/MMLU Panel Core Runs

Run only after the reconciliation gate confirms a ≥30-model panel is present or after the acquisition/Kaggle path creates one.

## Objective

Run the core real-panel MMLU analyses on the active HELM MMLU wide matrix.

## Inputs

Expected:

```text
cache/mmlu/wide/matrix.csv
cache/mmlu/wide/predictions.jsonl
data/external/mmlu/prediction_details_wide.jsonl
MMLU_PANEL_VALIDITY_REPORT.md
MMLU_EVIDENCE_GATE_REPORT.md
```

## Step 1 — Confirm panel shape

```bash
python3 - <<'PY'
import pandas as pd
from pathlib import Path
p = Path("cache/mmlu/wide/matrix.csv")
if not p.exists():
    raise SystemExit("BLOCKED: missing cache/mmlu/wide/matrix.csv")
df = pd.read_csv(p)
print("shape", df.shape)
print("columns", list(df.columns))
model_col = "model_id" if "model_id" in df.columns else "model"
print("models", df[model_col].nunique())
if df[model_col].nunique() < 30:
    raise SystemExit("BLOCKED: fewer than 30 models")
for col in ["item_id", "subject"]:
    if col in df.columns:
        print(col, df[col].nunique())
PY
```

## Step 2 — Run panel validity gate

Try:

```bash
python3 -m valideval panel-validity   --matrix cache/mmlu/wide/matrix.csv   --output results/mmlu/panel_validity   --strict
```

If CLI differs, inspect help and use implemented names.

## Step 3 — Run real-panel analyses

Try:

```bash
python3 -m valideval real-panel-ranking-audit   --matrix cache/mmlu/wide/matrix.csv   --predictions cache/mmlu/wide/predictions.jsonl   --output results/mmlu/real_panel_ranking_audit   --execute

python3 -m valideval diagnostic-disagreement-audit   --matrix cache/mmlu/wide/matrix.csv   --predictions cache/mmlu/wide/predictions.jsonl   --output results/mmlu/diagnostic_disagreement   --execute

python3 -m valideval subject-instability-audit   --matrix cache/mmlu/wide/matrix.csv   --predictions cache/mmlu/wide/predictions.jsonl   --output results/mmlu/subject_instability   --execute

python3 -m valideval real-panel-baselines   --matrix cache/mmlu/wide/matrix.csv   --predictions cache/mmlu/wide/predictions.jsonl   --output results/mmlu/real_panel_baselines   --execute
```

If commands only exist as preflights, implement minimal honest execution:

- accuracy-only ranking,
- subject-wise rankings,
- pairwise rank instability,
- model ability spread,
- item difficulty distribution,
- naive disagreement baseline,
- random subset baseline,
- subject-stratified subset baseline,
- no raw question text in outputs.

## Create report

```text
MMLU_REAL_PANEL_CORE_RUN_REPORT.md
```

Structure:

```markdown
# MMLU Real-Panel Core Run Report

## 1. Executive Summary
## 2. Inputs
## 3. Panel Shape
## 4. Panel Validity Gate
## 5. Accuracy Ranking
## 6. Subject Instability
## 7. Diagnostic Disagreement
## 8. Baselines
## 9. What Can Be Claimed
## 10. What Cannot Be Claimed
## 11. Result Artifacts
## 12. Failures / Limitations
## 13. Final Verdict
```

Final verdict:

```text
REAL_PANEL_CORE_RUN_COMPLETE
REAL_PANEL_CORE_RUN_BLOCKED
REAL_PANEL_CORE_RUN_NEEDS_FIXES
```

## Evidence updates

Allowed:

- if ≥30-model gate passes: panel-size blocker cleared;
- if analyses run: real-panel ranking/disagreement becomes artifact-backed.

Blocked:

- MMLU error detection success,
- “MMLU invalid,”
- external validation success unless Redux supports it.

## Verification

```bash
ruff check .
python3 -m pytest -q tests/test_real_panel_dryrun_commands.py
python3 -m pytest -q
```
