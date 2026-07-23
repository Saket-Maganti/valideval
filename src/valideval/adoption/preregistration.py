from __future__ import annotations

from pathlib import Path
from typing import Any

from valideval.schemas import utc_now


def generate_preregistration(
    *,
    benchmark: str,
    goal: str = "",
    domain: str = "general",
    panel: str = "TBD",
    artifact_scope: str = "TBD",
    diagnostics: list[str] | None = None,
    output_dir: str | Path = "docs/protocols",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"preregistration_{_slug(benchmark)}.md"
    path.write_text(
        _render_preregistration(
            benchmark=benchmark,
            goal=goal,
            domain=domain,
            panel=panel,
            artifact_scope=artifact_scope,
            diagnostics=diagnostics,
        ),
        encoding="utf-8",
    )
    return {
        "benchmark": benchmark,
        "domain": domain,
        "panel": panel,
        "artifact_scope": artifact_scope,
        "diagnostics": diagnostics or _default_diagnostics(domain),
        "path": str(path),
        "next_command": (
            "python3 -m valideval doctor "
            f"--benchmark {benchmark} --panel {panel if panel != 'TBD' else 'mock'}"
        ),
        "limitations": [
            "This preregistration scaffold must be edited before it represents an actual study plan."
        ],
    }


def _render_preregistration(
    *,
    benchmark: str,
    goal: str,
    domain: str,
    panel: str,
    artifact_scope: str,
    diagnostics: list[str] | None,
) -> str:
    selected_diagnostics = diagnostics or _default_diagnostics(domain)
    return "\n".join(
        [
            f"# Preregistration: {benchmark}",
            "",
            f"- Created: {utc_now()}",
            f"- Evaluation goal: {goal or 'TBD'}",
            f"- Domain: {domain}",
            f"- Model panel: {panel}",
            f"- Artifact scope: {artifact_scope}",
            f"- Planned diagnostics: {', '.join(selected_diagnostics)}",
            "",
            "## Benchmark Selection Criteria",
            "",
            "- Include benchmarks whose construct specification matches the intended decision.",
            "- Exclude benchmarks lacking item IDs, scoring rules, or provenance sufficient for this protocol.",
            "- Record access constraints, licenses, and any raw-content restrictions before public reporting.",
            "",
            "## Protocol Boundary",
            "",
            "- Validity will be reported as a multidimensional evidence profile, not one scalar score.",
            "- No paid API is a required dependency of this protocol.",
            "- Local or cached artifacts are preferred when response generation is not the research question.",
            "- Diagnostic evidence is conditional on the selected panel, prompt variants, and artifact scope.",
            "- Public reports must avoid raw restricted item text and raw model outputs when access is limited.",
            "",
            "## Hypotheses",
            "",
            "- Diagnostics may reveal evidence consistent with shortcut, scoring, reliability, or provenance threats.",
            "- Ranking changes will be reported as protocol-dependent evidence, not as true model order.",
            "",
            "## Diagnostics",
            "",
            *[f"- {diagnostic}" for diagnostic in selected_diagnostics],
            "",
            "## Claim-to-Evidence Map",
            "",
            "| Claim boundary | Required evidence | Reporting language |",
            "| --- | --- | --- |",
            (
                "| Shortcut threat | Baselines, answer artifacts, shortcut ablations | "
                "Evidence consistent with shortcut availability under this protocol |"
            ),
            (
                "| Item quality | IRT, distractor quality, saturation, power | "
                "Potential validity threat requiring item review |"
            ),
            (
                "| Scoring stability | Extraction robustness, reliability, human/judge agreement | "
                "Requires validation before score interpretation |"
            ),
            (
                "| Contamination/provenance | Local forensics and provenance completeness | "
                "Corpus-dependent signal, not proof of cleanliness |"
            ),
            "",
            "## Exclusion Rules",
            "",
            "- Exclude malformed items before scoring and record counts.",
            "- Exclude repaired-subset items only under documented repair policies and report removed IDs.",
            "",
            "## Tests and Multiplicity",
            "",
            "- Treat each diagnostic as a separate signal.",
            "- Where hypothesis tests are used, report correction policy and uncorrected values.",
            "- Do not combine validity evidence into one scalar score.",
            "",
            "## Reporting Plan",
            "",
            "- Report assumptions, confidence intervals when available, missing-evidence warnings, and limitations.",
            "- Include local artifacts, hashes, and reproduction commands.",
            "- Keep blocked diagnostics visible rather than replacing them with weaker substitute claims.",
            "- Avoid phrases such as proves contamination, benchmark is worthless, or true ranking.",
            "",
            "## Blocked or Negative Evidence",
            "",
            "- If required local inputs are missing, stop at readiness reporting.",
            "- If a cache-only audit lacks matrices, report the missing variants and do not generate new outputs.",
            "- If diagnostic coverage is incomplete, label findings preliminary or unavailable as applicable.",
            "- Negative or null diagnostic results remain part of the evidence profile.",
            "",
            "## Surprising Results",
            "",
            "- A shallow baseline close to the model panel.",
            "- Large ranking flips under prompt/scorer/repair conditions.",
            "- High local overlap or missing provenance in benchmark-critical items.",
            "",
            "## Limitations",
            "",
            "- Validity evidence is conditional on the corpus, model panel, scoring protocol, and diagnostics run.",
            "- Preregistration text is a protocol scaffold until reviewed and frozen by benchmark authors.",
            "",
        ]
    )


def _default_diagnostics(domain: str) -> list[str]:
    diagnostics = [
        "shallow baselines and answer artifacts",
        "reliability and prompt sensitivity",
        "item quality or IRT where response matrices are available",
        "data forensics and provenance completeness",
        "human or judge reliability when open-ended scoring is used",
    ]
    domain_lower = domain.lower()
    if "rag" in domain_lower:
        diagnostics.extend(["RAG faithfulness signals", "abstention or unanswerable balance"])
    elif "safety" in domain_lower:
        diagnostics.extend(["policy-version stability", "rubric and judge sensitivity"])
    elif "code" in domain_lower:
        diagnostics.extend(["hidden-test strength", "flaky rerun sensitivity"])
    return diagnostics


def _slug(value: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "_" for char in value).strip("_")
    return slug or "benchmark"
