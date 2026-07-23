#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
START = "<!-- V4_PRE_EXECUTION_CLAIMS_START -->"
END = "<!-- V4_PRE_EXECUTION_CLAIMS_END -->"


def main() -> int:
    args = parse_args()
    evidence = build_evidence_rows()
    table_paths = write_evidence_tables(evidence)
    claims_path = update_claims_ledger(evidence)
    evidence_path = PAPER / "current_evidence_state.md"
    evidence_path.write_text(render_evidence_state(evidence), encoding="utf-8")
    compile_result = compile_paper() if args.compile else {"status": "skipped"}
    audit = audit_paper_logs()
    payload = {
        "schema_version": "v4",
        "status": "ok" if compile_result.get("status") == "ok" else "needs_review",
        "tables": table_paths,
        "claims_ledger": str(claims_path),
        "evidence_state": str(evidence_path),
        "compile": compile_result,
        "audit": audit,
        "final_verdict": "PAPER_AUTO_UPDATE_READY"
        if compile_result.get("status") == "ok" and not audit["unresolved_citation_lines"]
        else "PAPER_AUTO_UPDATE_NEEDS_FIXES",
    }
    report_json = ROOT / "results" / "paper_update_v4" / "paper_update_report.json"
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_md = ROOT / "PAPER_AUTO_UPDATE_V4_REPORT.md"
    report_md.write_text(render_report(payload), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["final_verdict"] == "PAPER_AUTO_UPDATE_READY" else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update ValidEval paper surfaces from real artifacts only."
    )
    parser.add_argument("--no-compile", dest="compile", action="store_false")
    parser.set_defaults(compile=True)
    return parser.parse_args()


def build_evidence_rows() -> list[dict[str, str]]:
    mmlu_panel = load_json(ROOT / "results" / "mmlu" / "panel_validity" / "panel_validity.json")
    rows = [
        {
            "artifact": "MMLU 39-model panel",
            "path": "cache/mmlu/wide/matrix.csv",
            "state": "REAL_ARTIFACT"
            if (ROOT / "cache/mmlu/wide/matrix.csv").exists()
            else "MISSING",
            "claim": "MMLU panel diagnostics are artifact-backed and protocol-scoped.",
        },
        {
            "artifact": "MMLU panel validity",
            "path": "results/mmlu/panel_validity/panel_validity.json",
            "state": str(mmlu_panel.get("status", "missing")).upper(),
            "claim": "Panel shape supports local psychometric diagnostics when status is pass.",
        },
        {
            "artifact": "MMLU deep diagnostics",
            "path": "results/mmlu/deep_diagnostic_value",
            "state": "REAL_ARTIFACT"
            if (ROOT / "results/mmlu/deep_diagnostic_value").exists()
            else "MISSING",
            "claim": "Subject-level ranking sensitivity under the stated protocol.",
        },
        {
            "artifact": "GSM8K imported outputs",
            "path": "cache/gsm8k/wide/matrix.csv",
            "state": "REAL_ARTIFACT"
            if (ROOT / "cache/gsm8k/wide/matrix.csv").exists()
            else "RESULT_REQUIRED",
            "claim": "No GSM8K result claim until imported ZIP validates.",
        },
        {
            "artifact": "BBH imported outputs",
            "path": "cache/bbh/wide/matrix.csv",
            "state": "REAL_ARTIFACT"
            if (ROOT / "cache/bbh/wide/matrix.csv").exists()
            else "RESULT_REQUIRED",
            "claim": "No third-benchmark transfer claim until imported matrix validates.",
        },
        {
            "artifact": "Cross-benchmark analysis",
            "path": "results/cross_benchmark/cross_benchmark_manifest.json",
            "state": cross_state(),
            "claim": "Requires at least two validated benchmark matrices.",
        },
        {
            "artifact": "Human labels",
            "path": "results/*/human",
            "state": "RESULT_REQUIRED",
            "claim": "No human-label validation claim exists in V4 pre-execution state.",
        },
        {
            "artifact": "External labels beyond MMLU-Redux",
            "path": "schemas/external_label.schema.json",
            "state": "RESULT_REQUIRED",
            "claim": "Schema exists; new external-label evidence is not present.",
        },
    ]
    return rows


def cross_state() -> str:
    manifest = load_json(ROOT / "results" / "cross_benchmark" / "cross_benchmark_manifest.json")
    if manifest.get("status") == "ok":
        return "REAL_ARTIFACT"
    return "RESULT_REQUIRED"


