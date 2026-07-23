from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from valideval.io.cache import build_response_matrix, save_matrix, save_predictions
from valideval.schemas import BenchmarkItem, ConstructSpec, ModelPrediction, ResponseMatrix
from valideval.scoring.mcq import score_mcq
from valideval.scoring.mcq_utils import item_choice_map, option_with_extreme_length
from valideval.validation.flaw_generators import LABELS, base_items, inject_flaw

LEGACY_SYNTHETIC_HARNESS_STATUS = "legacy_wiring_only"
LEGACY_SYNTHETIC_HARNESS_WARNING = (
    "The controlled synthetic harness branches on injected flaw metadata and is retained as a "
    "wiring/sanity-check surface only. Its AUCs must not be treated as independent diagnostic-"
    "validation evidence."
)

CONTROLLED_MODEL_IDS = [
    "clean_reasoner",
    "shortcut_exploiter",
    "label_prior_model",
    "length_heuristic_model",
    "context_ignoring_model",
    "format_fragile_model",
    "noisy_strong_model",
    "noisy_weak_model",
    "random_model",
    "anti_discriminator_model",
]

IRT_VALIDATION_MODEL_IDS = [
    "ability_band_00",
    "ability_band_01",
    "ability_band_02",
    "ability_band_03",
    "ability_band_04",
    "ability_band_05",
    "ability_band_06",
    "ability_band_07",
    "ability_band_08",
    "ability_band_09",
    "ability_band_10",
    "ability_band_11",
    "ability_band_12",
    "ability_band_13",
]

PROMPT_VARIANTS = [
    "full",
    "question_only",
    "choices_only",
    "context_removed",
    "context_shuffled",
    "label_prior_only",
    "metadata_only",
    "answer_length_only",
    "format_only",
    "irrelevant_context",
    "retrieval_only",
    "zero_shot_direct",
    "direct_answer_only",
    "json_only",
    "answer_letter_only",
    "no_system_prompt",
    "terse_instructions",
    "verbose_instructions",
]

CONTEXT_REQUIRED_VARIANTS = {
    "question_only",
    "choices_only",
    "context_removed",
    "context_shuffled",
    "label_prior_only",
    "metadata_only",
    "answer_length_only",
    "format_only",
    "irrelevant_context",
    "direct_answer_only",
    "json_only",
    "answer_letter_only",
    "terse_instructions",
    "verbose_instructions",
}

FORMAT_VARIANTS = {
    "terse_instructions",
    "verbose_instructions",
    "json_only",
    "answer_letter_only",
    "no_system_prompt",
}

MODEL_ABILITIES = {
    "clean_reasoner": 1.25,
    "shortcut_exploiter": 0.15,
    "label_prior_model": -0.10,
    "length_heuristic_model": -0.10,
    "context_ignoring_model": 0.05,
    "format_fragile_model": 0.85,
    "noisy_strong_model": 0.95,
    "noisy_weak_model": -0.75,
    "random_model": -3.0,
    "anti_discriminator_model": 0.20,
    "ability_band_00": -2.10,
    "ability_band_01": -1.75,
    "ability_band_02": -1.40,
    "ability_band_03": -1.05,
    "ability_band_04": -0.70,
    "ability_band_05": -0.35,
    "ability_band_06": 0.00,
    "ability_band_07": 0.35,
    "ability_band_08": 0.70,
    "ability_band_09": 1.05,
    "ability_band_10": 1.40,
    "ability_band_11": 1.75,
    "ability_band_12": 2.10,
    "ability_band_13": 2.45,
}


