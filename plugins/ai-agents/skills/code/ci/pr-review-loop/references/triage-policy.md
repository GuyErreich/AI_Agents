# Triage Policy

Orchestrator classifies every finding (and every external unresolved thread) before the fixer runs. Policy-based — no Plan-mode gate per round unless something escalates.

## Hard litmus (read first — non-negotiable)

1. Can you state **Recommend: Fix** with a concrete fix shape? → **`Decision: Fix`** → hand to `pr-fixer`. **Never escalate.**
2. Are you unsure whether the current behavior is intentional product policy? → Escalate (propose Fix vs By design with your rationale).
3. **Forbidden blocked / Decision rationales:** anything whose pause reason is only severity or impact — e.g. “High severity…”, “Critical…”, “High — …”, “data-loss…”, “security…” alone. A blocked reason must name a **design ambiguity** (“unclear if X should remain”) or the finding must auto-fix.
4. Multiple equivalent safe fixes → pick the **simplest conservative** shape; do not escalate to ask which.

**Ask only when unsure of intent.** Importance, severity, and “easy important fix” are reasons to auto-fix, not to pause.

Before posting any escalation to the user: self-check — if you already wrote Recommend: Fix, **abort escalate and launch `pr-fixer`**.

Severity alone does **not** force escalation. Clear must-fixes auto-fix even at High/Critical.

## Severity floor (`manage_severity`)

Durable preference (and per-run override). Findings **below** this floor are not managed by the loop.

| Value | Loop manages |
|---|---|
| `low` | Low, Medium, High, Critical |
| `medium` (**default**) | Medium, High, Critical |
| `high` | High, Critical |
| `critical` | Critical only |

Order: `low` < `medium` < `high` < `critical`.

- Below floor → `Decision: Defer` — do not fix, do not escalate. Append to `closed_findings` with `status: "deferred"` so later rounds do not re-report them and clean-pass is not blocked.
- At or above floor → apply Auto-fix / Escalate / By design below.

Invocation overrides: `manage medium` / `manage high` / `manage_severity=high` / `only critical`. Printed at preflight with other caps.

## Diminishing returns (round-based ratchet)

After enough fix/review cycles, lingering non-Critical findings become follow-ups instead of blocking forever. Two durable preferences (also overridable per run):

| Preference | Default | Purpose |
|---|---|---|
| `diminishing_returns_round` | `2` | Round number at/after which the ratchet applies |
| `diminishing_returns_floor` | one tier above `manage_severity` (capped at `critical`) | Minimum severity still auto-fixed / escalated after that round. Below → Defer |

Examples with default `manage_severity=medium` → derived floor `high`:
- Round 1: Medium+ still managed as usual.
- Round ≥ 2: Medium (and Low) → `Decision: Defer (diminishing returns)`; High/Critical still Fix/Escalate.

Overrides: `"diminishing after round 3"` · `diminishing_returns_round=5` · `diminishing_returns_floor=high` · `diminishing_returns_floor=critical`. Floor is fully independent of `manage_severity` when set explicitly.

Deferred findings use the same `closed_findings` / `status: "deferred"` path as the severity floor, with rationale noting the round + floor so the summary canvas can list them as follow-ups.

## Post-fix verify (convergence)

Once any finding is closed with `status: fixed` this run (including ledger-seeded fixes), the loop is in **post-fix verify mode**:

- Verify surface = fixed paths ∪ last fixer diff ∪ hotspots ∪ one-hop dependents the orchestrator passes into `filter_post_fix_findings(..., fixer_paths=...)`.
- Keep: `Source: recurrence` / `contested` / `regression`, **Critical** (any path — escalate if outside surface), and any finding whose path is in the surface.
- Defer: all other drive-by findings outside the surface → `Decision: Defer (post-fix verify)` → `append_closed_finding(..., status="deferred", rationale="post-fix verify")`.

Use `_loop_state.has_fixed_this_run` / `filter_post_fix_findings`. Round-1 `full` discovery is unchanged until the first fix lands.

## Auto-fix (no ask)

