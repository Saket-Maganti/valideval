PYTHON ?= python3

.PHONY: setup test lint format format-check typecheck package-build toy audit report paper-assets bundle reviewer-risk release-check reproduce v5-evidence v5-planning v5-release-dry-run v5-check clean

setup:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

lint:
	ruff check .

format:
	ruff format .

format-check:
	ruff format --check .

typecheck:
	$(PYTHON) -m mypy src/valideval/evidence src/valideval/execution src/valideval/importers/kaggle_v5.py src/valideval/cross_benchmark src/valideval/planning src/valideval/statistics src/valideval/measurement src/valideval/leakage src/valideval/synthetic

package-build:
	$(PYTHON) -m build

toy:
	$(PYTHON) -m valideval toy

audit:
	$(PYTHON) -m valideval matrices --benchmark toy_mcq --panel mock
	$(PYTHON) -m valideval audit --benchmark toy_mcq --panel mock --diagnostics all-core
	$(PYTHON) -m valideval report --benchmark toy_mcq --panel mock

report:
	$(PYTHON) -m valideval report --benchmark toy_mcq --panel mock

paper-assets:
	$(PYTHON) paper/make_assets.py --benchmark toy_mcq --panel mock

bundle:
	$(PYTHON) -m valideval bundle --benchmark toy_mcq --panel mock
	$(PYTHON) -m valideval verify-bundle bundles/toy_mcq_mock_bundle

reviewer-risk:
	$(PYTHON) -m valideval reviewer-risk --report reportcards/toy_mcq_mock.md

release-check: test lint toy audit report paper-assets bundle reviewer-risk

reproduce: test audit

v5-evidence:
	$(PYTHON) scripts/reproduce_mmlu_evidence_v5.py
	$(PYTHON) scripts/build_claim_evidence_ledger_v5.py

v5-planning:
	$(PYTHON) scripts/build_common_panel_plan_v5.py
	$(PYTHON) scripts/estimate_execution_runtime_v5.py

v5-release-dry-run:
	$(PYTHON) scripts/build_release_v5.py --profile source
	$(PYTHON) scripts/build_release_v5.py --profile evidence
	$(PYTHON) scripts/build_release_v5.py --profile reviewer

v5-check: lint test typecheck package-build v5-evidence v5-planning v5-release-dry-run

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache build htmlcov
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
