# Adding a Diagnostic

Diagnostics should report conditional evidence, not verdicts.

Minimal plugin shape:

```python
import valideval


@valideval.diagnostic("my_diagnostic")
class MyDiagnostic:
    name = "my_diagnostic"
    version = "0.1"

    def run(self, benchmark, predictions, *, config=None):
        ...
```

Implementation expectations:

- Return `DiagnosticResult`.
- Put aggregate values in `summary_metrics`.
- Put item-specific values in `per_item_metrics`.
- Include warnings and limitations in cautious language.
- Keep toy/demo tests offline and deterministic.

Before merging a new public diagnostic, add docs and tests that cover both the measured case and the unavailable or insufficient-evidence case.
