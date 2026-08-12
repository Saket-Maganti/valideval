from __future__ import annotations

from collections.abc import Mapping
from typing import Any

RETAIN = "RETAIN"
RETIRE = "RETIRE"


def audit_diagnostic_dependencies(
    specifications: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Audit declared diagnostic inputs and retire exact dependency duplicates."""

    nodes: list[dict[str, Any]] = []
    signatures: dict[tuple[Any, ...], str] = {}
    for name in sorted(specifications):
        spec = dict(specifications[name])
        dependencies = tuple(sorted(str(value) for value in spec.get("source_data", [])))
        signature = (
            str(spec.get("formula", "")),
            dependencies,
            bool(spec.get("depends_on_accuracy", False)),
            bool(spec.get("depends_on_rank", False)),
            bool(spec.get("depends_on_external_labels", False)),
        )
        duplicate_of = signatures.get(signature)
        contaminated = bool(spec.get("post_selected", False)) or bool(
            spec.get("label_contaminated", False)
        )
        status = RETIRE if duplicate_of or contaminated else RETAIN
        if status == RETAIN:
            signatures[signature] = name
        nodes.append(
            {
                "diagnostic": name,
                "status": status,
                "duplicate_of": duplicate_of,
                "source_data": list(dependencies),
                "formula": signature[0],
                "depends_on_accuracy": signature[2],
                "depends_on_rank": signature[3],
                "depends_on_external_labels": signature[4],
                "post_selected": bool(spec.get("post_selected", False)),
                "label_contaminated": bool(spec.get("label_contaminated", False)),
            }
        )
    edges = []
    for node in nodes:
        for source in node["source_data"]:
            edges.append({"source": source, "target": node["diagnostic"], "kind": "uses"})
        if node["duplicate_of"]:
            edges.append(
                {
                    "source": node["duplicate_of"],
                    "target": node["diagnostic"],
                    "kind": "duplicate",
                }
            )
    return {
        "schema_version": "v7",
        "nodes": nodes,
        "edges": edges,
        "retained": [node["diagnostic"] for node in nodes if node["status"] == RETAIN],
        "retired": [node["diagnostic"] for node in nodes if node["status"] == RETIRE],
    }
