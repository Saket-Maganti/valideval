from __future__ import annotations

import random

from valideval.schemas import BenchmarkItem

SUPPORTED_FLAWS = [
    "clean",
    "shortcut_signal",
    "label_imbalance",
    "answer_length_artifact",
    "keyword_artifact",
    "dead_distractors",
    "redundancy",
    "low_discrimination",
    "negative_discrimination",
    "too_easy_saturation",
    "too_hard_floor",
    "scoring_ambiguity",
    "prompt_format_fragility",
    "extraction_ambiguity",
    "context_irrelevance",
    "context_leakage",
]

LABELS = ("A", "B", "C", "D")
NEGATIVE_DISCRIMINATION_MAX_FLAWED_FRACTION = 0.30


def flawed_indices(n_items: int, flaw_strength: float, *, seed: int) -> set[int]:
    strength = min(max(float(flaw_strength), 0.0), 1.0)
    count = int(round(strength * n_items))
    rng = random.Random(f"flaws|{seed}|{n_items}|{strength}")
    indices = list(range(n_items))
    rng.shuffle(indices)
    return set(indices[:count])


def negative_discrimination_indices(
    n_items: int,
    flaw_strength: float,
    *,
    seed: int,
) -> set[int]:
    """Select anti-correlated items while preserving clean anchors for ability orientation."""
    strength = min(max(float(flaw_strength), 0.0), 1.0)
    if strength <= 0:
        return set()
    count = int(round(strength * NEGATIVE_DISCRIMINATION_MAX_FLAWED_FRACTION * n_items))
    count = min(max(count, 1), max(n_items - 1, 1))
    rng = random.Random(f"negative-discrimination|{seed}|{n_items}|{strength}")
    indices = list(range(n_items))
    rng.shuffle(indices)
    return set(indices[:count])


def base_items(n_items: int, *, seed: int) -> list[BenchmarkItem]:
    rng = random.Random(f"base|{seed}|{n_items}")
    items = []
    for index in range(n_items):
        label = LABELS[index % len(LABELS)]
        concept = f"signal_{index:03d}"
        distractors = [f"distractor_{index:03d}_{slot}" for slot in range(3)]
        choices = _choices(label, concept, distractors)
        context = f"The construct-relevant evidence identifies {concept} as the supported option."
        prompt = (
            f"Which option is supported by the construct-relevant evidence for signal_{index:03d}?"
        )
        if rng.random() < 0.05:
            prompt = f"Which answer follows from the supplied evidence for signal_{index:03d}?"
        items.append(
            BenchmarkItem(
                item_id=f"synthetic_{index:03d}",
                prompt=prompt,
                answer=label,
                choices=choices,
                context=context,
                construct_tags=["synthetic_reasoning", "context_use"],
                construct_critical_fields=["prompt", "context", "choices"],
                metadata={
                    "flaw_type": "clean",
                    "flaw_strength": 0.0,
                    "is_flawed": False,
                    "ground_truth_signal": {
                        "true_difficulty": 0.45,
                        "true_discrimination": 0.75,
                        "context_required": True,
                    },
                },
            )
        )
    return items


def inject_flaw(
    items: list[BenchmarkItem],
    *,
    flaw_type: str,
    flaw_strength: float,
    seed: int,
) -> list[BenchmarkItem]:
    if flaw_type not in SUPPORTED_FLAWS:
        raise ValueError(f"Unknown synthetic flaw: {flaw_type}")
    if flaw_type == "clean" or flaw_strength <= 0:
        return [
            _with_metadata(item, flaw_type="clean", flaw_strength=0.0, is_flawed=False)
            for item in items
        ]
    if flaw_type == "negative_discrimination":
        flawed = negative_discrimination_indices(len(items), flaw_strength, seed=seed)
    else:
        flawed = flawed_indices(len(items), flaw_strength, seed=seed)
    output = []
    previous: BenchmarkItem | None = None
    for index, item in enumerate(items):
        is_flawed = index in flawed
        updated = _with_metadata(
            item,
            flaw_type=flaw_type if is_flawed else "clean",
            flaw_strength=float(flaw_strength),
            is_flawed=is_flawed,
        )
        if is_flawed:
            updated = _apply_flaw(
                updated, flaw_type=flaw_type, strength=flaw_strength, index=index, previous=previous
            )
        output.append(updated)
        previous = updated
    return output


