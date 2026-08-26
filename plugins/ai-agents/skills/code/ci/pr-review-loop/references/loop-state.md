# Loop State

Runtime files under `.review-loop/` at the repo root (gitignored — **not** under `.cursor/`, so writes do not trigger Cursor permission prompts):

| File | Role |
|---|---|
| `state.json` | This run’s ledger (rounds, costs, active flag) — reset each loop start |
| `preferences.json` | **Durable** caps/models across runs — never reset to factory on preflight |
| `pricing.json` | Local pricing table (bootstrapped from the skill asset) |
| `closed-ledger.json` | Per-PR durable closed / accepted memory |
| `review-lock.json` | Optional review-dedup fingerprints |

On first access, files under the legacy `.cursor/review-loop/` (and `.cursor/review-lock.json`) are copied into `.review-loop/` when the new path is missing.

## Preferences (durable)

```json
{
  "max_rounds": null,
  "max_tokens_est": 1000000,
  "max_usd_est": 2.0,
  "pricing_mode": "auto",
  "reviewer_model": "inherit",
  "fixer_model": "inherit",
  "clean_passes_required": 2,
  "manage_severity": "medium",
  "post_fix_focus": "delta",
  "diminishing_returns_round": 2,
  "diminishing_returns_floor": "high",
  "analysis_mode": "review"
}
```

| Key | Default | Purpose |
|---|---|---|
| `manage_severity` | `medium` | Minimum finding severity the loop manages (`low` \| `medium` \| `high` \| `critical`). Below → Defer (see `triage-policy.md`). |
| `post_fix_focus` | `delta` | Reviewer focus after a fixer round (`delta` \| `full`). |
| `diminishing_returns_round` | `2` | Round at/after which lingering findings below `diminishing_returns_floor` are deferred as follow-ups. |
| `diminishing_returns_floor` | one tier above `manage_severity` (capped at `critical`) | Minimum severity still fixed/escalated after the ratchet round. Fully overridable. |
| `analysis_mode` | `review` | Prompt-level reviewer stance (`review` \| `debug-like` \| `security`). **Not** Cursor's Agent/Plan/Debug UI mode. See `code/review/reviewer` → `analysis-modes.md`. |

Preflight **must** call `review_loop_init.py` (or `start_loop_state`) so a prior `max_rounds: null` (budget-only) is not overwritten with `3`. Only missing keys take factory defaults; invocation `overrides` update both preferences and the new state.

Invocation overrides: `manage medium` / `manage high` / `only critical` / `manage_severity=high` / `post_fix_focus=full` / `focus delta` / `diminishing after round 3` / `diminishing_returns_round=5` / `diminishing_returns_floor=high` / `analysis debug` / `analysis_mode=security` / `debug-like review`.

## State schema (per run)

```json
{
  "active": false,
  "pr_number": 0,
  "pr_url": "",
  "branch": "",
  "started_at": "",
  "pricing_mode": "auto",
  "reviewer_model": "inherit",
  "fixer_model": "inherit",
  "next_model": "inherit",
  "max_rounds": 3,
  "max_tokens_est": 1000000,
  "max_usd_est": 2.0,
  "clean_passes_required": 2,
  "manage_severity": "medium",
  "post_fix_focus": "delta",
  "diminishing_returns_round": 2,
  "diminishing_returns_floor": "high",
  "analysis_mode": "review",
  "round": 0,
  "escalation_pending": false,
  "toolchain_mode": "uv",
  "pricing_updated": "",
  "last_fingerprint": "",
  "last_validate_fingerprint": "",
  "last_lint": "",
  "last_build": "",
  "last_clean_fingerprint": "",
  "last_outcome": "",
  "seeded_from_ledger": false,
  "accepted_by_design": [],
  "closed_findings": [],
  "consecutive_clean_passes": 0,
  "escalations": [],
  "rounds": [],
  "totals": {
    "tokens_est": 0,
    "usd_est": 0,
    "turns": 0,
    "tool_calls": 0,
    "wall_clock_s": 0
  }
}
```

### Init-once validate fields

| Field | Meaning |
|---|---|
| `last_validate_fingerprint` | PR fingerprint from last successful Validate suite |
| `last_lint` / `last_build` | Opaque Validate-suite pass/fail slots (`pass` \| `fail` \| `""`). Success means **all** `AGENT.md` Validate commands passed. |

Orchestrator runs baseline validate at preflight; fixer updates after commit validate. Reviewers skip phase 9 when `validate_still_fresh(state, current_fp)` is true — including `full` / `confirm`.

### Role models

