# Stage Plan

## Stage 0: Repository Bootstrap

- Create package, config, docs, examples, cache, results, reportcard, and paper directories.
- Add engineering instructions and reproducibility guardrails.

Status: complete for the initial artifact.

## Stage 1: Offline Toy Audit

- Implement typed schemas for items, predictions, matrices, diagnostics, and validity profiles.
- Implement a small toy multiple-choice benchmark with prompt variants.
- Implement deterministic mock model runners.
- Build cached prediction JSONL files and response matrices.
- Implement shortcut, IRT proxy, and reliability diagnostics.
- Render a multidimensional Markdown validity report card.

Status: complete for the offline `toy_mcq`/`mock` demo.

## Stage 2: Research Artifact Hardening

- Add tests covering schema serialization, benchmark rendering, model behavior, matrix construction, diagnostics, CLI smoke, and report card rendering.
- Add cautious documentation for validity theory, audit protocol, reproducibility, and preregistered benchmark candidates.
- Scaffold real benchmark config/adapters honestly without inventing empirical results.

Status: initial version complete; docs and tests should expand as real benchmark loaders are added.

## Stage 3: Next Experimental Expansion

- Add local JSONL benchmark examples and validation.
- Add more robust uncertainty estimates and figure/table generation from cached results.
- Audit one real benchmark from a user-provided local export.

Status: next stage.

