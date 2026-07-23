from pathlib import Path


def test_v5_paper_uses_result_required_placeholders() -> None:
    root = Path(__file__).resolve().parents[1]
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((root / "paper/v5/sections").glob("*.tex"))
    )
    assert "\\resultrequired{" in text
    assert "Controlled Exact-Checkpoint Study" in text
    assert "benchmark is invalid" not in text.lower()
