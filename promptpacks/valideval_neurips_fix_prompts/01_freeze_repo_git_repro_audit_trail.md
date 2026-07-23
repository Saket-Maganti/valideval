# Prompt 01 — Freeze Features, Initialize Reproducibility, and Create Audit Trail

## Estimated working time / runtime

| Mode | Estimate |
|---|---:|
| Human/Codex working time | 45–90 min |
| CPU runtime | 1–3 min |
| GPU runtime | Not required |
| Expensive generation? | No |
| Run now or later? | Now |

## Purpose

Fixes the reproducibility/audit-trail criticism and freezes feature sprawl.

---

You are working inside the `valideval` repository.

## Global hard rules
- Do not add feature sprawl.
- Do not run expensive Ollama/LLM generation unless explicitly requested.
- Do not use paid or closed APIs.
- Do not expose raw GPQA text.
- Do not make real benchmark claims from toy/fixture/chance-level panels.
- Keep GPQA local-panel results labeled preliminary/protocol-only.
- Keep claims tied to evidence.

## Tasks
1. If not already a git repo, run `git init`.
2. Create/update `.gitignore`, `VERSION`, `CHANGELOG.md`, `RELEASE_NOTES.md`, `REPRODUCIBILITY_AUDIT_TRAIL.md`, `FEATURE_FREEZE.md`.
3. `.gitignore` must exclude runtime/large/private artifacts: `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.venv/`, `.env`, `.DS_Store`, `local_outputs/`, `cache/`, `logs/`, `large_raw_data/`, `*.sqlite`, `*.db`.
4. Do not ignore examples/configs/schemas/tests/docs/paper/reportcard markdown.
5. `FEATURE_FREEZE.md` must freeze domain packs, dashboards, badges, certificates, more GPQA micro-runs, and new diagnostics.
6. `REPRODUCIBILITY_AUDIT_TRAIL.md` must explain git-tracked vs manifest-hashed artifacts.
7. Run `python3 -m pytest -q` and `ruff check .`.

## Final response
Return summary, files changed, tests, frozen scope, and next prompt.
