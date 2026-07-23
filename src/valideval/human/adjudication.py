from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from valideval.human.common import (
    load_human_judgments,
    stable_json_hash,
    write_json,
)
from valideval.io.jsonl import write_jsonl
from valideval.schemas import AdjudicationDecision, HumanJudgment


def create_adjudication_queue(
    *,
    output_dir: str | Path,
    ranking_critical_items: set[str] | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    ambiguity_rows = _read_ambiguity_rows(output / "scoring_ambiguity.csv")
    judgments = load_human_judgments(output)
    judgments_by_task = _judgments_by_task(judgments)
    ranking_critical_items = ranking_critical_items or set()
    queue_rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in ambiguity_rows:
        reasons = set(str(row.get("reasons", "")).split(";"))
        task_id = str(row.get("task_id", ""))
        item_id = str(row.get("item_id", ""))
        queue_names = _queue_names(
            reasons,
            judgments_by_task.get(task_id, []),
            item_id in ranking_critical_items,
        )
        for queue_name in queue_names:
            key = (queue_name, task_id)
            if key in seen:
                continue
            seen.add(key)
            queue_rows.append(
                {
                    "queue": queue_name,
                    "priority": _priority(queue_name, row),
                    "task_id": task_id,
                    "item_id": item_id,
                    "model_id": row.get("model_id", ""),
                    "ambiguity_level": row.get("ambiguity_level", ""),
                    "reasons": row.get("reasons", ""),
                    "human_labels": row.get("human_labels", ""),
                    "judge_labels": row.get("judge_labels", ""),
                    "gold_answer": row.get("gold_answer", ""),
                    "notes": row.get("notes", ""),
                }
            )

    queue_rows.sort(key=lambda row: (int(row["priority"]), row["queue"], row["task_id"]))
    queue_path = output / "adjudication_queue.jsonl"
    summary_path = output / "adjudication_queue.json"
    write_jsonl(queue_path, queue_rows)
    summary = {
        "schema_version": "0.1",
        "n_queue_items": len(queue_rows),
        "queue_counts": _queue_counts(queue_rows),
        "artifacts": {"adjudication_queue_jsonl": str(queue_path)},
        "limitations": [
            "The queue prioritizes review candidates; final decisions require an adjudicator record."
        ],
    }
    write_json(summary_path, summary)
    return {
        **summary,
        "adjudication_queue_jsonl": str(queue_path),
        "adjudication_queue_json": str(summary_path),
    }


def apply_adjudication_decisions(
    judgments: list[HumanJudgment],
    decisions: list[AdjudicationDecision],
) -> dict[str, Any]:
    final_by_task = {decision.task_id: decision.final_label for decision in decisions}
    retained = [
        judgment
        for judgment in judgments
        if judgment.task_id not in final_by_task or judgment.invalid_item_flag
    ]
    return {
        "schema_version": "0.1",
        "n_original_judgments": len(judgments),
        "n_adjudicated_tasks": len(final_by_task),
        "final_labels": final_by_task,
        "retained_judgment_count": len(retained),
        "version_hash": stable_json_hash(
            {
                "judgments": [judgment.model_dump(mode="json") for judgment in judgments],
                "decisions": [decision.model_dump(mode="json") for decision in decisions],
            }
        ),
        "limitations": [
            "Adjudicated labels should be reported separately from raw human agreement."
        ],
    }


def _queue_names(
    reasons: set[str],
    judgments: list[HumanJudgment],
    ranking_critical: bool,
) -> list[str]:
    names: list[str] = []
    if "human_disagreement" in reasons or "human_ambiguity_flag" in reasons:
        names.append("low_agreement")
    if "judge_disagreement" in reasons or "strict_lenient_disagreement" in reasons:
        names.append("judge_human_mismatch")
    if _high_confidence_disagreement(judgments):
        names.append("high_confidence_disagreement")
    if ranking_critical:
        names.append("ranking_critical")
    return names or ["general_review"]


def _high_confidence_disagreement(judgments: list[HumanJudgment]) -> bool:
    labels = {judgment.label.strip().lower() for judgment in judgments}
    if len(labels) < 2:
        return False
    return sum(judgment.confidence >= 0.8 for judgment in judgments) >= 2


def _priority(queue_name: str, row: dict[str, Any]) -> int:
    if queue_name == "high_confidence_disagreement":
        return 0
    if row.get("ambiguity_level") == "high":
        return 1
    if queue_name in {"low_agreement", "judge_human_mismatch"}:
        return 2
    return 3


def _queue_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        queue = str(row["queue"])
        counts[queue] = counts.get(queue, 0) + 1
    return counts


def _judgments_by_task(judgments: list[HumanJudgment]) -> dict[str, list[HumanJudgment]]:
    grouped: dict[str, list[HumanJudgment]] = {}
    for judgment in judgments:
        grouped.setdefault(judgment.task_id, []).append(judgment)
    return grouped


def _read_ambiguity_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
