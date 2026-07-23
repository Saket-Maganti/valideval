# ValidEval V6 Controlled GPU Smoke Runbook

## 1. Purpose and boundary

This run exercises loading, prompting, extraction, resume, merge, packaging, and import for the
frozen S1 panel. Every result is `ENGINEERING_ONLY`. It does not establish benchmark validity,
scientific panel adequacy, model rankings, generalization, or absence of pretraining contamination.

## 2. Required source

- Baseline: `f7bdfda1676995ffda356c15884a3d10cda6b80b`
- Baseline tag: `valideval-v5-pre-execution`
- Required execution tag: `valideval-v6-controlled-gpu-smoke-ready`

Resolve the final SHA locally:

```bash
git rev-parse valideval-v6-controlled-gpu-smoke-ready^{commit}
git status --short
```

The second command must be empty. Build the upload without raw data or caches:

```bash
git archive --format=zip \
  --output valideval-v6-controlled-gpu-smoke-ready.zip \
  valideval-v6-controlled-gpu-smoke-ready
```

Upload that ZIP as a private Kaggle dataset. Do not upload the worktree, model cache, `.env`, raw
benchmark data, prior outputs, or another ZIP nested inside it.

## 3. Kaggle session

Select accelerator **GPU T4 x2** and turn **Internet on** for the initial immutable Hugging Face
downloads. No API key or secret is required because all five repositories are public. A Hugging
Face token is unnecessary and should not be embedded in cells.

Unpack and install in the first notebook:

```python
import os
import subprocess
from pathlib import Path

SOURCE_ZIP = Path("/kaggle/input/<your-dataset>/valideval-v6-controlled-gpu-smoke-ready.zip")
SOURCE_ROOT = Path("/kaggle/working/valideval-v6")
subprocess.run(["unzip", "-q", str(SOURCE_ZIP), "-d", str(SOURCE_ROOT)], check=True)
os.chdir(SOURCE_ROOT)
subprocess.run(
    ["python", "-m", "pip", "install", "-r", "requirements-kaggle-t4x2-v6.txt"],
    check=True,
)
subprocess.run(["python", "-m", "pip", "install", "--no-deps", "."], check=True)
```

Set the immutable source identity printed by local `git rev-parse`:

```python
os.environ["VALIDEVAL_SOURCE_COMMIT"] = "<FINAL_SHA_FROM_TAG>"
os.environ["VALIDEVAL_INSTALL_SOURCE"] = ""
os.environ["VALIDEVAL_EXECUTION_MODE"] = "smoke"
os.environ["VALIDEVAL_NOTEBOOK_OUTPUT_ROOT"] = "/kaggle/working/kaggle_max_ceiling_outputs"
```

The requirements file SHA-256 must be
`7842c8b72ce4fdc4eb5f253c115fb5aa2cbe7ed88800cc6a20bcf90d14fc4f53`.

## 4. Exact notebook order

Run these top-to-bottom in the same Kaggle session:

1. `kaggle_max_ceiling/00_valideval_t4x2_environment_and_preflight.ipynb`
2. `kaggle_max_ceiling/01_valideval_common_panel_mmlu_t4x2.ipynb`
3. `kaggle_max_ceiling/02_valideval_common_panel_gsm8k_t4x2.ipynb`
4. `kaggle_max_ceiling/03_valideval_common_panel_bbh_t4x2.ipynb`
5. `kaggle_max_ceiling/04_valideval_t4x2_merge_validate_package.ipynb`

Notebook 05 is optional and must not run during S1 unless a separate versioned robustness config is
explicitly supplied.

The exact configs are `configs/runs/mmlu_s1_v6.yaml`,
`configs/runs/gsm8k_s1_v6.yaml`, and `configs/runs/bbh_s1_v6.yaml`.

## 5. Exact panel

```text
Qwen/Qwen2.5-0.5B-Instruct@7ae557604adf67be50417f59c2c2f167def9a775
Qwen/Qwen2.5-1.5B-Instruct@989aa7980e4cf806f80c7fef2b1adb7bc71aa306
Qwen/Qwen2.5-3B-Instruct@aa8e72537993ba99e69dfaafa59ed015b17504d1
microsoft/Phi-3-mini-4k-instruct@f39ac1d28e925b323eae81227eaba4464caced4e
TinyLlama/TinyLlama-1.1B-Chat-v1.0@fe8a4ea1ffedaf415f4da2f062534de366a451e6
```

