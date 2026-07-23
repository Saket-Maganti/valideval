# ValidEval V6 Production Runner Implementation

Gate: `PRODUCTION_RUNNER_READY`

The canonical entry point is:

```bash
python -m valideval run --config configs/runs/<benchmark>_s1_v6.yaml
```

The runner validates the Pydantic configuration and referenced SHA-256 values, resolves the source
tag, validates the exact model registry and benchmark contract, checks dependencies/GPU count/free
disk before downloads, reconstructs the immutable frozen subset, and creates an atomic run
directory. It then dispatches one isolated model job per worker, renders gold-free prompts, loads
exact tokenizer/model revisions, generates, extracts without gold, scores through a separate
gold-aware call, and records per-item timing, token, device, cache, retry, and fallback fields.

Resume identity includes run/config/source/model/dataset/prompt/scorer/extractor/shard identities.
The scheduler persists atomic status and heartbeat files. Merge rejects missing or unexpected
shards, duplicate or contradictory identities, mixed conditions, and coverage gaps. Packaging
validates required artifacts and checksums before creating a sorted, deterministic ZIP.

Terminal states are `RUN_COMPLETE`, `RUN_COMPLETE_WITH_RECORDED_FAILURES`,
`RUN_INCOMPLETE_RETRYABLE`, `RUN_INCOMPLETE_FATAL`, `CONFIG_MISMATCH`,
`DATASET_RESOLUTION_FAILURE`, `MODEL_RESOLUTION_FAILURE`, `INSUFFICIENT_DISK`,
`INSUFFICIENT_GPU`, and `PACKAGE_VALIDATION_FAILURE`.

OOM recovery is bounded. It unloads reachable objects/clears the CUDA cache, reduces batch size
when possible, then reduces the configured maximum input length. Each changed condition is recorded
in the scheduler result and prediction rows. Dtype or quantization never changes silently; this S1
panel defines no quantization fallback.

Mock integration traverses this architecture but is explicitly `NON_EVIDENCE_FIXTURE`.
