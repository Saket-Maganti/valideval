# Reproducibility Audit Trail

## Repository State

This checkout was initialized as a git repository because the NeurIPS prompt pack requires a
tracked audit trail. If this is a detached export rather than the canonical project repository,
record the upstream source separately before submission.

## Tracked Artifacts

Track code, tests, configs, docs, paper scaffolds, examples, and report templates. These files
define the protocol and should be reviewable without private data.

## Manifest-Hashed Artifacts

Large or private runtime artifacts should be referenced by manifest hashes instead of copied into
public packets:

- `cache/`
- `local_outputs/`
- raw benchmark exports
- large prediction-detail files
- restricted GPQA-bearing artifacts

## Required Before Submission

1. Capture `python3 -m valideval environment --output environment.json`.
2. Build a reproducibility bundle for the final public lane.
3. Run reviewer-risk checks on paper/report artifacts.
4. Record exact paths and hashes for imported prediction matrices and external labels.
