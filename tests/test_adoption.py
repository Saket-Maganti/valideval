from __future__ import annotations

import csv
import json

import valideval
from valideval.adoption.advisor import advise_benchmark_selection
from valideval.adoption.doctor import run_doctor
from valideval.adoption.importers import import_outputs
from valideval.adoption.schemas import export_schema, validate_payload
from valideval.adoption.toolkit import init_benchmark, validate_benchmark
from valideval.cli import main
from valideval.io.jsonl import write_jsonl
from valideval.plugins import get_plugin
from valideval.schemas import BenchmarkItem


def test_plugin_decorator_registration():
    @valideval.diagnostic("unit_test_plugin", replace=True)
    class UnitDiagnostic:
        pass

    assert get_plugin("diagnostic", "unit_test_plugin") is UnitDiagnostic
    assert "unit_test_plugin" in valideval.list_plugins("diagnostic")


def test_schema_export_and_validation(tmp_path):
    items = _items()
    items_path = tmp_path / "items.jsonl"
    write_jsonl(items_path, items)

    exported = export_schema("all", tmp_path / "schemas")
    assert "benchmark" in exported
    assert (tmp_path / "schemas" / "audit_manifest.schema.json").exists()

    validation = validate_payload("benchmark", items_path)
    assert validation["valid"]
    assert validation["n_records"] == 2

    assert main(["schema", "export", "benchmark", "--output", str(tmp_path / "cli_schemas")]) == 0
    assert main(["schema", "validate", "benchmark", "--path", str(items_path)]) == 0


def test_generic_importer_and_cli(tmp_path):
    source = tmp_path / "outputs.csv"
    with source.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["model", "item_id", "prediction", "score", "raw_output"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "model": "model_a",
                "item_id": "item_1",
                "prediction": "A",
                "score": "1",
                "raw_output": "A",
            }
        )
    output = tmp_path / "normalized.jsonl"
    result = import_outputs(source, adapter="generic-csv", output_path=output)
    assert result["n_predictions"] == 1
    assert validate_payload("prediction", output)["valid"]

    cli_output = tmp_path / "normalized_cli.jsonl"
    assert (
        main(
            [
                "import-outputs",
                "--input",
                str(source),
                "--output",
                str(cli_output),
                "--adapter",
                "generic-csv",
            ]
        )
        == 0
    )
    assert cli_output.exists()


