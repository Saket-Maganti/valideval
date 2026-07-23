# GPQA Diamond Pre-Registration Draft

Artifact class: **real GPQA audit setup**.

This document contains no results. It defines the intended first real benchmark audit once a verified local GPQA Diamond JSONL export and cached open/local model outputs are available.

## 1. Audit objective

Assess whether evidence from a fixed GPQA Diamond audit protocol is consistent with the claimed interpretation of scores as graduate-level scientific question answering requiring expert-level domain reasoning. The audit reports a diagnostic profile, not a global valid/invalid verdict.

## 2. Benchmark identity

- Benchmark: GPQA Diamond
- Benchmark family: GPQA
- Split: diamond
- Format: multiple-choice
- Data policy: local JSONL export required; ValidEval does not download or redistribute GPQA data.

## 3. Claimed construct

Graduate-level scientific question answering requiring expert-level domain reasoning.

## 4. Why GPQA Diamond was selected

GPQA Diamond is current, compact, consequential, multiple-choice friendly, and has a clear construct claim. It is a stronger first scientific test than saturated headline benchmarks and avoids first-audit dependence on retrieval, code execution, agents, or LLM judge scoring.

## 5. Included diagnostics

Primary diagnostics: answer distribution, distractor quality, IRT/proxy item discrimination, reliability, extraction robustness, saturation, and shortcut ablations.

Secondary diagnostics: prompt sensitivity, redundancy, and data-forensics/provenance checks when local corpora and metadata are supplied.

## 6. Excluded diagnostics and why

LLM-judge reliability, RAG-specific diagnostics, agent/tool-use diagnostics, predictive validity, and consequential validity are excluded from the primary GPQA audit because they require different task interfaces, human/judge artifacts, or external outcome data.

## 7. Model panel plan

The primary audit uses open/local or cached open-model outputs only. The recommended minimum is 8 non-baseline real models plus 2 baselines. The panel should span small, mid, and stronger open models from multiple families when feasible. Closed or paid API models are not required and are excluded from primary claims.

## 8. Prompt templates

Templates are fixed before running the real audit:

- `full`
- `question_only`
- `choices_only`
- `randomized_choices`
- `answer_letter_only`

Prompt template hashes are recorded in artifacts. Randomized choices preserve original answer-label mapping.

## 9. Extraction/scoring rules

Primary extraction is strict single-letter extraction. Secondary checks use lenient letter extraction and normalized text matching against choice text. Invalid outputs are counted, not silently coerced.

## 10. Multiplicity correction

Item-level flags are treated as a family of screening tests. The planned correction is Benjamini-Hochberg at `q = 0.10` for item-level review flags. Corrected flags are candidates for human review, not proof of invalidity.

## 11. Materiality thresholds

- Invalid output rate warning: 0.05
- Strict-vs-lenient score shift warning: 0.03
- Prompt rank flip warning: 2 or more rank positions
- High shortcut retention warning: 0.70
- Near-zero discrimination fraction warning: 0.30
- Any negative-discrimination item: review
- Dead distractor fraction warning: 0.20
- Minimum parseable output rate: 0.90

## 12. Primary outcomes

Primary outcomes are item-quality profile, extraction/scoring robustness, prompt/reliability profile, shortcut-retention profile, and floor/saturation profile under the audited panel.

## 13. Secondary outcomes

Secondary outcomes are data-forensics/provenance completeness, redundancy, prompt-template ranking sensitivity, and candidate items for human benchmark-author review.

## 14. Stopping rules

Stop before real-audit claims if the local GPQA JSONL fails schema validation. Do not interpret IRT/item-discrimination estimates if fewer than 6 non-baseline real models produce parseable outputs on at least 90 percent of items. Treat all conclusions as exploratory if the panel is near random or near ceiling.

## 15. What counts as a material finding

A material finding requires a diagnostic signal above threshold, reproducible cached artifacts, a clear link to a construct-relevant threat, and cautious interpretation. Item-level flags require review before benchmark-maintenance decisions.

## 16. What would be boring but useful

It would still be useful if the audit finds stable extraction, no strong shortcut retention, adequate distractor use, no severe floor or ceiling effect, and mostly positive item discrimination under the open/local panel.

## 17. Limitations

The audit cannot prove GPQA Diamond is globally valid or invalid. The model panel is open/local unless separately replicated. Data-forensics depends on supplied corpora and provenance. Proxy IRT is panel-dependent and fragile with small panels.

## 18. Deviations log placeholder

Record any deviation from this protocol before inspecting real GPQA diagnostic outputs.

## How to provide real GPQA inputs

Expected item file:

```text
data/gpqa/gpqa_diamond.jsonl
```

ValidEval does not ship GPQA items. Obtain GPQA Diamond through appropriate local means and do not publish raw question text in generated reports.

Export a local CSV/JSONL source:

```bash
python3 -m valideval export-gpqa-diamond --source-file data/raw/gpqa_source.csv --output data/gpqa/gpqa_diamond.jsonl
```

Or export from an already available local Hugging Face cache:

```bash
python3 -m valideval export-gpqa-diamond --source hf --output data/gpqa/gpqa_diamond.jsonl
```

Validate the local item export:

```bash
python3 -m valideval validate-benchmark-file --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl
```

Check local/cached model readiness and generate cached raw outputs using open/local runners:

```bash
python3 -m valideval check-panel --panel gpqa_open_local
python3 -m valideval generate-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_open_local --prompt-variant full --output-dir local_outputs/gpqa/full
```

The optional `gpqa_smoke_local` panel and `--limit-items` are workflow checks only; they are not scientific results.

For already scored predictions:

```bash
python3 -m valideval import-outputs --input local_outputs/gpqa/full/<scored_output>.jsonl --output cache/gpqa_diamond/gpqa_open_local/predictions_full.jsonl --adapter generic-jsonl --benchmark-id gpqa_diamond --prompt-variant full
```

For raw unscored outputs:

```bash
python3 -m valideval score-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --input local_outputs/gpqa/full/<model_output>.jsonl --output cache/gpqa_diamond/gpqa_open_local/predictions_full.jsonl --prompt-variant full
```

Build and validate matrices:

```bash
python3 -m valideval matrix-from-predictions --benchmark gpqa_diamond --panel gpqa_open_local --variant full
python3 -m valideval validate-alignment --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --predictions cache/gpqa_diamond/gpqa_open_local/predictions_full.jsonl
python3 -m valideval extraction-audit --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --outputs local_outputs/gpqa/full/<model_output>.jsonl --prompt-variant full
python3 -m valideval validate-prompt-variants --benchmark gpqa_diamond --panel gpqa_open_local --required-variants full question_only choices_only randomized_choices answer_letter_only
python3 -m valideval gpqa-go-no-go --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_open_local
python3 -m valideval audit-manifest --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_open_local
```

Real-audit dry run:

```bash
python3 -m valideval audit --benchmark gpqa_diamond --panel gpqa_open_local --local-path data/gpqa/gpqa_diamond.jsonl --config configs/audits/gpqa_diamond_preregistered.yaml --from-cache --input-validated-only --dry-run-real
```

Input-validation artifacts are not GPQA validity findings. Do not report validity threats, rankings, contamination status, or benchmark health from these preflight checks.
