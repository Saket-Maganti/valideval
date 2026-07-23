# ValidEval V5 Benchmark Contract Audit

Audit date: 2026-07-16  
Scope: pre-execution, local-only contract review  
Evidence state: `PLANNED`

## Verdict

`BENCHMARK_CONTRACT_SCHEMA_PASS_BBH_PRE_S1_FREEZE_BLOCKED`

All three V5 YAML files now contain the complete Phase I field set, immutable dataset revisions, deterministic item-ID policies, explicit scoring/extraction/failure contracts, and gold-isolation rules. MMLU and GSM8K are structurally frozen. BBH still has two explicit pre-S1 blockers: the few-shot example hash and upstream license review. No controlled MMLU, GSM8K, or BBH result was generated in this pass.

## Files reviewed

- `configs/benchmarks/mmlu_v5.yaml`
- `configs/benchmarks/gsm8k_v5.yaml`
- `configs/benchmarks/bbh_v5.yaml`
- `configs/models/model_registry_v5.yaml`
- `src/valideval/execution/manifest.py`
- `src/valideval/leakage/guards.py`
- `tests/test_gold_answer_isolation_v5.py`

## Required-field audit

Phase I requires every contract to freeze these fields:

`benchmark_id`, `benchmark_version`, `dataset_source`, `dataset_revision`, `split`, `subtasks`, `item_id_method`, `prompt_template_version`, `few_shot_policy`, `few_shot_examples_hash`, `chat_template_policy`, `generation_mode`, `generation_parameters`, `scoring_version`, `extraction_version`, `failure_taxonomy`, `license`, `redistribution_policy`, and `expected_item_count`.

The current files have no missing required keys. A local structural read produced:

| Contract | Dataset revision | Subtasks | Expected items | Structural state |
|---|---|---:|---:|---|
| MMLU V5 | `c30699e8356da336a370243923dbaf21066bb9fe` | 57 exact subjects | 14,042 | Pass |
| GSM8K V5 | `740312add88f781978c0658806c59bc2815b9866` | `main` | 1,319 | Pass |
| BBH V5 | `982bb89fd79532a8ac676a61fc42eb1aeec63f99` | 27 exact tasks | 6,511 | Pass with explicit pre-S1 blockers |

The contracts correctly keep empirical claims in `RESULT_REQUIRED`. A schema pass establishes only that execution inputs are specified; it is not evidence that counts, prompts, extractors, or model behavior were validated by a run.

## What is already sound

- Study H and Study C are separated for MMLU. Historical aliases are not promoted to exact controlled-checkpoint identities.
- MMLU enumerates all 57 subjects, freezes zero-shot constrained choice generation, records the empty few-shot hash, and distinguishes generation scoring from option log-likelihood.
- GSM8K freezes zero-shot rationale generation plus the final marker and edge-case treatment for commas, fractions, units, negative values, scientific notation, multiple final numbers, refusal, timeout, truncation, and invalid extraction.
- BBH enumerates 27 tasks, includes task identity in deterministic item IDs, requires subtask outputs, and names the task-specific scoring registry.
- Each contract declares a generation view that excludes answer/gold fields and a scorer-only answer boundary.
- The shared V5 prediction schema distinguishes extraction and generation status from correctness.
- Gold-answer isolation tests cover nested metadata, few-shot target overlap, retry feedback, and explicit extraction failure.
- The optional fourth-benchmark lane was not expanded merely to increase benchmark count. No fourth runbook is justified until the three primary contracts are frozen and a distinct construct-validity purpose is documented.

## Benchmark-specific freeze requirements

### MMLU

The contract freezes the 57-subject list, `cais/mmlu` revision, test split, 14,042 expected items, item hash, zero-shot policy/hash, chat-template capture rule, constrained generation, answer format, extraction/scoring version, prompt-sensitivity variants, failure taxonomy, and redistribution rule. Before S1, the runner must reproduce the declared source count and hash the rendered prompt/chat template artifacts.

### GSM8K

The contract freezes the repository/revision, 1,319-item test split, rationale policy, maximum generation settings, final-answer delimiter, numeric edge cases, and explicit failure statuses. Before S1, executable extractor conformance fixtures must prove those written rules, while gold answers remain unavailable until raw generations are frozen.

### BBH

The contract freezes the exact 27-task list, source/revision, 6,511 expected items, task-aware scoring/extraction identities, cross-task collision policy, and subtask outputs. `few_shot_examples_hash: PLANNED_FREEZE_BEFORE_S1` and `license: UPSTREAM_LICENSE_REVIEW_REQUIRED` are deliberate fail-closed blockers. The few-shot corpus/hash and license/redistribution decision must be resolved before S1.

## Verification performed

The relevant leakage and protocol suite was run locally as part of the V5 execution/protocol check. The gold-isolation tests passed. These are code-path checks, not evidence that the benchmark contracts are frozen or that any benchmark was executed.

## Gate and next action

- Contract schema/code path: `VERIFIED_FROM_PRIMARY_ARTIFACT`
- MMLU/GSM8K contract freeze: `PLANNED` for S1 execution, with no unresolved YAML placeholder
- BBH contract freeze: `BLOCKED`
- Controlled benchmark results: `BLOCKED`
- Exact common-panel eligibility: `BLOCKED`
- Claim permission: only protocol/readiness claims

Exact next action: add/execute contract schema and source-count tests, build GSM8K/BBH extractor conformance fixtures, freeze and hash the BBH few-shot examples, and complete BBH upstream license review. Only then use these contracts as hashed S1 configuration inputs.
