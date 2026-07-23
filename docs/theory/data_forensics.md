# Data Forensics

Data forensics audits benchmark items for evidence consistent with contamination,
redundancy, split leakage, temporal staleness, and missing provenance. These
signals are corpus-dependent and metadata-dependent. They do not prove that a
benchmark is clean, contaminated, valid, or invalid.

## Signals

Each signal reports one of:

- `measured`
- `unavailable`
- `not_implemented`
- `insufficient_corpus`

Risk levels are categorical:

- `no local evidence found`
- `low local evidence`
- `moderate local evidence`
- `high local evidence`
- `unknown/unmeasured`
- `insufficient corpus`

The categories should be read per signal. They must not be combined into one
final contamination truth or a single validity score.

## Local Corpus Overlap

`python3 -m valideval forensics overlap --benchmark toy_mcq --corpus examples/toy_corpus/`
searches local `.txt`, `.md`, `.jsonl`, `.json`, and `.csv` files. The scanner
reports exact item match, question match, answer-text match, n-gram overlap,
longest common substring, top matching document, and item suspiciousness.

No local overlap means only that no overlap was found in the supplied corpus
under this protocol.

## Internal Duplicates

The duplicate report checks exact prompts, near lexical duplicates, shared
contexts, shared source documents, shared templates, answer-text duplicates, and
rationale duplicates. Embedding-backed semantic duplicate detection is reported
as unavailable unless explicitly configured in a future extension.

## Split Leakage

When items include `metadata.split`, the split-leakage report compares split
pairs for exact and near overlap, shared source documents, shared templates,
entity overlap, answer distributions, difficulty distributions, and temporal
split violations.

## Temporal Validity

Temporal validity uses item text and metadata only. It detects relative/current
phrasing and metadata risks such as missing `last_verified_date` for
time-sensitive items. Web verification is unavailable in the offline toy audit,
so the system says so instead of guessing current facts.

## Provenance

Benchmark items may include:

- `source_url`
- `source_document`
- `snapshot`
- `license`
- `created_by`
- `generated_by_model`
- `human_verified`
- `appears_in_paper_examples`
- `appears_in_readme`
- `appears_in_hf_preview`

The provenance completeness report identifies missing fields. Missing provenance
is an interpretability risk, not contamination evidence by itself.

## Audit Manifest

Each audit writes `results/{benchmark}/manifest.json` with dataset ID, item
count, split counts, item ID hash, item text hash, benchmark config hash, scorer
hash, prompt template hash, and diagnostic config hash.
