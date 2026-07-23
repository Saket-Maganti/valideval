# Core Diagnostics

These diagnostics are cheap offline screens for possible validity threats. They do not prove a benchmark is valid or invalid. They identify evidence consistent with artifacts that should be inspected under a declared protocol.

## Heuristic baselines

Threats: answer priors, lexical shortcuts, option-length artifacts, metadata leakage, arithmetic templates, and context-copy shortcuts.

Limitations: shallow baselines are intentionally weak and deterministic. A high baseline score is a possible validity threat, not proof that real models use the same shortcut.

## Answer distribution

Threats: label imbalance, answer-position bias, answer-length bias, repeated phrase artifacts, negation cues, all/none-of-the-above artifacts, and distractor-label imbalance.

Limitations: static distribution metrics do not establish model behavior. Human review is needed to judge whether a cue is construct-relevant or accidental.

## Distractor quality

Threats: dead distractors, implausible distractors, distractors selected by no model, distractors confusing even for stronger models, and low distractor discrimination.

Limitations: selection frequencies are conditional on the model panel and prompt variant. Lexical similarity is only a proxy for semantic plausibility.

## Shortcut retention

Threats: retained performance under question-only, choices-only, context-removed, context-shuffled, label-prior-only, metadata-only, answer-length-only, format-only, irrelevant-context, or retrieval-only ablations.

Limitations: retained performance can reflect legitimate construct-relevant information in the remaining fields. Low full-condition performance makes retention unstable.

## Prompt sensitivity

Threats: rank instability, prompt-template-specific score shifts, output-format failures, and robustness gaps across zero-shot, few-shot, JSON-only, direct-answer, randomized-order, terse, and verbose prompts.

Limitations: the estimate only covers templates implemented by the benchmark adapter. Prompt robustness is not a substitute for a full evaluation protocol.

## Extraction robustness

Threats: strict vs lenient score shifts, final-answer extraction disagreement, invalid outputs, refusals, and item-level scoring ambiguity.

Limitations: implemented extractors are audit probes. Human scoring-rule validation is still required for ambiguous answers, aliases, and numeric tolerance policies.

## Reliability v2

Threats: low perturbation reliability, prompt-format rank instability, low item stability, and fragile paired score differences.

Limitations: seed/test-retest and scorer reliability require additional cached matrices or independent scorer outputs. Missing components are reported as unavailable rather than invented.
