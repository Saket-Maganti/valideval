# Current Claims Allowed and Blocked

## Claims Allowed

- ValidEval treats benchmark validity as a multidimensional evidence profile.
- The active MMLU evidence source is the 39-model public HELM MMLU wide panel.
- The active MMLU panel-size blocker is cleared under the reconciled panel-validity artifact.
- The older 3-model MMLU files are historical/provenance only.
- Proxy IRT artifacts exist for the active MMLU panel.
- MMLU-Redux is a weak/negative external-validation stress test under structural alignment.
- Legacy synthetic AUCs are wiring/sanity-check artifacts only.
- Decoupled synthetic validation, real-panel ranking/disagreement, and second-benchmark evidence are future work until approved artifacts exist.

## Claims Blocked

- MMLU error-detection success.
- Global MMLU validity or invalidity.
- Direct/hash-confirmed MMLU-Redux alignment.
- Treating MMLU-Redux as positive validation evidence.
- Treating proxy IRT as full psychometric IRT or full 2PL.
- Treating historical 3-model pilot files as the active MMLU panel.
- Treating legacy synthetic AUCs as independent diagnostic-validation evidence.
- Claiming decoupled synthetic validation has run.
- Claiming real-panel ranking flips, disagreement, or materiality findings.
- Claiming second-benchmark transfer evidence.
- Claiming NeurIPS readiness.

## Required Placeholders

- `[RESULT REQUIRED: real-panel ranking audit]`
- `[RESULT REQUIRED: diagnostic-disagreement audit]`
- `[RESULT REQUIRED: subject-instability audit]`
- `[RESULT REQUIRED: real-panel baselines]`
- `[RESULT REQUIRED: decoupled synthetic validation]`
- `[RESULT REQUIRED: direct/hash MMLU-Redux alignment]`
- `[RESULT REQUIRED: second benchmark real-panel audit]`
- `[RESULT REQUIRED: final paper/reviewer gate]`
