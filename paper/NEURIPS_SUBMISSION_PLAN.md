# NeurIPS Submission Plan

## Track Choice

Primary: NeurIPS Evaluations and Datasets.

Why: the paper studies evaluation itself as the object of scientific work. The contribution is a
framework, toolkit, validation harness, and audit protocol for deciding whether benchmark scores
support their intended construct claims.

Not primary: main track, unless the paper is reframed as a broader ML methodology paper with
substantially stronger experimental evidence.

Fallback: NeurIPS workshop or reproducibility-focused venue for an intermediate paper; JOSS or
JMLR MLOSS for software-first publication.

## Target Paper Shape

Working title:

> Validity Is Not Accuracy: Auditing What AI Benchmarks Measure

One-sentence thesis:

> Benchmark-validity diagnostics should be validated as measurement instruments before they license
> claims about what a benchmark score measures.

## Contributions

1. A measurement-validity framework for benchmark diagnostics with explicit evidence states:
   supported, weak, blocked, or not run.
2. A diagnostic-validation harness that characterizes benchmark-validity diagnostics under
   controlled flaw injection.
3. A claims-ledger and evidence-gating workflow that prevents unsupported validity claims.
4. A real HELM MMLU / MMLU-Redux stress test showing that broad proxy diagnostics do not
   automatically validate against external issue labels.
5. An offline-safe toolkit and reproducible audit artifact format for benchmark authors and
   evaluators.

## Current Paper Gap

| Section | Current state | Required work |
| --- | --- | --- |
| Abstract | placeholder | Write after final claim set is frozen. |
| Introduction | scaffold | State the problem, thesis, and contributions crisply. |
| Related work | scaffold | Add measurement validity, psychometrics, benchmark auditing, data forensics, benchmark documentation, and leaderboard uncertainty. |
| Framework | scaffold | Formalize validity profile dimensions and the no-scalar rule. |
| Toolkit | scaffold | Describe CLI, diagnostics, reports, bundles, and offline-safe execution. |
| Audit protocol | scaffold | Explain preregistration, cache-only gates, manifests, and blocked diagnostics. |
| Results | placeholder | Populate from local artifacts only. |
| Analysis | scaffold | Explain what changed relative to accuracy-only reporting. |
| Limitations | placeholder | Include GPQA restrictions, synthetic-only limits, model-panel sensitivity, corpus dependence, and missing adoption. |
| Ethics | scaffold | Add responsible use and restricted-data handling. |

## Results Package

### Include Now

- Offline toy audit as software/reproducibility demonstration.
- Synthetic validation harness summary.
- Cross-flaw specificity, held-out generator validation, false-positive/error-control, and
  materiality summaries, with mixed evidence reported explicitly.
- Build-only confirmatory-run scaffolding: `CONFIRMATORY_RUN_COMMAND_MANIFEST.md`,
  `RUNBOOK_CONFIRMATORY_SYNTHETIC_VALIDATION.md`, `BUILD_ONLY_POLISH_AUDIT.md`, report templates,
  and the static no-run `scripts/preflight_confirmatory_synthetic.py` checker.
- Build-only real-panel, calibration, power/materiality, second-benchmark, and MMLU-Redux
  direct/hash-alignment preflights, all explicitly marked as dry-run only.
- `[RESULT REQUIRED]` placeholders for synthetic-harness power, numeric calibration with
  confidence/logprob outputs, and human-reviewed real-benchmark threshold calibration.
- `[RESULT REQUIRED]` placeholders for confirmatory cross-flaw and held-out outputs until the
  future approved execution phase actually produces artifacts.
- `[RESULT REQUIRED]` placeholders for real-panel ranking, diagnostic disagreement, subject
  instability, baseline comparison, calibration/logprob analysis, power/materiality analysis, and
  second-benchmark transfer.
- Reproducibility bundle verification.
- Reviewer-risk output as evidence of overclaim hygiene.
- HELM MMLU / MMLU-Redux reported only as a weak/negative external stress test.

### Include Only If Gate Passes

- GPQA amended-v2 diagnostic interpretation.
- Shortcut, prompt-sensitivity, or variant-reliability conclusions for GPQA.
- Any GPQA model ranking claims.

### Include As Blocked Evidence

- GPQA readiness state.
- Failed or incomplete go/no-go checks.
- Diagnostics that remain unavailable under the preregistered protocol.

## Tables and Figures

Required tables:

- Diagnostic profile table: measured / blocked / not run.
- Baselines and dumb-baseline-gap table.
- Artifact provenance table: command, output path, hash source.
- Synthetic validation table: diagnostic, flaw type, credibility status, limitations.
- Real benchmark readiness table: pass/fail checks, without raw restricted item text.
- Claims ledger table: claim, artifact, allowed wording.
- Confidence intervals and uncertainty table where available.
- Human-validation and judge-reliability status table, even when coverage is missing.

Required figures:

- Framework diagram.
- Diagnostic overview figure.
- Accuracy-only vs validity-profile interpretation figure.
- Ranking sensitivity figure, if backed by local artifacts.

## Claims Allowed Today

- ValidEval is an offline-capable validity-auditing toolkit.
- The toy audit and legacy synthetic harness are reproducible from local commands.
- Current synthetic AUCs are historical wiring/sanity-check artifacts only, not independent
  diagnostic-validation evidence.
- Cross-flaw and held-out artifacts exist, but their mixed results require diagnostic-specific
  claims.
- The cross-flaw and held-out confirmatory phase is preregistered and build-ready, with execution
  intentionally deferred and no evidence-state upgrade yet.
- The toolkit reports diagnostic profiles and blocked evidence instead of one benchmark-health number.
- The GPQA amended-v2 path is a near-complete but currently blocked real-benchmark workflow.
- The MMLU-Redux result is a weak/negative external-validation stress test that demonstrates
  evidence-gating discipline.

## Claims Not Allowed Today

- GPQA is valid or invalid.
- GPQA contamination, shortcut, prompt-sensitivity, or model-ranking findings are established.
- The synthetic validation harness establishes diagnostic performance on real benchmarks.
- Current synthetic AUCs are primary positive diagnostic-validation evidence.
- Universal diagnostic generalization across flaw families or held-out generators.
- Treating the build-only command manifest, runbook, templates, or preflight checker as empirical
  confirmatory evidence.
- Treating dry-run real-panel/calibration/power/second-benchmark manifests as evidence.
- A success interpretation for MMLU-Redux external validation.
- MMLU error-detection or MMLU-Redux label-validation claims.
- The report-card health badges can be averaged into one overall benchmark-health number.

## NeurIPS Review Risks

1. Real-benchmark evidence is blocked.
2. The paper may be perceived as a software demo rather than a scientific contribution.
3. Synthetic validation may be viewed as too close to the diagnostic assumptions.
4. Restricted-data handling may make reproduction harder for reviewers.
5. The repository needs a clean public release and adoption story.

## Next Writing Tasks

1. Fill the abstract with the final allowed claims.
2. Replace `paper/sections/06_results.tex` with artifact-backed tables and no invented numbers.
3. Replace `paper/sections/08_limitations.tex` with explicit blocked-evidence limitations.
4. Add a short "Reviewer checklist" appendix or supplement.
5. Run reviewer-risk on the paper draft before any public release.
6. Follow `MASTER_LATER_RUN_PLAN.md` and `LATER_RUN_APPROVAL_CHECKLIST.md` before any future
   empirical run.