class SyntheticBenchmark:
    def __init__(
        self,
        *,
        flaw_type: str = "clean",
        flaw_strength: float = 0.0,
        seed: int = 0,
        n_items: int = 64,
        benchmark_id: str | None = None,
    ):
        self.flaw_type = flaw_type
        self.flaw_strength = float(flaw_strength)
        self.seed = int(seed)
        self.benchmark_id = benchmark_id or (
            f"synthetic_{flaw_type}_{self.flaw_strength:.2f}_seed{seed}"
        ).replace(".", "p")
        self.claimed_construct = "synthetic context-grounded MCQ reasoning"
        self.construct_spec = ConstructSpec(
            claimed_construct=self.claimed_construct,
            construct_tags=["synthetic_reasoning", "context_use"],
            construct_critical_fields=["prompt", "context", "choices"],
            expected_threats=[
                "shortcuts",
                "answer artifacts",
                "redundancy",
                "low discrimination",
                "saturation",
                "format fragility",
                "extraction ambiguity",
            ],
            description=(
                "Synthetic benchmark with controlled ground-truth flaw metadata for "
                "diagnostic detector validation. It is not a real benchmark result."
            ),
            warnings=[
                "Synthetic validation estimates detector behavior under controlled generators only.",
                LEGACY_SYNTHETIC_HARNESS_WARNING,
            ],
        )
        clean = base_items(n_items, seed=seed)
        self._items = inject_flaw(
            clean,
            flaw_type=flaw_type,
            flaw_strength=self.flaw_strength,
            seed=seed,
        )

    def load_items(self) -> list[BenchmarkItem]:
        return list(self._items)

    def render_prompt(self, item: BenchmarkItem, variant: str = "full") -> str:
        choices = "\n".join(item.choices or [])
        if variant == "full":
            return f"Context: {item.context}\nQuestion: {item.prompt}\nChoices:\n{choices}\nAnswer:"
        if variant == "question_only":
            return f"Question: {item.prompt}\nChoices:\n{choices}\nAnswer:"
        if variant == "choices_only":
            return f"Choices:\n{choices}\nAnswer:"
        if variant == "context_removed":
            return f"Question: {item.prompt}\nChoices:\n{choices}\nAnswer:"
        if variant == "context_shuffled":
            return (
                "Context: This unrelated context was shuffled from another item.\n"
                f"Question: {item.prompt}\nChoices:\n{choices}\nAnswer:"
            )
        if variant in {"label_prior_only", "metadata_only"}:
            signal = item.metadata.get("ground_truth_signal", {})
            label = signal.get("shortcut_label") or signal.get("label_prior") or "unknown"
            return f"Metadata cue only: candidate label prior is {label}.\nChoices:\n{choices}\nAnswer:"
        if variant == "answer_length_only":
            return f"Choose from the option texts only.\nChoices:\n{choices}\nAnswer:"
        if variant == "format_only":
            return "Return only A, B, C, or D."
        if variant == "irrelevant_context":
            return (
                "Context: The context is irrelevant filler with no answer evidence.\n"
                f"Question: {item.prompt}\nChoices:\n{choices}\nAnswer:"
            )
        if variant == "retrieval_only":
            return f"Retrieved context: {item.context}\nAnswer:"
        if variant == "zero_shot_direct":
            return f"{item.context}\n{item.prompt}\n{choices}\nAnswer directly:"
        if variant == "direct_answer_only":
            return f"{item.prompt}\nReturn the answer label only."
        if variant == "json_only":
            return f"{item.context}\n{item.prompt}\n{choices}\nReturn JSON with key answer."
        if variant == "answer_letter_only":
            return f"{item.context}\n{item.prompt}\n{choices}\nOnly output the answer letter."
        if variant == "no_system_prompt":
            return f"{item.context}\n{item.prompt}\n{choices}"
        if variant == "terse_instructions":
            return f"{item.context}\n{item.prompt}\n{choices}\nLetter?"
        if variant == "verbose_instructions":
            return (
                "Read the context carefully, ignore spurious artifacts, and provide only "
                f"the best answer label.\nContext: {item.context}\nQuestion: {item.prompt}\n{choices}"
            )
        return self.render_prompt(item, variant="full")

    def score_prediction(self, item: BenchmarkItem, prediction: str):
        return score_mcq(item, prediction)

    def available_prompt_variants(self) -> list[str]:
        return list(PROMPT_VARIANTS)


def generate_synthetic_benchmark(
    *,
    flaw_type: str = "clean",
    flaw_strength: float = 0.0,
    seed: int = 0,
    n_items: int = 64,
) -> SyntheticBenchmark:
    return SyntheticBenchmark(
        flaw_type=flaw_type,
        flaw_strength=flaw_strength,
        seed=seed,
        n_items=n_items,
    )


def generate_controlled_predictions(
    benchmark: SyntheticBenchmark,
    *,
    variant: str = "full",
    seed: int = 0,
    model_ids: list[str] | None = None,
) -> list[ModelPrediction]:
    predictions: list[ModelPrediction] = []
    selected_models = model_ids or CONTROLLED_MODEL_IDS
    for model_id in selected_models:
        for item in benchmark.load_items():
            label, raw_output, metadata = _controlled_output(
                item,
                model_id=model_id,
                variant=variant,
                seed=seed,
            )
            score = benchmark.score_prediction(item, label)
            predictions.append(
                ModelPrediction(
                    model_id=model_id,
                    item_id=item.item_id,
                    prompt_variant=variant,
                    prediction=label,
                    score=score.score,
                    is_correct=score.is_correct,
                    logprob=None,
                    raw_output=raw_output,
                    metadata={
                        **metadata,
                        "controlled_model": model_id,
                        "ground_truth_flaw_type": item.metadata.get("flaw_type"),
                        "ground_truth_flaw_strength": item.metadata.get("flaw_strength"),
                        "ground_truth_is_flawed": item.metadata.get("is_flawed"),
                        "normalized_prediction": score.normalized_prediction,
                        "normalized_answer": score.normalized_answer,
                    },
                )
            )
    return predictions


