# NeurIPS Readiness Plan

## Target

Primary target: NeurIPS Evaluations and Datasets track, next available cycle.

Rationale: the project's strongest contribution is not a new leaderboard result. It is a
benchmark-evaluation methodology and software artifact for auditing whether benchmark scores
support their intended construct interpretations.

Fallback targets:

- NeurIPS workshop or MLRC-style reproducibility venue if the main Evaluations and Datasets
  package is not ready.
- JOSS or JMLR MLOSS for a software-first publication if the real-benchmark evidence remains
  blocked.

## Current Readiness

| Area | Status | Evidence | NeurIPS risk |
| --- | --- | --- | --- |
| Software artifact | strong | `132` tests pass; `ruff check .` passes; toy audit runs offline | low |
| Reproducibility | strong | verified toy bundle with environment capture and manifest hashes | low |
| Diagnostic validation | moderate to strong | synthetic validation harness produces summary artifacts | medium: synthetic evidence is not real-benchmark evidence |
| Paper scaffold | weak | `paper/main.tex` exists but major sections are placeholders | high |
| Real-benchmark case study | blocked | GPQA amended-v2 go/no-go is currently `no_go` | high |
| Public release posture | incomplete | local checkout has no visible git metadata in this environment | high |
| Adoption evidence | incomplete | no external users or independent replication recorded | medium |

## Non-Negotiable Publication Boundary

- Do not claim GPQA validity findings while go/no-go is `no_go`.
- Do not print raw GPQA item text in papers, docs, issue threads, public artifacts, or bundles.
- Do not frame any diagnostic as proof of global benchmark validity or invalidity.
- Do not collapse the validity profile into one scalar score.
- Do not use paid APIs as required dependencies for primary results.

## NeurIPS Story

Proposed title:

> Validity Is Not Accuracy: Auditing What AI Benchmarks Measure

Core claim:

> Benchmark evaluation should report a multidimensional validity profile that separates score
> accuracy from evidence about construct coverage, shortcut availability, item quality,
> contamination/provenance, scoring stability, saturation, and ranking sensitivity.

What the paper should establish:

- The toolkit operationalizes a principled validity-auditing workflow.
- The diagnostics are reproducible and can be validated on synthetic flaws.
- The workflow prevents overclaiming by making blocked evidence explicit.
- At least one real-benchmark case study can be audited without relying on paid APIs.

What the paper must not claim:

- That one audit settles benchmark quality in general.
- That GPQA has a definitive validity profile unless its gate passes.
- That a diagnostic-sensitive ranking is a final ordering.
- That local data-forensics absence establishes cleanliness.

## Evidence Gates

Run the combined readiness reporter before any submission-status update:

```bash
python3 -m valideval neurips-readiness --benchmark toy_mcq --panel mock
```

Use `--strict` in CI or release scripts when a non-zero exit should block packaging.

### Gate A: Software Artifact

Required commands:

```bash
python3 -m pytest -q
python3 -m ruff check .
python3 -m valideval doctor --benchmark toy_mcq --panel mock --strict
python3 -m valideval bundle --benchmark toy_mcq --panel mock
python3 -m valideval verify-bundle bundles/toy_mcq_mock_bundle
```

Current status: pass.

Reviewer-facing disclosures to preserve in the final package:

- Baselines: report shallow baselines and dumb-baseline gap wherever model scores are discussed.
- Confidence intervals: include bootstrap intervals or uncertainty fields where the diagnostic
  provides them; otherwise label uncertainty as unavailable.
- Human validation: report annotation, agreement, judge-reliability, and adjudication coverage as
  measured, missing, or not applicable.

### Gate B: Synthetic Detector Validation

Required commands:

```bash
python3 -m valideval validate-diagnostics --config configs/validation/all_sweeps.yaml
python3 -m valideval validation-report --report-dir validation_reports
python3 -m valideval validation-summary --report-dir validation_reports
```

Current status: pass, but use cautious wording. Synthetic detector validation supports detector
behavior under controlled generators only.

### Gate C: Real Benchmark Case Study

Preferred path: GPQA amended-v2 compliant local panel.

Required commands:

