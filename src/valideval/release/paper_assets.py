from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

PLACEHOLDER = "[TO BE FILLED AFTER RUNNING AUDIT]"

FIGURE_SPECS = [
    "framework_diagram",
    "shortcut_retention",
    "dumb_baseline_gap",
    "irt_difficulty_discrimination",
    "subset_fidelity",
    "naive_vs_validity_adjusted_rankings",
    "reliability",
    "judge_human_agreement",
    "saturation",
    "repair_before_after",
]

TABLE_SPECS = [
    "audited_benchmarks",
    "model_panel",
    "diagnostic_summary",
    "shortcut_results",
    "irt_item_quality",
    "ranking_flips",
    "subset_fidelity",
    "reliability",
    "human_agreement",
    "certificate_status",
]


def generate_paper_assets(
    *,
    benchmark: str = "toy_mcq",
    panel: str = "mock",
    results_root: str | Path = "results",
    paper_dir: str | Path = "paper",
) -> dict[str, Any]:
    paper = Path(paper_dir)
    figures_dir = paper / "figures"
    tables_dir = paper / "tables"
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    result_dir = Path(results_root) / benchmark / panel
    manifest_path = Path(results_root) / benchmark / "manifest.json"
    context = {
        "benchmark": benchmark,
        "panel": panel,
        "result_dir": result_dir,
        "manifest_path": manifest_path,
        "results": _load_results(result_dir),
        "manifest": _read_json(manifest_path),
        "item_forensics": _read_csv(result_dir / "item_forensics.csv"),
    }
    figures = {
        name: str(_write_figure(name, figures_dir / f"{name}.svg", context))
        for name in FIGURE_SPECS
    }
    tables = {
        name: str(_write_table(name, tables_dir / f"{name}.tex", context)) for name in TABLE_SPECS
    }
    index_path = paper / "assets_manifest.json"
    payload = {
        "schema_version": "0.1",
        "benchmark": benchmark,
        "panel": panel,
        "figures": figures,
        "tables": tables,
        "limitations": [
            "Figures and tables are generated only from local result artifacts. Missing artifacts produce labeled placeholders."
        ],
    }
    index_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    payload["assets_manifest"] = str(index_path)
    return payload


def _write_figure(name: str, path: Path, context: dict[str, Any]) -> Path:
    result_dir = context["result_dir"]
    if name == "framework_diagram":
        return _svg(
            path,
            "Validity Evidence Profile",
            "Conceptual scaffold; no empirical values are plotted.",
            ["Construct", "Items", "Scoring", "Diagnostics", "Claims"],
        )
    if name == "shortcut_retention":
        shortcut = context["results"].get("shortcut")
        if shortcut:
            rows = _summary_rows(shortcut)
            return _svg(
                path, "Shortcut Retention", _artifact_note(result_dir / "shortcut.json"), rows
            )
        return _placeholder_svg(path, "Shortcut Retention", result_dir / "shortcut.json")
    if name == "dumb_baseline_gap":
        baselines = context["results"].get("baselines")
        if baselines:
            metrics = baselines.get("summary_metrics", {})
            rows = [
                f"Best shallow baseline: {_fmt_nested(metrics.get('best_shallow_baseline'))}",
                f"Dumb baseline gap: {_fmt(metrics.get('dumb_baseline_gap'))}",
            ]
            return _svg(
                path, "Dumb Baseline Gap", _artifact_note(result_dir / "baselines.json"), rows
            )
        return _placeholder_svg(path, "Dumb Baseline Gap", result_dir / "baselines.json")
    if name == "irt_difficulty_discrimination":
        irt = context["results"].get("irt")
        if irt:
            per_item = irt.get("per_item_metrics", {})
            rows = [
                f"{item_id}: difficulty={_fmt(values.get('difficulty'))}, discrimination={_fmt(values.get('discrimination'))}"
                for item_id, values in list(per_item.items())[:8]
            ]
            return _svg(
                path, "IRT Difficulty/Discrimination", _artifact_note(result_dir / "irt.json"), rows
            )
        return _placeholder_svg(path, "IRT Difficulty/Discrimination", result_dir / "irt.json")
    if name == "subset_fidelity":
        repair = context["results"].get("repair_diff")
        if repair:
            ranking = repair.get("ranking_fidelity", {})
            rows = [
                f"Original items: {_fmt(repair.get('original_item_count'))}",
                f"Repaired items: {_fmt(repair.get('repaired_item_count'))}",
                f"Spearman: {_fmt(ranking.get('spearman'))}",
            ]
            return _svg(
                path, "Subset Fidelity", _artifact_note(result_dir / "repair_diff.json"), rows
            )
        return _placeholder_svg(path, "Subset Fidelity", result_dir / "repair_diff.json")
    if name == "naive_vs_validity_adjusted_rankings":
        rankings = context["results"].get("ranking_views")
        if rankings:
            views = rankings.get("views", rankings)
            rows = [f"{key}: available" for key in list(views)[:8]]
            return _svg(
                path, "Ranking Views", _artifact_note(result_dir / "ranking_views.json"), rows
            )
        return _placeholder_svg(path, "Ranking Views", result_dir / "ranking_views.json")
    if name == "reliability":
        reliability = context["results"].get("reliability")
        if reliability:
            rows = _summary_rows(reliability)
            return _svg(path, "Reliability", _artifact_note(result_dir / "reliability.json"), rows)
        return _placeholder_svg(path, "Reliability", result_dir / "reliability.json")
    if name == "judge_human_agreement":
        human = _read_json(result_dir / "human" / "agreement_report.json")
        if human:
            rows = [
                f"Raw agreement: {_fmt(human.get('raw_agreement'))}",
                f"Cohen kappa: {_fmt(human.get('cohen_kappa'))}",
                f"Annotated items: {_fmt(human.get('n_items'))}",
            ]
            return _svg(
                path,
                "Judge/Human Agreement",
                _artifact_note(result_dir / "human" / "agreement_report.json"),
                rows,
            )
        return _placeholder_svg(
            path, "Judge/Human Agreement", result_dir / "human" / "agreement_report.json"
        )
    if name == "saturation":
        saturation = context["results"].get("saturation")
        if saturation:
            rows = _summary_rows(saturation)
            return _svg(path, "Saturation", _artifact_note(result_dir / "saturation.json"), rows)
        return _placeholder_svg(path, "Saturation", result_dir / "saturation.json")
    if name == "repair_before_after":
        repair = context["results"].get("repair_diff")
        if repair:
            rows = [
                f"Before: {_fmt(repair.get('original_item_count'))} items",
                f"After: {_fmt(repair.get('repaired_item_count'))} items",
                f"Removed: {_fmt(repair.get('removed_item_count'))} items",
            ]
            return _svg(
                path, "Repair Before/After", _artifact_note(result_dir / "repair_diff.json"), rows
            )
        return _placeholder_svg(path, "Repair Before/After", result_dir / "repair_diff.json")
    return _placeholder_svg(path, name.replace("_", " ").title(), result_dir / f"{name}.json")


