# Prompt 05 — IRT and Psychometric Runs on the Wide Panel

## Objective

Run psychometric diagnostics on the active wide MMLU panel.

## Gate

```bash
python3 - <<'PY'
import pandas as pd
from pathlib import Path
p = Path("cache/mmlu/wide/matrix.csv")
if not p.exists():
    raise SystemExit("BLOCKED: missing matrix")
df = pd.read_csv(p)
model_col = "model_id" if "model_id" in df.columns else "model"
n = df[model_col].nunique()
print("models", n)
if n < 30:
    raise SystemExit("BLOCKED: fewer than 30 models")
PY
```

## Runs

Try:

```bash
python3 -m valideval fit-irt   --matrix cache/mmlu/wide/matrix.csv   --model proxy   --output results/mmlu/irt_proxy   --strict

python3 -m valideval fit-irt   --matrix cache/mmlu/wide/matrix.csv   --model rasch   --output results/mmlu/irt_rasch   --strict
```

If feasible and implemented:

```bash
python3 -m valideval fit-irt   --matrix cache/mmlu/wide/matrix.csv   --model 2pl   --output results/mmlu/irt_2pl   --strict
```

If 2PL is unavailable or fails, document as blocked. Do not fake it.

## Required outputs

- item difficulty,
- discrimination / point-biserial / proxy discrimination,
- negative discrimination flags,
- near-zero discrimination flags,
- extreme difficulty flags,
- subject-level summaries,
- model ability estimates/proxies,
- uncertainty if available,
- agreement between proxy/Rasch/2PL if available.

## Report

Create:

```text
MMLU_IRT_PSYCHOMETRIC_RUN_REPORT.md
```

Final verdict:

```text
IRT_RUN_COMPLETE
IRT_RUN_PARTIAL_PROXY_ONLY
IRT_RUN_BLOCKED
```

## Claims

Allowed:

- item-level psychometric diagnostics computed on this panel,
- panel gate passed/failed,
- item flags are diagnostic signals.

Blocked:

- MMLU errors detected,
- MMLU invalid,
- IRT flags externally validated unless Redux/other validation supports it.

## Verification

```bash
ruff check .
python3 -m pytest -q
```