When the finding is at/above `manage_severity`, **and** the correct fix is unambiguous (best practice / stated project rule — not a product trade-off):

- Lint, format, import order, and type errors
- Missing cleanup of listeners, timers, or Three.js disposal
- Missing a11y attributes or keyboard handlers on existing controls
- Magic values and naming violations already codified in `AGENT.md`
- Mechanical duplication extraction the `AGENT.md` mandatory-refactor rule already requires
- Doc and comment drift
- Clear security/logic defects with an obvious, local fix (e.g. missing `await`, wrong null check, hardcoded secret removal to env, missing dispose) — **including High/Critical** when there is no credible by-design reading
- **Follow-up migrations** — add a later timestamped migration with the intended SQL; never rewrite an already-applied migration version in place
- **Hydration / race / data-loss bugs** with a clear gate (e.g. disable edits until `isHydrated`) — pick the conservative shape; no user ask
- Documented secrets-map / deploy wiring when the path is already in project skills

Tag these `Decision: Fix` with a one-line rationale (include the chosen fix shape) and hand them to `pr-fixer`.

Stay inside the PR diff when possible; a **new** migration file that completes an in-diff schema change is allowed when that is the safe shape.

## Escalate (pause and alert)

Stop the loop and ask the user **only** when judgment is required — not because the severity label is high:

- **Design / product call** — ambiguous whether to keep current behavior; by-design evidence is plausible but not certain; “do we still want this?”
- **Security / access policy call** — trade-off between exposure and product need (e.g. unclear whether a role should keep SELECT), not a clear bug with a local fix
- Architectural refactors or changes to files **outside** the PR diff when the correct scope is unclear
- Public API, props contract, or **intentional** user-visible behavior changes where multiple valid **product** designs exist (not multiple equivalent bugfix shapes)
- A finding that **recurs after a fix** (`Source: recurrence`, same closed signature / same defect still present) — escalate once; do not re-open as a fresh auto-fix loop
- A finding that **contests a deliberate prior fix shape** (`Source: contested` — later reviewer wants to undo/rework what the fixer introduced per `closed_findings[].fix_shape`) — escalate once with both shapes; **never** auto-fix in the opposite direction
- Lint or Validate suite failing after a fix (non-zero exit from raw `AGENT.md` Validate commands)
- Infrastructure failures: no open PR, push rejection, merge conflict
- Projected next-round spend would cross `max_tokens_est` or `max_usd_est`

Do **not** escalate merely because the path is a migration, RLS, auth, or “data-loss” if Recommend would be Fix with a concrete safe shape.

Tag these `Decision: Escalate`. Set `escalation_pending: true` in `state.json`. The budget hook refuses new subagents until cleared.

### Escalation must propose — never blank-ask “by design”

When escalating, the orchestrator **tells** the user what looks intentional vs what should change. Do **not** ask the user to invent a by-design rationale.

For every escalated finding, include:

1. **Why this is an issue** — concrete harm or surprising behavior if left as-is.
2. **Category** — exactly one of: `security` | `logic` | `performance` | `best-practices` | `code-style`.
3. **Recommend** — Fix or By design, with fix shape or by-design evidence.
4. **Blocked auto-fix because** — the specific **design/policy ambiguity** only. If you cannot name an ambiguity, do not escalate — auto-fix instead.

| Recommend | When |
|---|---|
| **Fix** | Clear bug / security gap / inconsistent behavior relative to stated product rules — **if you pick Fix here, you must auto-fix, not escalate** |
| **By design** | Evidence in the PR, UI copy, comments, migrations, or prior accepted items that this is intentional |

| Category | Use when |
|---|---|
| `security` | Auth, secrets, RLS, injection, data exposure, privilege |
| `logic` | Wrong behavior, state bugs, race, incorrect contract |
| `performance` | Hot paths, N+1, unbounded work, render/jank cost |
| `best-practices` | Architecture, surprising UX, maintainability, a11y patterns |
| `code-style` | Naming, formatting, local conventions (rare to escalate) |

For each **By design** recommendation, write the rationale yourself (1–3 sentences). For escalations that are truly ambiguous, state both options; never escalate with Recommend: Fix as the only path.

