# AGENTS.md - ValidEval Repository Instructions

## Project Identity

This repository builds `valideval`, a psychometric validity-auditing toolkit for AI benchmarks. The central thesis is: validity is not accuracy. A benchmark score should be audited for whether it measures the claimed construct rather than shortcuts, contamination, scoring artifacts, low-discrimination items, or saturation.

## Non-Negotiables

- Do not invent empirical results.
- Do not use paid APIs as required dependencies.
- Do not claim a benchmark is globally invalid from one diagnostic.
- Do not collapse validity into one scalar score.
- Treat validity as a multidimensional profile.
- Prefer offline-safe tests and deterministic mock models.
- Keep the toy demo runnable without internet or Ollama.
- Use cached response matrices whenever possible.
- Update docs whenever public behavior changes.

## Commands

- Install dev mode: `python3 -m pip install -e ".[dev]"`
- Run tests: `python3 -m pytest`
- Lint: `ruff check .`
- Format: `ruff format .`
- Toy demo: `python3 -m valideval toy`
- Generate mock matrices: `python3 -m valideval matrices --benchmark toy_mcq --panel mock`
- Run audit: `python3 -m valideval audit --benchmark toy_mcq --panel mock --diagnostics shortcut irt reliability`
- Render report: `python3 -m valideval report --benchmark toy_mcq --panel mock`

## Research Standards

Use cautious language:

- "Evidence consistent with..."
- "Potential validity threat..."
- "Requires validation..."
- "Under this diagnostic/protocol..."

Avoid:

- "Proves contamination"
- "Benchmark is worthless"
- "This is the true ranking"

## Done Means

Before ending a task:

1. Run relevant tests.
2. Update docs if behavior changed.
3. Summarize files changed.
4. List known blockers.
5. Provide the best next command or prompt.
