from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def analyze_mcq_answer_positions(predictions_path: str | Path) -> dict[str, Any]:
    """Analyze gold/prediction positions and position-conditioned accuracy from JSONL."""

    path = Path(predictions_path)
    gold_by_item: dict[str, str] = {}
    gold_counts: Counter[str] = Counter()
    prediction_counts: Counter[str] = Counter()
    subject_gold: dict[str, Counter[str]] = defaultdict(Counter)
    model_prediction: dict[str, Counter[str]] = defaultdict(Counter)
    conditioned: dict[str, list[int]] = defaultdict(list)
    row_count = 0
    conflicts = 0
    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            if not raw.strip():
                continue
            row = json.loads(raw)
            item_id = str(row["item_id"])
            gold = str(row["gold"]).strip().upper()
            prediction = str(row["prediction"]).strip().upper()
            subject = str(row.get("subset", "unknown"))
            model = str(row["model_id"])
            existing = gold_by_item.setdefault(item_id, gold)
            if existing != gold:
                conflicts += 1
            prediction_counts[prediction] += 1
            model_prediction[model][prediction] += 1
            conditioned[gold].append(int(bool(row["correct"])))
            row_count += 1
    for item_id, gold in gold_by_item.items():
        gold_counts[gold] += 1
        subject = item_id.removeprefix("mmlu_").rsplit("_id", 1)[0]
        subject_gold[subject][gold] += 1
    return {
        "status": "REPRODUCED" if conflicts == 0 else "BLOCKED_IDENTITY_CONFLICT",
        "rows": row_count,
        "unique_items": len(gold_by_item),
        "gold_identity_conflicts": conflicts,
        "gold_position_distribution": _normalize(gold_counts),
        "prediction_position_distribution": _normalize(prediction_counts),
        "subject_gold_position_distribution": {
            subject: _normalize(counts) for subject, counts in sorted(subject_gold.items())
        },
        "model_prediction_position_distribution": {
            model: _normalize(counts) for model, counts in sorted(model_prediction.items())
        },
        "position_conditioned_accuracy": {
            position: sum(values) / len(values) for position, values in sorted(conditioned.items())
        },
        "claim_boundary": (
            "Position imbalance and response preference are forensic signals; neither alone "
            "identifies contamination or invalidity."
        ),
    }


def _normalize(counts: Counter[str]) -> dict[str, float | int]:
    total = sum(counts.values())
    return {
        key: {"count": int(value), "fraction": value / total if total else 0.0}
        for key, value in sorted(counts.items())
    }
