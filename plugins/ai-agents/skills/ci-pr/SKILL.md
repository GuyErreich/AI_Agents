---
name: ci-pr
description: Pull-request creation workflow — review at PR tier, then open the PR with a conventional title and Summary + Test plan body from the assets template. Use when the user asks to create or open a PR. Extends engineering.
disable-model-invocation: true
---

# CI — Pull Request

The milestone workflow for opening a pull request.

## Extends

Load `skills/engineering/SKILL.md` first.

## When to load references and assets

| Topic | Resource |
|---|---|
| Title prefix (`feat:`, `fix:`, etc.) and release-notes grouping | `references/title-conventions.md` |
| Refresh a stale existing PR body | `references/body-refresh.md` |
| PR body scaffold (Summary + Test plan) | `assets/pr-template.md` |

Load `title-conventions.md` before choosing the PR title. Copy/adapt `pr-template.md` for the body. Under **Summary**, place each change in the matching section (Features, Bug Fixes, etc.); **omit empty sections**. Load `body-refresh.md` when the user asks to update an existing PR body, or when step 1 finds a PR already open.

## Read-only during create

PR creation must **not** create commits or modify repository files. Describe the branch as it already is.

**Exception:** `pr-resolver` and `pr-review-loop` hold scoped consent to commit and push approved fixes — that is a different workflow, not this one.

## Workflow

1. **Existing-PR check.** `gh pr list --head <branch> --base <base> --state all` (base from `AGENT.md`). If a PR exists, print the URL and **stop** — or, if the user asked to refresh the body, follow `references/body-refresh.md`. Never attempt a duplicate create.
2. **Understand the full branch.** Inspect status, the full diff since the branch diverged from the base, and the commit history — not just the latest commit.
3. **Review at PR tier.** Run the reviewer (tier: pr, `merge-base...HEAD`). Require a clean verdict or an explicit skip before opening the PR.
4. **Ensure the branch is pushed.** Opening a PR requires the branch on the remote — but pushing requires explicit push consent (see `git-push-consent.mdc` and the push skill). Ask before pushing if needed.
5. **Open the PR:**
   - **Title** — one line; prefix from `references/title-conventions.md` matching the primary change type (prefer `feat:` / `fix:` for auto-semver repos).
   - **Body** — from `assets/pr-template.md`, passed via HEREDOC to `gh pr create --body "$(cat <<'EOF' ... EOF)"`. Group changes under Summary by type (Features, Bug Fixes, …); drop sections with no items.
   - Multi-concern branches: use multiple Summary sections when needed; **title** still reflects the dominant change type for squash-merge release notes (`header_only`).
6. Write complete sentences. Reflect all commits in the branch, not only the most recent. Return the PR URL when done.