def write_evidence_tables(rows: list[dict[str, str]]) -> dict[str, str]:
    table_dir = PAPER / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    csv_path = table_dir / "v4_evidence_state_summary.csv"
    tex_path = table_dir / "v4_evidence_state_summary.tex"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["artifact", "path", "state", "claim"])
        writer.writeheader()
        writer.writerows(rows)
    tex_path.write_text(render_tex_table(rows), encoding="utf-8")
    return {"csv": str(csv_path), "tex": str(tex_path)}


def update_claims_ledger(rows: list[dict[str, str]]) -> Path:
    path = PAPER / "CLAIMS_LEDGER.md"
    current = path.read_text(encoding="utf-8") if path.exists() else "# Claims Ledger\n"
    block = "\n".join([START, "", "## V4 Pre-Execution Claims", ""])
    for row in rows:
        block += f"- `{row['state']}` `{row['artifact']}`: {row['claim']} (`{row['path']}`)\n"
    block += "\n" + END + "\n"
    if START in current and END in current:
        before = current.split(START, 1)[0].rstrip()
        after = current.split(END, 1)[1].lstrip()
        updated = before + "\n\n" + block + "\n" + after
    else:
        updated = current.rstrip() + "\n\n" + block
    path.write_text(updated, encoding="utf-8")
    return path


def compile_paper() -> dict[str, Any]:
    if shutil.which("pdflatex") is None or shutil.which("bibtex") is None:
        return {"status": "blocked", "reason": "pdflatex_or_bibtex_not_found"}
    commands = [
        ["pdflatex", "-interaction=nonstopmode", "main.tex"],
        ["bibtex", "main"],
        ["pdflatex", "-interaction=nonstopmode", "main.tex"],
        ["pdflatex", "-interaction=nonstopmode", "main.tex"],
    ]
    runs = []
    for command in commands:
        proc = subprocess.run(
            command,
            cwd=PAPER,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        runs.append({"command": " ".join(command), "returncode": proc.returncode})
    pdf = PAPER / "main.pdf"
    return {
        "status": "ok"
        if pdf.exists() and all(run["returncode"] == 0 for run in runs)
        else "failed",
        "pdf": str(pdf) if pdf.exists() else None,
        "runs": runs,
    }


def audit_paper_logs() -> dict[str, Any]:
    log_path = PAPER / "main.log"
    blg_path = PAPER / "main.blg"
    log = log_path.read_text(encoding="utf-8", errors="ignore") if log_path.exists() else ""
    blg = blg_path.read_text(encoding="utf-8", errors="ignore") if blg_path.exists() else ""
    tex_files = [PAPER / "main.tex", *sorted((PAPER / "sections").glob("*.tex"))]
    placeholders = []
    for path in tex_files:
        text = path.read_text(encoding="utf-8")
        for idx, line in enumerate(text.splitlines(), start=1):
            if "TO BE FILLED" in line or "PLACEHOLDER" in line:
                placeholders.append(f"{path.relative_to(ROOT)}:{idx}: {line.strip()}")
    return {
        "unresolved_citation_lines": [
            line.strip()
            for line in (log + "\n" + blg).splitlines()
            if "Citation" in line and "undefined" in line
        ],
        "missing_figure_lines": [
            line.strip() for line in log.splitlines() if "File `" in line and "not found" in line
        ],
        "placeholder_lines": placeholders,
    }


def render_evidence_state(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Current Evidence State",
        "",
        "| Artifact | State | Claim boundary |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(f"| {row['artifact']} | `{row['state']}` | {row['claim']} |")
    return "\n".join(lines) + "\n"


def render_tex_table(rows: list[dict[str, str]]) -> str:
    body = "\n".join(
        f"{latex_escape(row['artifact'])} & {latex_escape(row['state'])} & {latex_escape(row['claim'])} \\\\"
        for row in rows
    )
    return (
        "\\begin{tabular}{lll}\n"
        "\\toprule\n"
        "Artifact & State & Claim boundary \\\\\n"
        "\\midrule\n"
        f"{body}\n"
        "\\bottomrule\n"
        "\\end{tabular}\n"
    )


def render_report(payload: dict[str, Any]) -> str:
    audit = payload["audit"]
    lines = [
        "# Paper Auto Update V4 Report",
        "",
        f"- Status: `{payload['status']}`",
        f"- Final verdict: `{payload['final_verdict']}`",
        f"- Compile status: `{payload['compile'].get('status')}`",
        f"- Unresolved citation lines: {len(audit['unresolved_citation_lines'])}",
        f"- Missing figure lines: {len(audit['missing_figure_lines'])}",
        f"- Placeholder lines preserved/reported: {len(audit['placeholder_lines'])}",
        "",
        "The updater reads existing artifacts only and preserves blocked evidence states.",
    ]
    return "\n".join(lines) + "\n"


def latex_escape(value: str) -> str:
    return (
        value.replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("_", "\\_")
        .replace("#", "\\#")
    )


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
