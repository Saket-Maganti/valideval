# Benchmark Repair

`valideval` repair is advisory. It helps benchmark authors inspect items,
construct cleaner candidate subsets, and document evidence. It does not prove
that a removed item is bad, that a retained item is valid, or that a repaired
subset is the correct benchmark.

## Item Forensics Table

`python3 -m valideval repair --benchmark toy_mcq --panel mock --policy conservative`
writes `results/{benchmark}/{panel}/item_forensics.csv`. The table merges local
diagnostic evidence into item-level fields:

- difficulty and discrimination
- negative discrimination and too easy/hard flags
- shortcut suspiciousness
- prompt and scorer instability
- duplicate cluster and local contamination overlap
- temporal risk and missing provenance fraction
- coverage tag and coverage-critical flag
- human ambiguity flag
- recommendation and confidence level

Recommendations are `keep`, `review`, `rewrite`, `remove`, `human validate`, or
`coverage-critical keep`.

## Policies

Repair policies are deterministic and offline-safe:

- `conservative`: remove clear local item-quality threats while preserving
  coverage-critical items.
- `stable`: prefer prompt/scorer-stable items and remove duplicates.
- `low_contamination_risk`: prefer items without high local overlap evidence.
- `high_information`: keep higher-discrimination items first while preserving
  coverage-critical items.

Coverage-critical items are retained when removing them would erase a construct
tag from the candidate subset. These items still appear in the diff as
coverage-critical overrides when they also show local risk evidence.

## Repair Report

The repair command writes:

- `item_forensics.csv`
- `repair_diff.json`
- `repair_report.md`

The report compares original and repaired candidate subsets by item count,
ranking fidelity, coverage change, discrimination change, duplicate reduction,
shortcut-risk reduction, reliability change, approximate CI change, and removed
items by reason.

## Validity Cards and Certificates

`python3 -m valideval card render --benchmark toy_mcq --panel mock` writes a
Validity Card JSON and Markdown artifact. The card records identity, hashes,
construct, intended and non-intended uses, sources, scoring, model panel,
diagnostics, reliability, item quality, contamination/provenance, coverage,
human validation status, known threats, recommended use, misuse warnings, and
reproduction commands.

When human-validation artifacts exist under `results/{benchmark}/{panel}/human/`,
the card records annotated item counts, agreement metrics, judge-human
agreement, and ambiguity rate. Missing artifacts are reported as unknown rather
than inferred.

`python3 -m valideval certificate issue --benchmark toy_mcq --panel mock` writes
an evidence profile / audit completeness profile. Profiles describe checks run
and evidence recorded, not scalar validity scores or quality grades:

- insufficient_evidence: required audit artifacts are missing or too sparse.
- metadata_and_provenance_recorded: metadata, reproducible card, basic provenance.
- core_diagnostics_recorded: shortcut, IRT/item quality, reliability.
- human_review_evidence_recorded: contamination/provenance, judge reliability, human-validated subset.
- external_validation_evidence_recorded: predictive validity, Goodhart/consequential validity, external replication.

Each dimension is reported separately as `strong`, `moderate`, `weak`,
`threatened`, `unknown`, `not applicable`, or `insufficient evidence`.

## Evidence Tracking

`python3 -m valideval evidence-matrix --benchmark toy_mcq --panel mock` writes a
claim-to-evidence matrix. It connects interpretive claims to diagnostics and
statuses so validity theory is traceable to concrete local evidence.
