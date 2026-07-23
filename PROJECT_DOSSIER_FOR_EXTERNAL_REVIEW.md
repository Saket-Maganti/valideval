# ValidEval Project Dossier for External Review

## 1. Executive Summary

ValidEval is a Python toolkit for auditing whether AI benchmark scores support the validity claim attached to them. Its central thesis is that validity is not accuracy: an accuracy score can be inflated or distorted by shortcuts, contamination, scoring artifacts, weak items, low reliability, saturation, or construct undercoverage.

The repository currently contains a substantial offline prototype. The strongest runnable path is a deterministic toy multiple-choice audit using synthetic items and an eight-model mock panel. It generates cached predictions, response matrices, diagnostics, report cards, validity cards, certificates, leaderboard/dashboard artifacts, paper assets, and reproducibility bundles without paid APIs, internet, or Ollama.

Current results are toy/demo results only. No real benchmark experiment was found or run. Config files exist for real benchmarks such as GSM8K, MMLU, BBH, TruthfulQA, and CausalAgentBench, but their loaders are explicit placeholders. The code supports local JSONL benchmark imports, but there is no validated real benchmark export in this repository.

The requested external review should evaluate whether the project has a meaningful research contribution, which diagnostics are scientifically credible now, what must be removed or delayed, and what first real benchmark audit would make the toolkit reviewable by researchers.

---

## 2. Project Thesis and Intended Contribution

The intended contribution is to make benchmark validity auditable as a multidimensional evidence profile rather than as a single score. The project argues that benchmark accuracy may reflect construct-relevant capability, but may also reflect shortcuts, contamination, scoring artifacts, low-discrimination items, saturation, unreliable prompt/scorer behavior, or construct undercoverage.

ValidEval aims to operationalize psychometric and validity concepts into computable diagnostics. Intended outputs include:

- response matrices and cached model predictions
- shortcut, artifact, reliability, IRT, saturation, DIF, power, calibration, forensics, and ranking diagnostics
- item-level forensic tables
- advisory benchmark repair suggestions
- validity cards and profile certificates
- dashboard/leaderboard views
- reproducibility bundles
- reviewer-risk checks and paper asset generation

Implemented now:

- offline toy MCQ benchmark with controlled artifacts
- deterministic mock model panel
- local JSONL benchmark adapter
- many diagnostics that return structured `DiagnosticResult` objects
- report card, validity card, certificate, leaderboard/dashboard, human-validation, domain-pack, adoption, and release tooling
- tests for major modules and CLI paths

Planned or incomplete:

- real benchmark loaders for MMLU, GSM8K, BBH, TruthfulQA, and CausalAgentBench
- real model panels beyond mock, except an optional unconfigured Ollama runner class
- full empirical validation of psychometric methods
- real human validation at meaningful scale
- full 2PL/MIRT IRT estimation
- predictive validity and Goodhart/consequential validity diagnostics
- external contamination/web-scale provenance checks
- paper-ready empirical results

---

## 3. Repository Snapshot

- Dossier generated at: 2026-06-03T18:37:05+05:30
- Working directory: `/Users/saketmaganti/Projects/Valideval`
- Git status: not available. `git status --short --branch` and `git rev-parse HEAD` both returned `fatal: not a git repository`.
- Latest commit hash: unavailable because this checkout has no `.git` directory.
- Current git branch: unavailable because this checkout has no `.git` directory.
- Python command status: `python` is not available under current pyenv config. `python3` works.
- Python version used: Python 3.11.9
- OS/environment: macOS/Darwin 25.5.0 on arm64, host `Sakets-MacBook-Air.local`
- Package version: `valideval 0.1.0`
- Top-level `PROJECT_STATUS_FOR_REVIEW.md`: not present.
- Top-level `certificates/`: not present. Certificate artifacts are written under `results/toy_mcq/mock/`.
- Top-level `schemas/`: not present. JSON schemas are under `docs/schemas/`.

Top-level repository tree observed:

```text
.
├── .github/
├── AGENTS.md
├── CHANGELOG.md
├── CITATION.cff
├── CONTRIBUTING.md
├── LICENSE
├── Makefile
├── README.md
├── bundles/
├── cache/
├── configs/
├── dashboard_data/
├── demo/
├── docs/
├── environment.json
├── examples/
├── leaderboard/
├── paper/
├── pyproject.toml
├── registry/
├── reportcards/
├── results/
├── site/
├── src/
└── tests/
```

Important directories:

- `src/valideval/`: package source, including benchmarks, models, scoring, diagnostics, psychometrics, forensics, repair, leaderboard, human validation, domain packs, adoption tooling, release tooling, and CLI.
- `tests/`: 20 test files covering schemas, CLI smoke paths, toy benchmark, response matrices, baselines, diagnostics, psychometrics, forensics, repair, report cards, leaderboard, human validation, domain packs, adoption, and release tooling.
- `configs/`: default config, diagnostic configs, placeholder real benchmark configs, and mock panel config.
- `examples/`: toy benchmark JSONL, toy corpus, toy human annotations, domain-pack sample JSONL files.
- `cache/`: cached toy mock predictions and response matrices for 22 prompt variants.
- `results/`: toy diagnostic outputs and generated audit artifacts.
- `reportcards/`: generated toy Markdown report card and manifest/reviewer-risk JSON.
- `bundles/`: generated toy reproducibility bundle.
- `site/`: generated static dashboard HTML/JSON.
- `paper/`: LaTeX scaffold, claims ledger, generated SVG figures, and generated LaTeX tables.
- `docs/`: theory, guides, protocols, schemas, engineering notes, and example report.
- `registry/` and `leaderboard/`: audit registry and benchmark atlas artifacts.

---

## 4. Implemented Features

