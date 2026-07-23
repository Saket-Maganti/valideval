# Prompt 19 — Final God-Tier Gate V3

## Objective

Make the honest final venue decision.

## Gate options

```text
NEURIPS_DB_READY_CANDIDATE
NEURIPS_DB_BORDERLINE_CANDIDATE
COLM_TMLR_READY_CANDIDATE
COLM_TMLR_AFTER_MINOR_FIXES
STRONG_WORKSHOP_READY
WORKSHOP_ONLY
NOT_READY
```

## Criteria

### NeurIPS D&B ready/borderline

Requires:

- at least two real benchmarks,
- preferably three or strong external/human labels,
- cross-benchmark evidence,
- clean bibliography,
- compiled paper,
- reviewer packet,
- no unsupported claims,
- reviewer risk not high.

### COLM/TMLR candidate

Requires:

- MMLU + GSM8K evidence or one very strong benchmark plus human/external validation,
- coherent measurement-science story,
- clean paper,
- artifact package.

### Strong workshop

MMLU-only or partial second-benchmark with honest blocked states.

## Output

```text
FINAL_GOD_TIER_GATE_V3.md
```

## Required sections

```markdown
# Final God-Tier Gate V3
## Verdict
## Why
## Evidence supporting verdict
## Remaining blockers
## Best venue now
## Highest plausible venue after next run
## Exact next action
```
