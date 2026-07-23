from __future__ import annotations

import json
from pathlib import Path

import pytest

try:
    import nbclient
    import nbformat
except ImportError:  # pragma: no cover - exercised in minimal environments
    nbclient = None
    nbformat = None

NOTEBOOK_ROOT = Path(__file__).parents[1] / "kaggle_max_ceiling"


@pytest.mark.parametrize("notebook_path", sorted(NOTEBOOK_ROOT.glob("*.ipynb")))
def test_notebook_executes_top_to_bottom_in_fixture_mode(
    notebook_path: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("VALIDEVAL_EXECUTION_MODE", "fixture")
    monkeypatch.setenv("VALIDEVAL_NOTEBOOK_OUTPUT_ROOT", str(tmp_path / "outputs"))
    if nbclient is not None and nbformat is not None:
        notebook = nbformat.read(notebook_path, as_version=4)
        client = nbclient.NotebookClient(
            notebook,
            timeout=120,
            kernel_name="python3",
            resources={"metadata": {"path": str(Path(__file__).parents[1])}},
        )
        executed = client.execute()
        assert all(
            not output.get("ename")
            for cell in executed.cells
            for output in cell.get("outputs", [])
            if output.get("output_type") == "error"
        )
    else:
        payload = json.loads(notebook_path.read_text(encoding="utf-8"))
        namespace = {"__name__": "__notebook_fixture__"}
        for index, cell in enumerate(payload["cells"]):
            if cell["cell_type"] == "code":
                source = "".join(cell["source"])
                exec(compile(source, f"{notebook_path.name}:cell-{index}", "exec"), namespace)
        assert namespace["RESULT"]["evidence_state"] == "NON_EVIDENCE_FIXTURE"