| Feature Area | Implemented? | Location | Evidence | Notes |
|---|---:|---|---|---|
| package structure | Yes | `src/valideval/`, `pyproject.toml` | Editable install passed with `python3 -m pip install -e ".[dev]"` | Clear modular package layout. |
| CLI | Yes | `src/valideval/cli.py` | `python3 -m valideval --help` lists 39 top-level/subcommand groups | Broad CLI exists. `python` alias unavailable in this environment. |
| toy benchmark | Yes | `src/valideval/benchmarks/toy.py` | `python3 -m valideval toy` reports 36 items, 22 variants | Synthetic only. |
| benchmark loaders | Partial | `benchmarks/base.py`, `local_jsonl.py`, `hf_loader.py` | `local_jsonl` exists; known real benchmark IDs route to `UnavailableBenchmark` | Real benchmark loaders are placeholders. |
| mock model panel | Yes | `models/mock.py`, `models/panel.py` | `load_panel("mock")`; matrices command writes 22 matrices | Deterministic eight-model mock panel. |
| model runner interfaces | Partial | `models/base.py`, `models/ollama_client.py` | Optional Ollama class exists | CLI panel loader only exposes `mock`. |
| Ollama/local model support | Partial | `models/ollama_client.py` | Optional dependency extra `ollama`; runner class posts to local Ollama API | Not wired into `load_panel()` config; requires manual integration. |
| cached prediction matrices | Yes | `cache/toy_mcq/mock/` | `matrices` command wrote 22 matrices and prediction JSONL files | Offline deterministic cache. |
| response matrix builder | Yes | `io/cache.py`, `AuditRunner` | Tests and matrix command passed | CSV plus metadata JSON outputs. |
| shortcut diagnostics | Yes | `diagnostics/shortcut.py` | `results/toy_mcq/mock/shortcut.json` | Measures ablation retention, not proof of invalidity. |
| heuristic baselines | Yes | `baselines/heuristics.py`, `diagnostics/baselines.py` | `metadata_artifact_baseline` scored 0.972 on toy | Shallow artifact probes only. |
| answer distribution diagnostics | Yes | `diagnostics/answer_distribution.py` | Label counts and answer-length metrics generated | Static artifact screen. |
| distractor diagnostics | Yes | `diagnostics/distractors.py` | JSON plus `distractor_quality.csv` generated | Conditional on mock panel selections. |
| prompt sensitivity | Yes | `diagnostics/prompt_sensitivity.py` | 11 templates, 28 toy ranking flips | Prompt variants are toy adapter-specific. |
| extraction robustness | Yes | `diagnostics/extraction_robustness.py`, `scoring/extraction.py` | Strict/lenient shift 0.076 on toy | Requires raw cached outputs. |
| reliability diagnostics | Yes | `diagnostics/reliability.py` | Reliability estimate 0.427; seed retest unavailable warning | Perturbation reliability only for current variants. |
| IRT/psychometrics | Partial/Prototype | `diagnostics/irt.py`, `psychometrics/irt_models.py` | Proxy, Rasch/1PL path, 2PL proxy, bootstrap uncertainty generated | Not full validated IRT; outputs warn not ground truth. |
| DIF | Partial/Prototype | `diagnostics/dif.py` | 21 suspicious toy items under model groups | Model-family behavior, not human demographic fairness. |
| saturation | Yes/Prototype | `diagnostics/saturation.py` | Toy category `moderate` | Conditional on mock panel. |
| power analysis | Yes/Prototype | `diagnostics/power.py`, `psychometrics/power.py` | Effective item count 29, MDD 0.254 | Planning aid, not definitive inference. |
| calibration | Partial/Prototype | `diagnostics/calibration.py`, `psychometrics/calibration.py` | ECE 0.507 using prompt-consistency fallback | No logprobs/confidences in mock outputs. |
| abstention metrics | Partial/Prototype | `domains/diagnostics.py`, `psychometrics/calibration.py` | `abstention_validity.json` generated | Toy outputs mostly do not abstain; confidence validity unavailable. |
| contamination/forensics | Partial | `diagnostics/data_forensics.py`, `forensics/` | Local duplicate/provenance/temporal signals generated | External/web/closed training corpora not searched. |
| duplicate detection | Yes/Prototype | `forensics/duplicates.py`, `psychometrics/redundancy.py` | Duplicate fraction 0.278 in data forensics; redundancy fraction 0.194 | Lexical/template; semantic duplicates unavailable. |
| split leakage | Stub/Unavailable for toy | `forensics/split_leakage.py` | Data forensics reports split leakage unavailable | Needs split metadata. |
| temporal validity | Partial | `forensics/temporal.py` | One toy temporal warning; no web verification | Offline metadata/text only. |
| provenance | Partial | `forensics/provenance.py` | Manifest hashes, provenance completeness fields | Toy items missing many provenance fields. |
| item forensics | Yes/Prototype | `repair/engine.py` | `item_forensics.csv` generated | Used by repair and dashboard. |
| benchmark repair engine | Yes/Advisory | `repair/` | Conservative repair selected 12/36 toy items | Advisory only; not validated item repair. |
| validity cards | Yes | `repair/engine.py` | `validity_card.json` and `.md` generated | Evidence profile, not scalar score. |
| certificates | Yes/Prototype | `repair/engine.py` | Certificate level `Silver` generated | Profile certificate; top-level `certificates/` absent. |
| leaderboard/registry | Yes/Prototype | `leaderboard/`, `registry/` | Registry valid; audit list has one toy audit | Conditional ranking views, not true leaderboard. |
| dashboard/site | Yes | `leaderboard/site.py`, `site/` | `site build` generated 11 files | Static local site. |
| human validation | Partial/Protocol | `human/`, `examples/toy_human_annotations.csv` | 6 toy judgments imported; 3 tasks; agreement report generated | Far too small for real validation. |
| judge reliability | Partial/Protocol | `human/judges.py` | Deterministic judge report generated | No paid/remote LLM judge required; deterministic probes only. |
| domain packs | Partial | `domains/` | `domain list` shows 8 packs; RAG/abstention runnable | Agent/code/graph/medical/multimodal/safety are scaffolds with no diagnostics. |
| plugin architecture | Partial | `plugins.py` | Tests register a plugin; `plugins list` empty in repo state | Registry exists, no installed project plugins. |
| importers/integrations | Partial | `adoption/importers.py` | Tests cover generic CSV/JSONL importers | Not exercised against major external eval frameworks. |
| design assistant | Partial/Scaffold | `adoption/design.py` | Tests create design artifacts | Scaffold generator, not interactive research design validation. |
| preregistration generator | Partial/Scaffold | `adoption/preregistration.py` | Tests generate preregistration markdown | Template-level support. |
| paper scaffold | Partial | `paper/main.tex`, `paper/sections/` | `paper/sections/06_results.tex` is placeholder | Not paper-ready. |
| paper asset generation | Yes/Prototype | `release/paper_assets.py` | Supported command generated 10 figures and 10 tables | Some assets may be placeholders if inputs missing. |
| reviewer-risk mode | Yes/Prototype | `release/reviewer.py` | Flags 2 low risks in toy report | Static text scan only. |
| reproducibility bundles | Yes | `release/bundle.py` | Bundle built 65 files; verify passed | Good for toy artifacts. |
| tests | Yes | `tests/` | `pytest -q`: 78 passed | Meaningful synthetic coverage. |
| docs | Yes/Partial | `README.md`, `docs/`, `paper/CLAIMS_LEDGER.md` | Extensive docs present | Some docs are roadmap/protocol/scaffold rather than validated results. |

---

## 5. Stubbed, Partial, or Placeholder Features

| Feature | Current State | Why Incomplete | Risk | Recommended Next Step |
|---|---|---|---|---|
| MMLU loader | Placeholder config and unavailable adapter | No data loader/scorer | High for real benchmark claims | Implement local JSONL recipe or actual loader with scoring validation. |
| GSM8K loader | Placeholder config | Numeric answer extraction not implemented for real data | High | Add validated local export format and numeric extraction tests. |
| BBH loader | Placeholder config | Task templates/scoring missing | High | Start with one BBH task before claiming BBH support. |
| TruthfulQA loader | Placeholder config | Judge/scoring validation missing | High | Avoid until human/judge protocol is stronger. |
| CausalAgentBench loader | Placeholder config | Agent trace/data/scoring unavailable | High | Treat as roadmap only. |
| real model panels | Mock only in `load_panel()` | Optional Ollama runner is not panel-configured | High | Add local open-model panel config and skip gracefully when unavailable. |
| Ollama support | Runner class only | Not exposed through panel loader | Medium | Wire config-driven runners or document manual usage. |
| Predictive validity | Explicit status result only | Requires external criterion outcomes | High if overclaimed | Keep as "not estimated" until criterion dataset exists. |
| Goodhart/consequential validity | Explicit status result only | Requires longitudinal/deployment/intervention data | High if overclaimed | Keep out of empirical claims. |
| Full 2PL/MIRT IRT | Proxy only | No full parametric 2PL/MIRT estimation/validation | Medium/High | Validate against synthetic and real panels before paper claims. |
| Calibration | Uses prompt-consistency fallback | No confidence/logprob values in mock outputs | Medium | Add confidence-capable local runners or treat as fallback only. |
| Human validation | Toy protocol with 6 labels | Too few annotations and no full adjudication | High | Run real annotation protocol on real benchmark subset. |
| Krippendorff alpha | Scaffold marked deferred | Agreement report says `not_implemented` | Medium | Implement or remove from report until ready. |
| Semantic duplicate detection | Unavailable | Embedding path not configured | Medium | Optional offline embeddings or explicit lexical-only docs. |
| Split leakage | Unavailable on toy | Needs split metadata | Medium | Add split metadata in local JSONL examples. |
| External contamination | Local corpus only | No web/closed training corpora search | High | Keep local-only language; add optional corpus ingestion. |
| Domain packs beyond RAG/abstention | Scaffolds only | No diagnostics registered | Medium | Prioritize one domain and postpone rest. |
| Plugin ecosystem | Registry exists, empty | No actual packaged plugins | Low/Medium | Add one example plugin package. |
| Paper results section | Placeholder | No real experiment | High | Fill only after real benchmark audit. |
| `paper-assets --all` | Unsupported CLI syntax | Help exposes benchmark/panel args, not `--all` | Low | Either implement `--all` or update docs/prompts. |
| formatting | `ruff format --check` fails | 9 files would be reformatted | Low | Run `ruff format .` in a formatting-only change. |

