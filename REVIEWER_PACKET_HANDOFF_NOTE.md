# Reviewer Packet Handoff Note

## 1. What This Packet Is

This is a reviewer-safe documentation/code/config/paper packet for `valideval` after the active MMLU real-panel run. It includes the compiled paper draft, paper-facing tables and figures, source code, tests, configs, claims ledgers, result reports, Kaggle execution package files, and reviewer guidance.

## 2. What This Packet Is Not

This is not a NeurIPS-ready submission package. It does not include raw benchmark text, raw HELM/MMLU prediction dumps, large cached matrices, Kaggle output ZIPs, or generated `results/mmlu/` trees. It does not establish MMLU error detection, MMLU validity/invalidity, full 2PL, second-benchmark evidence, or direct/hash MMLU-Redux validation.

## 3. ZIP Details

```text
dist/valideval_reviewer_packet.zip
1,463,606 bytes
587 files
SHA-256: da05f2d1f9225f643be4c52a17ccfec6fbaae66e7cc9b37971f6eb157e5d509f
```

ZIP audit:

```text
REVIEWER_PACKET_ZIP_AUDIT.md
```

Audit verdict:

```text
REVIEWER_ZIP_READY
```

## 4. Recommended Reading Order

1. `paper/main.pdf`
2. `ARTIFACT_MANIFEST_FOR_PAPER.md`
3. `CLAIMS_LEDGER_NEURIPS.md`
4. `paper/current_evidence_state.md`
5. `paper/current_claims_allowed_blocked.md`
6. `MMLU_REAL_PANEL_CORE_RUN_REPORT.md`
7. `MMLU_RANKING_DISAGREEMENT_BASELINES_REPORT.md`
8. `MMLU_REDUX_DIRECT_ALIGNMENT_VALIDATION_REPORT.md`
9. `DECOUPLED_SYNTHETIC_EXECUTION_REPORT.md`
10. `SECOND_BENCHMARK_RUN_REPORT.md`
11. `KAGGLE_NOTEBOOK_BUILD_REPORT.md`
12. `FINAL_SUBMISSION_GATE_AND_VENUE_STRATEGY.md` once created.

## 5. Evidence State Summary

- Active MMLU panel: 39-model HELM wide matrix.
- Panel-size blocker: cleared for active MMLU matrix.
- Real-panel ranking/disagreement: artifact-backed for active MMLU panel.
- Strongest current finding: subject-level rank sensitivity under the MMLU panel.
- Proxy IRT: available; full 2PL not claimed.
- MMLU-Redux: structural weak/negative; direct/hash blocked.
- Decoupled synthetic: execution blocked by missing guard artifacts.
- Second benchmark: no local run; Kaggle path prepared.
- Kaggle outputs: not present, import blocked.
- NeurIPS readiness: blocked.

## 6. Large Artifacts and Data Policy

The reviewer packet intentionally excludes:

- `cache/`
- `data/external/`
- `results/mmlu/`
- `results/synthetic/`
- `*.jsonl`
- `*.zip`
- large `*.csv`
- raw MMLU question text or answer-choice text

Reviewers should use sanitized reports, source code, configs, paper tables/figures, and claim ledgers.

## 7. Claims Allowed

- ValidEval is an offline-capable benchmark-validity auditing toolkit.
- The active MMLU panel is the 39-model HELM wide matrix.
- Subject-level rank sensitivity is artifact-backed under this panel.
- Proxy IRT diagnostics exist.
- MMLU-Redux remains weak/negative and direct/hash blocked.
- Kaggle package exists as a future execution path.

## 8. Claims Blocked

- MMLU error detection.
- MMLU is valid or invalid.
- Direct/hash MMLU-Redux alignment.
- Full 2PL.
- Decoupled synthetic validation result.
- Second-benchmark evidence.
- NeurIPS readiness.

## 9. Reproduce the Packet

```bash
ruff check .
python3 -m pytest -q tests/test_make_reviewer_packet.py
python3 scripts/make_reviewer_packet.py
```

Verify:

```bash
shasum -a 256 dist/valideval_reviewer_packet.zip
unzip -Z1 dist/valideval_reviewer_packet.zip
```
