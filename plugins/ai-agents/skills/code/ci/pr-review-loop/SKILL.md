---
name: ci-pr-review-loop
description: Autonomous PR review-fix loop — alternates a fresh reviewer subagent and a pr-resolver fixer subagent on the branch's open PR until findings reach zero, within a round and cost budget, escalating only when a real design/policy call is required. Extends engineering.
disable-model-invocation: true
---

# CI — PR Review Loop

Self-hosted Bugbot replacement. Default cycle: **full review → fixer → delta review → … → confirm clean**. Reuses `code/review/reviewer` and `code/review/pr-resolver`; this skill orchestrates, budgets, and reports.

## Extends

Load `skills/code/foundations/engineering/SKILL.md` first.

## Scoped consent

Invoking this skill (or an explicit "run the PR review loop" request) grants scoped commit and push consent for approved fix commits on the current PR branch only — same shape as pr-resolver scoped consent. Force-push and pushes to `dev`/`main` remain forbidden.

## Loop

```
preflight (auth, toolchain, pricing, baseline Validate from AGENT.md, cold budget)
  → Round N: pr-reviewer (focus: full | delta | confirm)
  → post inline comments only when there are new open findings
  → fetch unresolved threads (after review)
  → triage via references/triage-policy.md
  → Recommend:Fix → pr-fixer (never escalate for severity alone)
  → escalate only on design/policy ambiguity → pause
  → next focus per progression → canvas when consecutive cleans met
```

Success stop: **`clean_passes_required` consecutive** reviews with zero open findings (default 2). One clean pass is not enough.

## Performance (do not undo)

- **Focus progression** — not `full` every round. See below.
- **Init-once env/CI** — Validate suite from `AGENT.md`, `gh auth`, toolchain, pricing run at preflight (and after tree change / fixer). Reviewers skip phase-9 validate when fingerprint still matches — **including `full` / `confirm`**.
- **Triage** — `Recommend: Fix` + concrete shape never pauses the user.

## Review first — never resolve before reviewing

Hard rules, not defaults:

1. **Round 1 is always a review pass.** Even when the PR already has Copilot or human comments, do not open by resolving them.
2. **Fetch pre-existing unresolved threads only after the round-1 review completes.** Merge them into that round's triage table tagged `loop` vs `external`.
3. **Never launch `pr-fixer` with an empty findings set.** Zero findings on round 1 → go toward clean-pass counting / canvas (still need `clean_passes_required`).
4. **`review-lock.py check pr` cannot satisfy round 1.** It may skip a duplicate scan of an unchanged tree later, but round 1 always runs the reviewer for real.

## Preflight

1. Resolve the open PR for the checked-out branch (`gh pr view` or GitHub MCP). No open PR → stop and report.
2. Preflight `gh auth status` **once**; on failure fall back to GitHub MCP. Do not re-check every round unless posting fails.
3. Detect toolchain mode **once** via `hooks/run-python.sh --detect`. Do **not** run `npm run test:py` every round — only if detect fails or the user asks.
4. Bootstrap pricing **once** if `.review-loop/pricing.json` is missing or lacks a `modes` table.
5. Resolve **role models** (default both **`inherit`**):
   - Aliases: `auto`/`inherit` → `inherit`; `opus`/`opus-5` → `claude-opus-5-thinking-high`; `sonnet`/`sonnet-5` → `claude-sonnet-5-thinking-high`; see `references/loop-state.md`
6. Detect **pricing mode** for loop caps (`auto` default; `api` only when user says so).
7. Initialize state via **`hooks/run-python.sh review_loop_init.py`**. Overrides: `max 2 rounds`, `budget $1.50`, `budget-only` → `max_rounds: null`, `manage high`, `post_fix_focus=full`, `diminishing after round 3`, `diminishing_returns_floor=high`, `analysis debug` / `analysis_mode=security` / `debug-like review`.
8. **Baseline validate (required once):** run every command in the repo `AGENT.md` **Validate** section via **raw** shell. Store `last_validate_fingerprint`, `last_lint`, `last_build` on `state.json` (`last_lint` / `last_build` are opaque pass/fail slots for the Validate suite — success means **all** listed commands passed). Fingerprint via `python3 scripts/review-lock.py fingerprint pr --json`.
9. **Cold budget gate** before round 1. If over cap → escalate and stop; do not set `active: true`.
10. Set `active: true`. Print: `pricing_mode`, models, `analysis_mode`, `manage_severity`, `post_fix_focus`, `diminishing_returns_round`, `diminishing_returns_floor`, `max_rounds`, caps, cold projection, validate status, and whether `seeded_from_ledger` / short-circuit confirm applies. Note: `analysis_mode` is **prompt-level reviewer behavior**, not Cursor's Agent/Plan/Debug UI mode.
11. **Short-circuit check:** if `should_short_circuit_confirm(state, current_fingerprint)` → round 1 focus = `confirm` (see Focus progression).