---

## 6. CLI Command Audit

Commands discovered from `python3 -m valideval --help`:

```text
info, toy, matrices, audit, domain, schema, plugins, import-outputs,
quickstart-audit, init-benchmark, validate-benchmark, generate-card,
design-assistant, preregister, advisor, paper-assets, bundle, verify-bundle,
reviewer-risk, environment, baselines, diagnostics, psychometrics, report,
ranking, repair, card, certificate, checklist, evidence-matrix, leaderboard,
badges, registry, atlas, dashboard, site, audit-diff, forensics, human,
validate-config
```

| Command | Status | Output Artifact | Error/Notes |
|---|---|---|---|
| `python -m pip install -e ".[dev]"` | Failed | None | `python` command not found under pyenv. Environment issue; use `python3`. |
| `python -m valideval info` | Failed | None | Same `python` command-not-found issue. |
| `python -m valideval toy` | Failed | None | Same `python` command-not-found issue. |
| `python -m valideval --help` | Failed | None | Same `python` command-not-found issue. |
| `python3 -m pip install -e ".[dev]"` | Passed | Editable install | Installed `valideval 0.1.0`; dependencies already present. |
| `pytest -q` | Passed | Test output | 78 passed in 7.05s. |
| `ruff check .` | Passed | Lint output | All checks passed. |
| `ruff format --check .` | Failed | None | 9 files would be reformatted. Not changed during dossier task. |
| `python3 -m valideval --help` | Passed | CLI command list | Listed CLI surface above. |
| `python3 -m valideval info` | Passed | Console output | Reports `valideval 0.1.0`, toy benchmark, mock panel. |
| `python3 -m valideval toy` | Passed | Console preview | Reports 36 items and 22 prompt variants. |
| `python3 -m valideval matrices --benchmark toy_mcq --panel mock` | Passed | `cache/toy_mcq/mock/*` | Wrote 22 response matrices and prediction caches. |
| `python3 -m valideval audit --benchmark toy_mcq --diagnostics all-core` | Passed | `results/toy_mcq/mock/*.json`, manifest | Wrote 11 all-core diagnostic result files. |
| `python3 -m valideval psychometrics all --benchmark toy_mcq --panel mock` | Passed | `irt`, `saturation`, `power`, `dif`, `calibration`, `redundancy`, `ranking_uncertainty` JSON | Advanced toy psychometric outputs generated. |
| `python3 -m valideval report --benchmark toy_mcq --panel mock` | Passed | `reportcards/toy_mcq_mock.md` and manifest | Report card rendered. |
| `python3 -m valideval certificate issue --benchmark toy_mcq --panel mock` | Passed | `results/toy_mcq/mock/validity_certificate.*` | Certificate profile level is Silver. |
| `python3 -m valideval bundle --benchmark toy_mcq --panel mock` | Passed | `bundles/toy_mcq_mock_bundle/` | 65-file bundle, no missing expected artifacts. |
| `python3 -m valideval verify-bundle bundles/toy_mcq_mock_bundle` | Passed after clean rerun | Bundle verification output | A first parallel check failed because the bundle was being rebuilt concurrently; sequential rerun passed with 65 files checked. |
| `python3 -m valideval reviewer-risk --report reportcards/toy_mcq_mock.md` | Passed | `reportcards/toy_mcq_mock.reviewer_risk.json` | 2 low risks: missing preregistration and multiple-comparison discussion. |
| `python3 -m valideval site build` | Passed | `site/*.html`, `site/*.json` | Static site generated. |
| `python3 -m valideval paper-assets --all` | Failed | None | CLI does not recognize `--all`. Likely docs/prompt mismatch. |
| `python3 -m valideval paper-assets --benchmark toy_mcq --panel mock` | Passed | `paper/assets_manifest.json`, figures, tables | Supported syntax generated 10 figures and 10 tables. |
| `python3 -m valideval repair --benchmark toy_mcq --panel mock --policy conservative` | Passed | `item_forensics.csv`, `repair_report.md`, `repair_diff.json` | Advisory repair selected 12/36 toy items. |
| `python3 -m valideval card render --benchmark toy_mcq --panel mock` | Passed | `validity_card.json`, `validity_card.md` | Validity card generated. |
| `python3 -m valideval checklist --benchmark toy_mcq --panel mock` | Passed | `author_checklist.json`, `.md` | Benchmark-author checklist generated. |
| `python3 -m valideval evidence-matrix --benchmark toy_mcq --panel mock` | Passed | claim-evidence matrix JSON/CSV/MD | Generated. |
| `python3 -m valideval leaderboard --benchmark toy_mcq --panel mock` | Passed | ranking views, significance, registry/dashboard/atlas exports | Generated 10 ranking views, 11 flip comparisons, 7 badges. |
| `python3 -m valideval badges --benchmark toy_mcq --panel mock` | Passed | `health_badges.json` | Warns badges are not total validity score. |
| `python3 -m valideval atlas --benchmark toy_mcq --panel mock` | Passed | `leaderboard/benchmark_atlas.*` | Generated. |
| `python3 -m valideval dashboard export --benchmark toy_mcq --panel mock` | Passed | `dashboard_data/*` | Generated dashboard exports. |
| `python3 -m valideval registry validate` | Passed | registry validation output | 1 audit, 1 benchmark, 15 diagnostics, 1 panel; no errors. |
| `python3 -m valideval registry list` | Passed | registry JSON output | Lists one toy audit. |
| `python3 -m valideval domain list` | Passed | domain pack JSON | 8 packs listed; only RAG/abstention have diagnostics. |
| `python3 -m valideval domain describe rag` | Passed | RAG domain JSON | Shows RAG threats, diagnostics, and repair policy. |
| `python3 -m valideval audit --benchmark toy_mcq --panel mock --domain rag` | Passed | `rag_validity.json`, `abstention_validity.json` | RAG/abstention domain diagnostics generated. |
| `python3 -m valideval audit --benchmark toy_mcq --panel mock --domain abstention` | Passed | `abstention_validity.json` | Abstention domain diagnostic generated. |
| `python3 -m valideval plugins list` | Passed | empty plugin lists | Plugin architecture exists but no project plugins registered. |
| `python3 -m valideval forensics overlap --benchmark toy_mcq --corpus examples/toy_corpus/` | Passed | `results/toy_mcq/forensics_overlap.json` | 1 local document searched; one suspicious toy item. |
| `python3 -m valideval schema export all --output docs/schemas` | Passed | `docs/schemas/*.schema.json` | Exported 8 schemas. |
| `python3 -m valideval validate-config configs/default.yaml` | Passed | Console output | Loaded expected config keys. |
| `python3 -m valideval environment --output environment.json` | Passed | `environment.json` | Captured local environment metadata. |
| `python3 -m valideval human packet --benchmark toy_mcq --panel mock --sample-size 288` | Passed | `results/toy_mcq/mock/human/*` | 288 toy annotation tasks. |
| `python3 -m valideval human import --benchmark toy_mcq --panel mock --path examples/toy_human_annotations.csv` | Passed | `human_judgments.jsonl`, import report | 6 judgments imported, 0 errors. |
| `python3 -m valideval human agreement --benchmark toy_mcq --panel mock` | Passed | `agreement_report.json` | 3 tasks, 6 judgments, raw agreement 0.667. |
| `python3 -m valideval human judge --benchmark toy_mcq --panel mock` | Passed | `judge_reliability.json`, predictions JSONL | Deterministic judge variants only. |
| `python3 -m valideval human ambiguity --benchmark toy_mcq --panel mock` | Passed | scoring ambiguity JSON/CSV | 64/288 tasks flagged. |
| `python3 -m valideval human adjudication --benchmark toy_mcq --panel mock` | Passed | adjudication queue JSON/JSONL | 64 queue items. |
| `python3 -m valideval human ui --benchmark toy_mcq --panel mock` | Passed | static annotation viewer HTML | Viewer generated. |

