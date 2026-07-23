# Validity Framework

Benchmark accuracy is evidence of performance on a set of items. Validity asks whether that evidence supports the intended interpretation: that the benchmark measures the claimed construct.

## Construct Validity

Construct validity concerns whether item content, scoring, model behavior, and interpretations align with the target capability. In `valideval`, construct claims are represented through tags, construct-critical fields, prompt variants, and diagnostic evidence.

## Reliability

Reliability concerns stability. If model rankings swing under meaning-preserving perturbations, prompt variants, or scoring seeds, the benchmark may provide weak evidence for fine-grained comparisons.

## Shortcuts

Shortcuts occur when models can score well using non-construct cues, such as answer priors, label artifacts, or superficial lexical hints. The shortcut diagnostic measures retained performance after construct-critical information is removed or corrupted. High retained performance is evidence consistent with shortcut availability, not proof of shortcut use.

## Contamination

Contamination is a validity threat when benchmark items appear in training or evaluation-tuning data. Exact and n-gram overlap can flag suspicious items, but absence of overlap is not proof of cleanliness.

## Item Quality

Items with near-zero or negative discrimination may contribute little to model ranking, or may reward the wrong behavior under the current panel. The IRT diagnostic reports difficulty, discrimination, and high-information subsets as audit aids.

## Coverage

Content validity depends on whether items cover the claimed construct. Tag entropy and missing-tag checks expose metadata gaps, but final coverage judgments require human review.

## Criterion And Consequential Validity

Predictive validity requires external outcomes. Consequential validity and Goodhart risk require longitudinal or intervention evidence. `valideval` scaffolds these diagnostics but does not invent results without the required inputs.

## Multidimensional Reporting

Validity is not a single scalar. Report cards present a profile of evidence, warnings, limitations, and recommended actions.

