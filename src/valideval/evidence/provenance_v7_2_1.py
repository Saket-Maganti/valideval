from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class ProvenanceNodeKind(str, Enum):
    CLAIM = "CLAIM"
    ANALYSIS = "ANALYSIS"
    IMPORTED_PACKAGE = "IMPORTED_PACKAGE"
    RAW_RUN = "RAW_RUN"
    CONFIG = "CONFIG"
    SOURCE = "SOURCE"


@dataclass(frozen=True, slots=True)
class ProvenanceNode:
    node_id: str
    kind: ProvenanceNodeKind
    artifact_hash: str | None = None
    evidence_class: str | None = None


@dataclass(frozen=True, slots=True)
class ProvenanceEdge:
    dependent: str
    dependency: str


@dataclass(frozen=True, slots=True)
class InvalidationCause:
    node_id: str
    failure_type: str
    reason: str


def build_provenance_graph(
    nodes: Sequence[ProvenanceNode],
    edges: Sequence[ProvenanceEdge],
) -> dict[str, Any]:
    node_map = {node.node_id: node for node in nodes}
    if len(node_map) != len(nodes):
        raise ValueError("provenance node IDs must be unique")
    for edge in edges:
        if edge.dependent not in node_map or edge.dependency not in node_map:
            raise ValueError("provenance edge references an unknown node")
        if edge.dependent == edge.dependency:
            raise ValueError("provenance self-dependency is forbidden")
    _topological_order(node_map, edges)
    return {
        "schema_version": "valideval.provenance-dag.v7.2.1",
        "nodes": [
            {**asdict(node), "kind": node.kind.value}
            for node in sorted(nodes, key=lambda value: value.node_id)
        ],
        "edges": [
            asdict(edge)
            for edge in sorted(edges, key=lambda value: (value.dependent, value.dependency))
        ],
        "topological_order": _topological_order(node_map, edges),
    }


def propagate_invalidation(
    graph: Mapping[str, Any],
    causes: Sequence[InvalidationCause],
) -> dict[str, Any]:
    nodes = {str(node["node_id"]): dict(node) for node in graph["nodes"]}
    dependents: dict[str, set[str]] = defaultdict(set)
    for edge in graph["edges"]:
        dependents[str(edge["dependency"])].add(str(edge["dependent"]))
    invalidated: dict[str, dict[str, str]] = {}
    queue: deque[tuple[str, str, str]] = deque()
    for cause in causes:
        if cause.node_id not in nodes:
            raise ValueError(f"invalidation cause references unknown node: {cause.node_id}")
        queue.append((cause.node_id, cause.failure_type, cause.reason))
    while queue:
        node_id, failure_type, reason = queue.popleft()
        if node_id in invalidated:
            continue
        invalidated[node_id] = {
            "state": "INVALIDATED",
            "failure_type": failure_type,
            "reason": reason,
        }
        for dependent in sorted(dependents[node_id]):
            queue.append(
                (
                    dependent,
                    "UPSTREAM_INVALIDATION",
                    f"Dependency {node_id} was invalidated: {reason}",
                )
            )
    return {
        "schema_version": "valideval.invalidation-propagation.v7.2.1",
        "status": "INVALIDATION_PROPAGATED",
        "invalidated": dict(sorted(invalidated.items())),
        "invalidated_count": len(invalidated),
    }


def _topological_order(
    nodes: Mapping[str, ProvenanceNode],
    edges: Sequence[ProvenanceEdge],
) -> list[str]:
    dependencies: dict[str, set[str]] = {node_id: set() for node_id in nodes}
    dependents: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        dependencies[edge.dependent].add(edge.dependency)
        dependents[edge.dependency].add(edge.dependent)
    ready = deque(sorted(node_id for node_id, values in dependencies.items() if not values))
    order: list[str] = []
    while ready:
        node_id = ready.popleft()
        order.append(node_id)
        for dependent in sorted(dependents[node_id]):
            dependencies[dependent].discard(node_id)
            if not dependencies[dependent]:
                ready.append(dependent)
    if len(order) != len(nodes):
        raise ValueError("provenance graph must be acyclic")
    return order
