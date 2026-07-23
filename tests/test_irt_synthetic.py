import numpy as np

from valideval.diagnostics.irt import IRTDiagnostic
from valideval.psychometrics.irt_models import simulate_1pl
from valideval.psychometrics.reliability_stats import spearman_correlation
from valideval.schemas import ResponseMatrix


class DummyBenchmark:
    benchmark_id = "synthetic"
    claimed_construct = "synthetic latent trait"

    class construct_spec:
        construct_critical_fields = ["prompt"]

    def load_items(self):
        return []

    def render_prompt(self, item, variant="full"):
        return ""

    def score_prediction(self, item, prediction):
        raise NotImplementedError

    def available_prompt_variants(self):
        return ["full"]


def test_irt_proxy_recovers_ability_rank_order():
    abilities = np.linspace(-2, 2, 12)
    difficulties = np.linspace(-1.5, 1.5, 36)
    responses = simulate_1pl(abilities, difficulties, seed=3)
    matrix = ResponseMatrix(
        model_ids=[f"m{i}" for i in range(responses.shape[0])],
        item_ids=[f"i{j}" for j in range(responses.shape[1])],
        values=responses.tolist(),
        metadata={"prompt_variant": "full"},
    )

    result = IRTDiagnostic().run(
        DummyBenchmark(), matrix, config={"subset_sizes": [5], "random_subset_trials": 5}
    )
    estimated = [
        result.per_model_metrics[f"m{i}"]["latent_ability_proxy"] for i in range(responses.shape[0])
    ]

    assert spearman_correlation(abilities.tolist(), estimated) > 0.75


def test_irt_flags_near_zero_discrimination_item():
    values = [
        [1, 1, 0],
        [1, 1, 0],
        [0, 1, 1],
        [0, 1, 1],
        [0, 1, 0],
    ]
    matrix = ResponseMatrix(
        model_ids=[f"m{i}" for i in range(5)],
        item_ids=["disc", "constant", "mixed"],
        values=values,
        metadata={"prompt_variant": "full"},
    )

    result = IRTDiagnostic().run(
        DummyBenchmark(), matrix, config={"subset_sizes": [2], "random_subset_trials": 5}
    )

    assert result.per_item_metrics["constant"]["near_zero_discrimination"] is True


def test_irt_flags_anchor_oriented_negative_discrimination_item():
    values = [
        [0, 0, 0, 0, 1],
        [0, 0, 0, 1, 1],
        [0, 0, 1, 1, 1],
        [0, 1, 1, 1, 1],
        [1, 1, 1, 1, 0],
        [1, 1, 1, 1, 0],
        [1, 1, 1, 1, 0],
        [1, 1, 1, 1, 0],
    ]
    matrix = ResponseMatrix(
        model_ids=[f"m{i}" for i in range(8)],
        item_ids=["anchor_0", "anchor_1", "anchor_2", "anchor_3", "reversed"],
        values=values,
        metadata={"prompt_variant": "full"},
    )

    result = IRTDiagnostic().run(
        DummyBenchmark(), matrix, config={"subset_sizes": [2], "random_subset_trials": 5}
    )

    reversed_stats = result.per_item_metrics["reversed"]
    assert reversed_stats["negative_discrimination"] is True
    assert reversed_stats["discrimination_label"] == "negative_discrimination"