def build_controlled_matrices(
    benchmark: SyntheticBenchmark,
    *,
    variants: list[str],
    cache_root: str | Path,
    panel_id: str = "synthetic_validation",
    seed: int = 0,
    model_ids: list[str] | None = None,
) -> dict[str, ResponseMatrix]:
    matrices: dict[str, ResponseMatrix] = {}
    for variant in variants:
        predictions = generate_controlled_predictions(
            benchmark,
            variant=variant,
            seed=seed,
            model_ids=model_ids,
        )
        save_predictions(cache_root, benchmark.benchmark_id, panel_id, variant, predictions)
        matrix = build_response_matrix(
            predictions,
            benchmark_id=benchmark.benchmark_id,
            panel_id=panel_id,
            variant=variant,
            scoring_method="synthetic_mcq",
            seed=seed,
        )
        save_matrix(cache_root, benchmark.benchmark_id, panel_id, variant, matrix)
        matrices[variant] = matrix
    return matrices


def _controlled_output(
    item: BenchmarkItem,
    *,
    model_id: str,
    variant: str,
    seed: int,
) -> tuple[str, str, dict[str, Any]]:
    signal = dict(item.metadata.get("ground_truth_signal", {}))
    flaw_type = str(item.metadata.get("flaw_type", "clean"))
    is_flawed = bool(item.metadata.get("is_flawed", False))
    correct = _primary_label(item)
    wrong = _wrong_label(item, preferred=_preferred_wrong_label(model_id))
    rng = _rng(seed, model_id, item.item_id, variant)

    if flaw_type == "extraction_ambiguity" and is_flawed and variant == "full":
        if model_id in {"clean_reasoner", "noisy_strong_model", "format_fragile_model"}:
            alternate = _wrong_label(item, preferred="B")
            return (
                correct,
                f"{alternate}. Rationale mentions a distractor. Final answer: {correct}",
                {"rule": "ambiguous_raw_output"},
            )
        if model_id == "random_model":
            return (
                wrong,
                "Unable to choose between A and B",
                {"rule": "invalid_ambiguous_output"},
            )

    if flaw_type == "prompt_format_fragility" and is_flawed and variant in FORMAT_VARIANTS:
        if model_id != "random_model":
            return (
                wrong,
                "I cannot comply with this answer format",
                {"rule": "format_fragile_failure"},
            )
    if flaw_type == "prompt_format_fragility" and is_flawed and variant == "full":
        if model_id != "random_model":
            return correct, correct, {"rule": "format_fragile_full_success"}

    if flaw_type == "shortcut_signal" and is_flawed:
        if model_id in {
            "shortcut_exploiter",
            "label_prior_model",
            "context_ignoring_model",
        } and variant in {
            "full",
            "question_only",
            "context_removed",
            "label_prior_only",
            "metadata_only",
        }:
            return correct, correct, {"rule": "shortcut_label"}

    if flaw_type == "label_imbalance" and is_flawed and model_id == "label_prior_model":
        return "B", "B", {"rule": "label_prior"}

    if flaw_type == "answer_length_artifact" and is_flawed and model_id == "length_heuristic_model":
        label = option_with_extreme_length(item, longest=True)
        return label, label, {"rule": "longest_option"}

    if flaw_type == "context_irrelevance" and is_flawed and model_id == "context_ignoring_model":
        return correct, correct, {"rule": "prompt_only_signal"}

    if (
        flaw_type == "context_leakage"
        and is_flawed
        and model_id
        in {
            "shortcut_exploiter",
            "context_ignoring_model",
        }
    ):
        return correct, correct, {"rule": "context_leakage_label"}

    if flaw_type == "too_easy_saturation" and is_flawed:
        if model_id not in {"random_model", "anti_discriminator_model"}:
            return correct, correct, {"rule": "ceiling_item"}

    if flaw_type == "too_hard_floor" and is_flawed:
        if model_id != "random_model":
            return wrong, wrong, {"rule": "floor_item"}

    if flaw_type == "low_discrimination" and is_flawed:
        # Half the panel succeeds in a model-independent pattern.
        label = correct if _stable_coin(seed, item.item_id, "low_discrimination") else wrong
        return label, label, {"rule": "model_independent_noise"}

    if flaw_type == "negative_discrimination" and is_flawed:
        probability = _negative_discrimination_success_probability(
            item,
            model_id=model_id,
            variant=variant,
            signal=signal,
        )
        label = _choice_from_probability(correct, wrong, probability, rng)
        return (
            label,
            label,
            {
                "rule": "negative_discrimination_anti_ability",
                "success_probability": probability,
                "negative_discrimination_severity": float(
                    signal.get("negative_discrimination_severity", 1.0)
                ),
            },
        )

    if flaw_type == "dead_distractors" and is_flawed:
        if model_id in {"noisy_weak_model", "random_model"}:
            label = _wrong_label(item, preferred="D")
            return label, label, {"rule": "single_live_distractor"}

    if model_id == "random_model":
        label = rng.choice(list(LABELS))
        return label, label, {"rule": "random_label"}

    if model_id == "label_prior_model":
        label = str(signal.get("label_prior") or "B")
        return label if label in LABELS else "B", label, {"rule": "label_prior_default"}

    if model_id == "length_heuristic_model":
        label = option_with_extreme_length(item, longest=True)
        return label, label, {"rule": "longest_option_default"}

    if model_id == "context_ignoring_model" and variant in CONTEXT_REQUIRED_VARIANTS:
        label = _choice_from_probability(correct, wrong, 0.30, rng)
        return label, label, {"rule": "context_ignored"}

    if model_id == "anti_discriminator_model":
        label = correct if rng.random() < 0.35 else wrong
        return label, label, {"rule": "anti_discriminator_default"}

    probability = _base_success_probability(
        item,
        model_id=model_id,
        variant=variant,
        signal=signal,
    )
    label = _choice_from_probability(correct, wrong, probability, rng)
    return label, label, {"rule": "construct_signal", "success_probability": probability}