def test_quickstart_audit_outputs_and_artifact_schemas(tmp_path):
    items_path = tmp_path / "items.jsonl"
    write_jsonl(items_path, _items())
    card = tmp_path / "benchmark_card.md"
    card.write_text("# Toy local construct\n", encoding="utf-8")
    outputs = tmp_path / "outputs.jsonl"
    outputs.write_text(
        "\n".join(
            [
                json.dumps({"model": "model_a", "item_id": "item_1", "output": "A"}),
                json.dumps({"model": "model_a", "item_id": "item_2", "output": "B"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "quickstart"

    assert (
        main(
            [
                "quickstart-audit",
                "--items",
                str(items_path),
                "--outputs",
                str(outputs),
                "--benchmark-card",
                str(card),
                "--output-dir",
                str(output_dir),
            ]
        )
        == 0
    )

    assert (output_dir / "validity_card.md").exists()
    assert (output_dir / "validity_card.json").exists()
    assert (output_dir / "certificate.json").exists()
    assert (output_dir / "item_forensics.csv").exists()
    assert (output_dir / "repair_recommendations.md").exists()
    assert (output_dir / "audit_manifest.json").exists()
    assert (output_dir / "README_NEXT_STEPS.md").exists()
    assert validate_payload("validity_card", output_dir / "validity_card.json")["valid"]
    assert validate_payload("certificate", output_dir / "certificate.json")["valid"]
    assert validate_payload("audit_manifest", output_dir / "audit_manifest.json")["valid"]


def test_benchmark_author_toolkit_and_path_cli(tmp_path):
    benchmark_dir = tmp_path / "my_benchmark"
    init = init_benchmark(benchmark_dir)
    assert len(init["created"]) == 6
    assert validate_benchmark(benchmark_dir)["valid"]

    assert main(["init-benchmark", str(tmp_path / "cli_benchmark")]) == 0
    assert main(["validate-benchmark", str(benchmark_dir)]) == 0
    assert main(["generate-card", str(benchmark_dir)]) == 0
    assert (
        main(
            [
                "audit",
                str(benchmark_dir),
                "--cache-root",
                str(tmp_path / "cache"),
                "--results-root",
                str(tmp_path / "results"),
            ]
        )
        == 0
    )
    assert (tmp_path / "results" / "local_jsonl" / "manifest.json").exists()


def test_design_assistant_preregistration_advisor_and_plugins_cli(tmp_path):
    design_dir = tmp_path / "design"
    assert (
        main(
            [
                "design-assistant",
                "--noninteractive",
                "--benchmark-id",
                "rag_eval",
                "--construct",
                "RAG faithfulness under supplied evidence",
                "--domain",
                "rag",
                "--output-dir",
                str(design_dir),
            ]
        )
        == 0
    )
    assert (design_dir / "construct_spec.yaml").exists()
    assert (design_dir / "audit_plan.md").exists()
    assert (
        main(
            [
                "preregister",
                "--benchmark",
                "rag_eval",
                "--goal",
                "evaluate RAG faithfulness",
                "--domain",
                "rag",
                "--output-dir",
                str(tmp_path / "protocols"),
            ]
        )
        == 0
    )
    assert (tmp_path / "protocols" / "preregistration_rag_eval.md").exists()
    preregistration = (tmp_path / "protocols" / "preregistration_rag_eval.md").read_text(
        encoding="utf-8"
    )
    assert "## Protocol Boundary" in preregistration
    assert "No paid API is a required dependency" in preregistration
    assert "not one scalar score" in preregistration
    assert "## Blocked or Negative Evidence" in preregistration

    advice = advise_benchmark_selection("evaluate RAG faithfulness")
    assert advice["recommended_domain_pack"] == "rag"
    assert "unsupported citations" in advice["possible_validity_threats"]
    assert main(["advisor", "--goal", "evaluate RAG faithfulness"]) == 0
    assert main(["plugins", "list"]) == 0


def test_doctor_metadata_only_readiness_report(tmp_path):
    payload = run_doctor(
        benchmark_id="toy_mcq",
        panel_id="mock",
        cache_root=tmp_path / "cache",
        results_root=tmp_path / "results",
        reportcards_root=tmp_path / "reportcards",
    )
    serialized = json.dumps(payload, sort_keys=True)

    assert payload["status"] == "warning"
    assert payload["offline_safe"]
    assert payload["metadata_only"]
    assert "Which substance does the plant store" not in serialized
    assert "A plant uses sunlight" not in serialized
    assert any(check["name"] == "benchmark_load" for check in payload["checks"])
    assert any("python3 -m valideval matrices" in command for command in payload["next_commands"])

    assert (
        main(
            [
                "doctor",
                "--benchmark",
                "toy_mcq",
                "--panel",
                "mock",
                "--cache-root",
                str(tmp_path / "cache"),
                "--results-root",
                str(tmp_path / "results"),
                "--reportcards-root",
                str(tmp_path / "reportcards"),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "doctor",
                "--benchmark",
                "toy_mcq",
                "--panel",
                "mock",
                "--cache-root",
                str(tmp_path / "cache"),
                "--results-root",
                str(tmp_path / "results"),
                "--reportcards-root",
                str(tmp_path / "reportcards"),
                "--strict",
            ]
        )
        == 1
    )

    local_items = tmp_path / "items.jsonl"
    write_jsonl(local_items, _items())
    local_payload = run_doctor(
        benchmark_id="local_jsonl",
        panel_id="mock",
        local_path=local_items,
        cache_root=tmp_path / "cache",
        results_root=tmp_path / "results",
        reportcards_root=tmp_path / "reportcards",
    )
    assert any("--local-path" in command for command in local_payload["next_commands"])


def _items() -> list[BenchmarkItem]:
    return [
        BenchmarkItem(
            item_id="item_1",
            prompt="Which option follows from the context?",
            answer="A",
            choices=["A. Supported", "B. Unsupported", "C. Unrelated", "D. Ambiguous"],
            context="The context says the supported option follows.",
            source_document="unit_fixture",
            license="MIT",
            created_by="test",
            human_verified=True,
            construct_tags=["context_use"],
            construct_critical_fields=["prompt", "context", "choices"],
            metadata={"split": "test"},
        ),
        BenchmarkItem(
            item_id="item_2",
            prompt="Which label is correct?",
            answer="B",
            choices=["A. First", "B. Second", "C. Third", "D. Fourth"],
            context="The correct label is second.",
            source_document="unit_fixture",
            license="MIT",
            created_by="test",
            human_verified=True,
            construct_tags=["context_use"],
            construct_critical_fields=["prompt", "context", "choices"],
            metadata={"split": "test"},
        ),
    ]
