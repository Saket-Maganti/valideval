# ValidEval V7.2 Kaggle S1 Runbook

Authorized source: `valideval-v7.2-icml2027-kaggle-s1-ready` at `729727cc83c990f2a63dfa842997b6a98275f520`.

1. Check out exactly: `git checkout valideval-v7.2-icml2027-kaggle-s1-ready` and verify `git rev-parse HEAD` equals
   `729727cc83c990f2a63dfa842997b6a98275f520`. Archive or upload this tagged tree without caches, secrets, or model weights.
2. In Kaggle choose two T4 GPUs, enable Internet for public Hugging Face downloads, and provide at
   least the fail-closed disk amount printed by notebook 00.
3. Run notebooks in order: `00_v7_2_t4x2_preflight.ipynb`, then the MMLU, GSM8K, and BBH notebooks,
   then `04_v7_2_s1_validate_package.ipynb` after placing all three ZIPs together.
4. Use `VALIDEVAL_EXECUTION_MODE=smoke`. For interrupted work use `resume`; do not change configs.
   Bounded batch fallback is allowed. Sequence-length fallback is forbidden. A persistent OOM or
   systemic model failure requires repair and rerun, never silent checkpoint substitution.

Exact checkpoints:

- `Qwen/Qwen2.5-0.5B-Instruct` @ `7ae557604adf67be50417f59c2c2f167def9a775`
- `Qwen/Qwen2.5-1.5B-Instruct` @ `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`
- `Qwen/Qwen2.5-3B-Instruct` @ `aa8e72537993ba99e69dfaafa59ed015b17504d1`
- `microsoft/Phi-3-mini-4k-instruct` @ `f39ac1d28e925b323eae81227eaba4464caced4e`
- `TinyLlama/TinyLlama-1.1B-Chat-v1.0` @ `fe8a4ea1ffedaf415f4da2f062534de366a451e6`

Dataset revisions:

- mmlu: `c30699e8356da336a370243923dbaf21066bb9fe`
- gsm8k: `740312add88f781978c0658806c59bc2815b9866`
- bbh: `982bb89fd79532a8ac676a61fc42eb1aeec63f99`

Download these files:

- `valideval_v7_2_s1_mmlu_s1-v7-2-mmlu.zip`
- `valideval_v7_2_s1_gsm8k_s1-v7-2-gsm8k.zip`
- `valideval_v7_2_s1_bbh_s1-v7-2-bbh.zip`

Place them in `kaggle_icml2027_outputs/packages`, then run:

```bash
python -m valideval accept-s1-v7-2   --input-dir kaggle_icml2027_outputs/packages   --output-root imported/v7_2/s1
python -m valideval recalibrate-study-c-after-s1   --input-root imported/v7_2/s1   --output results/v7_2/planning/study_c_recalibration_after_s1.json
```

Accepted S1 unlocks engineering-health assessment and possible S2 authorization after measured
recalibration. It unlocks no benchmark-validity, ranking, transport, item-cause, or repair claim.
S3 remains blocked pending S2; S4 remains blocked pending S3.
