# ValidEval V5 Human Validation Protocol

Audit date: 2026-07-16  
Evidence state: `PLANNED`  
Human labels created: no

## Verdict

`HUMAN_PACKET_AND_IMPORT_FIXTURE_VALIDATED_STUDY_EXECUTION_BLOCKED`

The V5 configuration, blinded packet builder, private randomization mapping, annotation template, and fail-closed label importer are implemented and locally tested. No human packet was built from a frozen scientific sampling frame, no annotator was recruited, and no human label is evidence in this build.

## Frozen label taxonomy

- `INCORRECT_GOLD_ANSWER`
- `AMBIGUOUS_QUESTION`
- `AMBIGUOUS_OPTIONS`
- `MULTIPLE_DEFENSIBLE_ANSWERS`
- `INSUFFICIENT_CONTEXT`
- `OUTDATED_FACT`
- `SCORING_OR_EXTRACTION_ISSUE`
- `DOMAIN_SPECIALIST_DISPUTE`
- `NO_DETECTED_ISSUE`
- `UNSURE`

## Design encoded in the V5 configuration

- Primary sampling is a probability sample from a frozen frame; enrichment and controls are reported separately.
- The primary planned endpoint is adjudicated issue precision with a 95% confidence level.
- Recall is explicitly blocked for a high-score-only queue.
- A 30-item pilot requires at least two annotators per task and an agreement/control audit before progression.
- The full study plans at least three annotators per task, with final sample size selected by precision/power analysis.
- Annotators must attest expertise where needed and declare conflicts.
- Positive and negative controls are required and hidden from annotators.
- Diagnostic scores/ranks, model response patterns, selection status, external labels, intended hypothesis, and control expectations are blinded.
- Disagreement or `UNSURE` is planned for independent third-reviewer adjudication.
- Duplicate assignments, failed controls, missing expertise, impossible duration, and hash mismatch are exclusion grounds.

## Implemented safeguards

The packet builder:

- rejects duplicate source IDs and normalized question/option duplicates;
- uses deterministic simple-random selection and randomized presentation for a frozen seed;
- requires separate public packet and private audit directories;
- removes all configured blinded fields from public rows;
- replaces revealing control subjects with `unspecified`;
- writes a public packet hash and a private task-to-source/control mapping;
- requires both positive and negative controls by default.

The importer:

- verifies the packet SHA-256 against the private manifest;
- rejects malformed rows, unknown task IDs/labels, invalid anonymous IDs, duplicate annotator-task rows, invalid confidence/duration, and insufficient rationales when requested;
- blocks the whole accepted-label output if any row is invalid;
- checks per-task annotation counts and the frozen control-match threshold;
- keeps validated labels and source linkage in a private output.

The shared planning/agreement layer now also provides a Wilson-width planning quantity for the assumed human precision/sample size and nominal Krippendorff alpha for variable annotator counts. These are infrastructure outputs: the planning width depends on explicit assumptions, and agreement remains unavailable until real comparable labels exist.

## What the current design can and cannot estimate

| Quantity | Permission |
|---|---|
| Precision within a preregistered probability sample | Planned after adjudication and power freeze |
| Enrichment by preregistered diagnostic-score stratum | Planned; strata must be frozen in the sampling frame |
| Issue-type distribution in the sampled frame | Planned |
| Calibration across score strata | Planned, if probability sampling/weights and stratum coverage are retained |
| Recall from a high-score-only queue | Blocked |
| Population prevalence from controls or enrichment items | Blocked |

## Verification

```text
python3 -m pytest -q tests/test_human_validation_v5.py tests/test_human_validation.py tests/test_panel_power_v5.py
17 passed in 1.06s
```

These tests exercise deterministic blinding/randomization, public/private control separation, valid fixture import, invalid-label batch blocking, packet-tamper rejection, directory separation, required controls, nominal agreement metrics, bootstrap agreement intervals, and non-evidence precision planning. The inputs are synthetic test rows and assumptions, not human evidence.

## Remaining protocol gaps

- The scientific candidate frame, benchmark/subject allocation, diagnostic-score strata, raw-text license decision, and sample size are not frozen.
- The common-panel planner includes human precision/Wilson-width planning, but it is not empirical power validation and is not yet bound automatically to a frozen V5 packet sampling frame.
- Agreement (including nominal Krippendorff alpha) and adjudication are implemented as components but are not wired into one V5 end-to-end command.
- No annotator recruitment, expertise verification, consent/ethics determination, pilot, labels, adjudication, or endpoint analysis occurred.

## Exact next action

Freeze a licensed probability sampling frame and stratum allocation, bind the existing precision planner to that frozen packet design, integrate the V5 import/agreement/adjudication components, add privately stored positive/negative controls, then build the 30-item blinded pilot packet. Human claims remain `RESULT_REQUIRED` until imported labels, control performance, exclusions, agreement, and adjudication pass.
