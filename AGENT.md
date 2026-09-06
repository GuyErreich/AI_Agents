# Workspace Agent Notes

This repository is the portable Cursor plugin (`ai-agents`). Consuming apps keep only a project overlay (`.cursor/skills/project/**`, `.cursor/rules/project/**`, `AGENT.md`).

## Validate

- Base branch for branch/PR diffs: `dev` (feature work). Production consumers track `master`; staging tracks `staging`.
- Plugin manifests: `uv run python scripts/validate_plugin.py` — must succeed.
- Version sync: `uv run python scripts/sync_version.py --check` — must succeed (JSONs match `pyproject.toml`; ASC bumps them via `version_files`).
- Lint: `uv run ruff check plugins/ai-agents/hooks scripts` — 0 errors required.
- Format: `uv run ruff format --check scripts` — must succeed.
- Tests: `uv run pytest` — must succeed.
- Dependency audit: `uv audit --frozen` — must succeed; remediate with `uv audit --upgrade` when appropriate, then re-check.
- Release gate (local): `uv run python scripts/release_gate.py` — must succeed before tagging / promote.
- Secrets: Gitleaks in CI (`secret-scan.yml`); locally `pre-commit run gitleaks --all-files`.

CI and milestone skills read these commands and the base branch from this block.

- Run the full Validate suite (plugin, lint, format, tests, dependency audit) at review / commit / PR milestones.
- Run the release gate at the release milestone (before promote to `master` / production tag).
- Record pass/fail from raw shell exit codes.

## Review scope

When reviewing, materialize the full surface: the tier diff (for PR/push prefer `merge-base...HEAD` against `dev` for feature work, or against `master` for production release PRs), plus this `AGENT.md`, plus the skills routed by the changed file types.