## Focus progression

| Situation | Default focus |
|---|---|
| Round 1 (default) | `full` |
| Round 1 when `should_short_circuit_confirm(state, fingerprint)` | `confirm` |
| After a fixer this run | `post_fix_focus` (default **`delta`**) |
| After a clean `delta` (fix verified, not counted) | `confirm` |
| After first **counted** clean (`consecutive_clean_passes == 1`) | `confirm` |
| Coverage failed / issues outside hotspot set | `full` once |

**Unchanged-fingerprint short-circuit:** after init, if `_loop_state.should_short_circuit_confirm(state, current_fingerprint)` is true (prior run `last_outcome == confirmed_clean` at the same fingerprint), round 1 focus is **`confirm`** — not `full`. If that confirm is clean → set `consecutive_clean_passes = clean_passes_required`, canvas, `mark_run_outcome(..., "confirmed_clean", fingerprint)`, stop. If confirm finds real new/contested items → continue with the seeded closed set (do **not** wipe the ledger).

Invocation overrides (`focus full` / `focus delta` / `focus confirm`) win. Preference `post_fix_focus`: `delta` (default) or `full`.

Use `_loop_state.resolve_round_focus(...)` when deciding the next launch. Only `full` / `confirm` may increment `consecutive_clean_passes` (`clean_pass_counts` / `apply_clean_pass`).

## Per-round protocol

1. Best-effort debug: optionally stamp `started_at` / `reviewer_started_at` (informational only — cost accounting uses hook `_pending_subagent` + `agent_transcript_path`). Set `next_model` to `reviewer_model`.
2. Resolve **focus** via progression above. After any `status: fixed` exists (`has_fixed_this_run`), tell the reviewer this is **post-fix verify mode** and pass verify-surface paths (`verify_surface_paths` + last fixer paths + one-hop dependents). Launch **`pr-reviewer`**:
   - `run_in_background: true`, `model: <reviewer_model>`
   - Pass: PR, round, focus, **`analysis_mode`** (from state; default `review` — prompt behavior only, not Cursor Debug UI), `closed_findings`, `accepted_by_design`, `fix_hotspots`, `consecutive_clean_passes`, **`last_validate_fingerprint` / `last_lint` / `last_build`**, whether validate may be skipped, post-fix verify flag / surface paths, and the compact **fix ledger** from `_loop_state.format_fix_ledger_for_prompt(state)` (required every launch — not only the raw JSON dump).
   - Fresh context. Do **not** pass prior fixer reasoning. Say when this is post-fixer verify (not a new discovery pass).
   - Pairing tip: `analysis debug` + `reviewer_model=opus` for hardest semantic analysis without claiming Cursor Debug mode.
