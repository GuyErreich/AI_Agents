# Release & CD setup

Cursor has no artifact registry. This repo’s CD produces a **trustworthy git ref**; marketplaces index that ref.

## Channels

| Channel | Branch / tag | Consumers |
|---|---|---|
| Dev | `dev`, tags `X.Y.Z-dev` | Internal iteration |
| Staging | `staging`, tags `X.Y.Z-rc` | Team marketplace |
| Production | `master`, tags `X.Y.Z` | Public marketplace + team (stable) |

Default branch stays **`master`**. Feature work merges to **`dev`**.

## One-time GitHub setup

### 1. Channel branches

```bash
git push -u origin dev staging
```

### 2. GitHub App secrets

Install the same GitHub App used by [Action-Semver-Control](https://github.com/GuyErreich/Action-Semver-Control) on this repository (`contents: write`, `pull-requests: write`).

Set repository secrets (never commit values):

```bash
gh secret set GH_APP_ID          --repo GuyErreich/AI_Agents
gh secret set GH_APP_PRIVATE_KEY --repo GuyErreich/AI_Agents
```

Verify:

```bash
gh secret list --repo GuyErreich/AI_Agents
```

### 3. Environments

Applied live (2026-08-28):

| Environment | Branch policy | Protection |
|---|---|---|
| `staging` | `staging` only | No required reviewers |
| `production` | `master` only | Required reviewer: `@GuyErreich` |

Re-apply or inspect:

```bash
gh api repos/GuyErreich/AI_Agents/environments
```

### 4. Branch rulesets

Two rulesets mirror [PersonalWebsite](https://github.com/GuyErreich/PersonalWebsite) with plugin-specific deviations:

**Standard Flow (dev, staging & master)** — on `dev`, `staging`, `master`:

- Deletion / non-fast-forward blocked
- **Required signed commits** (semver + sync workflows use verified API commits)
- Required checks: `Lint, test, plugin`, `Workflow lint`, `Gitleaks`, `SAST`, `Analyze Python`
- PR: 1 approval, code-owner review, last-push approval, thread resolution
- **Squash merge only** (rebase merges cannot be signed by GitHub)
- Copilot review, code quality, CodeQL scanning, **90% coverage** (via `actions/upload-code-coverage`)

**Linear history (dev only)** — squash-only integration on `dev`; omitted on `staging`/`master` because promotions are merge commits.

`release/**` is intentionally **not** covered so Action-Semver-Control can force-push release branches.

Re-apply:

```bash
uv run python scripts/bootstrap_github.py --rulesets-only
```

Dry-run first:

```bash
uv run python scripts/bootstrap_github.py --dry-run
```

### 5. Labels & CODEOWNERS

- `.github/CODEOWNERS` — `@GuyErreich` (required for code-owner review)
- `semver-bump` label — created by `.github/workflows/pr-labeler.yml`

### 6. Cursor marketplace

- **Team marketplace:** import this repo; track `staging` or `master`; enable Auto Refresh (Cursor GitHub App).
- **Public marketplace:** submit once at https://cursor.com/marketplace/publish — every update is manually reviewed. Production publish workflow opens a tracking issue on the first release and attaches a plugin tarball to the GitHub Release.

## Verified commits

| Workflow | Mechanism |
|---|---|
| `sync-version.yml` | GraphQL `createCommitOnBranch` via `actions/github-script` + App token |
| `auto-semver.yml` / `promote.yml` | `Action-Semver-Control` with `signed-commits: true` |

**Pin:** temporarily on [Action-Semver-Control#219](https://github.com/GuyErreich/Action-Semver-Control/pull/219) (`2f52db3…`). After merge and promotion to a production tag, re-pin `auto-semver.yml` and `promote.yml` to that tag SHA.

## Version sync

`Action-Semver-Control` updates `pyproject.toml` only. `scripts/sync_version.py` (via `sync-version.yml` on `release/**`) keeps:

- `plugins/ai-agents/.cursor-plugin/plugin.json`
- `.cursor-plugin/marketplace.json`

`validate_plugin.py` fails if those drift.

## Local validation

```bash
uv sync --group dev
uv run python scripts/release_gate.py
uv run python scripts/validate_plugin.py
uv run pytest
```

## Coverage baseline

CI uploads Cobertura XML via `actions/upload-code-coverage`. Land coverage on `master` before the ruleset’s `max_coverage_drop` rule can evaluate PRs. Measured surface omits CLI-only scripts (`hook_install_smoke.py`, `release_gate.py`) and thin hook entrypoints not exercised in unit tests.

## Public marketplace checklist

Production tag must be an ancestor of `master` (enforced by `publish-production.yml`). On first production release, a GitHub issue is opened with the submission URL and checklist.