| Field | Default | Purpose |
|---|---|---|
| `reviewer_model` | `inherit` | Task `model` for every `pr-reviewer` launch |
| `fixer_model` | `inherit` | Task `model` for every `pr-fixer` launch |
| `next_model` | (set before launch) | Hint for the budget hook's cold/projection path |

`inherit` / `auto` follow the parent chat (Cursor Auto when the parent is on Auto) — **cheap by default**. Named frontier slugs cost more; estimate those segments at api-ish rates without flipping loop caps to `api` unless the user asks.

#### Aliases (user phrase → Task slug)

| Phrase | Task `model` |
|---|---|
| `auto`, `inherit`, `composer` | `inherit` |
| `opus`, `opus-5` | `claude-opus-5-thinking-high` |
| `sonnet`, `sonnet-5` | `claude-sonnet-5-thinking-high` |
| `fast` | `composer-2.5-fast` |
| exact Task slug | passed through when recognized |

Override examples: `review with opus, fix with auto` · `reviewer_model=opus fixer_model=inherit`.

`pricing_mode` (loop **caps** only):

| Mode | When | Effect |
|---|---|---|
| `auto` (default) | Always, unless user says otherwise | Cheap $/MTok table for Auto segments; defaults `max_tokens_est=1_000_000`, `max_usd_est=2` |
| `api` | User override only (`pricing api`) | API-like list rates for caps; defaults `max_tokens_est=400_000`, `max_usd_est=3` |

Token estimates are mode-invariant (same transcript math). Dollar estimates for a **named** reviewer/fixer segment use api-ish rates even when `pricing_mode` stays `auto`, so projective checks stay honest without defaulting everyone into expensive caps.

### Round entry

```json
{
  "n": 1,
  "focus": "full",
  "counted_clean": false,
  "started_at": "",
  "reviewer_started_at": "",
  "fixer_started_at": "",
  "findings": [],
  "new_signatures": [],
  "fixed": [],
  "accepted": [],
  "escalated": [],
  "commit_shas": [],
  "lint": "pass|fail|skip",
  "build": "pass|fail|skip",
  "fingerprint": "",
  "cost": {
    "tokens_in_est": 0,
    "tokens_out_est": 0,
    "tokens_est": 0,
    "usd_est": 0,
    "turns": 0,
    "tool_calls": 0,
    "wall_clock_s": 0,
    "model": "",
    "assumptions": ""
  }
}
```

`counted_clean` is `true` only when this review had zero open findings, coverage OK, **and** focus was `full` or `confirm` (`_loop_state.apply_clean_pass`). A clean `delta` is fix-verified (`counted_clean: false`) and does **not** increment `consecutive_clean_passes`.

`started_at` / `reviewer_started_at` / `fixer_started_at` on the round entry (and loop-level `started_at`) are **informational / debug only**. Cost accounting does **not** require the orchestrator to stamp them.

### Cost accounting (authoritative inputs)

| Source | Field | Role |
|---|---|---|
| `subagentStart` hook | `subagent_model` | Model actually used for this launch |
| `subagentStart` hook → state | `_pending_subagent` | Internal bridge: `{type, model, started_at}` written on allow; cleared on stop. Trusted only when `type` matches the stop event's `subagent_type` |
| `subagentStop` hook | `agent_transcript_path` | Exact transcript file to estimate — preferred over any filesystem mtime scan |
| `subagentStop` hook | `duration_ms`, `message_count`, `tool_call_count` | Ground-truth wall clock / turns / tool calls (override transcript re-parse when present) |
| `subagentStop` hook | `status` | `completed` \| `error` \| `aborted` — non-completed stops still record cost but follow-up advises retry/escalate, not normal triage |
| Fallback only | round `*_started_at` / loop `started_at` | Cutoff for the mtime scan when `agent_transcript_path` is missing/unreadable |

`_pending_subagent` is hook-owned — do not invent it from orchestrator prose. After ≥1 completed loop subagent, `totals.tokens_est` / `usd_est` must be > 0 and `project_next_cost` must leave cold defaults.

Internal hook-bridge fields (not orchestrator-written):

| Field | Role |
|---|---|
| `_pending_subagent` | Start→stop cost bridge (see above) |
| `_cost_warnings` | Appended when a completed stop yields 0 tokens with a discovery miss (`no transcripts found`). Prefixed onto the `subagentStop` follow-up message so the orchestrator/user sees it immediately |
| `_last_round_hook_at` | Dedup guard when user + project hooks both fire |

### Finding signature

Stable id for dedup across rounds: `sha256(path + "|" + normalized_finding_text)[:16]`. Store on each finding as `signature`.

### Closed findings (do not re-poop)

