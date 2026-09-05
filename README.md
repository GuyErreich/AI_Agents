# AI Agents

Portable [Cursor](https://cursor.com) plugin: skills, rules, subagents, and review-loop hooks. Project-specific overlay (Supabase, deploy secrets, `AGENT.md`) stays in each application repo.

Plugin: [`plugins/ai-agents`](plugins/ai-agents)

## Install in Cursor

### Local (this machine)

```bash
mkdir -p ~/.cursor/plugins/local
ln -sfn "$(pwd)/plugins/ai-agents" ~/.cursor/plugins/local/ai-agents
```

Reload the Cursor window. The plugin shows up as **AI Agents**.

### Team marketplace

1. Cursor **Dashboard → Settings → Plugins**
2. **Team Marketplaces → Import from Repo**
3. Paste `https://github.com/GuyErreich/AI_Agents`
4. Track branch by channel:
   - **staging** — pre-release (`X.Y.Z-rc`)
   - **master** — production (`X.Y.Z`)
5. Enable **Auto Refresh** (requires the [Cursor GitHub App](https://cursor.com/docs/integrations/github) on this repo)

Cursor reads [`.cursor-plugin/marketplace.json`](.cursor-plugin/marketplace.json). Mark **AI Agents** required or optional, then save.

### Public marketplace

Submit the repo at [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish). Updates are manually reviewed by Cursor; production tags on `master` are the publish surface (there is no upload package).

## Release channels

| Channel | Branch | Tags | Purpose |
|---|---|---|---|
| Dev | `dev` | `X.Y.Z-dev` | Integration |
| Staging | `staging` | `X.Y.Z-rc` | Team marketplace preview |
| Production | `master` | `X.Y.Z` | Public + stable team |

Versioning and promotion use [Action-Semver-Control](https://github.com/GuyErreich/Action-Semver-Control). See [docs/RELEASE.md](docs/RELEASE.md) for GitHub App secrets, environments, and the release gate.

## Layout

```
.cursor-plugin/marketplace.json   # GitHub / team import
plugins/ai-agents/
  .cursor-plugin/plugin.json
  assets/logo.svg
  skills/                         # foundations, code, ai-agent
  rules/                          # glob + always-on pointers
  agents/                         # pr-reviewer, pr-fixer
  hooks/                          # review-loop + npm dep gate
```

## Consuming repos

Keep only the project overlay:

```
AGENT.md tree
.cursor/skills/project/**
.cursor/rules/project/**
scripts/review-lock.py            # optional
```

Do not copy portable `skills/code/**` or `rules/code/**` into app repos once this plugin is installed — they would load twice.

## Validate (local)

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+:

```bash
uv sync --group dev
uv audit --frozen
uv run python scripts/sync_version.py --check
uv run python scripts/validate_plugin.py
uv run ruff check plugins/ai-agents/hooks scripts
uv run ruff format --check scripts
uv run pytest
uv run python scripts/release_gate.py   # before promote / production tag
pre-commit run --all-files   # gitleaks, JSON/YAML, ruff
```

CI on `dev` / `staging` / `master` and pull requests runs Gitleaks, Ruff, pytest, plugin validation, `uv audit`, license headers, CodeQL, and Semgrep. Tag pushes run the full **release gate** before creating a GitHub Release.

## Inheritance

Every skill under `code/` extends `skills/code/foundations/engineering`. Folder taxonomy lives in `skills/foundations/hierarchy`. Agent-library container tiers live in `skills/ai-agent/hierarchy`. Project skills may add stricter rules, never weaker ones.
