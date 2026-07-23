# Release Checklist

Before a release:

- [ ] Run `python3 -m pytest`.
- [ ] Run `python3 -m ruff check .`.
- [ ] Run `python3 -m valideval toy`.
- [ ] Run `python3 -m valideval matrices --benchmark toy_mcq --panel mock`.
- [ ] Run `python3 -m valideval audit --benchmark toy_mcq --panel mock --diagnostics all-core`.
- [ ] Run `python3 -m valideval report --benchmark toy_mcq --panel mock`.
- [ ] Run `python3 -m valideval bundle --benchmark toy_mcq --panel mock`.
- [ ] Run `python3 -m valideval verify-bundle bundles/toy_mcq_mock_bundle`.
- [ ] Run `python3 -m valideval reviewer-risk --report reportcards/toy_mcq_mock.md`.
- [ ] Regenerate paper assets with `python3 paper/make_assets.py`.
- [ ] Check `paper/CLAIMS_LEDGER.md`.
- [ ] Confirm no fake empirical results or placeholder numbers were added.
- [ ] Update `CHANGELOG.md`.
- [ ] Update version metadata if publishing a package.
- [ ] Confirm docs mention missing diagnostics and limitations.
- [ ] Confirm certificates and badges are not described as scalar scores.
