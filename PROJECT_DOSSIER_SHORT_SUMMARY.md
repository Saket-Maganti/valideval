# ValidEval External Review Short Summary

## Project Thesis

ValidEval is a psychometric validity-auditing toolkit for AI benchmarks. Its thesis is that validity is not accuracy: benchmark scores can reflect construct-relevant capability, but they can also reflect shortcuts, contamination, scoring artifacts, low-discrimination items, unreliable prompts/scorers, saturation, or construct undercoverage.

The project is designed to report multidimensional evidence profiles, not a scalar validity score.

## Current Implementation Status

This repository is a strong offline prototype with a complete toy audit path. It is not yet a real-benchmark empirical study.

What works:

- `python3 -m pip install -e ".[dev]"`
- `pytest -q`: 78 passed
- `ruff check .`: passed
- offline toy MCQ benchmark with 36 synthetic items
- deterministic eight-model mock panel
- 22 cached prompt-variant response matrices
- all-core diagnostics
- advanced psychometric diagnostics
- report cards, validity cards, profile certificates
- repair suggestions and item forensics
- leaderboard/dashboard/site artifacts
- human-validation protocol tooling on toy labels
- RAG and abstention domain-pack diagnostics
- schema export, environment capture, reviewer-risk mode, paper assets, reproducibility bundle

What is incomplete:

- real benchmark loaders for MMLU, GSM8K, BBH, TruthfulQA, and CausalAgentBench are placeholders
- no real benchmark results exist
- no real local/open model panel is wired into the CLI beyond mock
- Ollama runner exists but is not configured through `load_panel()`
- predictive validity and Goodhart diagnostics are status stubs requiring external data
- most domain packs are scaffolds with no diagnostics
- human validation is toy-scale only: 6 imported labels over 3 tasks
- paper results section is still placeholder
- `paper-assets --all` is unsupported
- `ruff format --check .` reports 9 files would reformat

## Verification Results

Environment note: `python` is not available in this pyenv setup, so exact `python -m ...` commands fail. The repo's own docs/Makefile use `python3`, and those commands work.

Passed:

- `python3 -m pip install -e ".[dev]"`
- `pytest -q`
- `ruff check .`
- `python3 -m valideval info`
- `python3 -m valideval toy`
- `python3 -m valideval matrices --benchmark toy_mcq --panel mock`
- `python3 -m valideval audit --benchmark toy_mcq --diagnostics all-core`
- `python3 -m valideval psychometrics all --benchmark toy_mcq --panel mock`
- `python3 -m valideval report --benchmark toy_mcq --panel mock`
- `python3 -m valideval certificate issue --benchmark toy_mcq --panel mock`
- `python3 -m valideval bundle --benchmark toy_mcq --panel mock`
- `python3 -m valideval verify-bundle bundles/toy_mcq_mock_bundle`
- `python3 -m valideval reviewer-risk --report reportcards/toy_mcq_mock.md`
- `python3 -m valideval site build`
- supported `python3 -m valideval paper-assets --benchmark toy_mcq --panel mock`

Failed or rough:

- `python -m ...`: fails because `python` command is unavailable
- `ruff format --check .`: 9 files would reformat
- `python3 -m valideval paper-assets --all`: unrecognized argument

## Generated Artifacts

Important outputs:

- `cache/toy_mcq/mock/`
- `results/toy_mcq/mock/`
- `reportcards/toy_mcq_mock.md`
- `reportcards/toy_mcq_mock.reviewer_risk.json`
- `results/toy_mcq/mock/validity_card.md`
- `results/toy_mcq/mock/validity_certificate.md`
- `leaderboard/benchmark_atlas.md`
- `dashboard_data/`
- `site/index.html`
- `paper/assets_manifest.json`
- `bundles/toy_mcq_mock_bundle/`

The bundle verified successfully on a clean rerun: 65 files checked, no errors.

## Toy Findings

These are toy/demo results only.

- Best shallow baseline: `metadata_artifact_baseline`, score 0.972
- Best mock model score: 0.611
- Shortcut full-condition score: 0.424
- High-retention variants: `question_only`, `context_removed`, `context_shuffled`, `label_prior_only`, `irrelevant_context`
- Reliability estimate: 0.427
- IRT proxy: 4 negative-discrimination items; near-zero discrimination fraction 0.306
- Saturation category: moderate
- Data forensics: local duplicate/provenance threats; no external corpus in all-core run
- Certificate profile: Silver, but still shows threatened/weak dimensions

Do not present these as real benchmark evidence.

## First Real Benchmark Recommendation

Recommended first real experiment: MMLU subset via local JSONL export.

Why:

- MCQ format matches current scoring and diagnostics.
- It avoids open-ended judge complexity.
- Many implemented diagnostics apply directly.
- A small local export can be audited without internet or paid APIs.

Minimum requirements:

- 100-300 validated MMLU-subset items in `BenchmarkItem` JSONL
- real local/open model outputs from at least 5 models
- hand-checked scoring and a preregistered audit protocol
- clear construct tags and provenance fields

## What We Want The External Reviewer To Judge

1. Is the validity-not-accuracy framing novel and useful?
2. Which diagnostics are credible now?
3. Which features should be removed, renamed, or delayed?
4. Are certificates and ranking views useful or too risky?
5. What first real benchmark would make the toolkit convincing?
6. What result would make this publishable?
7. Is the engineering strong enough for outside adoption?
8. What would a skeptical reviewer attack first?

## Honest Maturity Ratings

- Current maturity: prototype with strong offline toy demo
- Overall repo status: 6/10
- Research potential: 8/10
- Engineering maturity: 6.5/10
- First real benchmark readiness: 3.5/10

Single most important next step: run one real MCQ benchmark audit from a validated local JSONL export with real local model outputs.