def _base_success_probability(
    item: BenchmarkItem,
    *,
    model_id: str,
    variant: str,
    signal: dict[str, Any],
) -> float:
    ability = MODEL_ABILITIES.get(model_id, 0.0)
    difficulty = float(signal.get("true_difficulty", 0.45))
    discrimination = float(signal.get("true_discrimination", 0.75))
    if variant in CONTEXT_REQUIRED_VARIANTS and signal.get("context_required", True):
        ability -= 1.25
    if variant in FORMAT_VARIANTS and model_id == "format_fragile_model":
        ability -= 0.75
    logit = (ability - difficulty) * max(discrimination, 0.05)
    probability = 1.0 / (1.0 + pow(2.718281828459045, -logit))
    return min(max(probability, 0.05), 0.95)


def _negative_discrimination_success_probability(
    item: BenchmarkItem,
    *,
    model_id: str,
    variant: str,
    signal: dict[str, Any],
) -> float:
    severity = min(max(float(signal.get("negative_discrimination_severity", 1.0)), 0.0), 1.0)
    normal_signal = dict(signal)
    normal_signal["true_discrimination"] = 0.75
    normal_probability = _base_success_probability(
        item,
        model_id=model_id,
        variant=variant,
        signal=normal_signal,
    )
    ability = MODEL_ABILITIES.get(model_id, 0.0)
    slope = 1.40 + 2.10 * severity
    anti_logit = -ability * slope
    anti_probability = 1.0 / (1.0 + pow(2.718281828459045, -anti_logit))
    if model_id in {"shortcut_exploiter", "anti_discriminator_model"}:
        anti_probability = max(anti_probability, 0.75 + 0.20 * severity)
    probability = (1.0 - severity) * normal_probability + severity * anti_probability
    return min(max(probability, 0.02), 0.98)


def _choice_from_probability(
    correct: str,
    wrong: str,
    probability: float,
    rng: random.Random,
) -> str:
    return correct if rng.random() < probability else wrong


def _primary_label(item: BenchmarkItem) -> str:
    if isinstance(item.answer, list):
        return str(item.answer[0]).upper()
    return str(item.answer).upper()


def _wrong_label(item: BenchmarkItem, *, preferred: str = "A") -> str:
    correct = set(item.answer if isinstance(item.answer, list) else [item.answer])
    labels = list(item_choice_map(item)) or list(LABELS)
    if preferred in labels and preferred not in correct:
        return preferred
    for label in labels:
        if label not in correct:
            return label
    return "A"


def _preferred_wrong_label(model_id: str) -> str:
    preferences = {
        "clean_reasoner": "A",
        "shortcut_exploiter": "B",
        "label_prior_model": "B",
        "length_heuristic_model": "C",
        "context_ignoring_model": "D",
        "format_fragile_model": "A",
        "noisy_strong_model": "B",
        "noisy_weak_model": "C",
        "random_model": "D",
        "anti_discriminator_model": "D",
    }
    return preferences.get(model_id, "A")


def _rng(seed: int, model_id: str, item_id: str, variant: str) -> random.Random:
    return random.Random(f"synthetic-model|{seed}|{model_id}|{item_id}|{variant}")


def _stable_coin(seed: int, item_id: str, salt: str) -> bool:
    return random.Random(f"{seed}|{item_id}|{salt}").random() < 0.5
