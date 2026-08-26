# Posting a Review on the Open PR

When the user asks to review **the PR** (or tier is **pr** with an open PR), split delivery:

| Where | What |
|---|---|
| **Agent chat only** | Full findings table, counts, Validate detail, verdict rationale, own-PR event notes |
| **GitHub PR review** | **Only when there is ≥1 finding to attach inline** — short human body + inline comments on those lines |

Do **not** put the findings table (or duplicate finding prose) in the PR review body.

## 0. Clean pass — do not post on GitHub

**Hard rule:** if there are **zero** findings to attach as inline comments (including: review passed, confirming pass, only closed/accepted leftovers filtered out), **do not** create or submit any PR review.

| Forbidden on a clean pass | Why |
|---|---|
| `APPROVE` / `COMMENT` / `REQUEST_CHANGES` with “Review passed” | Contaminates the PR timeline; later fetches look like the code is certified clean |
| Empty or status-only bodies (`Verdict` / `Validate` / `0 new findings`) | Bot checklist noise |
| `gh pr comment` “all clear” notes | Same problem |

Report the clean verdict **in chat only** (and to the parent orchestrator). Leave the PR conversation untouched.

Validate failure with no line-level finding still stays **chat only** unless you can attach a concrete inline comment on a changed file.

## 1. Resolve the current open PR

Use the PR for the **checked-out branch** — never guess a number.

```bash
GH_PAGER=cat gh pr view --json number,url,title,state,headRefOid
```

| Result | Action |
|---|---|
| PR found (`state: OPEN`) | Use `number`, `url`, `headRefOid` |
| No PR | Chat only; tell the user no open PR exists for this branch |
| PR closed/merged | Chat only; do not post |

```bash
gh repo view --json nameWithOwner -q .nameWithOwner
```

## 2. Chat first — table stays here

Complete the review and show the unified findings table **only in chat** (see reviewer `## Output`). GitHub gets inline threads, not this table.

## 3. One submission — only when there are findings

Post **exactly one** pull request review per review pass **that has ≥1 inline finding**. Otherwise skip GitHub entirely (§0).

| Forbidden | Why |
|---|---|
| `gh pr comment` **and** `gh pr review` for the same pass | Double post |
| Findings table in the review body | Belongs in chat only |
| Separate summary review after inline comments | One submission only |
| Submitting before all inline comments are attached | Use pending review flow |
| Status-report bodies (`**Verdict:**`, round numbers, “0 new findings”, Validate checklists) | Sounds like a bot; confuses later comment fetches |
| Meta about GitHub event mechanics on the PR | e.g. “(Intended event: REQUEST_CHANGES; posted as COMMENT because …)” — **chat only**, never on the PR |

### Preferred flow (pending review — gh or GitHub MCP)

1. **Create** a pending review (no `event` yet).
2. **Add** one inline comment per finding (see §4).
3. **Submit once** with a short human body + `event`.

**gh CLI:**

```bash
# 1. pending — gh api POST .../pulls/PR/reviews with commit_id, no event
# 2. each inline — gh api POST .../pulls/PR/comments with path, line, body, commit_id
# 3. submit — gh api POST .../pulls/PR/reviews/REVIEW_ID/events with body + event
```

**GitHub MCP (when `gh` is unavailable):**

1. `pull_request_review_write` — `method: create`, `commitID: headRefOid`
2. `add_comment_to_pending_review` — once per finding (`path`, `line`, `body`, `side: RIGHT`)
3. `pull_request_review_write` — `method: submit_pending`, brief `body`, `event`

### Alternative: single REST call

One `POST .../pulls/{pr}/reviews` with `commit_id`, `event`, short `body`, and `comments` JSON array — **no** separate summary step.

## 4. Inline comments — one per finding

Every finding with a resolvable `path` gets an inline review comment on the PR diff.

Write like a concise human reviewer: the issue and, when helpful, the fix shape — not a severity badge wall.

**Comment body format:**

```markdown
{one or two sentences: what’s wrong and what to change}
```

Severity can lead when it helps triage; keep it light:

```markdown
**High** — Import type required by the project linter; breaks `AGENT.md` lint / CI. Use a type-only import.
```

**Line resolution:**

- `line` must exist on the **PR diff** for `headRefOid` (right/new side).
- Read the diff or PR files API to pick a line inside the changed hunk — do not guess from local-only context.
- If the file is not in the PR diff, or no valid line exists: **chat only** — note "not posted inline" in chat; do not dump it into the review body.

Prefer line-level comments (`subjectType: LINE`). Use file-level only when the finding applies to the whole file and no hunk line fits.

## 5. Review body — short lead-in only

The submitted review body is **one short sentence** pointing at the inline threads. **No table. No Verdict/Lint checklist. No round numbers. No “intended event” footnotes.**

Examples:

```markdown
A few issues on the diff — see inline.
```

```markdown
Blocking: lint failure on the changed slider — details inline.
```

If you cannot write a useful one-liner, use an empty body and let the inline threads carry the review (API permitting) — still never paste status-report templates.

## 6. Review event

| Situation | Event |
|---|---|
| Zero findings to post | **Do not post** (§0) — never `APPROVE` for “all clear” |
| ≥1 finding on someone else’s PR | `REQUEST_CHANGES` when any Critical/High or Validate suite fail; else `COMMENT` |
| ≥1 finding on **your own** PR | Always `COMMENT` (GitHub blocks `REQUEST_CHANGES` on own PRs) |

**Own PR:** use `COMMENT` silently. Record “would have been REQUEST_CHANGES” **in chat / parent report only** — never in the review body, never as a parenthetical on the PR.

## 7. After posting (or skipping)

Reply in chat with:

- Whether GitHub was skipped (clean) or posted
- PR URL when posted
- Event used when posted (`COMMENT` / `REQUEST_CHANGES`)
- Own-PR event fallback note when relevant (**chat only**)
- Count of inline comments posted vs findings kept chat-only

Do **not** commit, push, or resolve existing threads (that is `pr-resolver`).

## 8. Replying to existing threads

For **existing** review threads (not a new review), use `code/review/pr-resolver/references/graphql-fetch.md`.
