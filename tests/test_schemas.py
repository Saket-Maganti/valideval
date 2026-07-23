from valideval.schemas import (
    AdjudicationDecision,
    AnnotationAgreementReport,
    AnnotationPacket,
    AnnotationTask,
    BenchmarkItem,
    DiagnosticResult,
    HumanJudgment,
    JudgePrediction,
    ModelPrediction,
    ReportCardManifest,
    ResponseMatrix,
    ResponseMatrixMetadata,
)


def test_schema_serialization_round_trip():
    item = BenchmarkItem(
        item_id="i1",
        prompt="Question?",
        answer="A",
        choices=["A. yes", "B. no"],
        construct_tags=["toy"],
        construct_critical_fields=["prompt"],
    )
    prediction = ModelPrediction(
        model_id="m1",
        item_id=item.item_id,
        prompt_variant="full",
        prediction="A",
        score=1.0,
        is_correct=True,
        raw_output="A",
    )
    matrix = ResponseMatrix(
        model_ids=["m1"],
        item_ids=["i1"],
        values=[[1.0]],
        metadata={"benchmark_id": "toy"},
    )
    result = DiagnosticResult(
        benchmark_id="toy",
        diagnostic_name="unit",
        version="0",
        summary_metrics={"score": 1.0},
    )
    matrix_metadata = ResponseMatrixMetadata(
        benchmark_id="toy",
        panel_id="mock",
        prompt_variant="full",
        scoring_method="mcq",
        n_models=1,
        n_items=1,
        prediction_hash="abc",
    )
    manifest = ReportCardManifest(
        benchmark_id="toy",
        panel_id="mock",
        report_path="reportcards/toy_mock.md",
        diagnostics_run=["unit"],
        reproduction_commands=["python3 -m valideval report --benchmark toy --panel mock"],
    )
    task = AnnotationTask(
        task_id="i1::m1",
        item_id="i1",
        prompt="Question?",
        model_output="A",
        gold_answer="A",
        rubric="MCQ correctness rubric.",
        model_id="m1",
    )
    packet = AnnotationPacket(
        packet_id="packet",
        benchmark_id="toy",
        panel_id="mock",
        sampling_strategy="random",
        sample_size=1,
        tasks=[task],
        guidelines="guidelines",
        rubric="rubric",
    )
    judgment = HumanJudgment(
        task_id="i1::m1",
        item_id="i1",
        anonymized_annotator="ann_a",
        label="correct",
        confidence=0.9,
    )
    judge = JudgePrediction(
        judge_id="rule",
        judge_type="rule_based",
        variant="strict",
        task_id="i1::m1",
        item_id="i1",
        label="correct",
    )
    decision = AdjudicationDecision(
        decision_id="d1",
        task_id="i1::m1",
        item_id="i1",
        final_label="correct",
        adjudicator="lead",
    )
    agreement = AnnotationAgreementReport(
        benchmark_id="toy",
        panel_id="mock",
        n_items=1,
        n_tasks=1,
        n_judgments=2,
        n_annotators=2,
    )

    assert item.model_dump(mode="json")["answer"] == "A"
    assert prediction.model_dump(mode="json")["score"] == 1.0
    assert matrix.to_dataframe().loc["m1", "i1"] == 1.0
    assert result.model_dump(mode="json")["diagnostic_name"] == "unit"
    assert matrix_metadata.model_dump(mode="json")["schema_version"] == "0.1"
    assert manifest.model_dump(mode="json")["diagnostics_run"] == ["unit"]
    assert packet.model_dump(mode="json")["tasks"][0]["task_id"] == "i1::m1"
    assert judgment.model_dump(mode="json")["confidence"] == 0.9
    assert judge.model_dump(mode="json")["variant"] == "strict"
    assert decision.model_dump(mode="json")["final_label"] == "correct"
    assert agreement.model_dump(mode="json")["n_annotators"] == 2
