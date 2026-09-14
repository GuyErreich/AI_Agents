# Ankyr

Portable [Cursor](https://cursor.com) plugins: skills, rules, subagents, and review-loop hooks. Project-specific overlay (Supabase, deploy secrets, `AGENT.md`) stays in each application repo.

Ankyr (from Greek *ankyra*, anchor, and *Ananke*, necessity) is the default when a project is silent. The project's `AGENT.md` chain, rules, and skills always win.

Plugins:

- [`plugins/ankyr`](plugins/ankyr) — core (engineering, hierarchy, quality, always-on floor rules)
- [`plugins/ankyr-review`](plugins/ankyr-review) — reviewer, PR resolver, improve-code, review loops, subagents, hooks
- [`plugins/ankyr-git`](plugins/ankyr-git) — worktree, commit, PR, push, release
- [`plugins/ankyr-authoring`](plugins/ankyr-authoring) — agent-hierarchy, improvement-protocol
- [`plugins/ankyr-python`](plugins/ankyr-python) — Python
- [`plugins/ankyr-node`](plugins/ankyr-node) — TypeScript / JavaScript
- [`plugins/ankyr-web`](plugins/ankyr-web) — UI, UX, React, Three.js

## Install in Cursor

### Local (this machine)

```bash
mkdir -p ~/.cursor/plugins/local
ln -sfn "$(pwd)/plugins/ankyr" ~/.cursor/plugins/local/ankyr
ln -sfn "$(pwd)/plugins/ankyr-review" ~/.cursor/plugins/local/ankyr-review
ln -sfn "$(pwd)/plugins/ankyr-git" ~/.cursor/plugins/local/ankyr-git
ln -sfn "$(pwd)/plugins/ankyr-authoring" ~/.cursor/plugins/local/ankyr-authoring
ln -sfn "$(pwd)/plugins/ankyr-python" ~/.cursor/plugins/local/ankyr-python
ln -sfn "$(pwd)/plugins/ankyr-node" ~/.cursor/plugins/local/ankyr-node
ln -sfn "$(pwd)/plugins/ankyr-web" ~/.cursor/plugins/local/ankyr-web
```

Reload the Cursor window. The plugins show up as **Ankyr**, **Ankyr Review**, **Ankyr Git**, **Ankyr Authoring**, **Ankyr Python**, **Ankyr Node**, and **Ankyr Web**.

### Team marketplace

1. Cursor **Dashboard → Settings → Plugins**
2. **Team Marketplaces → Import from Repo**
3. Paste `https://github.com/GuyErreich/AI_Agents`
4. Cursor's plugin loader clones **`main`** (it does not honor `/tree/staging` URLs). Production lives on `main`. GitHub's default branch stays **`dev`** for PRs and CD.
5. Enable **Auto Refresh** (requires the [Cursor GitHub App](https://cursor.com/docs/integrations/github) on this repo)

Cursor reads [`.cursor-plugin/marketplace.json`](.cursor-plugin/marketplace.json). Mark **Ankyr** required; mark topical and language plugins required or optional, then save.

### Public marketplace

Submit the repo at [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish). Updates are manually reviewed by Cursor; production tags on `main` are the publish surface (there is no upload package).

## Release channels

| Channel | Branch | Tags | Purpose |
|---|---|---|---|
| Dev | `dev` | `X.Y.Z-dev` | Integration |
| Staging | `staging` | `X.Y.Z-rc` | Team marketplace preview |
| Production | `main` | `X.Y.Z` | Public + stable team |

Versioning and promotion use [Action-Semver-Control](https://github.com/GuyErreich/Action-Semver-Control). See [docs/RELEASE.md](docs/RELEASE.md) for GitHub App secrets, environments, and the release gate.

## Layout

```
.cursor-plugin/marketplace.json   # GitHub / team import
plugins/ankyr/                    # core + floor rules (no hooks/agents)
plugins/ankyr-review/             # review skills, agents, hooks
plugins/ankyr-git/                # CI milestone skills
plugins/ankyr-authoring/          # agent-hierarchy + improvement-protocol
plugins/ankyr-python/             # Python skill + rule
plugins/ankyr-node/               # TypeScript/JavaScript skill + rule
plugins/ankyr-web/                # UI / UX / React / Three.js
```

## Consuming repos

Keep only the project overlay:

```
AGENT.md tree
.cursor/skills/project/**
.cursor/rules/project/**
scripts/review-lock.py            # optional
```

Do not copy portable plugin `skills/**` or `rules/ankyr/**` into app repos once these plugins are installed — they would load twice.

## Migration from `ai-agents`

This is a breaking rename of the old single plugin.

1. Disable **AI Agents** and remove `~/.cursor/plugins/local/ai-agents`.
2. Enable **Ankyr** (Required) plus topical plugins (`ankyr-review`, `ankyr-git`, `ankyr-authoring`) and the language plugins you need.
3. Skill invocations are prefixed: `/python` is now `/ankyr-python`, `/reviewer` is `/ankyr-reviewer`.
4. Project overlays under `.cursor/skills/project/**` are unchanged and still win.

## Validate (local)

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+:

```bash
uv sync --group dev
uv audit --frozen
uv run python scripts/sync_version.py --check
uv run python scripts/validate_plugin.py
uv run ruff check plugins/ankyr-review/hooks scripts
uv run ruff format --check scripts
uv run pytest
uv run python scripts/release_gate.py   # before promote / production tag
pre-commit run --all-files   # gitleaks, JSON/YAML, ruff
```

CI on `dev` / `staging` / `main` and pull requests runs Gitleaks, Ruff, pytest, plugin validation, `uv audit`, license headers, CodeQL, and Semgrep. Tag pushes run the full **release gate** before creating a GitHub Release.

## Inheritance

Standards resolve project-first: the `AGENT.md` chain, then project rules, then project skills, then the matching Ankyr skill if installed. The first source that speaks wins. Consent, review-gate, and security floors always apply (shipped in core).

Core's `ankyr-engineering` and `ankyr-hierarchy` skills are **defaults**, not authorities. Folder taxonomy lives in `skills/ankyr-hierarchy`. Agent-library container tiers live in the `ankyr-authoring` plugin's `skills/ankyr-agent-hierarchy`. `ankyr-improve-code` (in `ankyr-review`) routes non-diff improvement through the reviewer and `ankyr-ci-local-review-loop`. Skills must not hard-load each other; domain orderings are preferred-if-installed.
