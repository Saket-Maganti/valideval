from __future__ import annotations

import pytest

from valideval.evidence.provenance_v7_2_1 import (
    InvalidationCause,
    ProvenanceEdge,
    ProvenanceNode,
    ProvenanceNodeKind,
    build_provenance_graph,
    propagate_invalidation,
)
from valideval.evidence.state_v7_2 import (
    EvidenceStateV72,
    transition_evidence_state_v7_2,
)
from valideval.execution.schema_v7_2_1 import (
    CURRENT_EXECUTION_SCHEMA,
    CURRENT_PACKAGE_MEMBERS,
    BenchmarkId,
    RunId,
    SourceCommit,
    export_current_package_schema,
)


def test_evidence_state_disallows_illegal_jumps_and_terminal_revival() -> None:
    with pytest.raises(ValueError, match="illegal evidence transition"):
        transition_evidence_state_v7_2(
            EvidenceStateV72.PLANNED,
            EvidenceStateV72.DECISION_LICENSED,
            reason="no prerequisites",
        )
    with pytest.raises(ValueError, match="illegal evidence transition"):
        transition_evidence_state_v7_2(
            EvidenceStateV72.INVALIDATED,
            EvidenceStateV72.PLANNED,
            reason="cannot silently revive invalid evidence",
        )
    transition = transition_evidence_state_v7_2(
        EvidenceStateV72.DECISION_LICENSED,
        EvidenceStateV72.INVALIDATED,
        reason="scorer defect",
    )
    assert transition["to"] == "INVALIDATED"


def test_invalidation_propagates_from_source_to_claim() -> None:
    nodes = [
        ProvenanceNode("source", ProvenanceNodeKind.SOURCE),
        ProvenanceNode("config", ProvenanceNodeKind.CONFIG),
        ProvenanceNode("run", ProvenanceNodeKind.RAW_RUN),
        ProvenanceNode("package", ProvenanceNodeKind.IMPORTED_PACKAGE),
        ProvenanceNode("analysis", ProvenanceNodeKind.ANALYSIS),
        ProvenanceNode("claim", ProvenanceNodeKind.CLAIM),
    ]
    edges = [
        ProvenanceEdge("config", "source"),
        ProvenanceEdge("run", "config"),
        ProvenanceEdge("package", "run"),
        ProvenanceEdge("analysis", "package"),
        ProvenanceEdge("claim", "analysis"),
    ]
    graph = build_provenance_graph(nodes, edges)
    result = propagate_invalidation(
        graph,
        [InvalidationCause("source", "SOURCE_MISMATCH", "tag moved")],
    )
    assert result["invalidated_count"] == 6
    assert result["invalidated"]["claim"]["failure_type"] == "UPSTREAM_INVALIDATION"


def test_provenance_graph_rejects_cycles() -> None:
    nodes = [
        ProvenanceNode("left", ProvenanceNodeKind.ANALYSIS),
        ProvenanceNode("right", ProvenanceNodeKind.ANALYSIS),
    ]
    with pytest.raises(ValueError, match="acyclic"):
        build_provenance_graph(
            nodes,
            [ProvenanceEdge("left", "right"), ProvenanceEdge("right", "left")],
        )


def test_current_package_schema_and_typed_identifiers() -> None:
    schema = export_current_package_schema()
    assert tuple(schema["required"]) == CURRENT_PACKAGE_MEMBERS
    assert CURRENT_EXECUTION_SCHEMA == "valideval.execution.v7.1"
    assert BenchmarkId("mmlu") is BenchmarkId.MMLU
    assert str(RunId("s1-v7-2-mmlu")) == "s1-v7-2-mmlu"
    assert str(SourceCommit("a" * 40)) == "a" * 40
    with pytest.raises(ValueError):
        RunId("../unsafe")
