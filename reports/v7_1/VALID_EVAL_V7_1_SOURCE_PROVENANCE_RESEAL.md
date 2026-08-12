# ValidEval V7.1 Source-Provenance Reseal

Baseline commit: `b5970ed9c1109a7e4aefc1218b7aa956d4ce102b`

Canonical tag: `valideval-v7.1-icml2027-scientific-execution-ready`

Tagged scientific commit: `f4f803a01daf89798d4b181e5610ce3f70355f32`

Git tree: `ae6109e77dc518a42ec50fd6c5277d003105e0f7`

All 22 V7 execution configs require the canonical tag. Run manifests record the required ref, its
resolved expected commit, the actual checkout commit, and whether they match. The importer checks
that tuple together with the config hash, model revisions, package checksums, and schema.

The immutable tag is created only after code, CPU evidence, tests, reports, formatting, type checks,
and package builds complete. Because a tracked file cannot contain the hash of the Git commit that
contains itself, the tagged commit is the scientific source seal; a following metadata-only commit
records that exact tagged hash in `VALID_EVAL_V7_1_MACHINE_STATE.json`. This is an explicit
two-commit provenance protocol, not a claim that a self-referential commit exists.

GitHub Actions run
[`31592006612`](https://github.com/Saket-Maganti/valideval/actions/runs/31592006612) passed on
the tagged SHA. The configuration/source hashes and repository cleanliness are recorded in the
machine state. A real run is accepted only when its manifest resolves to that tagged scientific
source commit.
