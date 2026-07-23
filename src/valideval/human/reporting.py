from __future__ import annotations

from pathlib import Path
from typing import Any

from valideval.human.common import read_json


def read_human_artifacts(audit_dir: str | Path | None) -> dict[str, Any]:
    if audit_dir is None:
        return {"available": False, "status": "not measured"}
    root = Path(audit_dir)
    human_dir = root / "human"
    packet = read_json(human_dir / "manifest.json")
    import_report = read_json(human_dir / "annotation_import_report.json")
    agreement = read_json(human_dir / "agreement_report.json")
    judge = read_json(human_dir / "judge_reliability.json")
    ambiguity = read_json(human_dir / "scoring_ambiguity.json")
    queue = read_json(human_dir / "adjudication_queue.json")
    available = any([packet, import_report, agreement, judge, ambiguity, queue])
    judge_human = judge.get("metrics", {}).get("judge_human_agreement", {})
    return {
        "available": available,
        "status": "measured" if available else "not measured",
        "human_dir": str(human_dir),
        "packet": packet,
        "import": import_report,
        "agreement": agreement,
        "judge": judge,
        "ambiguity": ambiguity,
        "adjudication_queue": queue,
        "annotated_item_count": agreement.get("n_items") or 0,
        "annotated_task_count": agreement.get("n_tasks") or 0,
        "judgment_count": agreement.get("n_judgments") or import_report.get("n_imported") or 0,
        "raw_agreement": agreement.get("raw_agreement"),
        "cohen_kappa": agreement.get("cohen_kappa"),
        "fleiss_kappa": agreement.get("fleiss_kappa"),
        "ambiguity_rate": agreement.get("ambiguity_rate")
        if agreement.get("ambiguity_rate") is not None
        else ambiguity.get("ambiguity_rate"),
        "judge_human_agreement": judge_human.get("agreement"),
        "inter_judge_agreement": judge.get("metrics", {})
        .get("inter_judge_agreement", {})
        .get("agreement"),
        "n_ambiguous_tasks": ambiguity.get("n_ambiguous_tasks"),
    }


def human_validated_subset_status(summary: dict[str, Any]) -> str:
    if not summary.get("available") or not summary.get("judgment_count"):
        return "unknown"
    raw = summary.get("raw_agreement")
    n_items = int(summary.get("annotated_item_count") or 0)
    if raw is None:
        return "insufficient evidence"
    raw = float(raw)
    if n_items >= 20 and raw >= 0.80:
        return "strong"
    if n_items >= 5 and raw >= 0.60:
        return "moderate"
    if raw >= 0.40:
        return "weak"
    return "threatened"


def judge_reliability_status(summary: dict[str, Any]) -> str:
    value = summary.get("judge_human_agreement")
    if value is None:
        return "unknown"
    value = float(value)
    if value >= 0.80:
        return "strong"
    if value >= 0.60:
        return "moderate"
    if value >= 0.40:
        return "weak"
    return "threatened"


def atlas_human_status(summary: dict[str, Any]) -> str:
    status = human_validated_subset_status(summary)
    if status == "unknown" and summary.get("packet"):
        return "packet prepared"
    return status


def validity_card_human_summary(summary: dict[str, Any]) -> dict[str, Any]:
    if not summary.get("available"):
        return {
            "status": "unknown",
            "reason": "Human agreement or adjudication artifacts were not found for this audit.",
        }
    return {
        "status": human_validated_subset_status(summary),
        "annotated_item_count": summary.get("annotated_item_count"),
        "annotated_task_count": summary.get("annotated_task_count"),
        "judgment_count": summary.get("judgment_count"),
        "raw_agreement": summary.get("raw_agreement"),
        "cohen_kappa": summary.get("cohen_kappa"),
        "fleiss_kappa": summary.get("fleiss_kappa"),
        "ambiguity_rate": summary.get("ambiguity_rate"),
        "judge_human_agreement": summary.get("judge_human_agreement"),
        "inter_judge_agreement": summary.get("inter_judge_agreement"),
        "human_dir": summary.get("human_dir"),
        "limitations": [
            "Human labels are protocol evidence and may still require adjudication.",
            "Coverage depends on the annotation packet sampling strategy.",
        ],
    }
