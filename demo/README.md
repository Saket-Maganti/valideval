# ValidEval Demo Walkthrough

This demo uses the offline toy benchmark. It is for software validation and does not make empirical claims about real models.

## 1. Build Cached Matrices

```bash
python3 -m valideval matrices --benchmark toy_mcq --panel mock
```

## 2. Run Diagnostics

```bash
python3 -m valideval audit --benchmark toy_mcq --panel mock --diagnostics all-core
```

Look for:

- Raw ranking and ranking views in `results/toy_mcq/mock/ranking_views.json` after running `leaderboard`.
- Shortcut signals in `results/toy_mcq/mock/shortcut.json`.
- IRT item-quality signals in `results/toy_mcq/mock/irt.json`.
- Reliability signals in `results/toy_mcq/mock/reliability.json`.

## 3. Render Report, Certificate, and Repair Suggestions

```bash
python3 -m valideval report --benchmark toy_mcq --panel mock
python3 -m valideval repair --benchmark toy_mcq --panel mock
python3 -m valideval card render --benchmark toy_mcq --panel mock
python3 -m valideval certificate issue --benchmark toy_mcq --panel mock
```

## 4. Generate Paper Assets and Bundle

```bash
python3 paper/make_assets.py
python3 -m valideval bundle --benchmark toy_mcq --panel mock
python3 -m valideval verify-bundle bundles/toy_mcq_mock_bundle
```

## Interpretation

The demo shows how ValidEval surfaces possible validity threats under a controlled protocol. Do not treat the toy benchmark as a real leaderboard or the certificate as a total score.
