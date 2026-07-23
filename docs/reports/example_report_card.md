# Validity Report Card: toy_mcq

## Claimed construct

toy reasoning under controlled artifacts

## Diagnostics run

answer_distribution, baselines, calibration, data_forensics, dif, distractor_quality, extraction_robustness, irt, power, prompt_sensitivity, ranking_uncertainty, redundancy, reliability, saturation, shortcut

## Provenance

- Benchmark: toy_mcq
- Panel: mock
- Items: 36 synthetic MCQ items
- Prompt variants: full, question_only, choices_only, context_removed, context_shuffled, label_prior_only, metadata_only, answer_length_only, format_only, irrelevant_context, retrieval_only, zero_shot_direct, few_shot, chain_of_thought_allowed, direct_answer_only, json_only, answer_letter_only, randomized_option_order, alternate_system_prompt, no_system_prompt, terse_instructions, verbose_instructions
- Intended use: offline software validation of the audit pipeline.

## Executive summary

This report summarizes evidence consistent with specific measurement threats. It does not assign a single validity score and does not prove that the benchmark is valid or invalid in general.

## Shallow baselines

- Best shallow baseline: metadata_artifact_baseline at 0.972
- Best strong-model score: 0.611
- Dumb Baseline Gap: -0.361

## Answer distribution

- Label counts: {'A': 8, 'B': 14, 'C': 8, 'D': 6}
- Longest-option correctness fraction: 0.222
- Repeated-phrase artifact item count: 0

## Shortcut validity

- Full-condition score: 0.424
- High retained performance under ablation suggests possible shortcut availability for: question_only, context_removed, context_shuffled, label_prior_only, irrelevant_context.
- answer_length_only: retained 0.525, drop 0.201
- choices_only: retained 0.549, drop 0.191
- context_removed: retained 0.713, drop 0.122
- context_shuffled: retained 1.008, drop -0.003
- format_only: retained 0.607, drop 0.167
- irrelevant_context: retained 0.721, drop 0.118
- label_prior_only: retained 1.787, drop -0.333
- metadata_only: retained 0.582, drop 0.177
- question_only: retained 0.754, drop 0.104
- retrieval_only: retained 0.533, drop 0.198

## Distractor quality

- Dead distractor fraction: 0.430
- Confusing distractor count: 14
- CSV artifact: results/toy_mcq/mock/distractor_quality.csv

## Prompt sensitivity

- Prompt robustness coefficient: 0.523
- Prompt-specific ranking flips: 28
- Prompt templates evaluated: 11

## Extraction robustness

- Strict vs lenient score shift: 0.076
- Invalid output rate: 0.000
- Extraction disagreement rate: 0.000

## Human validation

Not run. No human-validation coverage claim should be made.

## Judge reliability

Not run. Judge reliability is unmeasured.

## Scoring ambiguity

Not run. Scoring ambiguity requires human/judge artifacts.

## Reliability

- Benchmark-level reliability estimate: 0.427
- Mean perturbation sensitivity: 0.139

## Saturation

- Category: moderate
- Fraction solved by all top models: 0.528
- Effective discriminating item count: 27
- Ceiling proximity: 0.611

## Power analysis

- Effective item count: 29.000
- Minimum detectable difference: 0.254
- Do not overinterpret within points: 25.434

## IRT item analysis

- Near-zero discrimination fraction: 0.306
- Negative-discrimination item count: 4
- Example high-information subset k=5: toy_006, toy_021, toy_026, toy_029, toy_008

## Ranking comparison

- Raw accuracy order: context_aware, format_fragile, noisy_strong, shortcut_exploiter, majority_label, keyword_matcher, always_a, noisy_weak
- Latent-ability proxy order: context_aware, format_fragile, noisy_strong, shortcut_exploiter, majority_label, keyword_matcher, always_a, noisy_weak
- Rank correlation, raw vs proxy: 1.000
- Interpretation: this is a conditional ranking comparison under the diagnostic protocol, not a corrected leaderboard.

## Advanced psychometrics

- DIF suspicious item count: 21
- Calibration ECE: 0.507
- Abstention coverage: 1.000
- Redundancy fraction: 0.194
- Top-k bootstrap stability: 0.853

## Data forensics

- Local corpus searched: none supplied
- Web searched: False
- Not searched: paid APIs, remote web verification, closed model training corpora
- Dataset hash item count: 36
- Interpretation: these are corpus-dependent local signals, not a single contamination truth.

