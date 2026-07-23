from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JsonModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    def to_json_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class ConstructSpec(JsonModel):
    schema_version: str = "0.1"
    claimed_construct: str
    construct_tags: list[str] = Field(default_factory=list)
    construct_critical_fields: list[str] = Field(default_factory=list)
    expected_threats: list[str] = Field(default_factory=list)
    description: str | None = None
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BenchmarkItem(JsonModel):
    schema_version: str = "0.1"
    item_id: str
    prompt: str
    answer: str | list[str]
    choices: list[str] | None = None
    context: str | None = None
    source_url: str | None = None
    source_document: str | None = None
    snapshot: str | None = None
    license: str | None = None
    created_by: str | None = None
    generated_by_model: str | None = None
    human_verified: bool | None = None
    appears_in_paper_examples: bool | None = None
    appears_in_readme: bool | None = None
    appears_in_hf_preview: bool | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    construct_tags: list[str] = Field(default_factory=list)
    construct_critical_fields: list[str] = Field(default_factory=list)


class ScoreResult(JsonModel):
    schema_version: str = "0.1"
    score: float
    is_correct: bool | None = None
    normalized_prediction: str | None = None
    normalized_answer: str | None = None
    matched_answer: str | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelOutput(JsonModel):
    schema_version: str = "0.1"
    prediction: str
    raw_output: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelPrediction(JsonModel):
    schema_version: str = "0.1"
    model_id: str
    item_id: str
    prompt_variant: str
    prediction: str
    score: float
    is_correct: bool | None = None
    logprob: float | None = None
    raw_output: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResponseMatrixMetadata(JsonModel):
    schema_version: str = "0.1"
    benchmark_id: str
    panel_id: str
    prompt_variant: str
    scoring_method: str
    n_models: int
    n_items: int
    seed: int | None = None
    generated_at: str = Field(default_factory=utc_now)
    item_hash: str | None = None
    prediction_hash: str | None = None
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResponseMatrix(JsonModel):
    schema_version: str = "0.1"
    model_ids: list[str]
    item_ids: list[str]
    values: list[list[float]]
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.values, index=self.model_ids, columns=self.item_ids)

    @classmethod
    def from_dataframe(
        cls, frame: pd.DataFrame, metadata: dict[str, Any] | None = None
    ) -> ResponseMatrix:
        return cls(
            model_ids=[str(index) for index in frame.index.tolist()],
            item_ids=[str(column) for column in frame.columns.tolist()],
            values=frame.astype(float).values.tolist(),
            metadata=metadata or {},
        )


class DiagnosticResult(JsonModel):
    schema_version: str = "0.1"
    benchmark_id: str
    diagnostic_name: str
    version: str
    summary_metrics: dict[str, Any] = Field(default_factory=dict)
    per_model_metrics: dict[str, Any] = Field(default_factory=dict)
    per_item_metrics: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    artifacts: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now)


class ValidityProfile(JsonModel):
    schema_version: str = "0.1"
    benchmark_id: str
    diagnostics: dict[str, DiagnosticResult] = Field(default_factory=dict)
    interpretation: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class ReportCardManifest(JsonModel):
    schema_version: str = "0.1"
    benchmark_id: str
    panel_id: str
    report_path: str
    diagnostics_run: list[str]
    result_paths: list[str] = Field(default_factory=list)
    reproduction_commands: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now)


class AnnotationTask(JsonModel):
    schema_version: str = "0.1"
    task_id: str
    item_id: str
    prompt: str
    model_output: str
    gold_answer: str | list[str] | None = None
    rubric: str
    model_id: str | None = None
    sampling_strategy: str = "random"
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    task_hash: str | None = None
    created_at: str = Field(default_factory=utc_now)


class AnnotationPacket(JsonModel):
    schema_version: str = "0.1"
    packet_id: str
    benchmark_id: str
    panel_id: str
    sampling_strategy: str
    sample_size: int
    tasks: list[AnnotationTask]
    guidelines: str
    rubric: str
    manifest: dict[str, Any] = Field(default_factory=dict)
    version_hash: str | None = None
    created_at: str = Field(default_factory=utc_now)


class HumanJudgment(JsonModel):
    schema_version: str = "0.1"
    task_id: str
    item_id: str
    anonymized_annotator: str
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str | None = None
    model_id: str | None = None
    ambiguity_flag: bool = False
    invalid_item_flag: bool = False
    timestamp: str = Field(default_factory=utc_now)
    version_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class JudgePrediction(JsonModel):
    schema_version: str = "0.1"
    judge_id: str
    judge_type: str
    variant: str
    task_id: str
    item_id: str
    label: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    rationale: str | None = None
    model_id: str | None = None
    timestamp: str = Field(default_factory=utc_now)
    version_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AdjudicationDecision(JsonModel):
    schema_version: str = "0.1"
    decision_id: str
    task_id: str
    item_id: str
    final_label: str
    adjudicator: str
    rationale: str | None = None
    model_id: str | None = None
    source_labels: list[str] = Field(default_factory=list)
    ambiguity_resolved: bool = False
    timestamp: str = Field(default_factory=utc_now)
    version_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnnotationAgreementReport(JsonModel):
    schema_version: str = "0.1"
    benchmark_id: str
    panel_id: str
    n_items: int
    n_tasks: int
    n_judgments: int
    n_annotators: int
    raw_agreement: float | None = None
    cohen_kappa: float | None = None
    fleiss_kappa: float | None = None
    krippendorff_alpha: dict[str, Any] = Field(default_factory=dict)
    bootstrap_ci: dict[str, Any] = Field(default_factory=dict)
    confusion_matrix: dict[str, dict[str, int]] = Field(default_factory=dict)
    agreement_by_tag: dict[str, Any] = Field(default_factory=dict)
    agreement_by_item_type: dict[str, Any] = Field(default_factory=dict)
    agreement_by_model: dict[str, Any] = Field(default_factory=dict)
    ambiguity_rate: float | None = None
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now)
