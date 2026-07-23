# Prompt 01 — Evidence Reconciliation Gate: 3-Model vs 39-Model Truth

External audits conflict:

- one says the current real panel is only 3 models,
- prior artifacts say a 39-model HELM MMLU panel exists.

Resolve this from actual repo files before running major analyses.

## Do not

Do not run diagnostics.  
Do not recompute metrics.  
Do not run model inference.  
Do not download anything.  
Do not upgrade claims.

## Inspect paths

```text
cache/mmlu/
cache/mmlu/wide/
data/external/mmlu/
data/external/mmlu/lm_eval_outputs/
results/mmlu/
results/neurips_small_runs/
LIMITED_REAL_MMLU_PANEL_VALIDITY_REPORT.md
MMLU_WIDE_PANEL_ACQUISITION_REPORT.md
MMLU_PANEL_VALIDITY_REPORT.md
MMLU_EVIDENCE_GATE_REPORT.md
MMLU_REDUX_WEAK_SIGNAL_DIAGNOSIS.md
MMLU_REDUX_SUBJECT_NORMALIZED_VALIDATION_REPORT.md
REAL_EMPIRICAL_SPINE_REFRAME.md
FINAL_NO_RUN_READINESS_AUDIT.md
NEURIPS_SUBMISSION_GO_NO_GO.md
CLAIMS_LEDGER_NEURIPS.md
paper/CLAIMS_LEDGER.md
paper/claims.md
paper/experiments.md
paper/reframed_abstract_negative_result.md
paper/reframed_intro_negative_result.md
```

## Shape-only inspection

```bash
python3 - <<'PY'
import json
from pathlib import Path
import pandas as pd

paths = [
    Path("cache/mmlu/wide/matrix.csv"),
    Path("cache/mmlu/wide/predictions.jsonl"),
    Path("data/external/mmlu/prediction_details_wide.jsonl"),
    Path("data/external/mmlu/matrix.csv"),
    Path("results/mmlu/irt/item_parameters.csv"),
    Path("results/mmlu/panel_validity/panel_validity_report.json"),
]

for p in paths:
    print("\n==", p, "==")
    if not p.exists():
        print("MISSING")
        continue
    print("FOUND", p.stat().st_size, "bytes")
    if p.suffix == ".csv":
        df = pd.read_csv(p)
        print("shape", df.shape)
        print("columns", list(df.columns)[:30])
        for col in ["model_id", "model", "item_id", "subject"]:
            if col in df.columns:
                print(f"unique {col}", df[col].nunique())
    elif p.suffix == ".jsonl":
        rows = 0
        models, items, subjects = set(), set(), set()
        sample_keys = None
        with p.open() as f:
            for line in f:
                rows += 1
                obj = json.loads(line)
                if sample_keys is None:
                    sample_keys = sorted(obj.keys())
                models.add(obj.get("model_id", obj.get("model", "")))
                items.add(obj.get("item_id", obj.get("question_id", obj.get("id", ""))))
                if "subject" in obj:
                    subjects.add(obj["subject"])
        print("rows", rows)
        print("sample_keys", sample_keys)
        print("unique models", len(models))
        print("unique items", len(items))
        print("unique subjects", len(subjects))
    elif p.suffix == ".json":
        print(p.read_text()[:2000])
PY
```

## Search contradictory claims

```bash
rg "39-model|39 model|547,638|547638|14,042|14042|3-model|3 model|310 items|model_count_below_30|panel-validity|panel validity|blocked|RESULT_REQUIRED|WORKSHOP_FIRST|NeurIPS|DMLR|TMLR" .
```

## Create report

Create:

```text
VALID_EVAL_EVIDENCE_RECONCILIATION_AUDIT.md
```

Structure:

```markdown
# ValidEval Evidence Reconciliation Audit

## 1. Executive Summary

## 2. Files Inspected

## 3. Matrix Artifacts Found

| Path | Exists? | Rows | Models | Items | Subjects | Notes |
|---|---:|---:|---:|---:|---:|---|

## 4. Active Evidence Source

## 5. 3-Model Pilot Status

## 6. 39-Model Panel Status

## 7. IRT Status

## 8. MMLU-Redux Status

## 9. Synthetic Harness Status

## 10. Claims Allowed Now

## 11. Claims Blocked Now

## 12. Stale or Contradictory Docs

## 13. Venue Implication

## 14. Required Fixes

## 15. Final Verdict
```

Final verdict must be one of:

```text
ONLY_3_MODEL_PANEL_AVAILABLE_PANEL_CLAIMS_BLOCKED
39_MODEL_PANEL_PRESENT_BUT_DOCS_STALE
39_MODEL_PANEL_PRESENT_AND_ACTIVE
EVIDENCE_STATE_AMBIGUOUS_BLOCKED_UNTIL_FIXED
```

## If docs are stale

Update only claim/status docs, not result values. Allowed updates:

- 3-model pilot only; panel claims blocked,
- 39-model panel present but not yet analyzed for a new finding,
- MMLU-Redux remains weak/negative,
- synthetic harness remains demoted,
- real-panel ranking/disagreement remains `RESULT_REQUIRED`.

## Verification

```bash
ruff check .
python3 -m pytest -q tests/test_real_panel_dryrun_commands.py || true
```