## Contamination risk signals

- Corpus overlap signal: unavailable / unknown/unmeasured
- Documents searched: n/a
- Exact-match rate: n/a
- Question-match rate: n/a
- Suspicious item rate: n/a
- High-suspiciousness local item list: none

## Duplicate/redundancy analysis

- Internal duplicate signal: measured / high local evidence
- Duplicate fraction: 0.278
- Effective independent item count: 26
- Exact duplicate cluster sizes: []
- Near duplicate cluster sizes: [3, 2, 2]
- Semantic duplicate scan: unavailable

## Split validity

- Split leakage signal: unavailable / unknown/unmeasured
- Split counts: {}
- High-risk item list: none
- Temporal split violations: none

## Temporal validity

- Temporal validity signal: measured / low local evidence
- Items with temporal warnings: toy_005
- Temporal warning rate: 0.028
- Web verification: unavailable for offline toy audits.

## Provenance completeness

- Provenance signal: measured / high local evidence
- Fully complete item fraction: 0.000
- Missing-field counts: {'appears_in_hf_preview': 36, 'appears_in_paper_examples': 36, 'appears_in_readme': 36, 'created_by': 36, 'generated_by_model': 36, 'human_verified': 36, 'license': 36, 'snapshot': 36, 'source_document': 36, 'source_url': 36}

## Coverage profile

Not run. Content coverage requires tag metadata and, ideally, human review.

## Diagnostic-sensitive interpretation

Evidence should be interpreted by diagnostic profile. For this run, ranking and score interpretations are conditional on the mock panel, prompt variants, and synthetic toy items.

## Misuse warnings

- Do not claim broad reasoning beyond the claimed construct: toy reasoning under controlled artifacts.
- Do not treat the validity profile as a single scalar score.
- Do not overinterpret model differences within approximately 25.43 percentage points under this protocol.
- Do not rank top models as meaningfully separated when the audited panel shows saturation evidence.
- Do not compare model rankings across prompt templates without reporting prompt sensitivity.
- Do not compare across scorer or extractor configs without disclosure.
- Do not claim contamination-clean status from an unscanned corpus.
- Do not use time-sensitive items for current factuality claims without fresh verification.

## Benchmark author checklist

- Construct defined: complete (toy reasoning under controlled artifacts)
- Construct-critical fields identified: complete (prompt, context, choices)
- Sources documented: needs_review (provenance completeness=0.0)
- Contamination scan: complete (data_forensics)
- Duplicates checked: complete (data_forensics)
- Shortcut diagnostic: complete (shortcut)
- IRT/item quality: complete (irt)
- Reliability: complete (reliability)
- Scoring validation: complete (extraction_robustness)
- Human agreement: needs_review (not yet measured)
- Saturation: complete (saturation)
- Intended/non-intended use documented: needs_review (validity card recommended)
- Version/hash recorded: complete (results/{benchmark}/manifest.json)

## Recommended benchmark-author actions

- Inspect items with high ablated performance or low/negative discrimination.
- Compare strong-model results with shallow baseline results before interpreting rankings.
- Review dead or highly confusing distractors before making item-retention decisions.
- Check extraction-rule sensitivity when strict and lenient scoring disagree.
- Use saturation and power diagnostics before interpreting small model-score gaps.
- Verify construct tags and construct-critical fields with human benchmark authors.
- Treat IRT-selected subsets as audit aids, not replacements for substantive review.

## Limitations

- The toy benchmark is synthetic and intended for pipeline validation.
- Mock model behavior is deterministic and does not represent real model capability.
- IRT estimates are layered proxy/Rasch/uncertainty outputs and become fragile with small model panels.
- Synthetic toy items are intended for software validation, not empirical model claims.
- **answer_distribution:** Static answer-distribution diagnostics identify possible artifacts but do not establish model use of those artifacts.
- **baselines:** The baseline zoo is intentionally shallow and deterministic; it is a screen for artifacts, not an empirical model panel.
- **calibration:** Calibration metrics require confidence or logprob values; proxy consistency is only a fallback signal.
- **data_forensics:** Forensics signals are local, corpus-dependent evidence and must not be read as proof of contamination or cleanliness.
- **dif:** DIF-like diagnostics require meaningful model-group metadata and sufficient models per group.
- **distractor_quality:** Distractor selection frequencies are conditional on the available model panel and prompt variant.
- **extraction_robustness:** Extraction robustness is based on cached raw outputs and implemented extractors; it does not replace human scoring-rule validation.
- **irt:** IRT v2 uses layered estimates with graceful fallback; proxy, Rasch, and 2PL-proxy values should not be treated as ground truth.
- **power:** Power estimates assume item independence after a simple redundancy adjustment; they are planning aids, not definitive uncertainty bounds.
- **prompt_sensitivity:** Prompt-sensitivity estimates are conditional on the prompt templates implemented by the benchmark adapter.
- **ranking_uncertainty:** Rank uncertainty is conditional on the observed item set and bootstrap resampling assumptions.
- **redundancy:** Near-duplicate detection uses lexical similarity and simple template rules; manual review is required.
- **reliability:** Reliability v2 metrics are based on available cached variants; seed and scorer reliability require additional matrices or scorer outputs.
- **saturation:** Saturation is conditional on the audited model panel; historical saturation requires comparable audit snapshots.

