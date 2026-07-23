from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from valideval.evidence.status import EvidenceStatus

LEDGER_COLUMNS = [
    "claim_id",
    "claim_text",
    "claim_category",
    "paper_location",
    "reported_value",
    "verification_status",
    "primary_inputs",
    "reproduction_command",
    "observed_value",
    "tolerance",
    "code_revision",
    "input_hashes",
    "output_hashes",
    "allowed_wording",
    "blocked_wording",
    "notes",
]


def build_claim_evidence_ledger(
    root: str | Path,
    output_csv: str | Path,
    output_markdown: str | Path,
) -> list[dict[str, str]]:
    repository = Path(root)
    reproduction_path = (
        repository / "results/evidence/mmlu_reproduction_v5/mmlu_reproduction_v5.json"
    )
    if not reproduction_path.exists():
        raise FileNotFoundError(
            "Run scripts/reproduce_mmlu_evidence_v5.py before building the ledger."
        )
    reproduction = json.loads(reproduction_path.read_text(encoding="utf-8"))
    observed = reproduction["observed"]
    input_hashes = json.dumps(reproduction["hashes"], sort_keys=True)
    reproduction_outputs = [
        repository / "results/evidence/mmlu_reproduction_v5/mmlu_reproduction_v5.json",
        repository / "results/evidence/mmlu_reproduction_v5/matrix.reconstructed.v5.csv",
        repository / "results/evidence/mmlu_reproduction_v5/reported_vs_reproduced_v5.csv",
    ]
    output_hashes = json.dumps(
        {str(path.relative_to(repository)): _sha256(path) for path in reproduction_outputs},
        sort_keys=True,
    )
    reproduce_command = "python3 scripts/reproduce_mmlu_evidence_v5.py"
    rows = [
        _row(
            "MMLU-H-001",
            "The public HELM-derived MMLU panel contains 39 models and 14,042 items.",
            "historical_panel_provenance",
            "paper/main.tex:historical MMLU study",
            "39 models; 14,042 items",
            EvidenceStatus.REPRODUCED,
            "data/external/mmlu/prediction_details_wide.jsonl",
            reproduce_command,
            f"{observed['model_count']} models; {observed['item_count']} items",
            "exact",
            input_hashes,
            output_hashes,
            "Analysis of a public HELM-derived MMLU response panel covered 39 models and 14,042 items.",
            "ValidEval executed 39 models on MMLU.",
            "Study H is historical/imported, not a ValidEval-controlled execution.",
        ),
        _row(
            "MMLU-H-002",
            "The HELM-derived matrix has 547,638 observations and zero missing cells.",
            "data_integrity",
            "paper/main.tex:historical MMLU study",
            "547,638; zero missing",
            EvidenceStatus.REPRODUCED,
            "data/external/mmlu/prediction_details_wide.jsonl",
            reproduce_command,
            f"{observed['row_count']}; {observed['missing_cells']} missing",
            "exact",
            input_hashes,
            output_hashes,
            "The reconstructed matrix exactly matched the cached 547,638-cell matrix with no missing cells.",
            "The matrix proves benchmark validity.",
            "Completeness is a data-integrity property, not psychometric validation.",
        ),
        _row(
            "MMLU-H-003",
            "Observed aggregate accuracy spread is approximately 0.580188.",
            "descriptive_measurement",
            "paper/main.tex:historical MMLU study",
            "0.5801880074063523",
            EvidenceStatus.REPRODUCED,
            "cache/mmlu/wide/matrix.csv",
            reproduce_command,
            str(observed["ability_spread"]),
            "1e-12",
            input_hashes,
            output_hashes,
            "Under this imported panel, observed accuracy spanned about 0.5802.",
            "The ability spread validates IRT assumptions.",
            "Spread is part of minimum matrix adequacy only.",
        ),
        _row(
            "MMLU-H-004",
            "Subject-level raw rank ranges have median 19 and maximum 30.",
            "descriptive_ranking",
            "paper/main.tex:rank sensitivity",
            "median 19; maximum 30",
            EvidenceStatus.REPRODUCED,
            "cache/mmlu/wide/matrix.csv",
            reproduce_command,
            f"median {observed['median_subject_rank_range']}; maximum {observed['maximum_subject_rank_range']}",
            "exact",
            input_hashes,
            output_hashes,
            "Raw subject-conditioned ranks vary under this diagnostic protocol.",
            "The rank ranges prove material instability or benchmark invalidity.",
            "Materiality requires the V5 null-calibrated analysis.",
        ),
        _row(
            "MMLU-H-005",
            "Proxy diagnostic weighting stays close to accuracy ranking.",
            "proxy_ranking",
            "paper/main.tex:diagnostic-weighted ranking",
            "Spearman 0.9979757085; Kendall 0.9784075574; max delta 2",
            EvidenceStatus.REPRODUCED,
            "cache/mmlu/wide/matrix.csv; results/mmlu/irt_proxy/item_parameters.csv",
            reproduce_command,
            (
                f"Spearman {observed['diagnostic_weighted_spearman']}; "
                f"Kendall {observed['diagnostic_weighted_kendall']}; "
                f"max delta {observed['diagnostic_weighted_max_abs_rank_delta']}"
            ),
            "1e-12 for correlations; exact ranks",
            input_hashes,
            output_hashes,
            "The proxy-weighted ranking was close to aggregate accuracy under this protocol.",
            "This is the true ranking or a full 2PL result.",
            "The weighting source is an item-level proxy.",
        ),
        _row(
            "MMLU-H-006",
            "A raw rank range of at least 10 is a severe/material effect.",
            "post_hoc_threshold",
            "legacy materiality reports",
            "37 models severe",
            EvidenceStatus.RETIRED,
            "results/mmlu/deep_diagnostic_value/materiality_summary.json",
            reproduce_command,
            f"{observed['models_rank_range_ge_10_exploratory']} models cross an exploratory threshold",
            "not applicable",
            input_hashes,
            output_hashes,
            "Thirty-seven models crossed the legacy exploratory threshold; V5 does not interpret that threshold as severity.",
            "Thirty-seven models show severe instability.",
            "The threshold was not theory- or decision-calibrated.",
        ),
        _row(
            "MMLU-ABL-001",
            "The legacy eight-family output is a genuine diagnostic-family ablation.",
            "ablation",
            "legacy ablation report/table",
            "8 families; complete",
            EvidenceStatus.CONTRADICTED,
            "results/mmlu/diagnostic_family_ablation/diagnostic_family_ablation.csv",
            "static V5 code and artifact audit",
            "Seven named variants reuse accuracy-derived values; not a valid family ablation.",
            "exact code-path inspection",
            "{}",
            "{}",
            "The legacy table is retained as a historical artifact and excluded from V5 evidence.",
            "Eight diagnostic families were independently ablated.",
            "A future confirmatory ablation remains required.",
        ),
        _row(
            "REDUX-001",
            "MMLU-Redux provides confirmed item-level external validation.",
            "external_validation",
            "paper/main.tex:external validation",
            "weak structural metrics reported",
            EvidenceStatus.RETIRED,
            "results/mmlu/redux_alignment_rescue/*",
            "python3 -m pytest -q tests/test_mmlu_redux_linkage_v5.py",
            "No confirmed direct ID or content-hash linkage in sanitized local artifacts.",
            "confirmed identity required",
            "{}",
            "{}",
            "The Redux analysis is an unsuccessful exploratory linkage attempt.",
            "Redux validates ValidEval item-level detection.",
            "Structural subject/index alignment is not item identity.",
        ),
        _blocked_row(
            "STUDY-C-001",
            "Exact-model cross-benchmark transfer is established.",
            "cross_benchmark",
            "paper/main.tex:controlled common-panel study",
            "No controlled common-panel outputs are present.",
        ),
        _blocked_row(
            "HUMAN-001",
            "Human review confirms benchmark issues.",
            "human_validation",
            "paper/main.tex:human validation",
            "No human labels are present.",
        ),
        _blocked_row(
            "SYNTHETIC-001",
            "The decoupled synthetic protocol has confirmatory sensitivity/specificity evidence.",
            "synthetic_validation",
            "paper/main.tex:synthetic validation",
            "The V5 protocol is build-only; results remain required.",
        ),
    ]
    destination_csv = Path(output_csv)
    destination_csv.parent.mkdir(parents=True, exist_ok=True)
    with destination_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEDGER_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    destination_md = Path(output_markdown)
    destination_md.parent.mkdir(parents=True, exist_ok=True)
    destination_md.write_text(_render_markdown(rows), encoding="utf-8")
    return rows