def _write_table(name: str, path: Path, context: dict[str, Any]) -> Path:
    result_dir = context["result_dir"]
    results = context["results"]
    if name == "audited_benchmarks":
        manifest = context["manifest"]
        rows = [
            ["Benchmark", context["benchmark"]],
            ["Panel", context["panel"]],
            ["Item count", _fmt(manifest.get("item_count")) if manifest else PLACEHOLDER],
            ["Manifest", "available" if manifest else PLACEHOLDER],
        ]
        return _latex_table(path, "Audited Benchmarks", ["Field", "Value"], rows)
    if name == "model_panel":
        ranking = results.get("ranking_views")
        models = _model_ids_from_ranking(ranking)
        rows = [[model] for model in models] if models else [[PLACEHOLDER]]
        return _latex_table(path, "Model Panel", ["Model"], rows)
    if name == "diagnostic_summary":
        rows = [
            [
                payload.get("diagnostic_name", diagnostic),
                payload.get("version", ""),
                str(len(payload.get("warnings", []))),
            ]
            for diagnostic, payload in sorted(results.items())
            if isinstance(payload, dict) and "diagnostic_name" in payload
        ]
        return _latex_table(
            path,
            "Diagnostic Summary",
            ["Diagnostic", "Version", "Warnings"],
            rows or [[PLACEHOLDER, "", ""]],
        )
    if name == "shortcut_results":
        return _table_from_summary(
            path, "Shortcut Results", results.get("shortcut"), result_dir / "shortcut.json"
        )
    if name == "irt_item_quality":
        irt = results.get("irt")
        if irt:
            rows = [
                [item_id, _fmt(values.get("difficulty")), _fmt(values.get("discrimination"))]
                for item_id, values in list(irt.get("per_item_metrics", {}).items())[:12]
            ]
            return _latex_table(
                path, "IRT Item Quality", ["Item", "Difficulty", "Discrimination"], rows
            )
        return _placeholder_table(path, "IRT Item Quality", result_dir / "irt.json")
    if name == "ranking_flips":
        flips = results.get("ranking_flips")
        rows = _json_rows(flips, limit=8)
        return _latex_table(
            path,
            "Ranking Flips",
            ["Signal", "Value"],
            rows or [[PLACEHOLDER, str(result_dir / "ranking_flips.json")]],
        )
    if name == "subset_fidelity":
        repair = results.get("repair_diff")
        return _table_from_dict(
            path,
            "Subset Fidelity",
            repair or {},
            ["original_item_count", "repaired_item_count", "removed_item_count"],
        )
    if name == "reliability":
        return _table_from_summary(
            path, "Reliability", results.get("reliability"), result_dir / "reliability.json"
        )
    if name == "human_agreement":
        human = _read_json(result_dir / "human" / "agreement_report.json")
        return _table_from_dict(
            path,
            "Human Agreement",
            human or {},
            ["n_items", "n_judgments", "raw_agreement", "cohen_kappa"],
        )
    if name == "certificate_status":
        certificate = results.get("validity_certificate")
        return _table_from_dict(
            path, "Certificate Status", certificate or {}, ["profile_level", "interpretation"]
        )
    return _placeholder_table(path, name.replace("_", " ").title(), result_dir / f"{name}.json")


