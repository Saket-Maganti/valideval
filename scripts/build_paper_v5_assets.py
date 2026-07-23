from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _escape(value: object) -> str:
    text = str(value)
    for source, replacement in [
        ("\\", r"\textbackslash{}"),
        ("_", r"\_"),
        ("%", r"\%"),
        ("&", r"\&"),
        ("#", r"\#"),
    ]:
        text = text.replace(source, replacement)
    return text


def main() -> int:
    ledger_path = ROOT / "results/evidence/claim_evidence_ledger_v5.csv"
    reproduction_path = ROOT / "results/evidence/mmlu_reproduction_v5/mmlu_reproduction_v5.json"
    if not ledger_path.exists() or not reproduction_path.exists():
        raise FileNotFoundError("Build V5 evidence reproduction and claim ledger first.")
    with ledger_path.open(encoding="utf-8", newline="") as handle:
        claims = list(csv.DictReader(handle))
    reproduction = json.loads(reproduction_path.read_text(encoding="utf-8"))
    output = ROOT / "paper/v5/tables"
    output.mkdir(parents=True, exist_ok=True)

    counts = Counter(row["verification_status"] for row in claims)
    evidence_lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{V5 claim states. Counts are categorical and are not combined into a score.}",
        r"\begin{tabular}{lr}",
        r"\toprule",
        r"State & Claims \\",
        r"\midrule",
    ]
    evidence_lines.extend(f"{_escape(key)} & {value} \\\\" for key, value in sorted(counts.items()))
    evidence_lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    (output / "evidence_status_v5.tex").write_text(
        "\n".join(evidence_lines) + "\n", encoding="utf-8"
    )

    observed = reproduction["observed"]
    metrics = [
        ("Models", observed["model_count"]),
        ("Items", observed["item_count"]),
        ("Subjects", observed["subject_count"]),
        ("Response rows", observed["row_count"]),
        ("Missing cells", observed["missing_cells"]),
        ("Contradictory duplicates", observed["contradictory_duplicates"]),
        ("Observed accuracy spread", f"{observed['ability_spread']:.6f}"),
    ]
    mmlu_lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Independently reproduced Study H panel integrity.}",
        r"\begin{tabular}{lr}",
        r"\toprule",
        r"Quantity & Reproduced value \\",
        r"\midrule",
    ]
    mmlu_lines.extend(f"{_escape(key)} & {_escape(value)} \\\\" for key, value in metrics)
    mmlu_lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    (output / "mmlu_reproduction_v5.tex").write_text("\n".join(mmlu_lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PAPER_V5_ASSETS_BUILT", "table_count": 2}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
