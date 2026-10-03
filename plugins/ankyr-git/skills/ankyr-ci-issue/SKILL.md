---
name: ankyr-ci-issue
description: GitHub issue creation workflow — write a title and body, create with gh, and assign the authenticated local user. Use when the user asks to open, create, or file a GitHub issue.
disable-model-invocation: true
---

# CI — Issue

The milestone workflow for opening a GitHub issue.

## Foundation

Resolve standards in this order: the `AGENT.md` chain (leaf → root), then project rules, then project skills, then this plugin's matching skill if installed. The first source that speaks wins. Consent, review-gate, and security floors always apply.

## Workflow

1. **Resolve the authenticated user.** `gh api user --jq .login`. If `gh` is not authenticated, stop and say so — do not create the issue.
2. **Draft the issue.** Title and body in complete sentences. Prefer the repository's `.github/ISSUE_TEMPLATE/` when present; otherwise write a clear problem statement and any needed context.
3. **Create the issue:**

```bash
gh issue create \
  --title "<imperative or problem statement>" \
  --body "$(cat <<'EOF'
<body>
EOF
)" \
  --assignee @me
```

`@me` is the authenticated `gh` user. If the user named a different assignee, use that login instead of `@me`.

4. **Verify assignee.** `gh issue view --json assignees,url` — confirm the chosen login is present. If create did not assign, run `gh issue edit <n> --add-assignee @me` (or the named login) and re-check. If assignment still fails (for example the login cannot be assigned on that repo), report that; do not claim success.
5. Return the issue URL.
