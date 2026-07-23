# ValidEval V6 Repository and Provenance Seal

Status: `PROVENANCE_SEALED`

The repository began as an unborn Git worktree. Before V6 work, transient caches, raw benchmark
data, model caches, generated sites, imported outputs, ZIPs, virtual environments, and secrets-like
files were excluded. An explicit staged-file audit found no staged file above 5 MiB and the secret
scan found no credential value. The reviewed V5 source baseline was committed as
`f7bdfda1676995ffda356c15884a3d10cda6b80b` and tagged `valideval-v5-pre-execution`.

The V6 execution configs require the annotated source identity
`valideval-v6-controlled-gpu-smoke-ready`. At runtime the runner resolves that ref to an immutable
commit, compares it with the checked-out `HEAD` (or the explicit `VALIDEVAL_SOURCE_COMMIT` in a
source bundle without `.git`), and records the resolved SHA in every environment, prediction, and
run manifest. This tag indirection avoids an impossible commit-self-hash embedded in its own
contents while still making the execution identity exact.

Raw MMLU, GSM8K, and BBH records were used only to derive versioned item identities and hashes. They
are ignored and are not distributed by the V6 source commit. S1 ZIP packaging independently rejects
secrets, caches, hidden or temporary files, path traversal, and nested archives.

Final commit and tag are recorded in the root machine state and handoff after the completion commit.