---

## 7. Test and Lint Results

Exact test command run:

```bash
pytest -q
```

Result:

```text
78 passed in 7.05s
```

- Tests passed: 78
- Tests failed: 0
- Skipped tests: 0 reported
- Failing test names: none
- Failure summaries: none

Lint command:

```bash
ruff check .
```

Result:

```text
All checks passed!
```

Formatting check:

```bash
ruff format --check .
```

Result: failed. Ruff reported 9 files would be reformatted:

```text
src/valideval/adoption/__init__.py
src/valideval/adoption/importers.py
src/valideval/adoption/schemas.py
src/valideval/adoption/toolkit.py
src/valideval/plugins.py
src/valideval/release/__init__.py
src/valideval/release/bundle.py
src/valideval/release/paper_assets.py
src/valideval/release/reviewer.py
```

No formatting changes were applied because this task was to create a dossier, not to churn unrelated code.

---

## 8. Generated Artifacts

| Artifact | Path | Generated Successfully? | Notes |
|---|---|---:|---|
| prediction caches | `cache/toy_mcq/mock/predictions_*.jsonl` | Yes | 22 prompt variants. |
| response matrices | `cache/toy_mcq/mock/matrix_*.csv` | Yes | 22 prompt variants plus metadata JSON. |
| audit manifest | `results/toy_mcq/manifest.json` | Yes | Rewritten by audit commands. |
| shortcut diagnostic | `results/toy_mcq/mock/shortcut.json` | Yes | All-core audit. |
| baselines diagnostic | `results/toy_mcq/mock/baselines.json` | Yes | All-core audit. |
| answer distribution | `results/toy_mcq/mock/answer_distribution.json` | Yes | All-core audit. |
| distractor diagnostic | `results/toy_mcq/mock/distractor_quality.json` | Yes | All-core audit. |
| distractor CSV | `results/toy_mcq/mock/distractor_quality.csv` | Yes | Item/distractor table. |
| prompt sensitivity | `results/toy_mcq/mock/prompt_sensitivity.json` | Yes | All-core audit. |
| extraction robustness | `results/toy_mcq/mock/extraction_robustness.json` | Yes | All-core audit. |
| data forensics | `results/toy_mcq/mock/data_forensics.json` | Yes | Local-only signals. |
| IRT | `results/toy_mcq/mock/irt.json` | Yes | Proxy/Rasch/2PL-proxy toy outputs. |
| reliability | `results/toy_mcq/mock/reliability.json` | Yes | Perturbation reliability. |
| saturation | `results/toy_mcq/mock/saturation.json` | Yes | Advanced psychometrics. |
| power | `results/toy_mcq/mock/power.json` | Yes | Advanced psychometrics. |
| DIF | `results/toy_mcq/mock/dif.json` | Yes | Model-group residual diagnostic. |
| calibration | `results/toy_mcq/mock/calibration.json` | Yes | Uses prompt-consistency fallback. |
| redundancy | `results/toy_mcq/mock/redundancy.json` | Yes | Lexical/template redundancy. |
| ranking uncertainty | `results/toy_mcq/mock/ranking_uncertainty.json` | Yes | Bootstrap rank output. |
| RAG validity | `results/toy_mcq/mock/rag_validity.json` | Yes | Toy/domain metadata and perturbation signals. |
| abstention validity | `results/toy_mcq/mock/abstention_validity.json` | Yes | Toy abstention/proxy uncertainty signals. |
| local overlap forensics | `results/toy_mcq/forensics_overlap.json` | Yes | Used `examples/toy_corpus/`. |
| item forensics | `results/toy_mcq/mock/item_forensics.csv` | Yes | Repair/leaderboard input. |
| repair report | `results/toy_mcq/mock/repair_report.md` | Yes | Advisory only. |
| repair diff | `results/toy_mcq/mock/repair_diff.json` | Yes | Conservative repair selected 12 items. |
| validity card | `results/toy_mcq/mock/validity_card.json`, `.md` | Yes | Evidence profile. |
| certificate | `results/toy_mcq/mock/validity_certificate.json`, `.md` | Yes | Profile level Silver. |
| checklist | `results/toy_mcq/mock/author_checklist.json`, `.md` | Yes | Benchmark-author checklist. |
| claim evidence matrix | `results/toy_mcq/mock/claim_evidence_matrix.*` | Yes | JSON/CSV/MD. |
| ranking views | `results/toy_mcq/mock/ranking_views.json`, `.csv` | Yes | Leaderboard command. |
| ranking flips | `results/toy_mcq/mock/ranking_flips.json` | Yes | Leaderboard command. |
| ranking significance | `results/toy_mcq/mock/ranking_significance.json` | Yes | Leaderboard command. |
| health badges | `results/toy_mcq/mock/health_badges.json` | Yes | Per-dimension badges, not total score. |
| report card | `reportcards/toy_mcq_mock.md` | Yes | Markdown report. |
| report manifest | `reportcards/toy_mcq_mock.manifest.json` | Yes | Report provenance. |
| reviewer risk | `reportcards/toy_mcq_mock.reviewer_risk.json` | Yes | 2 low risks. |
| human packet | `results/toy_mcq/mock/human/packet.json`, `items.jsonl`, rubric/guidelines | Yes | 288 toy tasks. |
| human labels import | `results/toy_mcq/mock/human/human_judgments.jsonl` | Yes | 6 toy judgments. |
| human agreement | `results/toy_mcq/mock/human/agreement_report.json` | Yes | Tiny toy report. |
| judge reliability | `results/toy_mcq/mock/human/judge_reliability.json` | Yes | Deterministic judge variants. |
| scoring ambiguity | `results/toy_mcq/mock/human/scoring_ambiguity.*` | Yes | 64 toy tasks flagged. |
| adjudication queue | `results/toy_mcq/mock/human/adjudication_queue.*` | Yes | 64 queue items. |
| static annotation viewer | `results/toy_mcq/mock/human/annotation_viewer.html` | Yes | Local static viewer. |
| leaderboard atlas | `leaderboard/benchmark_atlas.json`, `.md` | Yes | Toy atlas. |
| dashboard data | `dashboard_data/*` | Yes | JSON/CSV exports. |
| static site | `site/*.html`, `site/*.json`, `site/assets/style.css` | Yes | Site build command. |
| paper assets | `paper/assets_manifest.json`, `paper/figures/*.svg`, `paper/tables/*.tex` | Yes | Supported command. |
| reproducibility bundle | `bundles/toy_mcq_mock_bundle/` | Yes | 65 files, verification passed. |
| environment capture | `environment.json`, bundle environment JSON | Yes | Captures no-git status. |
| exported schemas | `docs/schemas/*.schema.json` | Yes | 8 schemas. |

