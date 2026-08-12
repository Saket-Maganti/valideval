from __future__ import annotations

from valideval.execution.manifest import compute_configuration_hash
from valideval.scoring.extraction_stress_v7_2_1 import extraction_fixtures
from valideval.scoring.gsm8k import normalize_numeric_answer
from valideval.scoring.mmlu import parse_mmlu_answer
from valideval.scoring.reference_v7_2_1 import reference_numeric_normalize


def test_independent_numeric_reference_matches_golden_values() -> None:
    for value, expected in (
        ("1,234", "1234"),
        ("10.500", "10.5"),
        ("2/4", "1/2"),
        ("-0", "0"),
    ):
        assert normalize_numeric_answer(value) == expected
        assert reference_numeric_normalize(value) == expected


def test_extraction_fixture_registry_covers_adversarial_classes() -> None:
    names = {row["case"] for row in extraction_fixtures()}
    assert {
        "missing",
        "mmlu_multiple",
        "mmlu_embedded_word",
        "gsm_comma",
        "gsm_decimal",
        "gsm_fraction",
        "gsm_unicode_space",
        "gsm_multiple",
        "bbh_malformed",
    }.issubset(names)


def test_mmlu_answer_letter_embedded_in_word_is_not_extracted() -> None:
    parsed = parse_mmlu_answer("The answer is complicated")
    assert not parsed.succeeded
    assert parsed.value is None


def test_one_character_prompt_contract_mutation_changes_identity() -> None:
    contract = {
        "system_text": "Return one answer.",
        "prompt": "Question: {question}",
        "answer_format": "A/B/C/D",
        "few_shot": "zero",
        "stop": ["\n"],
        "max_tokens": 4,
    }
    baseline = compute_configuration_hash(contract)
    for key in contract:
        mutated = dict(contract)
        value = mutated[key]
        if isinstance(value, str):
            mutated[key] = value + "x"
        elif isinstance(value, list):
            mutated[key] = [*value, "x"]
        else:
            mutated[key] = int(value) + 1
        assert compute_configuration_hash(mutated) != baseline
