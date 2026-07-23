# Audit Protocol

## Benchmark Selection

State the benchmark ID, claimed construct, item format, scoring method, and construct-critical fields before running diagnostics.

GPQA Diamond is the first planned real benchmark audit target. The current GPQA artifacts are setup and fixture dry-run artifacts only until a verified local GPQA Diamond JSONL export and cached open/local model outputs are supplied.

## Model Panel

Use a preregistered panel when making empirical claims. For smoke tests and demos, use the deterministic mock panel only.

For the GPQA Diamond audit, use the open/local or cached-output panel plan in `configs/panels/gpqa_open_local.yaml`. Do not require paid APIs for primary claims. If fewer than 6 non-baseline real models produce parseable outputs on at least 90 percent of items, do not interpret item-discrimination estimates.

## Prompt Variants

Define `full` as the reference condition. Ablations should remove or corrupt construct-critical information while keeping the scoring interface stable when possible.

For GPQA Diamond, the pre-registered variants are `full`, `question_only`, `choices_only`, `randomized_choices`, and `answer_letter_only`. Randomized choices preserve answer-label mapping.

## Diagnostics

Run shortcut, IRT, and reliability diagnostics for the first report card. Add contamination and coverage when the necessary corpora and construct taxonomy are available.

## Statistical Discipline

Use fixed seeds, cached predictions, and bootstrap intervals where appropriate. Do not tune the diagnostic after seeing results unless the change is documented.

## Multiple Comparisons

Item-level flags are screening evidence. Treat them as candidates for review, not as isolated proof.

## Reporting Rules

Use cautious language:

- "Evidence consistent with..."
- "Potential threat..."
- "Requires human validation..."
- "Under this protocol..."

Do not report a single validity score.

Every artifact must state its evidence class: synthetic validation, toy/demo, GPQA fixture dry-run, or real GPQA audit. Fixture dry-runs are not benchmark findings.

## How to provide real GPQA inputs

Use a verified local item export and cached open/local outputs only. The canonical preflight sequence is:

```bash
python3 -m valideval validate-benchmark-file --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl
python3 -m valideval score-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --input local_outputs/gpqa_full_raw.jsonl --output cache/gpqa_diamond/gpqa_open_local/predictions_full.jsonl --prompt-variant full
python3 -m valideval matrix-from-predictions --benchmark gpqa_diamond --panel gpqa_open_local --variant full
python3 -m valideval validate-alignment --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --predictions cache/gpqa_diamond/gpqa_open_local/predictions_full.jsonl
python3 -m valideval extraction-audit --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --outputs local_outputs/gpqa_full_raw.jsonl --prompt-variant full
python3 -m valideval validate-prompt-variants --benchmark gpqa_diamond --panel gpqa_open_local --required-variants full question_only choices_only randomized_choices answer_letter_only
python3 -m valideval gpqa-go-no-go --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_open_local
python3 -m valideval audit-manifest --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_open_local
```

If outputs are already scored, use `import-outputs` instead of `score-outputs`. A real audit may proceed only after go/no-go passes; preflight artifacts must not be described as benchmark results.
