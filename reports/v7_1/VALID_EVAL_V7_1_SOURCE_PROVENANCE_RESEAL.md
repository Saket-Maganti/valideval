# ValidEval V7.1 Source-Provenance Reseal

Baseline commit: `b5970ed9c1109a7e4aefc1218b7aa956d4ce102b`

Canonical tag: `valideval-v7.1-icml2027-scientific-execution-ready`

All 22 V7 execution configs require the canonical tag. Run manifests record the required ref, its
resolved expected commit, the actual checkout commit, and whether they match. The importer checks
that tuple together with the config hash, model revisions, package checksums, and schema.

The immutable tag is created only after code, CPU evidence, tests, reports, formatting, type checks,
and package builds complete. Because a tracked file cannot contain the hash of the Git commit that
contains itself, the tagged commit is the scientific source seal; a following metadata-only commit
records that exact tagged hash in `VALID_EVAL_V7_1_MACHINE_STATE.json`. This is an explicit
two-commit provenance protocol, not a claim that a self-referential commit exists.

The final tagged SHA, configuration/source hashes, repository cleanliness, and CI conclusion are
recorded in the machine state. A real run is accepted only when its manifest resolves to that tagged
scientific source commit.