3. Alert: *Subagent panel may stay blank — I'll continue when the review finishes.* Wait for Task completion.
4. **Closed-finding filter** (`filter_open_findings`). Then **`filter_post_fix_findings`** — drive-by findings outside the verify surface → Defer (post-fix verify); keep recurrence/contested/regression, Critical, and in-surface rows. Contested-against-ledger → escalate once (never auto-fix). Post GitHub **only** for kept open signatures. Never post clean-pass reviews on the PR.
5. Fetch unresolved threads; merge tagged `external`.
6. Triage via `references/triage-policy.md`. **Self-check before escalate:** if Recommend is Fix with a concrete shape → `Decision: Fix` and launch fixer — never pause for High/Critical alone. Exceptions: contested-against-ledger → Escalate; outside verify surface (non-Critical) → Defer.
7. Auto-approved rows → `pr-fixer` (`run_in_background: true`). Include the same **fix ledger** table in the fixer prompt. Fixer always validates before commit; then orchestrator updates `last_validate_*`.
8. Record round outcome; append fixed / accepted / deferred to `closed_findings` via `append_closed_finding` (including post-fix-verify deferred). **`fix_shape` is required** on every `status=fixed` close (from the fixer's What changed / Why) — empty `fix_shape` on fixed is a process bug.
9. Projective budget before next launch.
10. Stop conditions; if continuing, launch next review with resolved focus (including after a single clean → `confirm`). On confirmed clean / stop / escalation exit, call `mark_run_outcome(state, outcome, fingerprint)`.

### Subagent launch contract (required)

- Always **`run_in_background: true`**. Panel may stay blank until finish — expected.
- Never nest Task inside `pr-reviewer` / `pr-fixer`.
- Fallback to `generalPurpose` only after two failed custom starts; re-check budget yourself (hooks won't match).
- Pass the role model on every Task call.
- Every `pr-reviewer` launch **must** include `analysis_mode` from state.
- Every `pr-reviewer` and `pr-fixer` prompt **must** include `format_fix_ledger_for_prompt(state)`.

### Validate ownership

| Who | When |
|---|---|
| Orchestrator init | Baseline Validate suite once |
| `pr-reviewer` | Skip if fingerprint matches stored pass; else re-run and update state |
| `pr-fixer` | Always raw Validate suite before commit; update `last_validate_*` on success |

Never trust `rtk`-wrapped exit codes for pass/fail. Never record Validate `pass` when any command failed.

## Stop conditions

Keep looping until one of:

- **Confirmed clean:** `consecutive_clean_passes >= clean_passes_required` (default **2**)
- Projected spend would cross caps
- Round cap (if set)
- Escalation pending (design ambiguity only)
- Validate suite failed and not fixed in-round

**Do not stop as “passed” when:** only one clean landed; the only zero-finding rounds were narrow (`delta`); open findings with no new signatures (recurrence/contested); unchanged fingerprint after a no-op fix.

Findings deferred below `manage_severity`, by the diminishing-returns ratchet, or by **post-fix verify** (`triage-policy.md`) are **closed** for this run — they do **not** block a clean verdict. List them on the summary canvas as follow-ups.

### After each reviewer report (orchestrator)

1. Write findings / fingerprint / coverage / focus into the round entry (`counted_clean` set in step 5).
2. Closed-finding filter (`filter_open_findings` — keeps `recurrence` / `contested` open).
3. Post-fix verify filter (`filter_post_fix_findings`) when `has_fixed_this_run` — defer drive-bys outside the verify surface; append deferred with rationale `post-fix verify`.
4. Kept open findings → `consecutive_clean_passes = 0`, triage, fixer.
5. Zero open but coverage failed → not clean; next focus `full` only if no fixes yet, else stay on verify surface / `confirm`.
6. Zero open + coverage OK:
   - focus `full` / `confirm` → `apply_clean_pass(...)` (`counted_clean: true`); if below required, next focus `confirm`; if at requirement → canvas + `active: false`.
   - focus `delta` → **fix verified, not a clean pass** (`counted_clean: false`; counter untouched); next focus `confirm`.

## Escalation format

Escalate **only** for design/policy ambiguity. Before posting: if Recommend is Fix → abort and auto-fix.

```markdown
## PR Review Loop — Escalation

**Round:** N
**Blocked auto-fix because:** <design/policy ambiguity — never “High severity…”>

**Recommendations** (orchestrator proposes; user confirms or corrects):

| # | Location | Severity | Category | Recommend | Why this is an issue | If fixing / By-design evidence |
|---|---|---|---|---|---|---|
| 1 | path:line | High | security | By design | <why intentional looks plausible> | <evidence> |
| 2 | path:line | Medium | logic | Fix | <harm> | <only when truly unsure — prefer auto-fix> |

**Spent / cap:** …

**Reply with:** confirm all · fix #… · accept #… as by design · stop
```

Prefer auto-fix whenever Recommend would be Fix. Escalation rows with Recommend: Fix alone are a process bug.

## Closing canvas

Read `state.json` and write the canvas per `references/summary-canvas.md`. Set `active: false`.

## Additional resources

- [triage-policy.md](references/triage-policy.md) — auto-fix vs escalate (hard litmus)
- [loop-state.md](references/loop-state.md) — state, budget, focus, validate fingerprint
- [summary-canvas.md](references/summary-canvas.md) — canvas contract

## Closed findings (do not re-poop)

Once fixed, accepted, or deferred, a finding's signature goes into `closed_findings` and the durable PR ledger (`.review-loop/closed-ledger.json`). A new loop on the same PR **seeds** that memory at init — do not rediscover fixed work. After the first fix, later rounds are **post-fix verify** (surface only) — not a fresh survey of the PR. True regressions use `Source: recurrence` / `Source: regression`. Opposite-shape findings on a path with a prior `fix_shape` are contested (`is_contested_against_ledger`) — escalate, never auto-revert.