---

## 9. Current Diagnostics and What They Actually Measure

### `baselines`

- Measures: performance of shallow deterministic baselines such as majority label, answer-length heuristic, lexical overlap, metadata artifact prior, and arithmetic regex.
- Inputs: benchmark items; optionally full response matrix for model comparison.
- Outputs: baseline scores, best shallow baseline, best strong-model score, Dumb Baseline Gap, per-item baseline predictions.
- Supports claims: evidence consistent with possible shallow artifacts when baselines perform well.
- Does not support claims: proof that a benchmark is invalid, or that real models use the same shortcut.
- Limitations: intentionally shallow and deterministic.

### `answer_distribution`

- Measures: answer-label imbalance, answer-length artifacts, repeated phrases, negation cues, all/none options, token artifacts.
- Inputs: benchmark item metadata and choices.
- Outputs: label counts, imbalance metrics, answer length bias, token artifact summaries, per-item flags.
- Supports claims: potential static answer-format artifacts.
- Does not support claims: actual model exploitation of those artifacts.
- Limitations: static item analysis only.

### `distractor_quality`

- Measures: dead distractors, confusing distractors, lexical similarity to correct answers, selection counts.
- Inputs: benchmark choices, cached full predictions, response matrix.
- Outputs: JSON metrics and distractor CSV.
- Supports claims: evidence consistent with implausible or confusing distractors under the audited panel.
- Does not support claims: general item invalidity without human review.
- Limitations: conditional on model panel and prompt.

### `shortcut`

- Measures: retained performance under ablated prompt variants such as question-only, choices-only, context-removed, label-prior-only, metadata-only, and irrelevant context.
- Inputs: full and ablation response matrices.
- Outputs: full score, per-variant retention/drop, high-retention variants, per-model and per-item metrics, bootstrap CIs.
- Supports claims: evidence consistent with shortcut availability under specific ablations.
- Does not support claims: proof of contamination or global invalidity.
- Limitations: depends on quality and construct relevance of prompt variants.

### `prompt_sensitivity`

- Measures: score/rank changes across prompt templates.
- Inputs: full matrix and prompt-template matrices.
- Outputs: robustness coefficient, rank flips, extraction-failure rates, per-model variance.
- Supports claims: evidence consistent with prompt-format sensitivity.
- Does not support claims: that one prompt format is the correct benchmark.
- Limitations: templates are adapter-specific.

### `extraction_robustness`

- Measures: strict-vs-lenient-vs-regex extraction effects, invalid outputs, refusals, ambiguous item flags.
- Inputs: cached raw outputs/predictions and benchmark answers.
- Outputs: strict/lenient/regex scores, score shift, invalid/refusal rates, per-model/per-item metrics.
- Supports claims: scoring/extraction rule sensitivity.
- Does not support claims: definitive human scoring validity.
- Limitations: implemented extractors only.

### `data_forensics`

- Measures: local corpus overlap when supplied, internal duplicates, split leakage where metadata exists, temporal validity warnings, provenance completeness, manifest hashes.
- Inputs: benchmark items, optional corpus path, metadata.
- Outputs: signals with status/risk/metrics, warnings, hashes.
- Supports claims: local corpus-dependent evidence about provenance and contamination risk.
- Does not support claims: proof of contamination, proof of cleanliness, or web-scale coverage.
- Limitations: local/offline only in current workflow.

### `contamination`

- Measures: internal duplicates and optional external local corpus overlap.
- Inputs: benchmark items and optional corpus path.
- Outputs: duplicate rate, exact/question overlap rates, per-item duplicate/overlap flags.
- Supports claims: local evidence consistent with duplicate/overlap risk.
- Does not support claims: contamination proof or no-contamination proof.
- Limitations: corpus-dependent, not in all-core default.

### `coverage`

- Measures: construct tag distribution and missing expected tags.
- Inputs: benchmark tags and configured expected tags.
- Outputs: item count, tag entropy, tag distribution, missing tags.
- Supports claims: metadata-level content coverage screen.
- Does not support claims: full content validity without expert/human review.
- Limitations: tag quality is subjective and not independently validated.

### `reliability`

- Measures: perturbation reliability across available prompt variants, rank correlations, item stability, model variance.
- Inputs: full and variant matrices.
- Outputs: benchmark reliability estimate, perturbation sensitivity, per-variant metrics, per-model variance.
- Supports claims: evidence about stability across cached prompt perturbations.
- Does not support claims: seed/test-retest or scorer reliability unless those matrices exist.
- Limitations: current toy run warns that seed/test-retest reliability was not estimated.

### `irt`

- Measures: proxy item difficulty/discrimination, raw-vs-latent ability proxy rankings, Rasch/1PL fit if feasible, 2PL slope proxies, bootstrap uncertainty, tag skill profiles, subset recommendations.
- Inputs: response matrix and construct tags.
- Outputs: per-item stats, model ability proxies, recommended subsets, warnings.
- Supports claims: evidence consistent with low/negative discrimination under the audited panel.
- Does not support claims: ground-truth latent traits or definitive psychometric calibration.
- Limitations: proxy-heavy; full 2PL/MIRT not validated.

### `saturation`

- Measures: ceiling proximity, fraction solved by top models, discriminating item count, compression, tag-level saturation.
- Inputs: full response matrix.
- Outputs: saturation category and per-item discrimination flags.
- Supports claims: evidence consistent with benchmark saturation under panel.
- Does not support claims: global saturation for all future models.
- Limitations: requires meaningful model panel and possibly historical snapshots.

### `power`

- Measures: effective item count, model standard errors, minimum detectable differences, required item counts.
- Inputs: response matrix and redundancy adjustment.
- Outputs: standard errors, pairwise intervals, "do not overinterpret within points".
- Supports claims: planning/uncertainty guidance.
- Does not support claims: definitive statistical inference in all settings.
- Limitations: simple independence assumptions after redundancy adjustment.

### `dif`

- Measures: model-group residual differences by item.
- Inputs: response matrix and model group metadata or defaults.
- Outputs: group scores, group advantages, suspicious items.
- Supports claims: model-family DIF-like behavior under this panel.
- Does not support claims: demographic fairness or human DIF.
- Limitations: needs meaningful groups and enough models per group.

### `calibration`

- Measures: expected calibration error, Brier, NLL, confidence-correctness, overconfidence on low-validity items, abstention summary.
- Inputs: predictions with confidence/logprob if available; otherwise prompt-consistency fallback.
- Outputs: calibration metrics by tag and abstention metrics.
- Supports claims: calibration proxy evidence if confidence is missing.
- Does not support claims: true probabilistic calibration without confidence/logprob.
- Limitations: mock outputs lack real confidence values.

### `redundancy`

- Measures: lexical/template duplicate clusters, repeated contexts, effective item count, cluster-weighted accuracy.
- Inputs: benchmark items and optional matrix.
- Outputs: redundancy fraction, redundant item count, clusters.
- Supports claims: evidence consistent with redundant items.
- Does not support claims: semantic duplicate completeness.
- Limitations: lexical/template only.

### `ranking_uncertainty`

- Measures: bootstrap rank distributions, top-k stability, pairwise beat probabilities.
- Inputs: response matrix.
- Outputs: rank distributions and rank uncertainty metrics.
- Supports claims: ranking instability under item resampling assumptions.
- Does not support claims: true ordering of models.
- Limitations: conditional on item set and bootstrap assumptions.