Every finding that was **fixed**, **accepted by design**, or **deferred** is appended here. Memory is **durable across loop runs** for the same PR via `.review-loop/closed-ledger.json` (gitignored with the rest of `.review-loop/`).

```json
{
  "signature": "...",
  "location": "path:line",
  "finding": "...",
  "status": "fixed|accepted|deferred",
  "closed_in_round": 2,
  "rationale": "optional — required when status is accepted",
  "fix_shape": "required when status=fixed — what the fixer changed; used to detect contested reverse-fixes"
}
```

#### Durable PR ledger (`closed-ledger.json`)

```json
{
  "by_pr": {
    "60": {
      "pr_number": 60,
      "branch": "feature/…",
      "updated_at": "…",
      "last_clean_fingerprint": "abc…",
      "last_outcome": "confirmed_clean|stopped|escalation",
      "closed_findings": [],
      "accepted_by_design": []
    }
  }
}
```

Helpers (`_loop_state`):

| Helper | Role |
|---|---|
| `load_pr_closed_memory` / `merge_closed_memory` | Read / idempotent write of the PR entry |
| `mark_run_outcome(state, outcome, fingerprint)` | Persist exit outcome + clean fingerprint |
| `should_short_circuit_confirm(state, fingerprint)` | Prior `confirmed_clean` at same fingerprint → round-1 `confirm` |
| `fix_ledger_entries` / `format_fix_ledger_for_prompt` | Compact table for every reviewer/fixer launch |
| `finding_path` / `is_contested_against_ledger` | Path-level anti-thrash: prior `fix_shape` → escalate, never Fix |
| `has_fixed_this_run` / `verify_surface_paths` / `filter_post_fix_findings` | Post-fix verify: after first fix, defer drive-bys outside surface |
| `append_closed_finding(..., fix_shape=)` | Closes a finding **and** merges into the durable ledger immediately |

`start_loop_state` seeds `closed_findings` / `accepted_by_design` from the ledger (dedupe by signature), sets `seeded_from_ledger`, and copies `last_clean_fingerprint` / `last_outcome` when present.

Orchestrator rules:

1. After each fix, by-design decision, or severity-floor / diminishing-returns defer, append via `append_closed_finding` (and to `accepted_by_design` when status is `accepted`). **`fix_shape` is required** from the fixer's "What changed / Why" when status is `fixed` — empty is a process bug.
2. Pass the full `closed_findings` list **and** `format_fix_ledger_for_prompt(state)` into every `pr-reviewer` and `pr-fixer` launch.
3. Before triage, drop re-reports via `filter_open_findings`. Then run `filter_post_fix_findings` when fixes exist — defer drive-bys outside the verify surface. Then run `is_contested_against_ledger` — if true, escalate contested; never auto-fix the opposite shape.
4. Exceptions that stay open for one escalation — **recurrence** and **contested**. Never auto-fix either in a loop. After the user decides, append with the decided shape so it cannot reopen.
5. On confirmed clean / stop / escalation exit, call `mark_run_outcome`.

### Post-fix verify mode

When `has_fixed_this_run(state)` is true:

- Confirm / delta **M** = `verify_surface_paths(state, fixer_paths)` (fixed paths ∪ last fixer diff ∪ one-hop dependents), not the whole branch.
- Orchestrator must call `filter_post_fix_findings` after `filter_open_findings` and append deferred rows with rationale `post-fix verify`.
- Critical outside the surface stays in keep (escalate); Medium/Low/High drive-bys outside surface are deferred.

### Accepted-by-design entry

```json
{ "signature": "...", "location": "path:line", "finding": "...", "rationale": "..." }
```

`accepted_by_design` remains the rationale store for by-design keeps; those signatures also appear in `closed_findings` with `status: "accepted"`. Severity-floor skips and diminishing-returns skips use `status: "deferred"` (rationale should note which).

## Defaults and overrides

| Cap / field | Default (`auto`) | Default (`api` caps) | Override example |
|---|---|---|---|
| `pricing_mode` | `auto` | `api` | "pricing api" / "use Auto rates" |
| `reviewer_model` | `inherit` | `inherit` | "review with opus" |
| `fixer_model` | `inherit` | `inherit` | "fix with auto" |
| `max_rounds` | 3 | 3 | `"max 2 rounds"` · **budget-only / unlimited rounds:** `0`, `null`, `"none"`, `"unlimited"`, or `"budget-only"` |
| `max_tokens_est` | 1000000 | 400000 | "budget 200k tokens" |
| `max_usd_est` | 2.00 | 3.00 | "budget $1.50" |
| `clean_passes_required` | 2 | 2 | `"1 clean pass"` (faster, riskier) / `"3 clean passes"` |
| `post_fix_focus` | `delta` | `delta` | `"post_fix_focus=full"` to restore full review after every fixer |
| `diminishing_returns_round` | 2 | 2 | `"diminishing after round 3"` / `diminishing_returns_round=5` |
| `diminishing_returns_floor` | one above `manage_severity` | one above `manage_severity` | `diminishing_returns_floor=high` / `diminishing_returns_floor=critical` |
| `analysis_mode` | `review` | `review` | `"analysis debug"` / `analysis_mode=security` / `"debug-like review"` — prompt stance only, not Cursor UI Debug |

