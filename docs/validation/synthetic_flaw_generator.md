# Synthetic Flaw Generator

The generator in `src/valideval/validation/` creates MCQ-style benchmark items with explicit ground-truth metadata:

```json
{
  "metadata": {
    "flaw_type": "shortcut_signal",
    "flaw_strength": 0.6,
    "is_flawed": true,
    "ground_truth_signal": {}
  }
}
```

Supported flaws include clean items, shortcut signals, label imbalance, answer-length artifacts, keyword artifacts, dead distractors, redundancy, low and negative discrimination, ceiling and floor effects, scoring ambiguity, prompt-format fragility, extraction ambiguity, context irrelevance, and context leakage.

Flaw strength is swept from `0.0` to `1.0`. At strength `0.0`, generated items are clean/null items. At higher strengths, a deterministic seed controls which items receive the flaw.

For `negative_discrimination`, the generator keeps clean anchor items in the benchmark and caps the flawed subset at 30% of items. Strength controls both the fraction and severity of anti-correlated items: higher-ability synthetic models increasingly miss those items while lower-ability or shortcut-like models pass them. This makes the ground truth identifiable under the IRT proxy; a benchmark where nearly every item rewards the wrong ability ordering cannot be oriented from the response matrix alone.

The controlled model panel includes reasoners, shortcut exploiters, label-prior and length heuristics, format-fragile behavior, random behavior, anti-discrimination behavior, and an ordered synthetic IRT validation panel. These are synthetic probes, not real models.

Generator limitations:

- The synthetic templates are intentionally simple.
- A diagnostic can overfit this generator and still fail on real benchmarks.
- Some flaws are harder to identify because the existing diagnostic output is not a direct detector for that flaw.
- Clean synthetic data is not a proof that a real benchmark is clean.
