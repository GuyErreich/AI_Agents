# Release & CD setup

Cursor has no artifact registry. This repo’s CD produces a **trustworthy git ref**; marketplaces index that ref.

## Channels

| Channel | Branch / tag | Consumers |
|---|---|---|
| Dev | `dev`, tags `X.Y.Z-dev` | Internal iteration |
| Staging | `staging`, tags `X.Y.Z-rc` | Team marketplace |
| Production | `master`, tags `X.Y.Z` | Public marketplace + team (stable) |

Default branch stays **`master`**. Feature work merges to **`dev`**.

## Checklist (one-time, outside this PR)

Complete these in GitHub / Cursor before the first real release:

1. **Push channel branches** (created locally as `dev` and `staging`):

```bash
git push -u origin dev staging
```

2. **GitHub App** with `contents: write` and `pull-requests: write`, installed on this repository.

3. Repository secrets:
   - `GH_APP_ID`
   - `GH_APP_PRIVATE_KEY`

4. **Environments** (Settings → Environments):
   - `staging` — optional reviewers
   - `production` — **required reviewer** before `publish-production.yml` creates the GitHub Release

5. **Branch protection** on `master` and `staging` (require PR + green CI). Keep `dev` as the integration branch.

6. **Label** `semver-bump` (used by release PRs from Action-Semver-Control).

7. **Cursor GitHub App** on this repo — required for team-marketplace **Auto Refresh** on push.

## Version sync caveat

`Action-Semver-Control` updates `pyproject.toml` only. `scripts/sync_version.py` (via `sync-version.yml` on `release/**`) keeps:

- `plugins/ai-agents/.cursor-plugin/plugin.json`
- `.cursor-plugin/marketplace.json`

`validate_plugin.py` fails if those drift.

## Public marketplace

Submit once at https://cursor.com/marketplace/publish. Every update is manually reviewed by Cursor — the production publish job prints a reminder; it does not upload a package.
