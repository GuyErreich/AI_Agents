---
name: ankyr-ci-local-review-loop
description: Controlled self-review loop — review, triage findings with the user, fix only approved items, re-review until clean, then offer to commit. No auto commit or push. Use to drive local code to zero review findings before a milestone.
disable-model-invocation: true
---

# CI — Local Review Loop

Drives local changes to zero review findings before a commit, with the user in control. This is the local counterpart to the PR-resolver loop: same discipline, applied to the working tree instead of a remote PR.

## Foundation

Resolve standards in this order: the `AGENT.md` chain (leaf → root), then project rules, then project skills, then this plugin's matching skill if installed. The first source that speaks wins. Consent, review-gate, and security floors always apply.

The reviewer applies project standards first and this plugin's skills only as defaults. Findings must trace to a standard that applies to this project.

## Loop

A caller may supply a path scope (file, module, or package) instead of the default change-tier diff. When that happens, run reviewer at the **file argument** tier on that path.

```
review (reviewer skill) → findings table
  → present triage: fix now | by design (keep) | defer
  → user approves which to fix
  → implement ONLY approved fixes (minimal, root-cause)
  → validate (AGENT.md Validate suite)
  → re-review
  → repeat until zero findings or user stops
→ offer to commit (never auto-commit)
```

## Rules

- **Not every finding must be fixed.** Some are intentional design — mark them "by design" and keep them, with a one-line rationale. The loop ends when the remaining findings are all accepted-by-design or fixed.
- **Fix only what the user approved.** Minimal, root-cause changes; no drive-by refactors.
- **No auto commit, no auto push.** When the loop ends clean, hand off to `ankyr-ci-commit` only if the user asks to commit.
- **Validate every iteration.** Run every command in the repo `AGENT.md` **Validate** section before re-reviewing.

## Triage table

```markdown
| # | Location | Severity | Finding | Decision | Rationale |
|---|---|---|---|---|---|
| 1 | path:line | High | ... | Fix | ... |
| 2 | path:line | Low | ... | By design | intentional ... |
```

Wait for the user to confirm the decisions before implementing.
