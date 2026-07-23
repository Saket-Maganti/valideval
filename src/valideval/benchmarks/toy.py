from __future__ import annotations

import random
import re

from valideval.schemas import BenchmarkItem, ConstructSpec, ScoreResult
from valideval.scoring import score_mcq


def _choice(label: str, text: str) -> str:
    return f"{label}. {text}"


def _item(
    item_id: str,
    prompt: str,
    answer: str | list[str],
    choices: tuple[str, str, str, str],
    context: str | None,
    tags: list[str],
    *,
    label_prior: str = "A",
    artifact_hint: bool = False,
    construct_critical_fields: list[str] | None = None,
) -> BenchmarkItem:
    labels = ("A", "B", "C", "D")
    return BenchmarkItem(
        item_id=item_id,
        prompt=prompt,
        answer=answer,
        choices=[_choice(label, text) for label, text in zip(labels, choices, strict=True)],
        context=context,
        construct_tags=tags,
        construct_critical_fields=construct_critical_fields or ["prompt", "context"],
        metadata={
            "source": "synthetic",
            "label_prior": label_prior,
            "artifact_hint": artifact_hint,
            "expected_threats": ["shortcut"] if artifact_hint else [],
        },
    )


class ToyMCQBenchmark:
    benchmark_id = "toy_mcq"
    claimed_construct = "toy reasoning under controlled artifacts"
    construct_spec = ConstructSpec(
        claimed_construct=claimed_construct,
        construct_tags=[
            "context_use",
            "quantitative_reasoning",
            "causal_reasoning",
            "lexical_shortcut",
            "answer_prior_artifact",
            "too_easy",
            "too_hard",
            "ambiguous_scoring_risk",
            "duplicate_near_duplicate",
        ],
        construct_critical_fields=["prompt", "context", "choices"],
        expected_threats=[
            "performance retained after context removal",
            "answer-label prior artifacts",
            "low-discrimination items",
            "ambiguous or scoring-risk items",
            "duplicate or near-duplicate items",
        ],
        limitations=[
            "Synthetic toy items are intended for software validation, not empirical model claims."
        ],
        description=(
            "A synthetic multiple-choice benchmark designed to exercise validity diagnostics. "
            "It is not an empirical claim about real model capability."
        ),
    )

    def load_items(self) -> list[BenchmarkItem]:
        return [
            _item(
                "toy_001",
                "Which substance does the plant store as energy after using sunlight?",
                "B",
                ("carbon dioxide", "glucose", "granite", "nitrogen"),
                "A plant uses sunlight and stores chemical energy as glucose.",
                ["context_use", "biology"],
                label_prior="B",
            ),
            _item(
                "toy_002",
                "How many tokens does Mira have after adding the two piles?",
                "C",
                ("5", "6", "7", "8"),
                "Mira starts with 3 tokens and receives 4 more tokens, making 7 tokens.",
                ["context_use", "quantitative_reasoning"],
                label_prior="C",
            ),
            _item(
                "toy_003",
                "Which event most directly caused the lamp to turn on?",
                "A",
                (
                    "the switch closing the circuit",
                    "the room becoming quiet",
                    "the carpet moving",
                    "the shade warming",
                ),
                "The lamp turned on immediately after the wall switch closed the circuit.",
                ["context_use", "causal_reasoning"],
                label_prior="A",
            ),
            _item(
                "toy_004",
                "Which city did the traveler reach second?",
                "D",
                ("Lima", "Oslo", "Quito", "Nairobi"),
                "The traveler visited Lima first, Nairobi second, and Oslo third.",
                ["context_use", "ordering"],
                label_prior="D",
            ),
            _item(
                "toy_005",
                "Which material is most likely to conduct electricity in the described setup?",
                "C",
                ("rubber", "dry wood", "copper", "glass"),
                "In the setup, the current flowed through the copper strip but not the rubber block.",
                ["context_use", "science_reasoning"],
                label_prior="C",
            ),
            _item(
                "toy_006",
                "What did the committee choose after comparing the proposals?",
                "B",
                ("delay the vote", "fund the clinic", "sell the lab", "cancel the survey"),
                "After comparing costs and benefits, the committee chose to fund the clinic.",
                ["context_use", "decision_reasoning"],
                label_prior="B",
            ),
            _item(
                "toy_007",
                "Which answer follows from the rule: if the alarm rings, the door locks?",
                "A",
                ("the door locks", "the window opens", "the alarm breaks", "the key melts"),
                "The alarm rings at 8:00, and the rule says that ringing causes the door to lock.",
                ["context_use", "logical_reasoning"],
                label_prior="A",
            ),
            _item(
                "toy_008",
                "Which option names the animal mentioned in the passage?",
                "D",
                ("otter", "falcon", "llama", "badger"),
                "The passage describes a badger digging near the old fence.",
                ["context_use", "retrieval"],
                label_prior="D",
            ),
            _item(
                "toy_009",
                "The word 'photosynthesis' is a clue for which option?",
                "B",
                ("banking", "plant energy", "geology", "architecture"),
                None,
                ["lexical_shortcut", "biology"],
                label_prior="B",
                artifact_hint=True,
                construct_critical_fields=["prompt"],
            ),
            _item(
                "toy_010",
                "The phrase 'sum of 9 and 6' points to which answer?",
                "C",
                ("11", "13", "15", "18"),
                None,
                ["lexical_shortcut", "quantitative_reasoning"],
                label_prior="C",
                artifact_hint=True,
                construct_critical_fields=["prompt"],
            ),
            _item(
                "toy_011",
                "When a prompt says 'because the bridge collapsed,' what causal factor is named?",
                "A",
                ("bridge collapse", "weather report", "city budget", "ticket price"),
                None,
                ["lexical_shortcut", "causal_reasoning"],
                label_prior="A",
                artifact_hint=True,
                construct_critical_fields=["prompt"],
            ),
            _item(
                "toy_012",
                "In this source format, examples tagged 'blue-ribbon' usually use answer label D.",
                "D",
                ("north", "east", "south", "west"),
                "The underlying task content is intentionally uninformative for this artifact item.",
                ["answer_prior_artifact"],
                label_prior="D",
                artifact_hint=True,
            ),
            _item(
                "toy_013",
                "In this source format, examples tagged 'green-stamp' usually use answer label A.",
                "A",
                ("alpha", "beta", "gamma", "delta"),
                "The underlying task content is intentionally uninformative for this artifact item.",
                ["answer_prior_artifact"],
                label_prior="A",
                artifact_hint=True,
            ),
            _item(
                "toy_014",
                "In this source format, examples tagged 'silver-stamp' usually use answer label B.",
                "B",
                ("red", "violet", "orange", "teal"),
                "The underlying task content is intentionally uninformative for this artifact item.",
                ["answer_prior_artifact"],
                label_prior="B",
                artifact_hint=True,
            ),
            _item(
                "toy_015",
                "Which option should be selected for a deliberately ambiguous item?",
                "A",
                ("choice one", "choice two", "choice three", "choice four"),
                "No construct-relevant information distinguishes the choices.",
                ["low_discrimination"],
                label_prior="A",
            ),
            _item(
                "toy_016",
                "Which option should be selected for a second deliberately ambiguous item?",
                "C",
                ("choice one", "choice two", "choice three", "choice four"),
                "No construct-relevant information distinguishes the choices.",
                ["low_discrimination"],
                label_prior="A",
            ),
            _item(
                "toy_017",
                "Which container holds the red bead?",
                "B",
                ("tin", "box", "jar", "bag"),
                "The tin holds a blue bead, while the box holds the red bead.",
                ["context_use", "retrieval"],
                label_prior="B",
            ),
            _item(
                "toy_018",
                "Which explanation best fits the ice melting?",
                "C",
                (
                    "the ice was painted",
                    "the bowl was named",
                    "heat was added",
                    "the spoon was counted",
                ),
                "The ice melted because heat was added to the bowl.",
                ["context_use", "causal_reasoning"],
                label_prior="C",
            ),
            _item(
                "toy_019",
                "Which number is the difference between 12 and 5?",
                "A",
                ("7", "8", "12", "17"),
                "The calculation subtracts 5 from 12, which leaves 7.",
                ["quantitative_reasoning"],
                label_prior="A",
            ),
            _item(
                "toy_020",
                "Which word is the synonym of rapid in the passage?",
                "D",
                ("dull", "late", "heavy", "fast"),
                "The passage says the runner was rapid, meaning fast.",
                ["context_use", "vocabulary"],
                label_prior="D",
            ),
            _item(
                "toy_021",
                "Which tool did the mechanic use to tighten the bolt?",
                "B",
                ("hammer", "wrench", "brush", "ladder"),
                "The mechanic tightened the bolt with a wrench.",
                ["context_use", "retrieval"],
                label_prior="B",
            ),
            _item(
                "toy_022",
                "Which claim is supported by the mini experiment?",
                "C",
                (
                    "salt cooled the cup",
                    "paper made light",
                    "magnet pulled iron",
                    "glass grew taller",
                ),
                "Only the iron filings moved when the magnet was placed nearby.",
                ["context_use", "science_reasoning"],
                label_prior="C",
            ),
            _item(
                "toy_023",
                "Which person arrived before Jin?",
                "A",
                ("Rosa", "Jin", "Uma", "Vic"),
                "Rosa arrived first, Jin arrived second, and Uma arrived third.",
                ["context_use", "ordering"],
                label_prior="A",
            ),
            _item(
                "toy_024",
                "Which option completes the pattern: red, blue, red, blue, red, ?",
                "B",
                ("red", "blue", "green", "yellow"),
                "The pattern alternates between red and blue.",
                ["pattern_reasoning"],
                label_prior="B",
            ),
            _item(
                "toy_025",
                "Which number is even?",
                "B",
                ("three", "four", "five", "seven"),
                "The only even number listed is four.",
                ["too_easy", "quantitative_reasoning"],
                label_prior="B",
                construct_critical_fields=["choices"],
            ),
            _item(
                "toy_026",
                "Which color is the sky described as in the passage?",
                "B",
                ("red", "blue", "green", "black"),
                "The passage says the noon sky was blue.",
                ["too_easy", "context_use", "retrieval"],
                label_prior="B",
            ),
            _item(
                "toy_027",
                "If every zup equals two blens and Nara has three zups, how many blens is that?",
                "B",
                ("four blens", "six blens", "eight blens", "ten blens"),
                "In this invented unit system, one zup equals two blens.",
                ["too_hard", "context_use", "quantitative_reasoning"],
                label_prior="B",
            ),
            _item(
                "toy_028",
                "Which ritual object was placed in the northern alcove?",
                "D",
                ("mirror", "cord", "basin", "lantern"),
                "The archival note says the lantern, not the mirror, was placed in the northern alcove.",
                ["too_hard", "context_use", "retrieval"],
                label_prior="D",
            ),
            _item(
                "toy_029",
                "Which option is acceptable under the intentionally loose scoring rubric?",
                ["B", "C"],
                ("decrease", "increase", "rise", "ignore"),
                "The rubric accepts both increase and rise as equivalent responses.",
                ["ambiguous_scoring_risk", "scoring_validity"],
                label_prior="B",
            ),
            _item(
                "toy_030",
                "Which instrument did the mechanic use to tighten the bolt?",
                "B",
                ("hammer", "wrench", "brush", "ladder"),
                "The mechanic tightened the bolt with a wrench.",
                ["duplicate_near_duplicate", "context_use", "retrieval"],
                label_prior="B",
            ),
            _item(
                "toy_031",
                "Which container has the red bead?",
                "B",
                ("tin", "box", "jar", "bag"),
                "The tin holds a blue bead, while the box holds the red bead.",
                ["duplicate_near_duplicate", "context_use", "retrieval"],
                label_prior="B",
            ),
            _item(
                "toy_032",
                "Which code word corresponds to signal 7 in the table?",
                "D",
                ("ember", "cobalt", "parcel", "lumen"),
                "The table maps signal 4 to ember, signal 5 to cobalt, and signal 7 to lumen.",
                ["too_hard", "context_use", "retrieval"],
                label_prior="D",
            ),
            _item(
                "toy_033",
                "The phrase 'opposite of cold' is a clue for which option?",
                "C",
                ("damp", "quiet", "hot", "round"),
                None,
                ["lexical_shortcut", "vocabulary"],
                label_prior="C",
                artifact_hint=True,
                construct_critical_fields=["prompt"],
            ),
            _item(
                "toy_034",
                "In this source format, examples tagged 'amber-ticket' usually use answer label B.",
                "B",
                ("circle", "square", "triangle", "line"),
                "The underlying task content is intentionally uninformative for this artifact item.",
                ["answer_prior_artifact"],
                label_prior="B",
                artifact_hint=True,
            ),
            _item(
                "toy_035",
                "Which option should be selected for a third deliberately ambiguous item?",
                "A",
                ("choice one", "choice two", "choice three", "choice four"),
                "No construct-relevant information distinguishes the choices.",
                ["low_discrimination", "ambiguous_scoring_risk"],
                label_prior="A",
            ),
            _item(
                "toy_036",
                "What follows if the gate opens only after the code is accepted and the code is accepted?",
                "C",
                ("the code is erased", "the guard leaves", "the gate opens", "the wall moves"),
                "The rule says the gate opens after the code is accepted, and the code is accepted.",
                ["context_use", "logical_reasoning"],
                label_prior="C",
            ),
        ]

    def render_prompt(self, item: BenchmarkItem, variant: str = "full") -> str:
        if variant not in self.available_prompt_variants():
            raise ValueError(f"Unknown prompt variant for toy benchmark: {variant}")

        choices = "\n".join(item.choices or [])
        instructions = "Answer with only the letter A, B, C, or D."
        context = item.context or "No additional context is provided."

        if variant == "full":
            return f"Context:\n{context}\n\nQuestion:\n{item.prompt}\n\nChoices:\n{choices}\n\n{instructions}"

        if variant == "question_only":
            return f"Question:\n{item.prompt}\n\n{instructions}"

        if variant == "choices_only":
            return f"Choices:\n{choices}\n\n{instructions}"

        if variant == "context_removed":
            return f"Context:\n[removed]\n\nQuestion:\n{item.prompt}\n\nChoices:\n{choices}\n\n{instructions}"

        if variant == "context_shuffled":
            context = item.context or ""
            tokens = re.findall(r"\w+|[^\w\s]", context)
            rng = random.Random(item.item_id)
            rng.shuffle(tokens)
            shuffled = " ".join(tokens) if tokens else "[no context]"
            return f"Context:\n{shuffled}\n\nQuestion:\n{item.prompt}\n\nChoices:\n{choices}\n\n{instructions}"

        if variant == "label_prior_only":
            label_prior = item.metadata.get("label_prior", "A")
            return (
                "Dataset artifact only:\n"
                f"A source-format label prior suggests answer label {label_prior}.\n\n"
                f"{instructions}"
            )

        if variant == "metadata_only":
            label_prior = item.metadata.get("label_prior", "A")
            tags = ", ".join(item.construct_tags)
            return (
                "Item metadata only:\n"
                f"Tags: {tags}\n"
                f"Artifact hint: {item.metadata.get('artifact_hint', False)}\n"
                f"Label prior: {label_prior}\n\n"
                f"{instructions}"
            )

        if variant == "answer_length_only":
            lengths = []
            for choice in item.choices or []:
                label, text = choice.split(".", 1)
                lengths.append(f"{label.strip()}. {len(text.strip())} characters")
            return "Answer-option lengths only:\n" + "\n".join(lengths) + f"\n\n{instructions}"

        if variant == "format_only":
            return (
                "Context:\n[format placeholder]\n\n"
                "Question:\n[format placeholder]\n\n"
                f"Choices:\n{choices}\n\n{instructions}"
            )

        if variant == "irrelevant_context":
            irrelevant = "A calendar note says the meeting moved from Tuesday to Friday."
            return f"Context:\n{irrelevant}\n\nQuestion:\n{item.prompt}\n\nChoices:\n{choices}\n\n{instructions}"

        if variant == "retrieval_only":
            return f"Context:\n{context}\n\nChoices:\n{choices}\n\n{instructions}"

        if variant == "zero_shot_direct":
            return f"{item.prompt}\n\n{choices}\n\nSelect the best answer."

        if variant == "few_shot":
            example = "Example:\nQuestion: Which option is the first letter?\nChoices:\nA. A\nB. B\nC. C\nD. D\nAnswer: A"
            return f"{example}\n\nQuestion:\n{item.prompt}\n\nChoices:\n{choices}\n\n{instructions}"

        if variant == "chain_of_thought_allowed":
            return (
                f"Context:\n{context}\n\nQuestion:\n{item.prompt}\n\nChoices:\n{choices}\n\n"
                "You may reason briefly, but end with a final answer letter."
            )

        if variant == "direct_answer_only":
            return (
                f"Question:\n{item.prompt}\n\nChoices:\n{choices}\n\nReturn only the answer letter."
            )

        if variant == "json_only":
            return (
                f"Context:\n{context}\n\nQuestion:\n{item.prompt}\n\nChoices:\n{choices}\n\n"
                'Return JSON like {"answer": "A"}.'
            )

        if variant == "answer_letter_only":
            return f"Question:\n{item.prompt}\n\nChoices:\n{choices}\n\nLetter only."

        if variant == "randomized_option_order":
            choice_lines = list(item.choices or [])
            rng = random.Random(f"order|{item.item_id}")
            rng.shuffle(choice_lines)
            return (
                f"Context:\n{context}\n\nQuestion:\n{item.prompt}\n\nChoices:\n"
                + "\n".join(choice_lines)
                + f"\n\n{instructions}"
            )

        if variant == "alternate_system_prompt":
            return (
                "System: You are evaluating a synthetic audit item.\n\n"
                f"Context:\n{context}\n\nQuestion:\n{item.prompt}\n\nChoices:\n{choices}\n\n{instructions}"
            )

        if variant == "no_system_prompt":
            return f"{context}\n\n{item.prompt}\n\n{choices}\n\n{instructions}"

        if variant == "terse_instructions":
            return f"Context:\n{context}\n\nQuestion:\n{item.prompt}\n\nChoices:\n{choices}\n\nA/B/C/D?"

        return (
            f"Context:\n{context}\n\nQuestion:\n{item.prompt}\n\nChoices:\n{choices}\n\n"
            "Give a careful answer using one of A, B, C, or D."
        )

    def score_prediction(self, item: BenchmarkItem, prediction: str) -> ScoreResult:
        return score_mcq(item, prediction)

    def available_prompt_variants(self) -> list[str]:
        return [
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
            "few_shot",
            "chain_of_thought_allowed",
            "direct_answer_only",
            "json_only",
            "answer_letter_only",
            "randomized_option_order",
            "alternate_system_prompt",
            "no_system_prompt",
            "terse_instructions",
            "verbose_instructions",
        ]
