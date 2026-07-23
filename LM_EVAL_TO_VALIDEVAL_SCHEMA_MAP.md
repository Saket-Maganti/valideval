# lm-eval To ValidEval Schema Map

This is a parser/acquisition bridge only. It does not create real MMLU evidence by itself.

## ValidEval Canonical Wide Prediction Row

`import-published-details` normalizes local prediction details to JSONL rows with:

| Field | Required | Meaning |
|---|---:|---|
| `benchmark` | yes | Benchmark family, e.g. `mmlu`. |
| `subset` | yes | Task/subject, e.g. `mmlu_high_school_biology`. |
| `item_id` | yes | Stable per-instance id. |
| `model_id` | yes | Model/run identifier. |
| `prediction` | yes | Model answer after lm-eval filtering. |
| `gold` | yes | Reference answer/target. |
| `correct` | recommended | Boolean correctness, usually from `acc` or `exact_match`. |
| `source` | yes | Provenance string, e.g. `lm_eval:log_samples`. |
| `source_file` | yes | Local file path for the source sample file. |
| `metadata` | no | Hashes, task details, and non-text provenance. |

`matrix-from-wide-predictions` then pivots these rows into:

- rows: `model_id`
- columns: `subset::item_id`
- values: `correct` as `0.0` or `1.0`

Duplicate `(model_id, subset, item_id)` rows are dropped by first-seen key during
lm-eval import and reported in the mapping summary. Matrix construction still
blocks if duplicate rows are present in the final normalized prediction file.

## lm-evaluation-harness Sample Fields

The `lm_eval` / `lm_eval_dir` / `lm_eval_jsonl` importer maps common
`--log_samples` fields:

| lm-eval field | ValidEval field |
|---|---|
| `task`, `task_name`, filename `samples_<task>.jsonl` | `subset` |
| `doc_id`, `item_id`, `sample_id`, `id`, `idx` | `item_id` |
| companion `results_*.json` `model_name`, then containing folder | `model_id` |
| `filtered_resps` choice loglikelihoods | `prediction` by argmax, mapped to `A`/`B`/`C`/`D` |
| fallback `resps`, `prediction`, `pred`, `answer` | `prediction` |
| numeric `target` such as `"0"` | `gold` mapped to `A` |
| `target`, `gold`, `correct_answer`, `label` | fallback `gold` |
| `doc.answer`, `doc.answer_key`, `doc.label` | fallback `gold` |
| `acc`, `exact_match`, `correct`, `is_correct` | `correct` |
| `metrics.acc`, `metrics.exact_match`, `metrics.correct` | fallback `correct` |
| `doc_hash`, `prompt_hash`, `target_hash`, choice scores, other non-text keys | `metadata` |

## Privacy / Evidence Boundary

Prompt and document text fields are discarded by default:

- `doc`
- `arguments`
- `prompt`
- `input`
- `ctx`
- `question`

Use `--include-text` only for private debugging. Do not include text-bearing artifacts in a public
packet unless licensing and privacy are explicitly cleared.
