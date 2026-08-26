---
name: ci-pr
description: Pull-request creation workflow — review at PR tier, then open the PR with a Summary + Test plan body. Use when the user asks to create or open a PR. Extends engineering.
disable-model-invocation: true
---

# CI — Pull Request

The milestone workflow for opening a pull request.

## Extends

Load `skills/code/foundations/engineering/SKILL.md` first.

## Workflow

1. **Understand the full branch.** Inspect status, the full diff since the branch diverged from the base, and the commit history — not just the latest commit.
2. **Review at PR tier.** Run the reviewer (tier: pr, `merge-base...HEAD`). Require a clean verdict or an explicit skip before opening the PR.
3. **Ensure the branch is pushed.** Opening a PR requires the branch on the remote — but pushing requires explicit push consent (see `git-push-consent.mdc` and the push skill). Ask before pushing if needed.
4. **Open the PR** with the body template below, passed via HEREDOC.

## Body template

```
## Summary
- <1-3 bullet points on what changed and why>

## Test plan
- [ ] <how to verify>
```

Write complete sentences. Reflect all commits in the branch, not only the most recent. Return the PR URL when done.
