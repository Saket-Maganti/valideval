from __future__ import annotations

import hashlib
import random
import re
from dataclasses import dataclass

from valideval.schemas import ModelOutput

CHOICE_RE = re.compile(r"^\s*([A-D])[\).]\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
PRIOR_RE = re.compile(
    r"(?:label prior suggests answer label|usually use answer label)\s+([A-D])",
    re.IGNORECASE,
)
STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "to",
    "of",
    "in",
    "is",
    "was",
    "with",
    "which",
    "what",
    "after",
    "from",
    "this",
    "that",
    "for",
    "as",
    "by",
    "only",
    "answer",
    "choice",
}


def _stable_rng(model_id: str, prompt: str, seed: int | None) -> random.Random:
    digest = hashlib.sha256(f"{model_id}|{seed}|{prompt}".encode()).hexdigest()
    return random.Random(int(digest[:16], 16))


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 1 and token not in STOPWORDS
    }


def _parse_choices(prompt: str) -> list[tuple[str, str]]:
    return [
        (match.group(1).upper(), match.group(2).strip()) for match in CHOICE_RE.finditer(prompt)
    ]


def _extract_context(prompt: str) -> str:
    match = re.search(r"Context:\s*(.*?)\n\nQuestion:", prompt, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    context = match.group(1).strip()
    if context.lower() in {"[removed]", "[no context]"}:
        return ""
    return context


def _extract_question(prompt: str) -> str:
    match = re.search(
        r"Question:\s*(.*?)(?:\n\nChoices:|\n\nAnswer|\Z)", prompt, flags=re.IGNORECASE | re.DOTALL
    )
    return match.group(1).strip() if match else prompt


def _label_prior(prompt: str) -> str | None:
    match = PRIOR_RE.search(prompt)
    return match.group(1).upper() if match else None


def _choice_by_overlap(prompt: str, *, use_context: bool) -> str | None:
    prior = _label_prior(prompt)
    if prior:
        return prior

    choices = _parse_choices(prompt)
    if not choices:
        return None

    source_parts = []
    context = _extract_context(prompt)
    if use_context and context:
        source_parts.append(context)
    source_parts.append(_extract_question(prompt))
    source_tokens = _tokens(" ".join(source_parts))

    best_label: str | None = None
    best_score = 0
    for label, text in choices:
        choice_tokens = _tokens(text)
        overlap = len(choice_tokens & source_tokens)
        if overlap > best_score:
            best_label = label
            best_score = overlap
    return best_label if best_score > 0 else None


@dataclass
class AlwaysA:
    model_id: str = "always_a"

    def generate(self, prompt: str, *, seed: int | None = None) -> ModelOutput:
        return ModelOutput(prediction="A", raw_output="A", metadata={"strategy": "always_a"})


@dataclass
class MajorityLabel:
    model_id: str = "majority_label"
    majority_label: str = "B"

    def generate(self, prompt: str, *, seed: int | None = None) -> ModelOutput:
        prior = _label_prior(prompt)
        label = prior or self.majority_label
        return ModelOutput(
            prediction=label,
            raw_output=label,
            metadata={
                "strategy": "majority_label",
                "assumed_majority_label": self.majority_label,
            },
        )


@dataclass
class KeywordMatcher:
    model_id: str = "keyword_matcher"

    def generate(self, prompt: str, *, seed: int | None = None) -> ModelOutput:
        label = _choice_by_overlap(prompt, use_context=False) or "A"
        return ModelOutput(
            prediction=label, raw_output=label, metadata={"strategy": "keyword_matcher"}
        )


@dataclass
class ShortcutExploiter:
    model_id: str = "shortcut_exploiter"

    def generate(self, prompt: str, *, seed: int | None = None) -> ModelOutput:
        label = _label_prior(prompt) or _choice_by_overlap(prompt, use_context=False) or "B"
        return ModelOutput(
            prediction=label,
            raw_output=label,
            metadata={"strategy": "shortcut_exploiter"},
        )


@dataclass
class ContextAwareMock:
    model_id: str = "context_aware"

    def generate(self, prompt: str, *, seed: int | None = None) -> ModelOutput:
        label = (
            _choice_by_overlap(prompt, use_context=True)
            or _choice_by_overlap(prompt, use_context=False)
            or "A"
        )
        return ModelOutput(
            prediction=label, raw_output=label, metadata={"strategy": "context_aware"}
        )


@dataclass
class NoisyStrongMock:
    model_id: str = "noisy_strong"

    def generate(self, prompt: str, *, seed: int | None = None) -> ModelOutput:
        rng = _stable_rng(self.model_id, prompt, seed)
        base = ContextAwareMock().generate(prompt, seed=seed).prediction
        has_context = bool(_extract_context(prompt))
        probability = 0.88 if has_context else 0.55
        if _label_prior(prompt):
            probability = 0.80
        label = base if rng.random() < probability else rng.choice(["A", "B", "C", "D"])
        return ModelOutput(
            prediction=label, raw_output=label, metadata={"strategy": "noisy_strong"}
        )


@dataclass
class NoisyWeakMock:
    model_id: str = "noisy_weak"

    def generate(self, prompt: str, *, seed: int | None = None) -> ModelOutput:
        rng = _stable_rng(self.model_id, prompt, seed)
        base = KeywordMatcher().generate(prompt, seed=seed).prediction
        probability = 0.45 if _extract_context(prompt) else 0.30
        if _label_prior(prompt):
            probability = 0.65
        label = base if rng.random() < probability else rng.choice(["A", "B", "C", "D"])
        return ModelOutput(prediction=label, raw_output=label, metadata={"strategy": "noisy_weak"})


@dataclass
class FormatFragile:
    model_id: str = "format_fragile"

    def generate(self, prompt: str, *, seed: int | None = None) -> ModelOutput:
        has_expected_shape = all(
            marker in prompt for marker in ["Context:", "Question:", "Choices:"]
        )
        has_removed_context = "[removed]" in prompt or "[no context]" in prompt
        if has_expected_shape and not has_removed_context:
            label = ContextAwareMock().generate(prompt, seed=seed).prediction
            return ModelOutput(
                prediction=label,
                raw_output=f"Answer: {label}",
                metadata={"strategy": "format_fragile", "format_ok": True},
            )
        return ModelOutput(
            prediction="unparseable",
            raw_output="I cannot answer from this prompt format.",
            metadata={"strategy": "format_fragile", "format_ok": False},
        )
