# ValidEval V6 S1 Leakage Seal

Gate: `S1_LEAKAGE_GUARDS_COMPLETE`

The frozen 150-target set passes all locally testable guards: unique item IDs; zero target/few-shot
exact, normalized-text, or option-aware overlap under the frozen zero-shot policy; zero
cross-benchmark exact duplicates; and zero cross-benchmark near-duplicate candidates at the
registered 0.90 similarity screen. Prompt templates and output/config paths contain no diagnostic
class labels.

Tests enforce that renderer, generator, and extractor inputs reject gold-bearing fields. Only the
scorer receives a parsed prediction and the private gold value. Generation and extraction failures
remain distinct from parsed-but-incorrect answers.

Machine-readable results are in `results/leakage/s1_leakage_checks_v6.json` and candidates in
`results/leakage/s1_overlap_candidates_v6.csv`.

This seal does not establish that benchmark content was absent from any checkpoint's pretraining
data. That remains an unresolved external-validity limitation.
