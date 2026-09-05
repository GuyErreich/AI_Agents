---
name: ci-release
description: Release / promote workflow — run the release gate, then promote a staging tag to master or prepare a marketplace submission. Never publish without explicit consent. Extends engineering.
disable-model-invocation: true
---

# CI — Release

The milestone workflow for promoting a version toward production and preparing marketplace publish.

## Extends

Load `skills/code/foundations/engineering/SKILL.md` first.

## Consent

Never promote to `master`, create a production tag, or submit to the public marketplace without **explicit** user consent for that action. Staging publishes (`*-rc`) still need an explicit release/promote request.

## Workflow

1. **Confirm the target channel** — `staging` (team marketplace / `-rc`) or `master` (public marketplace / final tag).
2. **Run the release gate** from `AGENT.md`:

```bash
uv run python scripts/release_gate.py
```

Record pass/fail from the exit code. Do not continue on failure.

3. **For staging → production**, prefer the Actions workflow (requires GitHub App secrets):

```bash
gh workflow run promote.yml -f from_tag=<X.Y.Z-rc> -f to_branch=master -f dry_run=true
# after dry-run looks good, and with explicit consent:
gh workflow run promote.yml -f from_tag=<X.Y.Z-rc> -f to_branch=master -f dry_run=false
```

4. **After a production tag**, remind the user:
   - GitHub Release is created by `publish-production.yml` (environment `production` may require a reviewer).
   - Public marketplace updates are **manually reviewed** by Cursor — submit/notify at https://cursor.com/marketplace/publish
   - Team marketplace: track `master`, enable Auto Refresh (Cursor GitHub App on the repo).

5. **Do not** push tags or merge release PRs unless the user explicitly asked.
