# ValidEval V5 Rebuttal Preparation

This is a preparation surface, not a collection of claimed rebuttal results.

## Answers that are currently supportable

- **“Was the 39-model study run by ValidEval?”** No. It is an analysis of a public HELM-derived MMLU
  response panel. V5 reconstructs the long table and matrix and records exact hashes.
- **“Does panel adequacy validate IRT?”** No. It only permits exploratory matrix analysis. Every
  measurement model has separate assumptions, recovery, uncertainty, and failure gates.
- **“Why is rank range meaningful?”** The raw range is descriptive only. V5 evaluates observed
  dispersion against explicit nulls and reports confidence sets and decision-relevant top-k/pairwise
  quantities. The legacy severe threshold is retired.
- **“Is Redux external validation?”** No confirmed direct or hash identity is available locally.
  The prior analysis is retained as an unsuccessful exploratory linkage attempt.
- **“Why three benchmarks?”** They define a controlled exact-checkpoint Study C spanning broad MCQ,
  arithmetic reasoning, and heterogeneous hard reasoning. Transfer remains protocol-scoped and can
  be unsupported or benchmark-specific.
- **“Could contamination explain the findings?”** Yes. V5 separates project-pipeline leakage,
  benchmark split overlap, label leakage, and model-pretraining contamination. The last cannot be
  ruled out by this build.

## Evidence still needed before rebuttal claims

1. Returned S1 smoke manifests and revised runtime estimates.
2. Adequate exact-revision Study C outputs for MMLU, GSM8K, and BBH.
3. Confirmatory null/materiality analyses on the controlled panel.
4. Blinded human pilot with controls and adjudication.
5. Confirmed external item linkage or formal exclusion of that pillar.
6. Decoupled confirmatory synthetic outputs.
7. Anonymous clean release from a real Git commit/tag.

## Do not answer with

- Build completeness as evidence of diagnostic validity.
- Fixture results as benchmark results.
- Structural alignment as item identity.
- Family-level overlap as exact-model transfer.
- A compiled PDF as submission readiness.
- A single scalar validity score.
