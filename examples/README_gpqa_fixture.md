# GPQA Diamond Tiny Fixture

Artifact class: **GPQA fixture dry-run**.

`examples/gpqa_diamond_tiny_fixture.jsonl` contains synthetic, non-real, GPQA-like multiple-choice records. It is only for validating local JSONL schema checks, prompt rendering, extraction/scoring behavior, cached matrix generation, diagnostics plumbing, and dry-run report generation.

This fixture is not GPQA Diamond, is not derived from GPQA Diamond, and is not scientific evidence about GPQA Diamond.

Expected local GPQA JSONL schema:

```json
{
  "item_id": "gpqa_diamond_0001",
  "question": "...",
  "choices": {
    "A": "...",
    "B": "...",
    "C": "...",
    "D": "..."
  },
  "answer": "C",
  "domain": "physics",
  "source": "gpqa",
  "split": "diamond",
  "metadata": {}
}
```

The adapter validates that item IDs and questions exist, choices are exactly A/B/C/D, the answer is one of those labels, item IDs are unique, optional domain metadata is preserved, and metadata does not contain likely answer-leakage keys or values.
