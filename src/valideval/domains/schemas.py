from __future__ import annotations

from typing import Any

from pydantic import Field

from valideval.schemas import JsonModel, utc_now


class RAGItemMetadata(JsonModel):
    item_id: str
    question: str
    retrieved_context: str
    support_spans: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    answerable: bool = True
    evidence_position: str | None = None
    distractor_contexts: list[str] = Field(default_factory=list)


class AgentTraceStep(JsonModel):
    step_index: int
    action: str
    tool_call: dict[str, Any] = Field(default_factory=dict)
    observation: str | None = None
    state_hash: str | None = None
    reward: float | None = None
    error: str | None = None
    judge_decision: str | None = None
    timestamp: str = Field(default_factory=utc_now)


class AgentTrace(JsonModel):
    trace_id: str
    item_id: str
    steps: list[AgentTraceStep]
    final_answer: str | None = None
    success: bool | None = None
    environment_seed: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MedicalSegmentationMetadata(JsonModel):
    item_id: str
    site_id: str | None = None
    anatomy: str | None = None
    severity: str | None = None
    annotator_count: int | None = None
    uncertainty_score: float | None = None
    clinical_utility_weight: float | None = None


class GraphFraudMetadata(JsonModel):
    item_id: str
    entity_id: str
    timestamp: str | None = None
    degree: int | None = None
    split: str | None = None
    label: str | None = None
    neighborhood_label_rate: float | None = None


class CodeEvalMetadata(JsonModel):
    item_id: str
    repository: str | None = None
    package_lock_hash: str | None = None
    hidden_test_count: int | None = None
    public_test_count: int | None = None
    flaky_rerun_count: int | None = None
    language: str | None = None


class SafetyMetadata(JsonModel):
    item_id: str
    policy_version: str
    risk_category: str
    turn_count: int = 1
    adversarial_style: str | None = None
    expected_refusal: bool | None = None
    rubric_version: str | None = None


class MultimodalMetadata(JsonModel):
    item_id: str
    modality: str
    asset_path: str | None = None
    ocr_text: str | None = None
    caption: str | None = None
    resolution: str | None = None
    crop_id: str | None = None


class AbstentionMetadata(JsonModel):
    item_id: str
    answerable: bool = True
    abstention_allowed: bool = True
    deferral_target: str | None = None
    decision_cost: float | None = None
    uncertainty_score: float | None = None
