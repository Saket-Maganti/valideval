# Human Validation and Judge Reliability

Human validation is scoring-validity evidence, not a replacement for validity judgment. It helps answer whether model outputs, rubrics, judge prompts, and scoring adapters support the claimed interpretation under a documented protocol.

## Annotation Packets

`python3 -m valideval human packet --benchmark toy_mcq --panel mock --sample-size 100` writes:

- `results/{benchmark}/{panel}/human/items.jsonl`
- `guidelines.md`
- `rubric.md`
- `manifest.json`

Sampling strategies include random, high-disagreement, low-discrimination, shortcut-suspicious, scorer-sensitive, coverage-balanced, and ranking-critical. Strategy-specific sampling depends on local cached artifacts when available; missing artifacts are reported as limitations rather than guessed.

## Import and Agreement

`python3 -m valideval human import --path annotations.csv` validates CSV or JSONL annotations. It checks required fields, anonymized annotator IDs, labels, confidence values, malformed rows, duplicates, and known packet item/task IDs when a packet exists.

`python3 -m valideval human agreement` computes raw agreement, pairwise Cohen's kappa, a Fleiss-style multi-rater kappa, bootstrap confidence intervals, confusion matrices, agreement by tag/item type/model, and ambiguity rate. Krippendorff's alpha is scaffolded as not implemented.

## Judge Reliability

`python3 -m valideval human judge` runs deterministic local judge variants:

- strict
- lenient
- regex
- mock

The suite reports judge-human agreement when human labels are available, inter-judge agreement, judge variance, answer-length/verbosity/refusal bias probes, and prompt-sensitivity availability. Optional LLM judges are not required and remain unavailable in offline toy workflows.

## Ambiguity and Adjudication

`python3 -m valideval human ambiguity` exports `scoring_ambiguity.csv` for human disagreement, judge disagreement, strict/lenient disagreement, multiple accepted answers, missing aliases, underspecified rubrics, ambiguous contexts, and possible gold-label conflicts.

`python3 -m valideval human adjudication` writes review queues for low agreement, high-confidence disagreement, judge-human mismatch, and ranking-critical items when available.

## Interpretation

Human labels are not perfect ground truth. They are evidence consistent with the scoring rule under the annotation protocol. Judge agreement is also protocol evidence; it does not prove that a scorer measures the intended construct. Report cards and certificates include human/judge evidence as separate dimensions and do not average them into one score.
