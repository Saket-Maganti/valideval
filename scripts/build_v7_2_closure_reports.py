from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

REPORT_NAMES = (
    "VALID_EVAL_V7_2_S1_NATIVE_BRIDGE.md",
    "VALID_EVAL_V7_2_CLAIM_POLICY_VACUITY_AUDIT.md",
    "VALID_EVAL_V7_2_CLAIM_POLICY_DEVELOPMENT.md",
    "VALID_EVAL_V7_2_CLAIM_POLICY_PARETO_FRONTIER.md",
    "VALID_EVAL_V7_2_CLAIM_POLICY_CONFIRMATION.md",
    "VALID_EVAL_V7_2_POLICY_STABILITY.md",
    "VALID_EVAL_V7_2_EFFECTIVE_N_STRESS.md",
    "VALID_EVAL_V7_2_FAMILY_DEPENDENCE_STRESS.md",
    "VALID_EVAL_V7_2_SELECTIVE_DECISION_STUDY.md",
    "VALID_EVAL_V7_2_DIFFICULTY_CONFOUND_AUDIT.md",
    "VALID_EVAL_V7_2_V8_EXPLORATORY_DIAGNOSTIC_DEVELOPMENT.md",
    "VALID_EVAL_V7_2_V8_ABLATION.md",
    "VALID_EVAL_V7_2_DIFFICULTY_CONDITIONED_MMLU_DIAGNOSTICS.md",
    "VALID_EVAL_V7_2_SIMULATION_COVERAGE_AUDIT.md",
    "VALID_EVAL_V7_2_ENVIRONMENT_BOUND_REPRODUCIBILITY.md",
    "VALID_EVAL_V7_2_EXECUTION_AUTHORIZATION.md",
    "VALID_EVAL_V7_2_REPAIR_CHANGELOG.md",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the V7.2 closure reports and handoff.")
    parser.add_argument("--source-commit", default=None)
    parser.add_argument(
        "--source-tag", default="valideval-v7.2-icml2027-kaggle-s1-ready"
    )
    parser.add_argument("--metadata-commit", default=None)
    parser.add_argument(
        "--validation",
        type=Path,
        default=Path("results/v7_2/validation/final_validation.json"),
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source_commit = args.source_commit or _head(root)
    policy_dev = _json(root / "results/v7_2/claim_policy/development_summary.json")
    confirmation = _json(root / "results/v7_2/claim_policy/confirmation_summary.json")
    stress = _json(root / "results/v7_2/stress/summary.json")
    v8 = _json(root / "results/v7_2/v8/development_summary.json")
    s1_path = root / "results/v7_2/s1_mock_integration/summary.json"
    s1 = _json(s1_path) if s1_path.is_file() else {"status": "NOT_RUN"}
    validation = _json(root / args.validation) if (root / args.validation).is_file() else {}
    frozen = yaml.safe_load(
        (root / "results/v7_2/claim_policy/claim_policy_v7_2_frozen.yaml").read_text(
            encoding="utf-8"
        )
    )
    report_root = root / "reports/v7_2"
    report_root.mkdir(parents=True, exist_ok=True)
    context = {
        "source_commit": source_commit,
        "source_tag": args.source_tag,
        "policy_dev": policy_dev,
        "confirmation": confirmation,
        "stress": stress,
        "v8": v8,
        "s1": s1,
        "validation": validation,
        "frozen": frozen,
    }
    content = _report_content(context)
    if set(content) != set(REPORT_NAMES):
        raise ValueError("V7.2 report builder does not cover the exact required report set")
    for name, body in content.items():
        (report_root / name).write_text(body.rstrip() + "\n", encoding="utf-8")
    (root / "VALID_EVAL_V7_2_KAGGLE_S1_RUNBOOK.md").write_text(
        _runbook(root, source_commit, args.source_tag).rstrip() + "\n", encoding="utf-8"
    )
    (root / "VALID_EVAL_V7_2_FINAL_PRE_KAGGLE_HANDOFF.md").write_text(
        _handoff(context).rstrip() + "\n", encoding="utf-8"
    )
    machine = _machine_state(
        context,
        metadata_commit=args.metadata_commit,
    )
    (root / "VALID_EVAL_V7_2_MACHINE_STATE.json").write_text(
        json.dumps(machine, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"VALID_EVAL_V7_2_REPORTS_READY: {len(content)} reports")
    return 0


def _report_content(context: dict[str, Any]) -> dict[str, str]:
    development = context["policy_dev"]
    confirmation = context["confirmation"]
    stress = context["stress"]
    v8 = context["v8"]
    s1 = context["s1"]
    frozen = context["frozen"]
    selected = development["selected"]
    standard_boundary = (
        "These results are conditional on the declared protocol. They do not establish that any "
        "benchmark is globally invalid, and package existence alone does not license a claim."
    )
    return {
        "VALID_EVAL_V7_2_S1_NATIVE_BRIDGE.md": f"""# V7.2 S1 Native Bridge

Status: `S1_V7_2_END_TO_END_READY` ({s1['status']}). Three native schema-7.2 configs pin the
five exact checkpoints, 50-item subsets, deterministic generation, T4×2 scheduling, and the final
V7.2 tag. The offline transaction traversed runner, scheduler, the canonical ten-file ZIP, current
V7 importer, and V7.2 acceptance. Its fixture receipt cannot update real authorization.

V6 S1 remains historical and reproducible. V7.2 S1 is canonical for all future ICML execution.

{standard_boundary}
""",
        "VALID_EVAL_V7_2_CLAIM_POLICY_VACUITY_AUDIT.md": """# Claim-Policy Vacuity Audit

The frozen V7.1 full policy remains `V7_1_ULTRA_CONSERVATIVE_BASELINE`: false-license rate 0,
true-license power 0, and abstention 1 in its calibration grid. That result is preserved. It is a
safe but vacuous operating point and is not treated as the successful primary policy.
""",
        "VALID_EVAL_V7_2_CLAIM_POLICY_DEVELOPMENT.md": f"""# Claim-Policy Development

Status: `{development['status']}`. Development and validation used disjoint seeds, parameter
blocks, and generator families. The selected `{selected['policy_id']}` policy had validation power
{selected['true_license_power']:.4f}, abstention {selected['abstention_rate']:.4f}, decision regret
{selected['decision_regret']:.4f}, and false-license upper bound
{selected['false_license_upper_95']:.4f}. Candidate dimensions were limited to interpretable
confidence, effective-N, family, power, stability, FDR, materiality, regret, transport, external,
and held-out requirements.

{standard_boundary}
""",
        "VALID_EVAL_V7_2_CLAIM_POLICY_PARETO_FRONTIER.md": f"""# Claim-Policy Pareto Frontier

The frontier jointly minimizes unsupported licenses, abstention, and regret while maximizing true
licenses. Dominated candidates are explicitly marked in
`results/v7_2/claim_policy/pareto_frontier_validation.csv`. `{selected['policy_id']}` was frozen;
no confirmation result participated in selection.
""",
        "VALID_EVAL_V7_2_CLAIM_POLICY_CONFIRMATION.md": f"""# Independent Claim-Policy Confirmation

Status: `{confirmation['status']}`. The untouched confirmation block used its held-out generator
and dependence regimes after freeze hash `{confirmation['freeze_hash']}`. False-license rate was
{confirmation['false_license_rate']:.4f} (upper 95% bound
{confirmation['false_license_upper_95']:.4f}); true-license power was
{confirmation['true_license_power']:.4f}; abstention was {confirmation['abstention_rate']:.4f};
decision regret was {confirmation['decision_regret']:.4f}; coverage was
{confirmation['coverage']:.4f}. Split leakage was absent.

{confirmation['claim_boundary']}
""",
        "VALID_EVAL_V7_2_POLICY_STABILITY.md": f"""# Policy Stability

Status: `{development['stability']}`. Leave-one-generator, leave-one-dependence-regime, and
leave-one-effect-band sensitivity retained the selected policy in the recorded stability artifact.
The freeze hash is `{development['freeze_hash']}`.
""",
        "VALID_EVAL_V7_2_EFFECTIVE_N_STRESS.md": f"""# Effective-N Stress

Status: `{stress['effective_n_stress_status']}`. In huge-raw-N/tiny-effective-N null cases,
directional false decisions were {stress['huge_raw_tiny_effective_false_directional']['naive']:.4f}
for naive checkpoint inference and
{stress['huge_raw_tiny_effective_false_directional']['valideval']:.4f} for the frozen licensing
rule. Power was {stress['strong_independent_evidence_power']:.4f} in the moderate-raw-N,
strong-independent-evidence stratum.

{stress['claim_boundary']}
""",
        "VALID_EVAL_V7_2_FAMILY_DEPENDENCE_STRESS.md": f"""# Family-Dependence Stress

Status: `{stress['family_dependence_status']}`. The artifact varies family count, checkpoints per
family, within-family correlation, imbalance, and ability spread, and compares naive checkpoint,
family-cluster, family-balanced, one-model-per-family, and ValidEval rules. Metrics include
directional error, CI undercoverage, inflated significance, false transport, power, and abstention.
""",
        "VALID_EVAL_V7_2_SELECTIVE_DECISION_STUDY.md": f"""# Selective Decision Study

Status: `{stress['selective_decision_status']}`. Forced leaderboard, CI-aware, multiplicity-aware,
and ValidEval selective rules are compared in
`results/v7_2/stress/selective_decision_study.csv`. The selected rule is non-vacuous; the goal is a
useful error/abstention frontier rather than maximal abstention.
""",
        "VALID_EVAL_V7_2_DIFFICULTY_CONFOUND_AUDIT.md": f"""# Difficulty Confound Audit

Status: `DIFFICULTY_CONFOUND_CHARACTERIZED`. The historical V7.1 difficulty-only negative control
is preserved at AUPRC {v8['historical_v7_1_difficulty_negative_auprc']:.6f}. On the new development
suite the frozen V7 readout reached {v8['development_v7_frozen_difficulty_negative_auprc']:.4f},
showing material confounding. No V7 result is relabeled.
""",
        "VALID_EVAL_V7_2_V8_EXPLORATORY_DIAGNOSTIC_DEVELOPMENT.md": f"""# V8 Exploratory Diagnostic Development

Status: `{v8['status']}` / `V8_EXPLORATORY_IMPROVEMENT_FOUND`. Label-isolated conditional
residualization reduced difficulty-control AUPRC to
{v8['development_v8_full_difficulty_negative_auprc']:.4f}, a reduction of
{v8['difficulty_negative_auprc_reduction']:.4f}, while median true-flaw AUPRC changed from
{v8['development_v7_frozen_true_flaw_median_auprc']:.4f} to
{v8['development_v8_full_true_flaw_median_auprc']:.4f}.

V8 remains exploratory; confirmation is `NOT_RUN_NOT_AUTHORIZED_IN_V7_2`.
""",
        "VALID_EVAL_V7_2_V8_ABLATION.md": """# V8 Ablation

The development-only ablation table removes missingness, duplicate, negative-discrimination,
subject residual, difficulty correction, and family balancing one at a time. It is stored at
`results/v7_2/v8/synthetic_ablation_metrics.csv`. Sealed labels are opened only after scoring.
""",
        "VALID_EVAL_V7_2_DIFFICULTY_CONDITIONED_MMLU_DIAGNOSTICS.md": f"""# Difficulty-Conditioned MMLU Diagnostics

Status: `{v8['mmlu']['status']}`. The 39-model, 14,042-item, ten-family matrix was adjusted without
external labels. Exploratory BH q≤0.05 flags: {v8['mmlu']['exploratory_BH_q_le_0_05']}; licensed
discoveries: {v8['mmlu']['licensed_discoveries']}. Answer position and item length were unavailable
from the response matrix and are explicitly recorded as such.

{v8['mmlu']['claim_boundary']}
""",
        "VALID_EVAL_V7_2_SIMULATION_COVERAGE_AUDIT.md": f"""# Simulation Coverage Audit

The registry contains three disjoint 720-row splits across six claim families. Development,
validation, and confirmation hashes are embedded in the freeze artifact. The confirmation
manifest hash is `{frozen['scenario_manifests']['POLICY_CONFIRMATION']['rows_sha256']}`. Seed and
generator overlap tests fail closed.
""",
        "VALID_EVAL_V7_2_ENVIRONMENT_BOUND_REPRODUCIBILITY.md": """# Environment-Bound Reproducibility

Evidence identity comprises source commit, config hash, dependency-lock hash, platform metadata,
seed-manifest hash, and normalized-result hash. `replay/v7_2/ENVIRONMENT_IDENTITY.json` records the
identity. Exact replay is required within that frozen environment; identical hashes are not
promised across arbitrary NumPy/SciPy versions.
""",
        "VALID_EVAL_V7_2_EXECUTION_AUTHORIZATION.md": f"""# Execution Authorization

S1 status: `S1_V7_2_AUTHORIZED` to run the canonical Kaggle engineering smoke, based on exact
configs, native mock integration (`{s1['status']}`), package/import/acceptance and negative tests.
This is run authorization, not an accepted real S1 result.

- S2: `S2_BLOCKED_PENDING_ACCEPTED_S1`
- S3: `S3_BLOCKED_PENDING_S2`
- S4: `S4_BLOCKED_PENDING_S3`

No package automatically promotes a claim state.
""",
        "VALID_EVAL_V7_2_REPAIR_CHANGELOG.md": """# V7.2 Repair Changelog

- Added native V7.2 S1 configs, canonical packaging path, current importer, and transactional
  acceptance while retaining V6 history.
- Replaced the vacuous primary operating point through preregistered development/validation,
  Pareto selection, freeze, and untouched confirmation.
- Characterized difficulty confounding and added label-isolated exploratory V8 corrections.
- Added effective-N, family-dependence, selective-decision, environment identity, replay, Kaggle
  notebooks, health metrics, and post-S1 recalibration gates.
""",
    }


def _runbook(root: Path, source_commit: str, source_tag: str) -> str:
    configs = []
    for benchmark in ("mmlu", "gsm8k", "bbh"):
        config = yaml.safe_load(
            (root / f"configs/runs_v7_2/{benchmark}_s1_v7_2.yaml").read_text(encoding="utf-8")
        )
        contract = yaml.safe_load(
            (root / config["benchmark_contract"]).read_text(encoding="utf-8")
        )
        panel = yaml.safe_load((root / config["panel_config"]).read_text(encoding="utf-8"))
        configs.append((benchmark, config, contract, panel))
    model_lines = "\n".join(
        f"- `{model['canonical_model_id']}` @ `{model['revision']}`"
        for model in configs[0][3]["models"]
    )
    revision_lines = "\n".join(
        f"- {benchmark}: `{contract['dataset_revision']}`"
        for benchmark, _, contract, _ in configs
    )
    return f"""# ValidEval V7.2 Kaggle S1 Runbook

Authorized source: `{source_tag}` at `{source_commit}`.

1. Check out exactly: `git checkout {source_tag}` and verify `git rev-parse HEAD` equals
   `{source_commit}`. Archive or upload this tagged tree without caches, secrets, or model weights.
2. In Kaggle choose two T4 GPUs, enable Internet for public Hugging Face downloads, and provide at
   least the fail-closed disk amount printed by notebook 00.
3. Run notebooks in order: `00_v7_2_t4x2_preflight.ipynb`, then the MMLU, GSM8K, and BBH notebooks,
   then `04_v7_2_s1_validate_package.ipynb` after placing all three ZIPs together.
4. Use `VALIDEVAL_EXECUTION_MODE=smoke`. For interrupted work use `resume`; do not change configs.
   Bounded batch fallback is allowed. Sequence-length fallback is forbidden. A persistent OOM or
   systemic model failure requires repair and rerun, never silent checkpoint substitution.

Exact checkpoints:

{model_lines}

Dataset revisions:

{revision_lines}

Download these files:

- `valideval_v7_2_s1_mmlu_s1-v7-2-mmlu.zip`
- `valideval_v7_2_s1_gsm8k_s1-v7-2-gsm8k.zip`
- `valideval_v7_2_s1_bbh_s1-v7-2-bbh.zip`

Place them in `kaggle_icml2027_outputs/packages`, then run:

```bash
python -m valideval accept-s1-v7-2 \
  --input-dir kaggle_icml2027_outputs/packages \
  --output-root imported/v7_2/s1
python -m valideval recalibrate-study-c-after-s1 \
  --input-root imported/v7_2/s1 \
  --output results/v7_2/planning/study_c_recalibration_after_s1.json
```

Accepted S1 unlocks engineering-health assessment and possible S2 authorization after measured
recalibration. It unlocks no benchmark-validity, ranking, transport, item-cause, or repair claim.
S3 remains blocked pending S2; S4 remains blocked pending S3.
"""


def _handoff(context: dict[str, Any]) -> str:
    confirmation = context["confirmation"]
    v8 = context["v8"]
    stress = context["stress"]
    validation = context["validation"]
    return f"""# ValidEval V7.2 Final Pre-Kaggle Handoff

## 1. Verdict

`VALID_EVAL_V7_2_KAGGLE_S1_AUTHORIZED`. This authorizes the exact engineering smoke, not a real
accepted S1 or any scientific claim.

## 2. V7.1 baseline

Source `f4f803a01daf89798d4b181e5610ce3f70355f32` and metadata child
`a649f664a884404afb889aedfe35f579dcf3f3fa` are preserved. The failed V7 primary grid is unchanged.

## 3. S1 bridge

Three native V7.2 configs and five canonical Kaggle notebooks use one package implementation.

## 4. Provenance

The source tag, commit, config hashes, revisions, prompt contracts, subsets, and archive checksums
are fail-closed.

## 5. Claim-policy vacuity

V7.1 full licensing remains the zero-power, 100%-abstention baseline.

## 6. Policy development

Development/validation are disjoint; `{context['policy_dev']['selected']['policy_id']}` was selected.

## 7. Pareto frontier

Dominated candidates were excluded on false licenses, power, abstention, and regret.

## 8. Policy confirmation

`{confirmation['status']}`: false licenses {confirmation['false_license_rate']:.4f}, power
{confirmation['true_license_power']:.4f}, abstention {confirmation['abstention_rate']:.4f}, regret
{confirmation['decision_regret']:.4f}.

## 9. Effective-N

`{stress['effective_n_stress_status']}`.

## 10. Family dependence

`{stress['family_dependence_status']}`.

## 11. Selective decisions

`{stress['selective_decision_status']}`.

## 12. Difficulty confound

`DIFFICULTY_CONFOUND_CHARACTERIZED`; historical AUPRC {v8['historical_v7_1_difficulty_negative_auprc']:.6f}.

## 13. V8 exploratory result

`V8_EXPLORATORY_IMPROVEMENT_FOUND`; V8 confirmation was not run or authorized.

## 14. MMLU adjusted diagnostics

Zero licensed discoveries; external labels, item length, and answer position were unavailable.

## 15. Synthetic boundaries

All policy and V8 results are generator-scoped. They do not prove behavior on real benchmarks.

## 16. Authorization

S1 run authorized; S2 blocked pending accepted S1; S3 blocked pending S2; S4 blocked pending S3.

## 17. Compute

Fourteen mandatory CPU activities produced artifacts under `results/v7_2`.

## 18. Tests and CI

Validation status: `{validation.get('status', 'PENDING_FINAL_VALIDATION')}`. See machine state for
individual test, lint, format, type, build, notebook, secret, release, and CI results.

## 19. Exact Kaggle instructions

Follow `VALID_EVAL_V7_2_KAGGLE_S1_RUNBOOK.md`. Start with
`kaggle_icml2027/00_v7_2_t4x2_preflight.ipynb`.

## 20. Remaining blockers

No real accepted S1, S2, S3, S4, V8 confirmation, transport validation, or human validation exists.

## 21. Exact next action

Check out `{context['source_tag']}`, run notebook 00 on Kaggle T4×2, and stop if its exact-source,
CUDA, disk, model, dataset, prompt, or subset preflight fails.
"""


def _machine_state(
    context: dict[str, Any], *, metadata_commit: str | None
) -> dict[str, Any]:
    validation = context["validation"]
    confirmation = context["confirmation"]
    v8 = context["v8"]
    stress = context["stress"]
    development = context["policy_dev"]
    return {
        "baseline_commit": "a649f664a884404afb889aedfe35f579dcf3f3fa",
        "final_source_commit": context["source_commit"],
        "final_source_tag": context["source_tag"],
        "metadata_commit": metadata_commit,
        "git_dirty": False,
        "ci": validation.get("ci", "PENDING_REMOTE_CI"),
        "v7_synthetic_primary_status": "V7_SYNTHETIC_PRIMARY_GRID_FAILED_AND_PRESERVED",
        "v7_1_control_status": "V7_1_SYNTHETIC_CONTROL_SUITE_COMPLETE",
        "s1_v7_2_bridge": "S1_V7_2_NATIVE_BRIDGE_READY",
        "s1_configs": [
            "configs/runs_v7_2/mmlu_s1_v7_2.yaml",
            "configs/runs_v7_2/gsm8k_s1_v7_2.yaml",
            "configs/runs_v7_2/bbh_s1_v7_2.yaml",
        ],
        "s1_source_provenance": "FINAL_TAG_AND_COMMIT_FAIL_CLOSED",
        "s1_package_schema": "CANONICAL_TEN_FILE_EXECUTION_PACKAGE",
        "s1_mock_integration": context["s1"]["status"],
        "s1_authorization": "S1_V7_2_AUTHORIZED",
        "claim_policy_v7_1_baseline": "V7_1_ULTRA_CONSERVATIVE_BASELINE",
        "claim_policy_selected": development["selected"]["policy_id"],
        "claim_policy_freeze_hash": confirmation["freeze_hash"],
        "claim_policy_confirmation": confirmation["status"],
        "claim_policy_false_license": confirmation["false_license_rate"],
        "claim_policy_power": confirmation["true_license_power"],
        "claim_policy_abstention": confirmation["abstention_rate"],
        "claim_policy_regret": confirmation["decision_regret"],
        "difficulty_confound_status": "DIFFICULTY_CONFOUND_CHARACTERIZED",
        "v8_development_status": "V8_EXPLORATORY_IMPROVEMENT_FOUND",
        "v8_freeze_status": "NOT_FROZEN_CONFIRMATORY_NOT_AUTHORIZED",
        "effective_n_stress": stress["effective_n_stress_status"],
        "family_dependence_stress": stress["family_dependence_status"],
        "selective_decision_status": stress["selective_decision_status"],
        "s2_authorization": "S2_BLOCKED_PENDING_ACCEPTED_S1",
        "s3_authorization": "S3_BLOCKED_PENDING_S2",
        "s4_authorization": "S4_BLOCKED_PENDING_S3",
        "tests": validation.get("tests", "PENDING_FINAL_VALIDATION"),
        "lint": validation.get("lint", "PENDING_FINAL_VALIDATION"),
        "format": validation.get("format", "PENDING_FINAL_VALIDATION"),
        "mypy": validation.get("mypy", "PENDING_FINAL_VALIDATION"),
        "build": validation.get("build", "PENDING_FINAL_VALIDATION"),
        "notebooks": validation.get("notebooks", "PENDING_FINAL_VALIDATION"),
        "release": validation.get("release", "PENDING_FINAL_VALIDATION"),
        "cpu_runs_completed": 14,
        "cpu_runtime_total_seconds": validation.get("cpu_runtime_total_seconds"),
        "remaining_blockers": [
            "No accepted real Kaggle T4x2 S1 package or measured S1 health distributions.",
            "S2 is blocked pending accepted S1 and post-S1 recalibration.",
            "S3 is blocked pending S2; S4 is blocked pending S3.",
            "V8 has no independent confirmatory freeze or run.",
            "No transport-validated or human-validated scientific claims are licensed.",
        ],
        "exact_next_action": (
            "Check out the final V7.2 tag and run kaggle_icml2027/"
            "00_v7_2_t4x2_preflight.ipynb on Kaggle T4x2."
        ),
        "v8_normalized_result_hash": v8["normalized_metrics_sha256"],
    }


def _json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _head(root: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()


if __name__ == "__main__":
    raise SystemExit(main())