def _apply_flaw(
    item: BenchmarkItem,
    *,
    flaw_type: str,
    strength: float,
    index: int,
    previous: BenchmarkItem | None,
) -> BenchmarkItem:
    metadata = dict(item.metadata)
    signal = dict(metadata.get("ground_truth_signal", {}))
    choices = list(item.choices or [])
    prompt = item.prompt
    context = item.context
    answer: str | list[str] = item.answer
    tags = list(item.construct_tags)
    label = str(item.answer if isinstance(item.answer, str) else item.answer[0])

    if flaw_type == "shortcut_signal":
        prompt = f"{prompt} Dataset shortcut cue says label {label} is usually correct."
        signal["shortcut_label"] = label
        signal["context_required"] = True
        tags.append("shortcut_signal")
    elif flaw_type == "label_imbalance":
        label = "B"
        answer = label
        choices = _relabel_correct_choice(choices, label, f"signal_{index:03d}")
        signal["label_prior"] = label
        tags.append("answer_prior_artifact")
    elif flaw_type == "answer_length_artifact":
        choices = _make_correct_longest(choices, label)
        signal["longest_label"] = label
        tags.append("answer_length_artifact")
    elif flaw_type == "keyword_artifact":
        prompt = f"{prompt} The keyword signal_{index:03d} appears in the question."
        signal["keyword_label"] = label
        tags.append("keyword_artifact")
    elif flaw_type == "dead_distractors":
        choices = _make_dead_distractors(choices, label, index)
        signal["dead_distractor_labels"] = [
            choice[0] for choice in choices if not choice.startswith(label)
        ]
        tags.append("dead_distractors")
    elif flaw_type == "redundancy" and previous is not None:
        prompt = previous.prompt
        context = previous.context
        choices = list(previous.choices or choices)
        answer = previous.answer
        signal["duplicate_of"] = previous.item_id
        tags.append("duplicate_near_duplicate")
    elif flaw_type == "low_discrimination":
        signal["true_discrimination"] = 0.02
        signal["true_difficulty"] = 0.50
        tags.append("low_discrimination")
    elif flaw_type == "negative_discrimination":
        severity = min(max(float(strength), 0.0), 1.0)
        signal["true_difficulty"] = 0.50
        signal["true_discrimination"] = -(0.35 + 0.65 * severity)
        signal["negative_discrimination"] = True
        signal["negative_discrimination_severity"] = severity
        signal["expected_response_pattern"] = (
            "Higher-ability synthetic models should systematically miss this item while "
            "lower-ability or shortcut-like models should pass it."
        )
        tags.append("negative_discrimination")
    elif flaw_type == "too_easy_saturation":
        signal["true_difficulty"] = 0.02
        signal["expected_top_model_score"] = 1.0
        tags.append("too_easy")
    elif flaw_type == "too_hard_floor":
        signal["true_difficulty"] = 0.98
        signal["expected_top_model_score"] = 0.0
        tags.append("too_hard")
    elif flaw_type == "scoring_ambiguity":
        alternate = next(candidate for candidate in LABELS if candidate != label)
        answer = [label, alternate]
        signal["accepted_labels"] = [label, alternate]
        tags.append("ambiguous_scoring_risk")
    elif flaw_type == "prompt_format_fragility":
        signal["format_fragile"] = True
        tags.append("prompt_format_fragility")
    elif flaw_type == "extraction_ambiguity":
        signal["ambiguous_output_expected"] = True
        tags.append("extraction_ambiguity")
    elif flaw_type == "context_irrelevance":
        context = "This context is deliberately irrelevant and contains no construct signal."
        prompt = f"{prompt} The prompt alone names signal_{index:03d}."
        signal["context_required"] = False
        signal["irrelevant_context"] = True
        tags.append("context_irrelevance")
    elif flaw_type == "context_leakage":
        context = f"{context} Leaked answer label: {label}."
        signal["context_leakage_label"] = label
        tags.append("context_leakage")

    metadata["ground_truth_signal"] = signal
    return item.model_copy(
        deep=True,
        update={
            "prompt": prompt,
            "context": context,
            "choices": choices,
            "answer": answer,
            "construct_tags": sorted(set(tags)),
            "metadata": metadata,
        },
    )


def _with_metadata(
    item: BenchmarkItem,
    *,
    flaw_type: str,
    flaw_strength: float,
    is_flawed: bool,
) -> BenchmarkItem:
    metadata = dict(item.metadata)
    signal = dict(metadata.get("ground_truth_signal", {}))
    metadata.update(
        {
            "flaw_type": flaw_type,
            "flaw_strength": float(flaw_strength),
            "is_flawed": bool(is_flawed),
            "ground_truth_signal": signal,
        }
    )
    return item.model_copy(deep=True, update={"metadata": metadata})


def _choices(correct_label: str, correct_text: str, distractors: list[str]) -> list[str]:
    values: dict[str, str] = {}
    distractor_iter = iter(distractors)
    for label in LABELS:
        values[label] = correct_text if label == correct_label else next(distractor_iter)
    return [f"{label}. {values[label]}" for label in LABELS]


def _relabel_correct_choice(choices: list[str], label: str, correct_text: str) -> list[str]:
    texts = {choice[0]: choice.split(".", 1)[1].strip() for choice in choices}
    for candidate in LABELS:
        if candidate != label and texts.get(candidate) == correct_text:
            texts[candidate] = f"distractor_rebalanced_{candidate}"
    texts[label] = correct_text
    return [f"{candidate}. {texts[candidate]}" for candidate in LABELS]


def _make_correct_longest(choices: list[str], label: str) -> list[str]:
    output = []
    for choice in choices:
        choice_label, text = choice.split(".", 1)
        text = text.strip()
        if choice_label == label:
            text = f"{text} with an unusually long explanatory option artifact"
        else:
            text = text[:18]
        output.append(f"{choice_label}. {text}")
    return output


def _make_dead_distractors(choices: list[str], label: str, index: int) -> list[str]:
    output = []
    for choice in choices:
        choice_label, text = choice.split(".", 1)
        if choice_label == label:
            output.append(choice)
        else:
            output.append(f"{choice_label}. obviously_wrong_placeholder_{index}_{choice_label}")
    return output