Model and tokenizer use the same immutable revision. The panel SHA-256 is
`84a65d684fb839a1929d00b04961fd99f9f6883dfa89651de0235c8fda2f394a`.

## 6. Frozen subsets and protocol

- MMLU: 50 test items from `cais/mmlu@c30699e8356da336a370243923dbaf21066bb9fe`
- GSM8K: 50 test items from `openai/gsm8k@740312add88f781978c0658806c59bc2815b9866`
- BBH: 50 test items across all 27 tasks from
  `lukaemon/bbh@982bb89fd79532a8ac676a61fc42eb1aeec63f99`
- All benchmarks: frozen zero-shot policy, seed `20260723`

Do not edit configs or notebooks in Kaggle. Any edit changes the condition and must fail acceptance.

## 7. Disk and runtime planning

Declared model bytes total 20.13 GB (18.75 GiB); preflight requires about 25.75 GiB free. Planning
ranges below are assumption-based, not measured T4 results:

| Stage | Optimistic | Expected | Conservative |
|---|---:|---:|---:|
| MMLU | 0.20 h | 0.48 h | 1.16 h |
| GSM8K | 0.54 h | 1.09 h | 2.54 h |
| BBH | 0.41 h | 0.85 h | 1.99 h |

Allow extra time for package installation and first-cache downloads. Recalibrate only after accepted
S1 runtime fields exist.

## 8. Resume and recovery

Keep `/kaggle/working/kaggle_max_ceiling_outputs`. For an interrupted benchmark:

```python
os.environ["VALIDEVAL_EXECUTION_MODE"] = "resume"
```

Rerun only that benchmark notebook. Resume refuses any source, config, model, dataset, prompt,
scorer, extractor, or shard mismatch. It reuses only completed exact-match jobs.

OOM handling is bounded: clear CUDA state, reduce batch size when possible, reduce maximum input
length once, then record the model failure and continue. S1 defines no dtype/quantization fallback.
Never manually enable `device_map="auto"`, `trust_remote_code`, a different checkpoint, or an
unrecorded quantization.

Interpret terminal states literally. `RUN_COMPLETE_WITH_RECORDED_FAILURES` is packageable but must
be assessed by the importer. `INSUFFICIENT_GPU`, `INSUFFICIENT_DISK`, any mismatch, incomplete run,
or package validation failure is a stop condition.

## 9. Expected outputs

Return exactly these files from:
`/kaggle/working/kaggle_max_ceiling_outputs/packages/`

```text
valideval_v6_s1_mmlu_s1-v6-mmlu.zip
valideval_v6_s1_gsm8k_s1-v6-gsm8k.zip
valideval_v6_s1_bbh_s1-v6-bbh.zip
```

Download them locally into:

```text
kaggle_outputs/v6/
```

Do not rename, unpack/repack, combine, or add files to the archives.

## 10. Local validation, acceptance, and recalibration

```bash
python -m valideval accept-s1 \
  --input-dir kaggle_outputs/v6 \
  --output-root imported/v6

python -m valideval recalibrate-runtime \
  --input-root imported/v6 \
  --output results/planning/runtime_recalibration_v6.json
```

Acceptance requires three exact ZIPs; resolved final source SHA; exact config, model/tokenizer,
dataset, subset, and prompt identities; valid checksums; no contradictory/duplicate rows; declared
model failures; complete per-model item coverage; and extraction reliability at least 0.95.

Proceed to S2 planning only after `S1_SMOKE_ACCEPTED` or
`S1_SMOKE_ACCEPTED_WITH_RECORDED_MODEL_FAILURES`, review of every failure, and measured runtime/disk
recalibration. A repeated model load/OOM failure, unexpected extraction degradation, identity drift,
or missing coverage is a stop.

S1 can show that this exact engineering path runs on T4×2 under the recorded condition. It cannot
show scientific panel adequacy, reliable rankings, benchmark validity, cross-benchmark construct
equivalence, population generalization, or absence of training contamination.
