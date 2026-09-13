# Tiers & Scope

Determine the tier before reviewing.

| Tier | When | Git scope |
|---|---|---|
| **change** | Before commit (gate) | `git diff HEAD` + `git diff --cached` (uncommitted only) |
| **commit** | After commit, or when change tier just passed on the identical tree | `git diff HEAD~1..HEAD` (last commit) |
| **pr** | Before push or PR open (gate) | `git diff merge-base...HEAD` (full branch, PR-equivalent) |
| **file argument** | User names a path | that file/area only |

If the tier is unclear, ask once. Default to **pr** when the user mentions PR or branch review; default to **change** for pre-commit.

## List changed files

```bash
# change
git diff --name-only HEAD && git diff --cached --name-only

# commit
git diff --name-only HEAD~1..HEAD

# pr (base branch is a project setting — see the repo AGENT.md; falls back to main)
git diff --name-only $(git merge-base HEAD "$BASE" 2>/dev/null || git merge-base HEAD main)...HEAD
```

The base branch name (for example `dev` or `main`) is a project setting; read it from the repository `AGENT.md`.

## PR tier — comment on the open PR

When the user asks to review **the PR**, after the review completes load `references/pr-comments.md`: findings table in chat only; on GitHub post only when there is ≥1 finding (concise inline comments + one-sentence body). Clean passes and event-fallback notes stay in chat — do not post “Review passed” or status checklists on the PR. Always run `references/thoroughness-pass.md` before a clean verdict. If no open PR exists, report in chat only.

## Lockfile protocol (advisory)

If the repo ships a review-dedup helper (for example `scripts/review-lock.py`), the gate rule may use it to avoid duplicate scans:

1. `check <tier>` — if it reports the tier already reviewed on the current tree, reply one line and stop, unless the user asked for a forced re-review.
2. Run the phases on the tier scope.
3. `record <tier> --verdict passed|failed` — record the outcome (failed if findings > 0 or Validate suite fails).
4. After a commit with no further edits, the commit tier can inherit the change-tier verdict.

This is advisory: never let the lockfile substitute for an actual review when the tree has changed, and never let its absence block work.

## Supersession

- `pr` covers the full branch — once recorded, skip change/commit checks for the same branch state until the diff changes.
- `change` covers local edits — if unchanged since last review, do not re-run before commit.
