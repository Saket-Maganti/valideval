from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def build_static_site(
    *,
    site_dir: str | Path = "site",
    registry_root: str | Path = "registry",
    leaderboard_root: str | Path = "leaderboard",
    results_root: str | Path = "results",
    reportcards_root: str | Path = "reportcards",
) -> dict[str, str]:
    site = Path(site_dir)
    site.mkdir(parents=True, exist_ok=True)
    (site / "assets").mkdir(exist_ok=True)
    (site / "assets" / "style.css").write_text(_css(), encoding="utf-8")

    registry = _read_json(Path(registry_root) / "audits.json", {"audits": []})
    atlas = _read_json(Path(leaderboard_root) / "benchmark_atlas.json", {"benchmarks": []})
    outputs = {}
    pages = {
        "index.html": _home_page(registry, atlas),
        "benchmark_atlas.html": _atlas_page(atlas),
        "audit_registry.html": _registry_page(registry),
        "ranking_comparisons.html": _artifact_page(
            "Ranking Comparisons",
            Path(results_root),
            ["ranking_views.json", "ranking_flips.json"],
        ),
        "certificates.html": _artifact_page(
            "Certificates",
            Path(results_root),
            ["validity_certificate.md", "validity_certificate.json"],
        ),
        "report_cards.html": _reportcards_page(Path(reportcards_root)),
        "item_forensics.html": _artifact_page(
            "Item Forensics Downloads",
            Path(results_root),
            ["item_forensics.csv"],
        ),
        "methodology.html": _methodology_page(),
        "misuse_warnings.html": _misuse_page(Path(results_root)),
    }
    for name, content in pages.items():
        path = site / name
        path.write_text(content, encoding="utf-8")
        outputs[name] = str(path)
    (site / "data_registry.json").write_text(
        json.dumps(registry, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (site / "data_atlas.json").write_text(
        json.dumps(atlas, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    outputs["data_registry.json"] = str(site / "data_registry.json")
    outputs["data_atlas.json"] = str(site / "data_atlas.json")
    return outputs


def _layout(title: str, body: str) -> str:
    nav = (
        '<nav><a href="index.html">Home</a><a href="benchmark_atlas.html">Atlas</a>'
        '<a href="audit_registry.html">Registry</a><a href="ranking_comparisons.html">Rankings</a>'
        '<a href="certificates.html">Certificates</a><a href="report_cards.html">Reports</a>'
        '<a href="methodology.html">Methodology</a><a href="misuse_warnings.html">Misuse</a></nav>'
    )
    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        f'<title>{html.escape(title)}</title><link rel="stylesheet" href="assets/style.css">'
        f"</head><body>{nav}<main><h1>{html.escape(title)}</h1>{body}</main></body></html>"
    )


def _home_page(registry: dict[str, Any], atlas: dict[str, Any]) -> str:
    body = (
        "<p>ValidEval reports benchmark-health profiles. It does not collapse validity into one score.</p>"
        f"<p>Audits registered: {len(registry.get('audits', []))}</p>"
        f"<p>Benchmarks in atlas: {len(atlas.get('benchmarks', []))}</p>"
    )
    return _layout("ValidEval Audit Dashboard", body)


def _atlas_page(atlas: dict[str, Any]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(row.get('benchmark_id', ''))}</td>"
        f"<td>{html.escape(row.get('panel_id', ''))}</td>"
        f"<td>{html.escape(row.get('certificate_level', ''))}</td>"
        f"<td>{html.escape(row.get('shortcut_resistance', ''))}</td>"
        f"<td>{html.escape(row.get('item_quality', ''))}</td>"
        f"<td>{html.escape(row.get('reliability', ''))}</td>"
        "</tr>"
        for row in atlas.get("benchmarks", [])
    )
    body = (
        "<p>Dimension profiles are shown separately; there is no total score.</p>"
        "<table><thead><tr><th>Benchmark</th><th>Panel</th><th>Certificate</th>"
        "<th>Shortcut</th><th>Item Quality</th><th>Reliability</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )
    return _layout("Benchmark Atlas", body)


def _registry_page(registry: dict[str, Any]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(audit.get('audit_id', ''))}</td>"
        f"<td>{html.escape(audit.get('benchmark_id', ''))}</td>"
        f"<td>{html.escape(audit.get('panel_id', ''))}</td>"
        f"<td>{html.escape(audit.get('certificate_level', ''))}</td>"
        f"<td>{html.escape(audit.get('status', ''))}</td>"
        "</tr>"
        for audit in registry.get("audits", [])
    )
    body = (
        "<table><thead><tr><th>Audit</th><th>Benchmark</th><th>Panel</th>"
        f"<th>Certificate</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table>"
    )
    return _layout("Audit Registry", body)


def _artifact_page(title: str, root: Path, filenames: list[str]) -> str:
    links = []
    for name in filenames:
        for path in sorted(root.rglob(name)):
            links.append(f"<li>{html.escape(str(path))}</li>")
    body = "<ul>" + "".join(links or ["<li>No matching artifacts found.</li>"]) + "</ul>"
    return _layout(title, body)


def _reportcards_page(root: Path) -> str:
    links = [f"<li>{html.escape(str(path))}</li>" for path in sorted(root.glob("*.md"))]
    return _layout(
        "Report Cards", "<ul>" + "".join(links or ["<li>No report cards found.</li>"]) + "</ul>"
    )


def _methodology_page() -> str:
    return _layout(
        "Methodology",
        (
            "<p>Ranking views are diagnostic-sensitive sensitivity analyses: raw accuracy, "
            "bootstrap-conservative accuracy, IRT proxy ability, reliability sensitivity score, "
            "shortcut sensitivity score, prompt-stable score, extraction-robust score, "
            "contamination-aware score, saturation-aware interpretation, and human-validation-aware view.</p>"
            "<p>These views are not a true ranking and should be reported with assumptions and warnings.</p>"
        ),
    )


def _misuse_page(results_root: Path) -> str:
    warnings = set()
    for path in results_root.rglob("validity_card.json"):
        payload = _read_json(path, {})
        warnings.update(payload.get("misuse_warnings", []))
    body = "<ul>" + "".join(f"<li>{html.escape(w)}</li>" for w in sorted(warnings)) + "</ul>"
    return _layout("Misuse Warnings", body)


def _read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _css() -> str:
    return """
body { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; color: #20242a; background: #f7f7f5; }
nav { display: flex; gap: 1rem; padding: 0.9rem 1.25rem; background: #1e2a32; }
nav a { color: #fff; text-decoration: none; font-size: 0.92rem; }
main { max-width: 1040px; margin: 0 auto; padding: 2rem 1.25rem 4rem; }
h1 { font-size: 2rem; margin: 0 0 1rem; }
table { width: 100%; border-collapse: collapse; background: white; }
th, td { border: 1px solid #ddd; padding: 0.55rem; text-align: left; font-size: 0.9rem; }
th { background: #e9ece8; }
li { margin: 0.35rem 0; }
"""
