---
name: pr-resolver
description: Controlled loop that resolves GitHub PR review threads — review, post findings, fetch threads, Plan-mode triage table, implement approved fixes, commit, push, reply, resolve, re-review until clean. Use to read, resolve, or address PR review comments. Extends engineering.
disable-model-invocation: true
---

# PR Resolver

A controlled loop for resolving Copilot or human review comments on a pull request. Runs the reviewer, triages every thread with the user in Plan mode, fixes only what is approved, commits and pushes to the PR branch, replies on threads, and repeats until no unresolved issues remain.

## Extends

Load `skills/code/foundations/engineering/SKILL.md` first. Load `skills/code/review/reviewer/SKILL.md` when you need project-convention context to judge a thread.

**Hard stop:** Do not edit code, commit, push, post replies, or resolve threads until the user explicitly approves the plan from the triage step.

## Scoped consent

Approving the resolver plan **or** an explicit request to resolve PR comments counts as consent to **commit and push only the approved fix commits** on the current PR branch. This scoped consent does not apply to unrelated work outside the approved plan.

## Loop

```
reviewer(pr) on the branch diff
  → post new findings on the open PR (reviewer references/pr-comments.md)
  → fetch ALL threads (GraphQL — see references/graphql-fetch.md)
  → SwitchMode → plan: present triage table (fix | by design | blocked)
  → wait for explicit user approval
  → implement ONLY approved "fix" rows (minimal, root-cause)
  → post fix summary in chat (see Step 4)
  → validate (AGENT.md Validate suite)
  → commit (change-tier review — ci/commit) when code changed
  → push (PR-tier review — ci/push) so CI and reviewers see the fix
  → post threaded replies; resolve threads per the rules below
  → re-review → repeat until unresolved count is 0
```

## Step 1 — Fetch all threads

Always use GraphQL and paginate fully — REST tooling silently misses threads beyond page one. See `references/graphql-fetch.md` for the query and pagination. Filter to unresolved threads.

## Step 2 — Understand each thread

For every unresolved thread: read the full thread, read the flagged file around the reported line, and summarize what the reviewer wants in plain language. Then classify a **proposed** outcome (do not act yet):

| Outcome | When |
|---|---|
| **Fix** | Real bug, regression, safety issue, or clear maintainability win with a minimal diff |
| **By design** | Intentional trade-off, false positive, stylistic preference, or out-of-scope suggestion |
| **Blocked** | Needs a product/architecture decision, missing context, or an external dependency |

Review suggestions are input, not orders. Keep intentional design as-is when the trade-off was considered and the code is correct.

## Step 3 — Plan mode & approval gate

Switch to Plan mode and present a per-thread table:

```markdown
## PR Resolver Plan — PR #<number>

| # | File:Line | Reviewer | Proposed | Why it fixes / why keep |
|---|---|---|---|---|
| 1 | path:42 | @reviewer | Fix | one-sentence rationale |
| 2 | path:88 | @copilot | By design | one-sentence rationale |
```

Then stop and wait. Do not proceed until the user explicitly approves or revises. If they revise, update the table and wait again.

## Step 4 — Execute approved plan only

Apply only what was approved; follow any user override. Fix threads get minimal root-cause changes. By-design and blocked threads get a prepared in-thread reply, no code change.

After code changes, **always** post a fix summary in the chat session (not on GitHub) before validating, committing, or replying on threads:

```markdown
## PR Resolver — Fix summary

| # | File | Finding | What changed |
|---|---|---|---|
| 1 | path/to/file | one-line reviewer ask | one-line concrete fix |
```

One row per approved **Fix** thread. For **By design** / **Blocked**, add a short **Replies only** subsection with file and the rationale you will post on GitHub. Update with commit SHA after commit and remote SHA after push.

## Step 5 — Validate

Run every command in the repo `AGENT.md` **Validate** section when the approved plan changed code. Skip when there were no code changes. Do not commit or push until validation passes.

## Step 6 — Commit & push

When the approved plan changed code:

1. **Commit** — follow `skills/code/ci/commit/SKILL.md` (change-tier review). Scoped consent from Step 3 applies.
2. **Push** — follow `skills/code/ci/push/SKILL.md` (PR-tier review), then `git push -u origin HEAD` if needed. Scoped consent from Step 3 applies.

Skip commit and push when the plan was replies-only (by design / blocked only). If push fails, stop: post replies noting the blocker, leave fix threads unresolved, and report in chat.

## Step 7 — Reply & resolve

Post a threaded reply on every approved thread. Resolution rules:

| Outcome | Resolve when |
|---|---|
| Fix (code changed) | after the fix is pushed to the remote PR branch and the reply cites the remote commit SHA |
| By design / Blocked (no code change) | after posting the in-thread reply |

Never resolve a fix thread while the fix exists only locally.

## Step 8 — Re-review

Re-run the loop until the unresolved count is 0. End the session with a brief chat recap: unresolved count, commit SHA(s), push confirmation, and CI status if available.
