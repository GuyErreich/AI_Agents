# Refresh an existing PR body

Use when the user asks to update a PR description, or when create-PR finds a PR already open and the user wants the body brought current (for example after `pr-review-loop` fix commits).

## Rules

- Re-derive the body from the **full** `merge-base...HEAD` diff and the complete commit list — not only the newest commits.
- Keep the existing template (`assets/pr-template.md`): Summary sections by type, Test plan, omit empty sections.
- Do **not** create commits or modify repository files. The update is `gh pr edit` only.
- Do not change the title unless the user asked, or the current title no longer matches the dominant change type.

## Workflow

1. Resolve the PR: `gh pr view --json number,url,title,body,baseRefName` (or the number the user named).
2. Read the base from `AGENT.md`. Diff `$(git merge-base HEAD <base>)...HEAD` and `git log <base>..HEAD`.
3. Draft the body from `assets/pr-template.md`. Drop empty Summary sections.
4. Apply:

```bash
gh pr edit <n> --body "$(cat <<'EOF'
## Summary

### Features

- …

## Test plan

- [ ] …
EOF
)"
```

5. Return the PR URL. Confirm what changed in the body in one or two sentences.
