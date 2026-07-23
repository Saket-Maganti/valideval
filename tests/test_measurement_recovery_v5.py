from valideval.measurement.hierarchical_subject import synthetic_recovery_check


def test_measurement_recovery_fixture_recovers_ordering():
    result = synthetic_recovery_check(
        n_models=12,
        n_subjects=3,
        items_per_subject=50,
        seed=4,
    )
    assert result["status"] == "PASS"
    assert result["evidence_status"] == "NON_EVIDENCE_FIXTURE"
    assert result["ability_spearman"] >= 0.8
    assert result["subject_easiness_spearman"] >= 0.8
