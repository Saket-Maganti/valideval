from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from valideval.human.common import load_annotation_tasks
from valideval.schemas import AnnotationTask


def render_annotation_viewer(
    *,
    output_dir: str | Path,
    title: str = "ValidEval Annotation Viewer",
) -> dict[str, Any]:
    output = Path(output_dir)
    tasks = load_annotation_tasks(output)
    html_path = output / "annotation_viewer.html"
    html_path.write_text(_render_html(tasks, title=title), encoding="utf-8")
    return {
        "annotation_viewer_html": str(html_path),
        "n_tasks": len(tasks),
        "limitations": [
            "The static viewer exports local JSONL in the browser; it does not store labels server-side."
        ],
    }


def _render_html(tasks: list[AnnotationTask], *, title: str) -> str:
    task_cards = "\n".join(_task_card(index, task) for index, task in enumerate(tasks))
    task_payload = json.dumps([task.model_dump(mode="json") for task in tasks], sort_keys=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #f7f7f5; color: #1f2933; }}
    header {{ position: sticky; top: 0; background: #ffffff; border-bottom: 1px solid #d7d7d2; padding: 12px 18px; display: flex; gap: 12px; align-items: center; justify-content: space-between; }}
    main {{ max-width: 980px; margin: 0 auto; padding: 18px; }}
    section {{ background: #ffffff; border: 1px solid #d7d7d2; border-radius: 6px; margin-bottom: 14px; padding: 14px; }}
    pre {{ white-space: pre-wrap; background: #f1f5f9; border-radius: 6px; padding: 10px; }}
    label {{ display: block; font-weight: 600; margin-top: 10px; }}
    input, select, textarea {{ width: 100%; box-sizing: border-box; border: 1px solid #b9c0c8; border-radius: 4px; padding: 8px; font: inherit; background: #fff; }}
    button {{ border: 1px solid #243b53; background: #243b53; color: #fff; border-radius: 4px; padding: 8px 12px; font-weight: 600; }}
    .meta {{ color: #52616b; font-size: 0.9rem; }}
    .row {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }}
    @media (max-width: 720px) {{ .row {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
<header>
  <strong>{html.escape(title)}</strong>
  <button type="button" onclick="downloadJsonl()">Export JSONL</button>
</header>
<main>
  {task_cards or "<p>No annotation tasks found.</p>"}
</main>
<script>
const tasks = {task_payload};
function value(id) {{ return document.getElementById(id)?.value || ""; }}
function checked(id) {{ return document.getElementById(id)?.checked || false; }}
function downloadJsonl() {{
  const lines = tasks.map((task, index) => JSON.stringify({{
    task_id: task.task_id,
    item_id: task.item_id,
    model_id: task.model_id,
    anonymized_annotator: value(`annotator-${{index}}`),
    label: value(`label-${{index}}`),
    confidence: Number(value(`confidence-${{index}}`)),
    rationale: value(`rationale-${{index}}`),
    ambiguity_flag: checked(`ambiguity-${{index}}`),
    invalid_item_flag: checked(`invalid-${{index}}`)
  }}));
  const blob = new Blob([lines.join("\\n") + "\\n"], {{type: "application/jsonl"}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "human_annotations.jsonl";
  a.click();
  URL.revokeObjectURL(url);
}}
</script>
</body>
</html>
"""


def _task_card(index: int, task: AnnotationTask) -> str:
    return f"""<section>
  <div class="meta">Task {index + 1}: {html.escape(task.task_id)} | Item {html.escape(task.item_id)} | Model {html.escape(task.model_id or "item-only")}</div>
  <h2>{html.escape(task.item_id)}</h2>
  <label>Prompt</label>
  <pre>{html.escape(task.prompt)}</pre>
  <label>Model Output</label>
  <pre>{html.escape(task.model_output or "(none)")}</pre>
  <label>Rubric</label>
  <pre>{html.escape(task.rubric)}</pre>
  <div class="row">
    <div><label for="annotator-{index}">Annotator</label><input id="annotator-{index}" placeholder="ann_001"></div>
    <div><label for="label-{index}">Label</label><select id="label-{index}"><option value=""></option><option>correct</option><option>incorrect</option><option>unscorable</option><option>A</option><option>B</option><option>C</option><option>D</option></select></div>
    <div><label for="confidence-{index}">Confidence</label><input id="confidence-{index}" type="number" min="0" max="1" step="0.01" value="0.80"></div>
  </div>
  <label for="rationale-{index}">Rationale</label>
  <textarea id="rationale-{index}" rows="3"></textarea>
  <div class="row">
    <label><input id="ambiguity-{index}" type="checkbox"> Ambiguity</label>
    <label><input id="invalid-{index}" type="checkbox"> Invalid item</label>
  </div>
</section>"""
