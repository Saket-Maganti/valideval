from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from typing import Any

import numpy as np

from valideval.benchmarks.base import Benchmark
from valideval.diagnostics.base import MatrixInput
from valideval.schemas import DiagnosticResult
from valideval.scoring.mcq_utils import (
    LABELS,
    accepted_labels,
    choice_text,
    incorrect_choice_map,
    item_choice_map,
    option_with_extreme_length,
    primary_answer_label,
    tokenize,
)

NEGATION_CUES = {"not", "except", "least", "never", "false"}
ALL_NONE_CUES = {"all of the above", "none of the above"}


class AnswerDistributionDiagnostic:
    name = "answer_distribution"
    version = "0.1"

    def run(
        self,
        benchmark: Benchmark,
        predictions: MatrixInput,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> DiagnosticResult:
        items = benchmark.load_items()
        label_counts = Counter(primary_answer_label(item) for item in items)
        distractor_counts = Counter(label for item in items for label in incorrect_choice_map(item))
        n_items = len(items)
        expected = n_items / len(LABELS) if items else 0.0
        max_label_fraction = max(label_counts.values()) / n_items if items else 0.0
        label_imbalance_l1 = (
            sum(abs(label_counts.get(label, 0) - expected) for label in LABELS) / n_items
            if items
            else 0.0
        )

        longest_correct = [
            option_with_extreme_length(item, longest=True) in accepted_labels(item)
            for item in items
        ]
        shortest_correct = [
            option_with_extreme_length(item, longest=False) in accepted_labels(item)
            for item in items
        ]

        correct_lengths = []
        distractor_lengths = []
        option_token_counts: Counter[str] = Counter()
        correct_token_counts: Counter[str] = Counter()
        all_none_items = []
        negation_items = []
        repeated_phrase_items = []
        per_item: dict[str, Any] = {}

        for item in items:
            choices = item_choice_map(item)
            accepted = set(accepted_labels(item))
            correct_texts = [choices[label] for label in choices if label in accepted]
            distractor_texts = [choices[label] for label in choices if label not in accepted]
            correct_lengths.extend(len(text) for text in correct_texts)
            distractor_lengths.extend(len(text) for text in distractor_texts)
            option_token_counts.update(
                token for text in choices.values() for token in tokenize(text)
            )
            correct_token_counts.update(token for text in correct_texts for token in tokenize(text))

            cue_text = f"{item.prompt} {item.context or ''}".lower()
            has_negation = any(cue in cue_text.split() for cue in NEGATION_CUES)
            has_all_none = any(
                cue in choice_text(choice).lower()
                for choice in item.choices or []
                for cue in ALL_NONE_CUES
            )
            repeated_phrase = _repeated_phrase(item)
            if has_negation:
                negation_items.append(item.item_id)
            if has_all_none:
                all_none_items.append(item.item_id)
            if repeated_phrase:
                repeated_phrase_items.append(item.item_id)
            per_item[item.item_id] = {
                "answer_labels": accepted_labels(item),
                "correct_option_length": float(np.mean([len(text) for text in correct_texts]))
                if correct_texts
                else 0.0,
                "longest_option_correct": option_with_extreme_length(item, longest=True)
                in accepted,
                "shortest_option_correct": option_with_extreme_length(item, longest=False)
                in accepted,
                "has_negation_cue": has_negation,
                "has_all_none_option": has_all_none,
                "repeated_phrase": repeated_phrase,
            }

        token_artifacts = {
            token: {
                "correct_count": correct_token_counts[token],
                "all_option_count": option_token_counts[token],
                "correct_fraction_when_present": correct_token_counts[token]
                / option_token_counts[token],
            }
            for token, _ in option_token_counts.most_common(20)
            if option_token_counts[token] >= 2
        }

        warnings = []
        if max_label_fraction >= 0.4:
            warnings.append(
                "Answer labels are imbalanced; evidence is consistent with possible answer-position artifacts."
            )
        if float(np.mean(longest_correct)) >= 0.4:
            warnings.append(
                "Longest-option correctness is elevated under this diagnostic; inspect answer-length artifacts."
            )

        return DiagnosticResult(
            benchmark_id=benchmark.benchmark_id,
            diagnostic_name=self.name,
            version=self.version,
            summary_metrics={
                "n_items": n_items,
                "label_counts": {label: label_counts.get(label, 0) for label in LABELS},
                "label_balance": {
                    label: label_counts.get(label, 0) / n_items if n_items else 0.0
                    for label in LABELS
                },
                "max_label_fraction": max_label_fraction,
                "label_imbalance_l1": label_imbalance_l1,
                "answer_length_bias": {
                    "mean_correct_length": float(np.mean(correct_lengths))
                    if correct_lengths
                    else 0.0,
                    "mean_distractor_length": float(np.mean(distractor_lengths))
                    if distractor_lengths
                    else 0.0,
                    "longest_option_correct_fraction": float(np.mean(longest_correct))
                    if longest_correct
                    else 0.0,
                    "shortest_option_correct_fraction": float(np.mean(shortest_correct))
                    if shortest_correct
                    else 0.0,
                },
                "option_token_frequency_artifacts": token_artifacts,
                "negation_cue_items": negation_items,
                "all_none_of_the_above_items": all_none_items,
                "repeated_phrase_items": repeated_phrase_items,
                "distractor_choice_distribution": {
                    label: distractor_counts.get(label, 0) for label in LABELS
                },
            },
            per_item_metrics=per_item,
            warnings=warnings,
            limitations=[
                "Static answer-distribution diagnostics identify possible artifacts but do not establish model use of those artifacts."
            ],
        )


def _repeated_phrase(item) -> str | None:
    phrase_counts: Counter[str] = Counter()
    for text in item_choice_map(item).values():
        tokens = tokenize(text)
        phrase_counts.update(
            " ".join(tokens[index : index + 2]) for index in range(len(tokens) - 1)
        )
    repeated = [phrase for phrase, count in phrase_counts.items() if count > 1 and phrase]
    return repeated[0] if repeated else None