### `rag_validity`

- Measures: context removal/shuffling/distractor score shifts, support-span or lexical answer support, citation checks when metadata exists, unanswerable metadata, evidence position.
- Inputs: matrices and RAG-style item metadata/context.
- Outputs: domain signals and per-item RAG metrics.
- Supports claims: local RAG validity evidence under supplied context/metadata.
- Does not support claims: semantic faithfulness proof.
- Limitations: citation/unanswerable signals unavailable without metadata; lexical support is weak evidence.

### `abstention_validity`

- Measures: selective risk, coverage, refusal correctness, deferral utility, confidence validity correlation if metadata exists, prompt instability.
- Inputs: cached predictions and matrices.
- Outputs: abstention signals and per-item coverage/abstention counts.
- Supports claims: local refusal/coverage behavior under protocol.
- Does not support claims: deployment readiness.
- Limitations: confidence validity unavailable without confidence/logprob metadata.

### `predictive`

- Measures: none currently.
- Inputs required: external criterion outcome dataset.
- Outputs: status `requires_external_criterion`.
- Supports claims: only that predictive validity was not estimated.
- Limitations: stub/status diagnostic.

### `goodhart`

- Measures: none currently.
- Inputs required: longitudinal, deployment, or intervention data.
- Outputs: status `requires_longitudinal_or_intervention_data`.
- Supports claims: only that consequential validity was not estimated.
- Limitations: stub/status diagnostic.

---

## 10. Toy Benchmark Results

These are toy/demo results only. They are not scientific evidence about real benchmarks or real model capability.

The toy benchmark is a 36-item synthetic MCQ benchmark designed to exercise known validity threats:

- context-use items
- lexical shortcut items
- answer-prior artifacts
- deliberately ambiguous/low-discrimination items
- too-easy and too-hard items
- duplicate/near-duplicate items
- prompt/scoring sensitivity cases

Key toy results from the current run:

- Full mock-panel mean score under shortcut diagnostic: 0.424
- Best shallow baseline: `metadata_artifact_baseline`, score 0.972
- Best mock model score: 0.611
- Dumb Baseline Gap: -0.361, meaning the shallow metadata baseline outperformed the best mock model on this intentionally artifacted toy set.
- High shortcut-retention variants: `question_only`, `context_removed`, `context_shuffled`, `label_prior_only`, `irrelevant_context`
- Label counts: A=8, B=14, C=8, D=6
- Distractor dead fraction: 0.430
- Prompt robustness coefficient: 0.523, with 28 prompt-specific ranking flips
- Strict-vs-lenient extraction score shift: 0.076
- Reliability estimate: 0.427; seed/test-retest reliability not estimated
- IRT proxy: 4 negative-discrimination items, near-zero discrimination fraction 0.306, too-hard fraction 0.222
- Saturation category: moderate
- Power diagnostic: effective item count 29, do-not-overinterpret threshold about 25.43 percentage points
- DIF-like model-group suspicious item count: 21
- Calibration ECE: 0.507 using prompt-consistency fallback
- Redundancy fraction: 0.194
- Ranking top-k stability: 0.853
- Data forensics: internal duplicate signal high local evidence; provenance completeness 0.0 for required provenance fields; no external corpus in all-core data-forensics run
- Forensics overlap command with `examples/toy_corpus/`: 1 document searched, exact match rate 0.0, question match rate 0.0278, suspicious item `toy_001`
- Certificate profile level: Silver, with shortcut/item-quality/reliability/provenance threats still present

Important toy output paths:

- `reportcards/toy_mcq_mock.md`
- `results/toy_mcq/mock/shortcut.json`
- `results/toy_mcq/mock/baselines.json`
- `results/toy_mcq/mock/irt.json`
- `results/toy_mcq/mock/reliability.json`
- `results/toy_mcq/mock/data_forensics.json`
- `results/toy_mcq/mock/validity_card.md`
- `results/toy_mcq/mock/validity_certificate.md`
- `bundles/toy_mcq_mock_bundle/`

---

## 11. Real Benchmark Readiness

| Benchmark | Loader Ready? | Outputs Ready? | Diagnostics Applicable? | Expected Difficulty | Recommendation |
|---|---:|---:|---:|---|---|
| GSM8K | No | No | Partial if local JSONL and numeric scoring are added | Medium | Best first real target if numeric extraction is implemented carefully. |
| MMLU subset | No direct loader; local JSONL possible | No real outputs | Many MCQ diagnostics applicable | Low/Medium | Strong candidate for first real audit via local JSONL export. |
| TruthfulQA | No | No | Some diagnostics applicable, but judging/scoring hard | High | Delay until judge/human protocol is stronger. |
| BBH | No | No | Task-dependent | High | Start with one task only if prompt/scoring adapter is built. |
| HotpotQA/NQ-style QA | No | No | Some extraction/forensics/reliability diagnostics applicable | High | Needs open-ended scorer and local data recipe. |
| RAG faithfulness benchmark | No general loader | No | RAG/abstention domain pack partially applicable | Medium/High | Good future target if local RAG item schema includes support spans/citations. |
| CausalAgentBench | No | No | Mostly not ready | High | Keep as roadmap. |
| agent/tool benchmark | No | No | Agent domain pack is scaffold only | High | Not ready. |
| code benchmark | No | No | Code domain pack is scaffold only | High | Not ready. |
| safety benchmark | No | No | Safety domain pack is scaffold only; abstention may help | High | Delay until policy/judge/versioning protocol exists. |

Bottom line: the repo is ready to run toy audits and local JSONL smoke audits. It is not yet ready to make real benchmark claims without implementing or supplying a validated local benchmark export, scoring adapter, and model outputs.

---

## 12. Engineering Quality Assessment

- Code organization: strong for a prototype. Modules are separated by responsibility: benchmarks, models, scoring, diagnostics, psychometrics, forensics, repair, leaderboard, human, domains, adoption, release, audit, report.
- Modularity: good. Diagnostics share `DiagnosticResult`; benchmark/model abstractions exist; CLI routes through `AuditRunner`.
- Schema quality: good. Pydantic models exist for benchmark items, predictions, matrices, diagnostics, report manifests, and human artifacts. JSON schemas can be exported.
- Config quality: adequate. Default and per-diagnostic configs exist. Real benchmark configs honestly state placeholder/scaffold status.
- Caching/provenance: good for toy. Predictions/matrices are cached; manifests and hashes are generated.
- Dependency management: good. Core dependencies are modest and offline-safe. Optional extras exist for datasets, parquet, Ollama.
- Test coverage: good for synthetic/unit coverage. 78 tests passed and cover many modules. Missing real integration tests.
- Failure handling: generally good. Placeholder benchmarks raise clear errors; predictive/Goodhart status diagnostics avoid fake estimates.
- Documentation quality: strong for prototype. README, docs, protocols, guides, self-review, claims ledger, and report cards are present.
- Reproducibility quality: strong for toy. Bundle, environment capture, manifests, and cached matrices work. No `.git` metadata in this checkout reduces provenance.
- Formatting: minor issue. `ruff check` passes, but `ruff format --check` reports 9 files would be reformatted.

---

## 13. Scientific and Statistical Quality Assessment