## Warnings

- **baselines:** Baselines are heuristic probes; high baseline performance is a possible validity threat, not proof of invalidity.
- **baselines:** No training split was available; this uses question-only lexical overlap.
- **calibration:** No confidence/logprob values were available; numeric calibration output requires confidence outputs.
- **data_forensics:** Contamination scans are corpus-dependent evidence, not proof of cleanliness.
- **data_forensics:** Do not combine these signals into a single final contamination truth.
- **data_forensics:** No local corpus was supplied; external overlap was not measured.
- **data_forensics:** Duplicate detection uses local lexical/template signals; semantic duplicates require embeddings.
- **data_forensics:** Split leakage was not measured because fewer than two splits were present.
- **data_forensics:** Temporal validity is based on item text and metadata only; web verification was not performed.
- **data_forensics:** Missing provenance fields reduce audit interpretability but are not contamination evidence by themselves.
- **dif:** DIF here means model-family benchmark behavior, not human demographic fairness.
- **dif:** Some items show group-conditioned residual differences; evidence is consistent with possible model-group DIF under this panel.
- **extraction_robustness:** Lenient extraction changes scores relative to strict extraction; inspect scoring-rule robustness.
- **irt:** 2PL values are proxy slopes from item-total discrimination, not a full parametric 2PL fit.
- **irt:** Construct tag 'ambiguous_scoring_risk' has only 2 item(s); skill estimates are unstable.
- **irt:** Construct tag 'biology' has only 2 item(s); skill estimates are unstable.
- **irt:** Construct tag 'decision_reasoning' has only 1 item(s); skill estimates are unstable.
- **irt:** Construct tag 'duplicate_near_duplicate' has only 2 item(s); skill estimates are unstable.
- **irt:** Construct tag 'logical_reasoning' has only 2 item(s); skill estimates are unstable.
- **irt:** Construct tag 'ordering' has only 2 item(s); skill estimates are unstable.
- **irt:** Construct tag 'pattern_reasoning' has only 1 item(s); skill estimates are unstable.
- **irt:** Construct tag 'science_reasoning' has only 2 item(s); skill estimates are unstable.
- **irt:** Construct tag 'scoring_validity' has only 1 item(s); skill estimates are unstable.
- **irt:** Construct tag 'too_easy' has only 2 item(s); skill estimates are unstable.
- **irt:** Construct tag 'vocabulary' has only 2 item(s); skill estimates are unstable.
- **irt:** Negative-discrimination items are evidence consistent with item-quality threats under this model panel.
- **irt:** Near-zero discrimination items may contribute little ranking information under this panel.
- **power:** Do not overinterpret model score differences within approximately 25.43 percentage points under this protocol.
- **prompt_sensitivity:** Prompt-specific ranking flips were observed; evidence is consistent with prompt-format sensitivity under this panel.
- **redundancy:** Duplicate or near-duplicate clusters were detected; evidence is consistent with redundancy affecting effective item count.
- **reliability:** Seed/test-retest reliability was not estimated because no full_seed_* matrices were available.
- **saturation:** Evidence is consistent with moderate benchmark saturation under this model panel.
- **shortcut:** High retained performance under ablation suggests possible shortcut availability for: question_only, context_removed, context_shuffled, label_prior_only, irrelevant_context.

## Reproduction

```bash
python3 -m valideval matrices --benchmark toy_mcq --panel mock
python3 -m valideval audit --benchmark toy_mcq --panel mock --diagnostics all-core
python3 -m valideval report --benchmark toy_mcq --panel mock
```