def _row(
    claim_id: str,
    claim_text: str,
    category: str,
    paper_location: str,
    reported_value: str,
    status: EvidenceStatus,
    primary_inputs: str,
    command: str,
    observed_value: str,
    tolerance: str,
    input_hashes: str,
    output_hashes: str,
    allowed_wording: str,
    blocked_wording: str,
    notes: str,
) -> dict[str, str]:
    return dict(
        zip(
            LEDGER_COLUMNS,
            [
                claim_id,
                claim_text,
                category,
                paper_location,
                reported_value,
                status.value,
                primary_inputs,
                command,
                observed_value,
                tolerance,
                "",
                input_hashes,
                output_hashes,
                allowed_wording,
                blocked_wording,
                notes,
            ],
            strict=True,
        )
    )


def _blocked_row(
    claim_id: str,
    claim_text: str,
    category: str,
    paper_location: str,
    notes: str,
) -> dict[str, str]:
    return _row(
        claim_id,
        claim_text,
        category,
        paper_location,
        "RESULT_REQUIRED",
        EvidenceStatus.BLOCKED,
        "",
        "",
        "",
        "not applicable",
        "{}",
        "{}",
        "[RESULT REQUIRED: exact artifact]",
        claim_text,
        notes,
    )


def _render_markdown(rows: list[dict[str, str]]) -> str:
    counts = Counter(row["verification_status"] for row in rows)
    lines = [
        "# ValidEval V5 Claim-Evidence Ledger",
        "",
        "This is the paper-facing claim gate. Evidence states are categorical, not a scalar score.",
        "",
        "## Status counts",
        "",
    ]
    lines.extend(f"- `{status}`: {count}" for status, count in sorted(counts.items()))
    lines.extend(["", "## Claims", ""])
    for row in rows:
        lines.extend(
            [
                f"### {row['claim_id']} — `{row['verification_status']}`",
                "",
                f"- Claim: {row['claim_text']}",
                f"- Observed: {row['observed_value'] or 'Not available'}",
                f"- Allowed wording: {row['allowed_wording']}",
                f"- Blocked wording: {row['blocked_wording']}",
                f"- Reproduction: `{row['reproduction_command'] or 'BLOCKED'}`",
                "",
            ]
        )
    return "\n".join(lines)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
