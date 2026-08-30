---
name: ci-pr
description: Pull-request creation workflow — review at PR tier, then open the PR with a conventional title and Summary + Test plan body from the assets template. Use when the user asks to create or open a PR. Extends engineering.
disable-model-invocation: true
---

# CI — Pull Request

The milestone workflow for opening a pull request.

## Extends

Load `skills/code/foundations/engineering/SKILL.md` first.

## When to load references and assets

| Topic | Resource |
|---|---|
| Title prefix (`feat:`, `fix:`, etc.) and release-notes grouping | `references/title-conventions.md` |
| PR body scaffold (Summary + Test plan) | `assets/pr-template.md` |

Load `title-conventions.md` before choosing the PR title. Copy/adapt `pr-template.md` for the body.

## Workflow

1. **Understand the full branch.** Inspect status, the full diff since the branch diverged from the base, and the commit history — not just the latest commit.
2. **Review at PR tier.** Run the reviewer (tier: pr, `merge-base...HEAD`). Require a clean verdict or an explicit skip before opening the PR.
3. **Ensure the branch is pushed.** Opening a PR requires the branch on the remote — but pushing requires explicit push consent (see `git-push-consent.mdc` and the push skill). Ask before pushing if needed.
4. **Open the PR:**
   - **Title** — one line; prefix from `references/title-conventions.md` matching the primary change type (prefer `feat:` / `fix:` for auto-semver repos).
   - **Body** — from `assets/pr-template.md`, passed via HEREDOC to `gh pr create --body "$(cat <<'EOF' ... EOF)"`.
   - Multi-concern branches: prefer one PR per concern, or title the dominant type; secondary changes go in Summary bullets only.
5. Write complete sentences. Reflect all commits in the branch, not only the most recent. Return the PR URL when done.
