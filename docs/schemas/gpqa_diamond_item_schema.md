# GPQA Diamond Item Schema

Artifact class: **gpqa_real_input_validation**.

ValidEval does not bundle or download GPQA Diamond. A real audit expects a local JSONL export where each line follows `schemas/gpqa_diamond_item.schema.json`.

Required fields:

- `item_id`: unique local item ID, preferably `gpqa_diamond_...`.
- `question`: non-empty question text.
- `choices`: exactly four choices labeled `A`, `B`, `C`, and `D`.
- `answer`: one of `A`, `B`, `C`, or `D`.

Recommended fields:

- `domain` or `metadata.discipline`.
- `source`: usually `gpqa`.
- `split`: `diamond`.
- `metadata.source_id`, `metadata.license`, and `metadata.provenance`.

Validation behavior:

- Duplicate item IDs, invalid answer labels, missing choices, wrong split, answer leakage, and fixture-like records block the real audit.
- Duplicate question text, duplicate answer choices, missing domain, missing license, and missing provenance are warnings.
- Reports list item IDs only where possible and do not reproduce full benchmark item text.

Command:

```bash
python3 -m valideval validate-benchmark-file --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl
```
