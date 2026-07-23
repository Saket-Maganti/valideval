# ValidEval V5 Model Identity Audit

## Verdict

**Status: `COMMON_PANEL_PARTIAL`.** Five public Study C checkpoints now have frozen immutable
revisions and local hashes for their retrieved configuration surfaces. They form an exact
checkpoint-identity S1/S2 candidate panel. They do not yet form a scientifically adequate S3
panel, and no checkpoint has a reproduced T4 execution identity.

The canonical source is `configs/models/model_registry_v5.yaml`.

## Study separation

### Study H — historical MMLU

The reproduced HELM-derived panel contains 39 model aliases, 14,042 items, and 57 subjects.
HELM release provenance is recorded, but immutable upstream model revisions, quantization,
chat templates, prompt regimes, and decoding identities are unavailable. Its identity status
is therefore `BLOCKED_REVISION_UNKNOWN`. Study H supports within-MMLU historical analyses only.

### Study C — controlled common panel

The following checkpoint identities were live-verified against the Hugging Face model API on
2026-07-16 and frozen in the registry:

| Canonical checkpoint | Immutable revision | Family | License metadata | Current role |
|---|---|---|---|---|
| `Qwen/Qwen2.5-0.5B-Instruct` | `7ae557604adf67be50417f59c2c2f167def9a775` | Qwen2.5 | Apache-2.0 | exact S1/S2 candidate |
| `Qwen/Qwen2.5-1.5B-Instruct` | `989aa7980e4cf806f80c7fef2b1adb7bc71aa306` | Qwen2.5 | Apache-2.0 | exact S1/S2 candidate |
| `Qwen/Qwen2.5-3B-Instruct` | `aa8e72537993ba99e69dfaafa59ed015b17504d1` | Qwen2.5 | repository reports `other` | exact S1/S2 candidate; license review required |
| `microsoft/Phi-3-mini-4k-instruct` | `f39ac1d28e925b323eae81227eaba4464caced4e` | Phi-3 | MIT | exact S1/S2 candidate |
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | `fe8a4ea1ffedaf415f4da2f062534de366a451e6` | TinyLlama | Apache-2.0 | exact S1/S2 candidate |

`google/gemma-2-2b-it` is pinned to repository SHA
`299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8`, but gated configuration and chat-template
access were not verified. It is excluded until access is resolved.

## Checkpoint identity is not execution identity

A controlled row becomes exact only when its run manifest also fixes and verifies:

- quantization class and weight hashes;
- base/instruction/chat status and chat-template hash;
- prompt-regime and few-shot manifest hashes;
- decoding parameters and seed;
- extraction implementation version;
- benchmark contract and immutable dataset revision.

The five entries above satisfy the frozen repository/checkpoint part. Their `runnable_on_t4`
state remains `PLANNED_BENCHMARK`, so the exact execution identity is `PLANNED`, not
`REPRODUCED`.

## Diversity and dependence audit

The partial panel has five checkpoints across three nominal families; three of five are
Qwen2.5. This is useful for engineering smoke and scale sensitivity within Qwen2.5, but it is
not family-balanced and cannot identify a family-deduplicated cross-benchmark estimand. Family
labels are grouping metadata, never proof of equivalent checkpoints.

The S3 planner currently requires 32 exact checkpoints across at least eight independent
families under its stated planning criterion. The current exact candidate panel supplies
5/32 checkpoints and 3/8 nominal families.

## Claims

Allowed: “Five immutable public checkpoint revisions are frozen for the controlled engineering
pilot.”

Blocked: “The exact scientific common panel is complete,” “the same models have been run on all
three benchmarks,” “T4 feasibility is verified,” and any transfer result that mixes Study H
aliases with Study C checkpoints.

## Exact next action

Run the S1 T4×2 smoke on the five included checkpoint revisions, import and validate execution
manifests, exclude any identity drift, and expand the registry toward the family-balanced S3
target before making scientific common-panel claims.