def _load_results(result_dir: Path) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for path in sorted(result_dir.glob("*.json")):
        output[path.stem] = _read_json(path)
    return output


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {"value": payload}


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _summary_rows(payload: dict[str, Any], *, limit: int = 8) -> list[str]:
    summary = payload.get("summary_metrics", payload)
    rows: list[str] = []
    for key, value in list(summary.items())[:limit]:
        rows.append(f"{key}: {_fmt_nested(value)}")
    return rows or [PLACEHOLDER]


def _json_rows(payload: dict[str, Any] | None, *, limit: int = 8) -> list[list[str]]:
    if not payload:
        return []
    rows: list[list[str]] = []
    for key, value in list(payload.items())[:limit]:
        rows.append([str(key), _fmt_nested(value)])
    return rows


def _table_from_summary(
    path: Path, caption: str, payload: dict[str, Any] | None, artifact: Path
) -> Path:
    if not payload:
        return _placeholder_table(path, caption, artifact)
    rows = _json_rows(payload.get("summary_metrics", payload), limit=10)
    return _latex_table(path, caption, ["Metric", "Value"], rows)


def _table_from_dict(path: Path, caption: str, payload: dict[str, Any], keys: list[str]) -> Path:
    rows = [[key, _fmt_nested(payload.get(key, PLACEHOLDER))] for key in keys]
    if all(row[1] == PLACEHOLDER for row in rows):
        rows = [[PLACEHOLDER, "missing result artifact"]]
    return _latex_table(path, caption, ["Field", "Value"], rows)


def _model_ids_from_ranking(ranking: dict[str, Any] | None) -> list[str]:
    if not ranking:
        return []
    views = ranking.get("views", {})
    for view in views.values() if isinstance(views, dict) else []:
        rows = view.get("ranking", []) if isinstance(view, dict) else []
        model_ids = [
            str(row.get("model_id"))
            for row in rows
            if isinstance(row, dict) and row.get("model_id")
        ]
        if model_ids:
            return model_ids
    return []


def _placeholder_svg(path: Path, title: str, artifact: Path) -> Path:
    return _svg(path, title, f"Missing artifact: {artifact}", [PLACEHOLDER])


def _svg(path: Path, title: str, subtitle: str, rows: list[str]) -> Path:
    height = max(180, 96 + 24 * len(rows))
    safe_title = _xml(title)
    safe_subtitle = _xml(subtitle)
    lines = "\n".join(
        f'<text x="32" y="{110 + index * 24}" font-size="14" fill="#1f2937">{_xml(row[:140])}</text>'
        for index, row in enumerate(rows)
    )
    path.write_text(
        "\n".join(
            [
                f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{height}" viewBox="0 0 900 {height}">',
                '<rect width="900" height="100%" fill="#ffffff"/>',
                '<rect x="20" y="20" width="860" height="44" fill="#edf2f7" stroke="#2d3748"/>',
                f'<text x="32" y="49" font-size="20" font-family="Arial" font-weight="700" fill="#111827">{safe_title}</text>',
                f'<text x="32" y="84" font-size="13" font-family="Arial" fill="#4b5563">{safe_subtitle}</text>',
                f'<g font-family="Arial">{lines}</g>',
                "</svg>",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _placeholder_table(path: Path, caption: str, artifact: Path) -> Path:
    return _latex_table(path, caption, ["Status", "Artifact"], [[PLACEHOLDER, str(artifact)]])


def _latex_table(path: Path, caption: str, headers: list[str], rows: list[list[str]]) -> Path:
    column_spec = "ll" if len(headers) <= 2 else "l" * len(headers)
    header = " & ".join(_tex_escape(header) for header in headers) + r" \\"
    body = "\n".join(" & ".join(_tex_escape(str(cell)) for cell in row) + r" \\" for row in rows)
    path.write_text(
        "\n".join(
            [
                r"\begin{table}[t]",
                r"\centering",
                rf"\caption{{{_tex_escape(caption)}}}",
                rf"\begin{{tabular}}{{{column_spec}}}",
                r"\toprule",
                header,
                r"\midrule",
                body,
                r"\bottomrule",
                r"\end{tabular}",
                r"\end{table}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _artifact_note(path: Path) -> str:
    return f"Generated from {path}"


def _fmt(value: Any) -> str:
    if value is None:
        return PLACEHOLDER
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _fmt_nested(value: Any) -> str:
    if value is None:
        return PLACEHOLDER
    if isinstance(value, float):
        return f"{value:.3f}"
    if isinstance(value, dict | list):
        return json.dumps(value, sort_keys=True)[:180]
    return str(value)


def _xml(value: str) -> str:
    return (
        value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def _tex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in value)
