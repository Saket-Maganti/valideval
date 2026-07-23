from __future__ import annotations

import re
from collections import Counter

from valideval.schemas import BenchmarkItem
from valideval.scoring.mcq import normalize_mcq_label

LABELS = ("A", "B", "C", "D")
STOPWORDS = {
    "a",
    "an",
    "and",
    "answer",
    "as",
    "by",
    "choice",
    "for",
    "from",
    "in",
    "is",
    "of",
    "only",
    "or",
    "that",
    "the",
    "this",
    "to",
    "what",
    "which",
    "with",
}


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 1 and token not in STOPWORDS
    ]


def choice_label(choice: str) -> str | None:
    return normalize_mcq_label(choice)


def choice_text(choice: str) -> str:
    return re.sub(r"^\s*[A-D][\).:\s-]*", "", choice, flags=re.IGNORECASE).strip()


def item_choice_map(item: BenchmarkItem) -> dict[str, str]:
    choices = item.choices or []
    output: dict[str, str] = {}
    for choice in choices:
        label = choice_label(choice)
        if label:
            output[label] = choice_text(choice)
    return output


def accepted_labels(item: BenchmarkItem) -> list[str]:
    answers = item.answer if isinstance(item.answer, list) else [item.answer]
    return [normalize_mcq_label(str(answer)) or str(answer).strip().upper() for answer in answers]


def primary_answer_label(item: BenchmarkItem) -> str:
    labels = accepted_labels(item)
    return labels[0] if labels else "A"


def correct_choice_text(item: BenchmarkItem) -> str:
    return item_choice_map(item).get(primary_answer_label(item), "")


def incorrect_choice_map(item: BenchmarkItem) -> dict[str, str]:
    accepted = set(accepted_labels(item))
    return {label: text for label, text in item_choice_map(item).items() if label not in accepted}


def jaccard_similarity(left: str, right: str) -> float:
    left_tokens = set(tokenize(left))
    right_tokens = set(tokenize(right))
    if not left_tokens and not right_tokens:
        return 1.0
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def most_common_label(items: list[BenchmarkItem], default: str = "A") -> str:
    counts = Counter(primary_answer_label(item) for item in items)
    if not counts:
        return default
    return counts.most_common(1)[0][0]


def option_with_extreme_length(item: BenchmarkItem, *, longest: bool) -> str:
    choices = item_choice_map(item)
    if not choices:
        return "A"
    return sorted(
        choices,
        key=lambda label: (len(choices[label]), label),
        reverse=longest,
    )[0]


def option_with_keyword_overlap(item: BenchmarkItem, *, include_context: bool = True) -> str:
    choices = item_choice_map(item)
    if not choices:
        return "A"
    source = item.prompt
    if include_context and item.context:
        source = f"{item.context} {source}"
    source_tokens = set(tokenize(source))
    scores = {label: len(source_tokens & set(tokenize(text))) for label, text in choices.items()}
    best_score = max(scores.values()) if scores else 0
    if best_score <= 0:
        return "A"
    return sorted(scores, key=lambda label: (scores[label], label), reverse=True)[0]
