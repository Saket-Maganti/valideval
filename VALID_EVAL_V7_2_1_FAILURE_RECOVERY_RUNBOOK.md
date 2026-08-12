# ValidEval V7.2.1 Failure Recovery Runbook

- Session death: resume from the identity-matched shard manifest; block if identity cannot be revalidated.
- Internet loss: resume only from exact-revision cache; never fetch an unpinned latest revision.
- OOM: apply the bounded registered fallback; block after retry budget exhaustion.
- Disk full: stop, preserve valid completed shards, clear only documented caches, then resume.
- Model failure: record the typed failure; continue only if stage acceptance permits recorded model failures.
- Package corruption: reject and rerun packaging from validated source artifacts.
- Extraction reliability below 0.95: block acceptance; inspect parser outputs and rerun only after a source-controlled repair and reseal.
- Checksum, config, source, parser, or scorer failure: never retry blindly; repair, invalidate dependents, reseal, and rerun.