The user only **confirms, corrects, or stops** — they should not have to invent the “why.”

## Closed findings (fixed, accepted, or deferred)

Anything already in `state.closed_findings` is **done for this loop run**.

- After fixes exist, later reviews are **post-fix verify** on the verify surface — not a fresh PR survey.
- **Do not** re-triage, re-fix, or re-comment the same closed issue (same signature, or same path + same underlying defect restated).
- Drop accidental re-reports and outside-surface drive-bys in the orchestrator before the triage table.
- True regressions via `Source: recurrence` / `Source: regression`. Contested opposite shapes escalate once.

## By design (keep)

Intentional trade-offs, false positives, stylistic preferences already accepted, or out-of-scope suggestions. Tag `Decision: By design` with a one-line (or short) rationale **written by the orchestrator**. Add to `accepted_by_design` **and** `closed_findings` (`status: "accepted"`) so later rounds do not re-poop them.

When the orchestrator can classify by design **without** needing a security/product call, do that in the triage table immediately — do not escalate just to ask for a rationale.

After a successful fix, append the finding to `closed_findings` with `status: "fixed"` **and** a non-empty `fix_shape` (persists to the durable PR ledger immediately).

## External threads

Pre-existing Copilot or human threads (origin `external`) go through the same matrix. They are never acted on before the round-1 review finishes.

## Triage table shape

```markdown
| # | Origin | Location | Severity | Category | Finding | Decision | Rationale |
|---|---|---|---|---|---|---|---|
| 1 | loop | path:line | Medium | logic | ... | Fix | unambiguous null check |
| 2 | loop | path:line | Low | code-style | ... | Defer | below manage_severity=medium |
| 3 | loop | path:line | Medium | best-practices | ... | Defer (diminishing returns) | round≥2, below diminishing_returns_floor=high |
| 4 | loop | path:line | High | security | ... | Fix | clear missing dispose / no design ambiguity |
| 5 | loop | path:line | High | logic | ... | Fix | disable UI until hydrated (conservative) |
| 6 | loop | path:line | High | security | ... | Escalate → recommend By design or Fix | unclear if role should keep SELECT |
| 7 | loop | other.ts:1 | Medium | best-practices | ... | Defer (post-fix verify) | outside verify surface after fixes |
| 8 | external | path:line | Medium | best-practices | ... | By design | intentional … |
```

## Decision order (orchestrator)

1. Closed-finding filter (drop re-reports; keep `recurrence` / `contested` open via `filter_open_findings`).
2. **Post-fix verify filter** (`filter_post_fix_findings`) when `has_fixed_this_run` — outside surface (non-Critical) → **Defer (post-fix verify)**; never Fix. Critical outside surface stays in keep for Escalate.
3. **Anti-thrash path guard:** if `_loop_state.is_contested_against_ledger(finding, state)` (path already closed as `fixed` with a non-empty `fix_shape`) → tag `Source: contested` / **Escalate once** with both shapes — **never** `Decision: Fix`. Do not silently reverse a prior deliberate fix.
4. Below `manage_severity` → **Defer**.
5. Round ≥ `diminishing_returns_round` and severity below `diminishing_returns_floor` → **Defer (diminishing returns)** — same `closed_findings` / `status: deferred` as the severity floor; tag rationale with the round + floor (use `_loop_state.should_defer_for_diminishing_returns`).
6. `Source: recurrence` or `Source: contested` → **Escalate once** (never auto-fix / never reverse a deliberate fix shape). After the user decides, append to `closed_findings` with the decided shape so it cannot reopen.
7. Unambiguous must-fix (Recommend would be Fix) → **Fix** (any severity) — including migrations/hydration/data-loss with a clear shape. `Source: regression` in-surface → Fix.
8. Clear intentional trade-off → **By design**.
9. Real design/policy **ambiguity** or infra/budget → **Escalate**.

After a successful fixer report, `append_closed_finding(..., status="fixed", fix_shape=<What changed / Why>)` is **required**. Empty `fix_shape` on `status=fixed` is a process bug (breaks anti-thrash).