When `max_rounds` is unlimited, stop conditions are **budget + consecutive clean reviews** — the loop may run round 4+ until projected spend would cross the token/USD caps, or until `consecutive_clean_passes >= clean_passes_required`. Do **not** stop on a single clean review, “no new signatures”, or fingerprint alone. After `diminishing_returns_round`, findings below `diminishing_returns_floor` are deferred (follow-ups) and do not block clean.

`analysis_mode` reshapes how `pr-reviewer` investigates (evidence bar / threat emphasis). Pair `analysis debug` with `reviewer_model=opus` for hardest analysis. It never switches Cursor's Agent/Plan/Debug chat mode.

## Round focus (reviewer → developer until zero)

Default cycle: **full → (fix) → delta → … → confirm**. Success is **`clean_passes_required` consecutive counted** reviews with zero **open** findings (default 2). Only `full` / `confirm` may increment `consecutive_clean_passes`.

| When | Focus | Scope |
|---|---|---|
| Round 1 (default) | `full` | Whole branch diff — all applicable phases. No mandatory re-lint if init validate fingerprint still matches. |
| Round 1 when `should_short_circuit_confirm` | `confirm` | Prior run confirmed clean at this fingerprint — confirm only; if clean, meet `clean_passes_required` and stop |
| After a fixer | `post_fix_focus` (default `delta`) | **Post-fix verify** — fixer diff + hotspots + fixed paths + one-hop dependents; not a new full-PR survey |
| After a clean `delta` (fix verified) | `confirm` | Verify surface only when fixes exist (thoroughness-pass confirm M); narrow clean does not count toward consecutive cleans |
| After first counted clean | `confirm` | Verify fixed hotspots + surface; only concrete reproducible defects (thoroughness-pass §5) |
| Coverage fail / out-of-hotspot issues | `full` | One recovery full pass |
| User override | `full` / `delta` / `confirm` | Invocation wins |

Use `_loop_state.resolve_round_focus(...)` (pass `last_focus` / `last_round_clean` after a clean delta). Do **not** force `full` every round.

Orchestrator rule: `focus = resolve_round_focus(...)` unless the user overrode focus for this launch.
## Projective budget check

Alert **before** spending — never start a loop/round that is already projected over cap.

### Preflight (before `active: true` / before round 1)

1. Resolve caps and role models.
2. Cold-project the first reviewer launch (`cold_projection` / mode defaults; named `reviewer_model` raises USD projection).
3. If projected tokens or USD exceed caps → escalate (spent=0 / projected / cap) and **stop**. Do not set `active` or launch Task.

### Before every subagent when `active` (orchestrator + `subagentStart` hook)

1. If `escalation_pending` → deny.
2. If `max_rounds` is set (not unlimited) and `round > max_rounds` → deny (the final allowed round, `round == max_rounds`, must still run — including its fixer). Unlimited / budget-only: skip this check.
3. Projected next cost = max(last round cost, running average of round costs), or cold projection when no rounds yet. If `totals + projected` crosses `max_tokens_est` or `max_usd_est` → deny and escalate with spent / projected / cap.
4. Unchanged fingerprint does **not** block `pr-reviewer` (re-scan for false cleans / recurrence). Unchanged fingerprint after a fix **does** block another `pr-fixer` — escalate instead.

In degraded toolchain mode the orchestrator applies the same checks from `state.json` itself.

## Hook scoping

`subagentStart` / `subagentStop` are registered globally but filtered:

1. **hooks.json `matcher`:** `pr-reviewer|pr-fixer` — Cursor never invokes the scripts for `explore`, `shell`, `generalPurpose`, etc.
2. **In-code guard:** even if the matcher is missing, scripts no-op unless `subagent_type` is a loop agent **and** `state.active` is true.
3. **Git guard** (`beforeShellExecution`) uses `matcher: git` and still only enforces when `active: true` (scoped consent / no force-push to protected branches during a loop).

## Fingerprint

```bash
python3 scripts/review-lock.py fingerprint pr --json
```

Store the `fingerprint` field on each round and as `last_fingerprint`.