```bash
python3 -m valideval gpqa-go-no-go \
  --benchmark gpqa_diamond \
  --items data/gpqa/gpqa_diamond.jsonl \
  --panel gpqa_minimal_open_local_amended_v2_compliant \
  --config configs/audits/gpqa_diamond_amended_v2.yaml
```

Current status: blocked.

Current blocker:

- `question_only_answer_only_v2` per-model extraction success for
  `qwen2.5:1.5b-instruct` is below the preregistered threshold.

Allowed paths forward:

1. Preserve the current outputs as protocol-development artifacts and replace the failing model
   only under a documented extraction-compliance replacement policy.
2. Create a formal threshold or per-variant amendment before interpretation, with reviewer-risk
   review and explicit rationale.
3. Keep GPQA as a blocked-readiness case study and add a second real benchmark whose inputs and
   outputs pass all gates.

Disallowed paths:

- Interpreting shortcut, prompt-sensitivity, or variant-reliability diagnostics while the gate is
  `no_go`.
- Relaxing thresholds after seeing diagnostic results.
- Selecting replacement models based on accuracy, ranking, or item-quality outcomes.

### Gate D: Paper and Review Package

Required artifacts:

- NeurIPS-format paper with filled abstract, method, experiments, limitations, ethics, and
  reproducibility sections.
- Claims ledger with every claim tied to an artifact path.
- Anonymous or public code release plan, depending on the target year and submission policy.
- Reproducibility bundle small enough for review.
- Reviewer-risk report with no high-risk findings.

Current status: blocked by incomplete paper text and real-benchmark gate.

## Work Plan

### Phase 1: Stabilize the NeurIPS Package

- Freeze the paper thesis and contribution list.
- Convert `paper/main.tex` to NeurIPS-compatible formatting when targeting a specific cycle.
- Fill the results section using only local artifacts.
- Add a table that separates `measured`, `blocked`, and `not run` diagnostics.
- Add an ablation showing why validity profiles should not be collapsed into accuracy.

### Phase 2: Resolve Real-Benchmark Evidence

- Decide whether GPQA remains the primary case study.
- If GPQA remains primary, resolve the extraction-compliance blocker before any new interpretation.
- If GPQA remains blocked, choose a public/open real benchmark case study that can be distributed
  safely and audited end-to-end.
- Preserve all blocked diagnostics in the paper rather than silently dropping them.

### Phase 3: Strengthen Reviewer Defensibility

- Run reviewer-risk on every narrative report and the paper draft.
- Add independent reproduction instructions from a clean checkout.
- Add a table mapping each result to the command that produced it.
- Add failure-mode discussion for diagnostics that are prototype-only or synthetic-only.
- Add responsible use language for benchmark audits and restricted datasets.

### Phase 4: Submission Packaging

- Create a release tag and archive.
- Produce a sanitized bundle for reviewers.
- Verify that no raw restricted benchmark item text is copied into public-facing docs or bundles.
- Prepare an OpenReview-ready abstract and contribution checklist.
- Prepare a one-page response plan for likely reviewer concerns.

## Likely Reviewer Concerns

| Concern | Response needed |
| --- | --- |
| "This is just a software toolkit." | Show scientific contribution: validity profile formalization, diagnostic taxonomy, synthetic validation, real-benchmark gate behavior. |
| "Synthetic validation is not enough." | Include a passing real-benchmark case study or explicitly frame synthetic validation as detector validation only. |
| "Diagnostics are heuristic." | Report validated-vs-experimental status, materiality, multiplicity, and failure modes. |
| "Why no single benchmark-health number?" | Argue from measurement validity: different threats affect different interpretations and should not be averaged. |
| "GPQA results are cherry-picked." | Use preregistration, cache-only execution, manifest hashes, and blocked diagnostics. |
| "Restricted data cannot be reviewed." | Provide metadata-only artifacts, hashes, schema validation, and instructions for licensed local reproduction. |

## Definition of NeurIPS-Ready

The project is NeurIPS-ready only when:

- The paper makes a clear evaluation-science contribution.
- All empirical claims are backed by local artifact paths.
- At least one real benchmark passes its preregistered readiness gate.
- Reviewer-risk reports no high-severity overclaim or disclosure gaps.
- Reproduction works from a clean checkout without paid APIs.
- Restricted benchmark content remains sanitized in public artifacts.
