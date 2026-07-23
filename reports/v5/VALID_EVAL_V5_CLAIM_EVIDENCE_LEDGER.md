# ValidEval V5 Claim-Evidence Ledger

This is the paper-facing claim gate. Evidence states are categorical, not a scalar score.

## Status counts

- `BLOCKED`: 3
- `CONTRADICTED`: 1
- `REPRODUCED`: 5
- `RETIRED`: 2

## Claims

### MMLU-H-001 — `REPRODUCED`

- Claim: The public HELM-derived MMLU panel contains 39 models and 14,042 items.
- Observed: 39 models; 14042 items
- Allowed wording: Analysis of a public HELM-derived MMLU response panel covered 39 models and 14,042 items.
- Blocked wording: ValidEval executed 39 models on MMLU.
- Reproduction: `python3 scripts/reproduce_mmlu_evidence_v5.py`

### MMLU-H-002 — `REPRODUCED`

- Claim: The HELM-derived matrix has 547,638 observations and zero missing cells.
- Observed: 547638; 0 missing
- Allowed wording: The reconstructed matrix exactly matched the cached 547,638-cell matrix with no missing cells.
- Blocked wording: The matrix proves benchmark validity.
- Reproduction: `python3 scripts/reproduce_mmlu_evidence_v5.py`

### MMLU-H-003 — `REPRODUCED`

- Claim: Observed aggregate accuracy spread is approximately 0.580188.
- Observed: 0.5801880074063523
- Allowed wording: Under this imported panel, observed accuracy spanned about 0.5802.
- Blocked wording: The ability spread validates IRT assumptions.
- Reproduction: `python3 scripts/reproduce_mmlu_evidence_v5.py`

### MMLU-H-004 — `REPRODUCED`

- Claim: Subject-level raw rank ranges have median 19 and maximum 30.
- Observed: median 19.0; maximum 30.0
- Allowed wording: Raw subject-conditioned ranks vary under this diagnostic protocol.
- Blocked wording: The rank ranges prove material instability or benchmark invalidity.
- Reproduction: `python3 scripts/reproduce_mmlu_evidence_v5.py`

### MMLU-H-005 — `REPRODUCED`

- Claim: Proxy diagnostic weighting stays close to accuracy ranking.
- Observed: Spearman 0.9979757085020243; Kendall 0.9784075573549258; max delta 2.0
- Allowed wording: The proxy-weighted ranking was close to aggregate accuracy under this protocol.
- Blocked wording: This is the true ranking or a full 2PL result.
- Reproduction: `python3 scripts/reproduce_mmlu_evidence_v5.py`

### MMLU-H-006 — `RETIRED`

- Claim: A raw rank range of at least 10 is a severe/material effect.
- Observed: 37 models cross an exploratory threshold
- Allowed wording: Thirty-seven models crossed the legacy exploratory threshold; V5 does not interpret that threshold as severity.
- Blocked wording: Thirty-seven models show severe instability.
- Reproduction: `python3 scripts/reproduce_mmlu_evidence_v5.py`

### MMLU-ABL-001 — `CONTRADICTED`

- Claim: The legacy eight-family output is a genuine diagnostic-family ablation.
- Observed: Seven named variants reuse accuracy-derived values; not a valid family ablation.
- Allowed wording: The legacy table is retained as a historical artifact and excluded from V5 evidence.
- Blocked wording: Eight diagnostic families were independently ablated.
- Reproduction: `static V5 code and artifact audit`

### REDUX-001 — `RETIRED`

- Claim: MMLU-Redux provides confirmed item-level external validation.
- Observed: No confirmed direct ID or content-hash linkage in sanitized local artifacts.
- Allowed wording: The Redux analysis is an unsuccessful exploratory linkage attempt.
- Blocked wording: Redux validates ValidEval item-level detection.
- Reproduction: `python3 -m pytest -q tests/test_mmlu_redux_linkage_v5.py`

### STUDY-C-001 — `BLOCKED`

- Claim: Exact-model cross-benchmark transfer is established.
- Observed: Not available
- Allowed wording: [RESULT REQUIRED: exact artifact]
- Blocked wording: Exact-model cross-benchmark transfer is established.
- Reproduction: `BLOCKED`

### HUMAN-001 — `BLOCKED`

- Claim: Human review confirms benchmark issues.
- Observed: Not available
- Allowed wording: [RESULT REQUIRED: exact artifact]
- Blocked wording: Human review confirms benchmark issues.
- Reproduction: `BLOCKED`

### SYNTHETIC-001 — `BLOCKED`

- Claim: The decoupled synthetic protocol has confirmatory sensitivity/specificity evidence.
- Observed: Not available
- Allowed wording: [RESULT REQUIRED: exact artifact]
- Blocked wording: The decoupled synthetic protocol has confirmatory sensitivity/specificity evidence.
- Reproduction: `BLOCKED`
