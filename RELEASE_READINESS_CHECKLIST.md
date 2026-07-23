# Release Readiness Checklist

## Code

- [x] Source code is included in the safe packet scope.
- [x] Packaging script exists: `scripts/make_reviewer_packet.py`.
- [x] Static confirmatory preflight script exists: `scripts/preflight_confirmatory_synthetic.py`.
- [ ] Full release branch hygiene and tag state are not checked in this no-run packaging pass.

## Tests

- [x] Focused confirmatory preflight tests are available.
- [x] Reviewer packet packaging tests are available.
- [x] `python3 -m pytest -q tests/test_preflight_confirmatory_synthetic.py` passed.
- [x] `python3 -m pytest -q tests/test_make_reviewer_packet.py` passed.
- [ ] Full test suite is not run in this no-run packaging pass.

## Lint

- [x] `ruff check .` is the expected lint gate for this phase.
- [x] `ruff check .` passed.

## Docs

- [x] Reviewer packet manifest exists.
- [x] Reviewer reading guide exists.
- [x] Artifact exclusion policy exists.
- [x] No-run release audit exists.
- [x] Static confirmatory preflight report exists.

## Claims Ledger

- [x] NeurIPS claims ledger exists.
- [x] Paper claims ledger exists.
- [x] Blocked claims remain visible.
- [x] MMLU-Redux remains weak/negative external validation.
- [x] GPQA remains protocol/demo unless wide-panel evidence exists.

## Evidence Status

- [x] Cross-flaw specificity remains `WEAK`.
- [x] Held-out generator transfer remains `WEAK`.
- [x] Calibration remains `BLOCKED`.
- [x] Synthetic-to-real threshold validation remains `NOT_RUN`.
- [x] Confirmatory follow-up remains `RESULT_REQUIRED`.
- [x] `[RESULT REQUIRED]` placeholders remain in place.

## Large Artifacts

- [x] Default packet excludes `cache/`.
- [x] Default packet excludes `data/external/`.
- [x] Default packet excludes `results/mmlu/`.
- [x] Default packet excludes `results/synthetic/`.
- [x] Default packet excludes `*.jsonl`.
- [x] Default packet excludes `*.csv` files larger than 5 MB.

## Reproducibility

- [x] Future confirmatory commands are documented but deferred.
- [x] Static preflight has passed.
- [x] Reviewer packet packaging script can be tested without running validation.
- [ ] Final zip creation in the live repository should be performed only after reviewing exclusions.

## Reviewer Packet

- [x] Manifest exists.
- [x] Reading guide exists.
- [x] Exclusion policy exists.
- [x] No-run release audit exists.
- [x] Packaging script exists.
- [x] Required top-level reviewer documents are listed for inclusion.

## Known Blockers

- Confirmatory synthetic validation has not run.
- Cross-flaw specificity remains `WEAK`.
- Held-out generator transfer remains `WEAK`.
- Numeric calibration remains `BLOCKED`.
- Synthetic-to-real threshold validation remains `NOT_RUN`.
- MMLU-Redux remains weak/negative external validation.
- GPQA remains protocol/demo unless future wide-panel evidence exists.
- Full release/tag/DOI/public-archive state is not checked in this no-run pass.

## Final Verdict

`REVIEW_PACKET_READY`

Strict rationale: the reviewer packet structure, artifact exclusion policy, packaging script, and
focused static checks are ready for reviewer-packet packaging. This verdict does not mean empirical
confirmation is complete, and it does not change any evidence state.
