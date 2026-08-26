# Workspace Agent Notes

This repository is the portable Cursor plugin (`ai-agents`). Consuming apps keep only a project overlay (`.cursor/skills/project/**`, `.cursor/rules/project/**`, `AGENT.md`).

## Validate

- Base branch for branch/PR diffs: `master`.
- Plugin manifests: `uv run python scripts/validate_plugin.py` — must succeed.
- Lint: `uv run ruff check plugins/ai-agents/hooks scripts` — 0 errors required.
- Format: `uv run ruff format --check scripts` — must succeed.
- Tests: `uv run pytest` — must succeed.
- Secrets: Gitleaks in CI (`secret-scan.yml`); locally `pre-commit run gitleaks --all-files`.

CI and milestone skills read these commands and the base branch from this block.

- Run the full Validate suite (plugin, lint, format, tests) at review / commit / PR milestones.
- Record pass/fail from raw shell exit codes.

## Review scope

When reviewing, materialize the full surface: the tier diff (for PR/push prefer `merge-base...HEAD` against `master`), plus this `AGENT.md`, plus the skills routed by the changed file types.
