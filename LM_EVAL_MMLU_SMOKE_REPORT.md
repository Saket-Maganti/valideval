# lm-eval MMLU Smoke Report

Timestamp UTC: 2026-06-12T10:04:24Z

## Status

Smoke status: completed with a real limited MMLU subject run.

This is acquisition evidence, not a full MMLU benchmark result.

## Successful Smoke

- Model: `Qwen/Qwen2.5-0.5B-Instruct`
- Device: `mps`
- Task: `mmlu_high_school_biology`
- Limit: `25`
- Few-shot setting: `0`
- Batch size: `1`
- Wall-clock runtime: `47.25s`
- lm-eval reported evaluation time: `42.32829779200256s`
- Sample rows found: `25`
- Per-instance predictions exist: yes

Command:

```bash
lm_eval \
  --model hf \
  --model_args pretrained=Qwen/Qwen2.5-0.5B-Instruct \
  --tasks mmlu_high_school_biology \
  --num_fewshot 0 \
  --device mps \
  --batch_size 1 \
  --limit 25 \
  --log_samples \
  --output_path data/external/mmlu/lm_eval_outputs/qwen2_5_0_5b_smoke
```

Output files:

- `data/external/mmlu/lm_eval_outputs/qwen2_5_0_5b_smoke/Qwen__Qwen2.5-0.5B-Instruct/results_2026-06-12T15-22-35.587898.json`
- `data/external/mmlu/lm_eval_outputs/qwen2_5_0_5b_smoke/Qwen__Qwen2.5-0.5B-Instruct/samples_mmlu_high_school_biology_2026-06-12T15-22-35.587898.jsonl`

Sample file SHA256:

```text
df89e72705a71ed1a878dfc2b12562c513e90536f39e8fe5c07b82058fc68c45
```

## Failed Or Aborted Attempts

Attempt 1 failed before evaluation because `accelerate` was missing:

```text
ModuleNotFoundError: No module named 'accelerate'
```

Resolution: installed `accelerate` in the current Python environment.

Attempt 2 used all-subject `mmlu`, `--limit 25`, and `--batch_size auto`.
It reached scoring but stalled during auto batch-size detection on MPS and was
interrupted. No completed all-subject smoke evidence is claimed from that
attempt.

## Evidence Boundary

- The successful smoke is real lm-evaluation-harness output.
- It is limited to `mmlu_high_school_biology`.
- It does not use `examples/mmlu_subset.jsonl`.
- It does not use MMLU-Redux mock files.
- It does not establish full MMLU or MMLU-Redux validation.
