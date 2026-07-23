# GPQA Data Acquisition Report

## 1. Executive Summary

GPQA Diamond was acquired from the official GPQA GitHub repository after the official Hugging Face path remained gated in this environment.

The official archive was extracted locally, `gpqa_diamond.csv` was exported into the ValidEval local JSONL schema, and the exported item file passed input validation. No raw GPQA question text is included in this report.

The real audit remains **no-go** because no real `gpqa_open_local` cached predictions, local/open model runners, or response matrices are available yet.

## 2. Acquisition Path Attempted

1. Official Hugging Face dataset: `Idavidrein/gpqa`
2. Official GitHub fallback: `https://github.com/idavidrein/gpqa.git`

Only official sources were used. No mirror or third-party dataset copy was used.

## 3. Hugging Face Status

Status: **blocked**.

- `datasets` package: installed
- `huggingface_hub` package: installed
- `huggingface-cli`: not available on `PATH`
- `HF_TOKEN`: not set
- `HUGGING_FACE_HUB_TOKEN`: not set
- Export command reported gated dataset access for `Idavidrein/gpqa`

Recorded blocker:

```text
HF acquisition blocked: terms/token/access required
```

## 4. Official GitHub Status

Status: **succeeded**.

- Official repo URL: `https://github.com/idavidrein/gpqa.git`
- Local repo path: `data/raw/gpqa_official_repo/`
- Checked-out commit: `56686c06f5e19865c153de0fdb11be3890014df7`
- Official archive: `data/raw/gpqa_official_repo/dataset.zip`
- Extracted path: `data/raw/gpqa_official/`

The archive password was read from the official repository README and was not written into this report.

## 5. Source File Used

Source file:

```text
data/raw/gpqa_official/dataset/gpqa_diamond.csv
```

Metadata-only summary:

- Row count: 198
- Appears to be Diamond split: yes, by filename
- Required GPQA columns present: yes
- Raw row contents printed in reports: no

## 6. Export Status

Status: **passed**.

Command:

```bash
python3 -m valideval export-gpqa-diamond --source-file data/raw/gpqa_official/dataset/gpqa_diamond.csv --output data/gpqa/gpqa_diamond.jsonl
```

Exported file:

```text
data/gpqa/gpqa_diamond.jsonl
```

Export metadata:

- Item count: 198
- Domain counts: Biology 19, Chemistry 93, Physics 86
- Duplicate item ID count: 0
- Duplicate question hash count: 0
- Validation status: pass
- Report includes raw question text: no

## 7. Item Validation Status

Status: **passed**.

Validation command:

```bash
python3 -m valideval validate-benchmark-file --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl
```

Validation summary:

- JSONL parsed: yes
- Unique item IDs: 198
- Fixture-like items: 0
- Missing domain metadata: 0
- Missing license metadata: 0
- Missing provenance metadata: 0
- Fatal validation errors: 0
- Warning-only duplicate-choice item IDs: 3
- Warning-only question/answer text-overlap item IDs: 8

Question/answer text overlap is reported by item ID only for review and is not treated as a schema/alignment failure.

## 8. Dataset Hashes

- Official archive SHA-256: `461ae7329f15a3e35f8184d2dac24b990f34fdf12f366ca4062d8e6638cd08dc`
- Official Diamond CSV SHA-256: `41d1213cd7a4998605a26c2798500652572007161b3a92817ba46b35befcd305`
- Local JSONL SHA-256: `d0538cdb231be9bde946e825c9f3824899854c12b718f36a39ffad81b0b6fbd6`
- ValidEval stable item-file hash: `bd6f79c7b1b460564ae6bcec2afb86756b0071c809b042bc7613cb1896f8e88c`

## 9. Metadata Summary

- Source provenance: official GPQA GitHub repository archive
- Split/source file: `gpqa_diamond.csv`
- Exported split label: `diamond`
- Choice labels: A/B/C/D
- Answer labels: A/B/C/D
- Deterministic choice shuffling: applied by exporter
- Answer remapping after shuffling: applied by exporter
- Prompt templates changed: no
- Extraction/scoring rules changed: no
- Input-validation warning behavior changed: question/answer text overlap is now warning-only; metadata answer leakage remains fatal.

## 10. Access / Licensing Notes

The Hugging Face dataset path requires access approval in this environment. The official GitHub archive was used instead. The repository license and archive license file remain in `data/raw/gpqa_official_repo/` and `data/raw/gpqa_official/dataset/license.txt`.

Do not redistribute raw GPQA items in public reports or docs.

## 11. Do-Not-Expose Reminder

- Do not paste raw GPQA question text into Markdown reports.
- Do not paste raw answer choices into public docs.
- Do not expose archive passwords in reports.
- Do not publish local raw dataset files as ValidEval docs or examples.
- Do not interpret diagnostics from acquisition, validation, or smoke outputs.

## 12. Next Commands

Real open/local output generation is blocked until models or cached outputs are available:

```bash
python3 -m valideval check-panel --panel gpqa_open_local
python3 -m valideval generate-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_open_local --prompt-variant full --output-dir local_outputs/gpqa/full
```

For imported scored outputs:

```bash
python3 -m valideval import-outputs --input local_outputs/gpqa/full/<scored_output>.jsonl --output cache/gpqa_diamond/gpqa_open_local/predictions_full.jsonl --adapter generic-jsonl --benchmark-id gpqa_diamond --prompt-variant full
python3 -m valideval matrix-from-predictions --benchmark gpqa_diamond --panel gpqa_open_local --variant full
python3 -m valideval gpqa-go-no-go --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_open_local
```