- IRT implementation: acceptable prototype. Proxy, Rasch/1PL optimization, 2PL slope proxy, bootstrap uncertainty, and subset recommendations exist. Risky if described as definitive IRT or psychometric calibration.
- Reliability statistics: acceptable prototype. Perturbation reliability and rank correlation are useful; seed/test-retest and scorer reliability are not fully covered by current matrices.
- Bootstrap/confidence intervals: useful but simple. Bootstrap CIs appear in shortcut, IRT uncertainty, ranking uncertainty, and power-related outputs. Assumptions should be disclosed.
- Ranking uncertainty: acceptable prototype. Bootstrap rank distributions and pairwise probabilities exist. Must not be described as true ranking uncertainty in a population sense.
- Power analysis: acceptable planning aid. Effective item count and MDD are useful; independence assumptions and redundancy adjustment are simple.
- Saturation metrics: credible as a panel-conditional screen. Needs stronger real panels and historical snapshots for serious claims.
- DIF/model-group analysis: prototype. Useful for model-family residual differences; not human demographic DIF.
- Calibration: weak/proxy in current toy run because no confidence/logprob values exist. Prompt-consistency fallback is not true calibration.
- Judge reliability: protocol prototype. Deterministic judges are useful for scoring sensitivity, not a substitute for human adjudication or LLM-judge validation.
- Contamination evidence: local/offline only. Duplicate/provenance checks are useful; no external training-data or web-scale claims are supported.

Classification:

- Credible now: offline toy pipeline, schema/caching/report generation, static artifact screens, local duplicate/provenance signals, deterministic tests.
- Acceptable prototype: shortcut ablations, prompt sensitivity, reliability, IRT proxy/Rasch fallback, saturation, power, ranking uncertainty, repair recommendations.
- Needs validation: DIF, calibration, human/judge reliability, RAG/abstention domain diagnostics, validity certificates, validity-adjusted ranking views.
- Risky/misleading if overclaimed: certificates, IRT ability estimates, contamination results, repaired subsets, rank views, predictive/Goodhart stubs.

---

## 14. Overclaiming and Validity Risks

Potential overclaiming/risk locations:

| Location | Risk | Recommended Wording Fix |
|---|---|---|
| `README.md` "What Works Now" | The list is long and may make scaffold/prototype features sound mature. | Add labels such as "prototype", "toy-only", "scaffold", or "requires local data" beside advanced features. |
| `README.md` "Paper/release tooling" | Paper tooling can sound paper-ready. | Say "paper scaffold and toy-result asset generator; no real empirical paper results yet." |
| `validity_certificate.md` | "Silver" may be read as certification of benchmark validity. | Keep prominent wording that certificate is an evidence profile, not a validity score or approval. |
| leaderboard/ranking views | "validity-adjusted ranking" can sound like corrected true ranking. | Use "conditional ranking view under stated assumptions." |
| IRT outputs | `latent_ability_proxy` can sound like real latent ability. | Keep "proxy" in all labels and paper text. |
| contamination/forensics | Local duplicate/overlap could sound conclusive. | Continue saying "local evidence" and "absence of evidence is not cleanliness." |
| repair output | Repaired subset can sound superior benchmark. | State "advisory subset for author review; not replacement benchmark." |
| human validation report | 6 labels could sound like validation. | Label current toy labels as workflow fixture only. |
| RAG support span metrics | Lexical answer support can sound like faithfulness. | State that semantic faithfulness requires human/local verifier review. |
| `paper/figures` and `paper/tables` | Generated assets may be mistaken for real paper results. | Add captions marking toy/demo or placeholders until real experiments exist. |

Reviewer-risk mode on `reportcards/toy_mcq_mock.md` found no high-risk overclaim patterns, but flagged two low-severity missing disclosures:

- missing preregistration discussion
- missing multiple-comparison discussion

---

## 15. Paper Readiness

Current paper scaffold status:

- LaTeX skeleton exists under `paper/`.
- `paper/CLAIMS_LEDGER.md` is cautious and useful.
- `paper/sections/06_results.tex` is still a placeholder: `[TO BE FILLED AFTER RUNNING AUDIT]`.
- Generated figures and tables exist, but they are derived from toy local artifacts and may include placeholders.
- No real benchmark results are present.

Available real results: none found.

Missing empirical evidence:

- at least one real benchmark audit
- real model panel outputs
- validated scoring for real benchmark
- preregistered audit protocol
- human/item review on flagged items
- model-panel sensitivity
- comparison against existing benchmark-auditing/eval tools

Missing baselines:

- real shallow baselines on real benchmark
- random/majority/lexical/artifact baselines tailored to real benchmark
- existing eval harness comparison

Missing ablations:

- prompt variant sensitivity for real benchmark
- scorer/extractor sensitivity for real benchmark
- local vs model-panel differences
- item removal/repair sensitivity

Missing literature positioning:

- psychometrics in ML eval
- benchmark contamination/benchmark auditing tools
- data leakage and shortcut learning
- uncertainty in model rankings
- validity frameworks in educational measurement and AI evals

Best-fit venue right now: workshop/demo/tooling venue only, if framed as an offline prototype with a toy demonstration.

Best-fit venue after real experiments: benchmark/evaluation workshop, ML systems/eval track, or applied NLP/ML evaluation workshop. A main-conference paper would require real benchmark audits and stronger empirical validation.

```text
Paper readiness: 3/10
Reason: strong scaffold and toy artifacts, but no real benchmark results or validated empirical study.
```

---

## 16. Open-Source Adoption Readiness

- Installability: good with `python3 -m pip install -e ".[dev]"`; poor if user assumes `python` exists in this environment.
- Quickstart quality: good for toy workflow.
- Docs: extensive, though feature maturity labels should be clearer.
- Examples: toy MCQ, toy corpus, toy human annotations, domain-pack example JSONLs.
- Schema clarity: good; schemas can be exported.
- Plugin story: architecture exists; no actual plugins registered by default.
- Integration story: local JSONL and generic output importers exist; major benchmark/eval harness integrations are not validated.
- Dashboard/report usability: good for generated toy artifacts.
- Generated artifacts: many and reproducible for toy.
- Friction points: real benchmark configs are placeholders; `paper-assets --all` is unsupported; `python` alias may fail; formatting check fails; no `.git` metadata in checkout; no real panel besides mock.

```text
Adoption readiness: 6/10
Reason: a researcher can run and inspect the toy audit quickly, but serious use requires local data preparation, scoring adapters, and model-output integration.
```

---

## 17. Top Strengths

1. Clear central thesis: validity is not accuracy.
2. Offline deterministic toy audit requires no paid APIs, internet, or Ollama.
3. Broad, coherent CLI surface with many working toy commands.
4. Strong modular organization and typed schema layer.
5. Meaningful synthetic test suite: 78 tests passed.
6. Cautious docs and claims ledger explicitly discourage overclaiming.
7. Cached predictions and matrices make toy audits reproducible.
8. Report cards, validity cards, certificates, bundles, and static site are generated end to end.
9. Placeholder real benchmark loaders fail honestly instead of inventing results.
10. Release/reviewer-risk tooling is unusually useful for audit hygiene.

---

## 18. Top Weaknesses / Blockers

