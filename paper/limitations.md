# Limitations — V5

- Study H comes from public HELM-derived outputs; ValidEval reproduced the artifact but did not run
  those models. Historical aliases do not prove immutable checkpoint identity.
- Study H is a single benchmark panel. No diagnostic establishes that MMLU is globally valid or
  invalid, and no panel ranking is the true model ranking.
- Raw subject rank range is descriptive. The legacy threshold `>=10` has no validated severity or
  materiality interpretation and is retired.
- Proxy diagnostic weighting is not a full parametric 2PL or a validated latent-construct ranking.
- The old “diagnostic-family ablation” is contradicted because seven columns reuse accuracy. It
  cannot support diagnostic contribution claims.
- MMLU-Redux linkage is structural rather than direct/hash-confirmed. The weak/negative metrics do
  not establish generic MMLU error detection.
- Synthetic validation can be circular when a generator or readout encodes the target detector. The
  legacy synthetic AUCs are historical wiring/sanity-check artifacts, not independent validation
  evidence.
- The decoupled synthetic protocol is preregistered but not executed; it remains `BLOCKED` and
  `RESULT_REQUIRED` for empirical paper claims.
- Human-validation infrastructure exists, but no V5 human labels have been imported. Human
  confirmation remains `BLOCKED`.
- Controlled Study C MMLU, GSM8K, and BBH runs have not been returned and imported. Exact-model
  transfer, ability transfer, construct specialization, and cross-benchmark ranking stability remain
  `BLOCKED`.
- Fixture notebooks and fixture ZIPs are `NON_EVIDENCE_FIXTURE`. Passing their tests demonstrates
  code-path behavior, not scientific findings.
- Model loading, licensing, gated access, quantization, prompt templates, extraction behavior, and
  T4x2 resource limits may alter future Study C coverage.
- The V5 importer and overlap gate reduce provenance and identity risk but cannot guarantee broader
  construct validity.
- Validity is multidimensional. ValidEval intentionally does not produce a universal scalar validity
  score.
