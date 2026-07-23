from __future__ import annotations

import math
import random
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field

from valideval.benchmarks.base import Benchmark
from valideval.schemas import BenchmarkItem
from valideval.scoring.mcq_utils import (
    LABELS,
    correct_choice_text,
    item_choice_map,
    most_common_label,
    option_with_extreme_length,
    option_with_keyword_overlap,
    tokenize,
)


@dataclass
class BaselinePrediction:
    baseline_id: str
    item_id: str
    prediction: str
    score: float
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class BaselineResult:
    baseline_id: str
    score: float
    predictions: list[BaselinePrediction]
    warnings: list[str] = field(default_factory=list)


BaselineFn = Callable[[BenchmarkItem, list[BenchmarkItem], int], tuple[str, dict[str, object]]]


def _stable_rng(seed: int, baseline_id: str, item_id: str) -> random.Random:
    return random.Random(f"{seed}|{baseline_id}|{item_id}")


def _option_frequency_prior(items: list[BenchmarkItem]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for item in items:
        text = correct_choice_text(item)
        counts.update(tokenize(text))
    return counts


def _answer_length_target(items: list[BenchmarkItem]) -> float:
    lengths = [len(correct_choice_text(item)) for item in items if correct_choice_text(item)]
    return float(sum(lengths) / len(lengths)) if lengths else 0.0


def _bm25_idf(items: list[BenchmarkItem]) -> Counter[str]:
    document_count = 0
    document_frequency: Counter[str] = Counter()
    for item in items:
        for text in item_choice_map(item).values():
            document_count += 1
            document_frequency.update(set(tokenize(text)))
    idf: Counter[str] = Counter()
    for token, count in document_frequency.items():
        idf[token] = math.log((document_count - count + 0.5) / (count + 0.5) + 1.0)
    return idf


def always_first_option(
    item: BenchmarkItem, items: list[BenchmarkItem], seed: int
) -> tuple[str, dict[str, object]]:
    return "A", {"rule": "always_first_option"}


def majority_label(
    item: BenchmarkItem, items: list[BenchmarkItem], seed: int
) -> tuple[str, dict[str, object]]:
    label = most_common_label(items)
    return label, {"majority_label": label}


def random_label(
    item: BenchmarkItem, items: list[BenchmarkItem], seed: int
) -> tuple[str, dict[str, object]]:
    label = _stable_rng(seed, "random_label", item.item_id).choice(list(LABELS))
    return label, {"seed": seed}


def longest_option(
    item: BenchmarkItem, items: list[BenchmarkItem], seed: int
) -> tuple[str, dict[str, object]]:
    return option_with_extreme_length(item, longest=True), {"rule": "longest_option"}


def shortest_option(
    item: BenchmarkItem, items: list[BenchmarkItem], seed: int
) -> tuple[str, dict[str, object]]:
    return option_with_extreme_length(item, longest=False), {"rule": "shortest_option"}


def answer_length_heuristic(
    item: BenchmarkItem, items: list[BenchmarkItem], seed: int
) -> tuple[str, dict[str, object]]:
    target = _answer_length_target(items)
    choices = item_choice_map(item)
    if not choices:
        return "A", {"target_answer_length": target}
    label = sorted(
        choices,
        key=lambda option: (abs(len(choices[option]) - target), option),
    )[0]
    return label, {"target_answer_length": target}


def keyword_overlap(
    item: BenchmarkItem, items: list[BenchmarkItem], seed: int
) -> tuple[str, dict[str, object]]:
    return option_with_keyword_overlap(item, include_context=True), {
        "source_fields": ["prompt", "context"]
    }


def bm25_lexical(
    item: BenchmarkItem, items: list[BenchmarkItem], seed: int
) -> tuple[str, dict[str, object]]:
    choices = item_choice_map(item)
    if not choices:
        return "A", {"rule": "bm25_lexical"}
    source_tokens = set(tokenize(f"{item.context or ''} {item.prompt}"))
    idf = _bm25_idf(items)
    scores = {
        label: sum(idf[token] for token in set(tokenize(text)) & source_tokens)
        for label, text in choices.items()
    }
    best_score = max(scores.values()) if scores else 0.0
    if best_score <= 0:
        return "A", {"rule": "bm25_lexical", "fallback": "A"}
    label = sorted(scores, key=lambda option: (scores[option], option), reverse=True)[0]
    return label, {"rule": "bm25_lexical", "score": scores[label]}


def option_frequency_prior(
    item: BenchmarkItem, items: list[BenchmarkItem], seed: int
) -> tuple[str, dict[str, object]]:
    choices = item_choice_map(item)
    prior = _option_frequency_prior(items)
    if not choices:
        return "A", {"rule": "option_frequency_prior"}
    scores = {
        label: sum(prior[token] for token in tokenize(text)) for label, text in choices.items()
    }
    label = sorted(scores, key=lambda option: (scores[option], option), reverse=True)[0]
    return label, {"rule": "option_frequency_prior", "score": scores[label]}


def regex_arithmetic_solver(
    item: BenchmarkItem, items: list[BenchmarkItem], seed: int
) -> tuple[str, dict[str, object]]:
    text = f"{item.context or ''} {item.prompt}".lower()
    numbers = [int(value) for value in re.findall(r"\b\d+\b", text)]
    target: int | None = None
    if len(numbers) >= 2 and any(word in text for word in ["sum", "plus", "adding", "add"]):
        target = numbers[-2] + numbers[-1]
    elif len(numbers) >= 2 and any(word in text for word in ["difference", "subtract"]):
        target = abs(numbers[-2] - numbers[-1])
    elif "every" in text and "two" in text and numbers:
        target = 2 * numbers[-1]
    if target is None:
        return "A", {"rule": "regex_arithmetic_solver", "matched": False}

    for label, option_text in item_choice_map(item).items():
        if str(target) in option_text or _number_word(target) in option_text.lower():
            return label, {"rule": "regex_arithmetic_solver", "target": target}
    return "A", {"rule": "regex_arithmetic_solver", "target": target, "matched": False}


def context_copy_baseline(
    item: BenchmarkItem, items: list[BenchmarkItem], seed: int
) -> tuple[str, dict[str, object]]:
    context = (item.context or "").lower()
    choices = item_choice_map(item)
    for label, text in choices.items():
        if text and text.lower() in context:
            return label, {"rule": "context_copy_baseline", "matched": True}
    return option_with_keyword_overlap(item, include_context=True), {
        "rule": "context_copy_baseline",
        "matched": False,
    }


def question_only_shallow_classifier(
    item: BenchmarkItem, items: list[BenchmarkItem], seed: int
) -> tuple[str, dict[str, object]]:
    return option_with_keyword_overlap(item, include_context=False), {
        "rule": "question_only_shallow_classifier",
        "training_split_available": False,
    }


def metadata_artifact_baseline(
    item: BenchmarkItem, items: list[BenchmarkItem], seed: int
) -> tuple[str, dict[str, object]]:
    label = str(item.metadata.get("label_prior", "A")).upper()
    if label not in LABELS:
        label = "A"
    return label, {"rule": "metadata_artifact_baseline", "metadata_key": "label_prior"}


def _number_word(value: int) -> str:
    words = {
        0: "zero",
        1: "one",
        2: "two",
        3: "three",
        4: "four",
        5: "five",
        6: "six",
        7: "seven",
        8: "eight",
        9: "nine",
        10: "ten",
        11: "eleven",
        12: "twelve",
        13: "thirteen",
        14: "fourteen",
        15: "fifteen",
    }
    return words.get(value, str(value))


BASELINE_REGISTRY: dict[str, BaselineFn] = {
    "always_first_option": always_first_option,
    "majority_label": majority_label,
    "random_label": random_label,
    "longest_option": longest_option,
    "shortest_option": shortest_option,
    "answer_length_heuristic": answer_length_heuristic,
    "keyword_overlap": keyword_overlap,
    "bm25_lexical": bm25_lexical,
    "option_frequency_prior": option_frequency_prior,
    "regex_arithmetic_solver": regex_arithmetic_solver,
    "context_copy_baseline": context_copy_baseline,
    "question_only_shallow_classifier": question_only_shallow_classifier,
    "metadata_artifact_baseline": metadata_artifact_baseline,
}


def evaluate_baselines(
    benchmark: Benchmark,
    *,
    baseline_ids: list[str] | None = None,
    seed: int = 0,
) -> list[BaselineResult]:
    items = benchmark.load_items()
    selected = baseline_ids or list(BASELINE_REGISTRY)
    results: list[BaselineResult] = []
    for baseline_id in selected:
        if baseline_id not in BASELINE_REGISTRY:
            raise ValueError(f"Unknown baseline: {baseline_id}")
        baseline = BASELINE_REGISTRY[baseline_id]
        predictions = []
        warnings = []
        for item in items:
            prediction, metadata = baseline(item, items, seed)
            score = benchmark.score_prediction(item, prediction)
            predictions.append(
                BaselinePrediction(
                    baseline_id=baseline_id,
                    item_id=item.item_id,
                    prediction=prediction,
                    score=score.score,
                    metadata=metadata,
                )
            )
            if baseline_id == "question_only_shallow_classifier":
                warnings = [
                    "No training split was available; this uses question-only lexical overlap."
                ]
        baseline_score = (
            sum(prediction.score for prediction in predictions) / len(predictions)
            if predictions
            else 0.0
        )
        results.append(
            BaselineResult(
                baseline_id=baseline_id,
                score=baseline_score,
                predictions=predictions,
                warnings=warnings,
            )
        )
    return results