| Issue | Severity | Evidence | Fix |
| ----- | -------- | -------- | --- |
| No real benchmark results | Critical | Only toy outputs exist; real configs are `placeholder`/`scaffold_only` | Run first real benchmark audit. |
| Real benchmark loaders missing | Critical | `hf_loader.py` raises `NotImplementedError` for known real benchmarks | Implement one validated loader or local JSONL recipe. |
| Real model panels missing | Critical | `load_panel()` only accepts `mock` | Add local open-model panel support. |
| Toy metrics could be overread | High | Many generated artifacts look polished | Label every toy result as software validation. |
| IRT is proxy-heavy | High | Code says 2PL proxy and warns not ground truth | Validate or soften paper language. |
| Calibration lacks real confidence | High | Calibration warns prompt-consistency fallback used | Add confidence/logprob outputs or avoid calibration claims. |
| Human validation tiny | High | 6 judgments over 3 tasks | Run meaningful annotation study. |
| Predictive validity stub | High | Diagnostic returns `requires_external_criterion` | Do not include as implemented empirical feature. |
| Goodhart stub | High | Diagnostic returns `requires_longitudinal_or_intervention_data` | Do not include as implemented empirical feature. |
| External contamination not measured | High | Data forensics says web/remote corpora not searched | Keep local-only claims. |
| Domain packs mostly scaffolds | Medium/High | Only RAG/abstention have diagnostics | Reduce advertised surface or implement one domain deeply. |
| `paper/sections/06_results.tex` placeholder | High | File contains `[TO BE FILLED AFTER RUNNING AUDIT]` | Fill only after real run. |
| `paper-assets --all` fails | Medium | CLI unrecognized argument | Implement flag or correct docs/prompts. |
| `python` alias fails | Medium | pyenv command-not-found | Docs already say `python3`; keep using it. |
| Format check fails | Low/Medium | 9 files would reformat | Run `ruff format .` in separate cleanup. |
| Top-level `certificates/` absent | Low | Certificate artifacts under `results/` | Either document path or create top-level export if desired. |
| No git metadata | Medium | Not a git repository | External packet should include environment note; use real git checkout for release. |
| Plugin registry empty | Low | `plugins list` returns empty arrays | Add example plugin if plugin story matters. |
| Local JSONL benchmark limited | Medium | Only full prompt variant | Add perturbation support for local benchmarks. |
| Static site not visually verified here | Low | Command generated files only | Open/check site in browser before public demo. |

---

## 19. Recommended First Real Experiment

Chosen benchmark: MMLU subset via local JSONL export.

Why this is the best first target:

- It is MCQ, matching the strongest current scoring and diagnostic machinery.
- It avoids open-ended judge complexity.
- Shortcut, answer distribution, distractor, prompt sensitivity, reliability, IRT, DIF, saturation, power, redundancy, and ranking uncertainty are naturally applicable.
- The repo already has a placeholder MMLU config that honestly asks for a local export.

Required data:

- A small validated local JSONL export in `BenchmarkItem` schema.
- Start with 100-300 items from a small number of subjects.
- Include source/provenance fields where possible.
- Include construct tags such as subject/domain/difficulty/source.
- Include split/source metadata if split leakage is to be tested.

Required model panel:

- At least 5-8 local/open models or locally cached outputs from real models.
- Include model metadata sufficient for grouping if DIF-like analysis is used.
- No paid API should be required.

Diagnostics to run:

- `baselines`
- `answer_distribution`
- `distractor_quality`
- `shortcut` where local benchmark perturbations exist
- `prompt_sensitivity` if prompt variants are implemented
- `extraction_robustness`
- `data_forensics`
- `reliability`
- `irt`
- `saturation`
- `power`
- `dif`
- `redundancy`
- `ranking_uncertainty`

Exact command sequence possible today for a minimal local JSONL scaffold:

```bash
python3 -m pip install -e ".[dev]"
python3 -m valideval schema validate benchmark --path data/mmlu_subset/items.jsonl
python3 -m valideval import-outputs --input data/mmlu_subset/model_outputs.csv --output data/mmlu_subset/normalized_outputs.jsonl --adapter generic-csv --benchmark-id mmlu_subset
python3 -m valideval quickstart-audit --items data/mmlu_subset/items.jsonl --outputs data/mmlu_subset/normalized_outputs.jsonl --benchmark-card data/mmlu_subset/benchmark_card.md --output-dir real_audits/mmlu_subset
```

Exact full `AuditRunner` command sequence is not yet possible for MMLU by ID because `mmlu` loader is a placeholder. To make it possible, implement a local benchmark directory or adapter and then run:

```bash
python3 -m valideval audit path/to/mmlu_subset_benchmark --results-root results_real --cache-root cache_real
python3 -m valideval report --benchmark local_jsonl --panel mock --results-root results_real --cache-root cache_real
```

Expected artifacts:

- normalized local outputs
- validity card
- item forensics
- report card
- diagnostic JSON
- repair recommendations
- environment and reproduction commands

Success criteria:

- No invented or internet-dependent data.
- Scoring validated on a hand-checked subset.
- At least one diagnostic identifies actionable item or scoring concerns.
- Report explicitly states limitations and does not claim global validity/invalidity.

Interesting result:

- A shallow artifact baseline or prompt ablation retains unexpectedly high performance on certain subjects or item types.
- Low/negative discrimination clusters align with identifiable item patterns.
- Model rankings are unstable under item resampling or prompt variants.

Boring but useful result:

- Diagnostics find mostly low local risk, but the workflow produces a clean reproducible audit and clarifies what evidence is still missing.

---

## 20. Next Action Plan

### Next 24 hours

- Fix documentation/CLI mismatch for `paper-assets --all`.
- Run `ruff format .` in a formatting-only commit/change.
- Add a short `REAL_BENCHMARK_STATUS.md` or update README with explicit "toy-only results" and "real loaders placeholder" labels.
- Add a command note that certificate outputs live under `results/`, not top-level `certificates/`.

### Next 3 days

- Build a small local JSONL MMLU-subset fixture.
- Add a local real-output import example.
- Add tests for local JSONL audit limitations and unsupported perturbation diagnostics.
- Add provenance fields to example local benchmark items.

### Next 1 week

- Run first real empirical audit on a small MMLU subset.
- Add real local model outputs from at least 5 open/local models.
- Hand-review a sample of flagged items.
- Generate a real report card clearly labeled as preliminary.

### Next 1 month

- Expand to one additional benchmark, likely GSM8K if numeric extraction is validated.
- Add robust local model panel configuration.
- Validate IRT/power/ranking uncertainty against synthetic and real response matrices.
- Add paper results, limitations, and related-work positioning.
- Prepare a public artifact bundle with git metadata.

### Stop doing

- Stop expanding scaffold domain packs until one real benchmark audit is complete.
- Stop adding certificate/leaderboard polish before validating real use.
- Stop adding paper text beyond methods until real results exist.
- Stop implying broad benchmark support from placeholder configs.

---

## 21. External Reviewer Questions

1. Is the novelty sufficient over existing benchmark auditing/evaluation tools?
2. Which diagnostics are scientifically strongest today?
3. Which diagnostics are misleading unless delayed or reframed?
4. Should validity certificates be kept, renamed, or removed?
5. Is the psychometric framing accurate enough for AI benchmark auditing?
6. What first real benchmark would be most convincing?
7. What real result would make this publishable?
8. What result would be boring but still useful?
9. Is the engineering modular enough for outside researchers?
10. Are the report cards useful or too broad?
11. Should the paper focus on a toolkit, a protocol, or an empirical benchmark audit?
12. Does the project overclaim despite its disclaimers?
13. Which features should be cut before a public release?
14. What would Reviewer 2 attack first?
15. What minimum human validation protocol is needed?
16. Are the IRT and power methods acceptable as prototypes?
17. Are ranking views helpful or too easy to misuse?
18. How should domain packs be prioritized?
19. What integrations matter most for adoption?
20. Is "validity is not accuracy" framed in a publishable way?

---

## 22. Final Honest Status

- Current maturity level: prototype with a strong offline toy demo. Not paper-ready and not yet a serious real-benchmark research toolkit.
- Overall repo status rating: 6/10
- Research potential rating: 8/10
- Engineering maturity rating: 6.5/10
- First real benchmark readiness rating: 3.5/10
- Single most important next step: run one carefully scoped real MCQ benchmark audit from a validated local JSONL export with real local model outputs, then rewrite the paper/results around that evidence.

