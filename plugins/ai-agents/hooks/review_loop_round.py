#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""subagentStop round accounting for the PR review loop."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _cost import CostEstimate, estimate_since, project_next_cost  # noqa: E402
from _loop_state import (  # noqa: E402
    emit,
    is_active,
    is_loop_subagent,
    load_pricing,
    load_state,
    loop_subagent_type,
    now_iso,
    read_stdin_json,
    resolve_max_rounds,
    save_state,
)


def resolve_clean_passes_required(state: dict[str, Any]) -> int:
    """How many consecutive clean full reviews are required before success stop."""
    raw = state.get("clean_passes_required", 2)
    try:
        value = int(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 2
    return max(1, value)


def _pending_matches_event(
    pending: dict[str, Any] | None,
    event: dict[str, Any],
) -> bool:
    """True when ``_pending_subagent.type`` matches this stop's subagent type."""
    if not pending:
        return False
    return str(pending.get("type") or "") == loop_subagent_type(event)


def _cost_warning_prefix(state: dict[str, Any]) -> str:
    """Format any pending cost-accounting warnings for the follow-up message."""
    warnings_raw = state.get("_cost_warnings")
    if not isinstance(warnings_raw, list) or not warnings_raw:
        return ""
    latest = str(warnings_raw[-1] or "").strip()
    if not latest:
        return ""
    return f"WARNING: {latest} "


def decide_round_followup(state: dict[str, Any], event: dict[str, Any] | None = None) -> str:
    """Advise the orchestrator after a loop subagent stops.

    Do **not** declare success from an empty ``findings`` list here — the
    orchestrator usually writes findings *after* subagentStop, so an empty
    list would false-trigger "passed". Success is consecutive clean reviews
    recorded by the orchestrator per the skill (default 2) or budget/escalation.
    """
    event = event or {}
    warn = _cost_warning_prefix(state)
    if state.get("escalation_pending"):
        return (
            warn
            + "PR review loop: escalation pending — pause and alert the user. "
            "Do not start another subagent."
        )

    round_n = int(state.get("round", 0) or 0)
    max_rounds = resolve_max_rounds(state)
    totals_raw = state.get("totals")
    totals: dict[str, Any] = totals_raw if isinstance(totals_raw, dict) else {}
    proj_t, proj_u = project_next_cost(state)
    spent_t = float(totals.get("tokens_est", 0) or 0)
    spent_u = float(totals.get("usd_est", 0) or 0)
    max_t = float(state.get("max_tokens_est", 400_000) or 400_000)
    max_u = float(state.get("max_usd_est", 3.0) or 3.0)
    required = resolve_clean_passes_required(state)
    consecutive = int(state.get("consecutive_clean_passes", 0) or 0)
    sub = loop_subagent_type(event)

    status = str(event.get("status") or "completed").strip().lower() or "completed"
    if status != "completed":
        return (
            warn
            + f"PR review loop: {sub or 'subagent'} stopped with status={status} "
            "(not completed) — do not treat as a normal review/fix result. "
            "Retry once with a fresh subagent, or escalate if it fails again."
        )

    if spent_t + proj_t > max_t or spent_u + proj_u > max_u:
        return (
            warn
            + "PR review loop: projected spend would exceed budget — "
            f"spent≈{spent_t:.0f} tok / ${spent_u:.2f}; "
            f"projected next≈{proj_t:.0f} tok / ${proj_u:.2f}; "
            f"caps={max_t:.0f} tok / ${max_u:.2f}. Escalate to the user, "
            "then write the canvas if they stop."
        )

    if max_rounds is not None and round_n > max_rounds:
        return (
            warn
            + "PR review loop: round cap reached — write the summary canvas "
            "and set active=false."
        )

    if consecutive >= required:
        return (
            warn
            + f"PR review loop: {consecutive}/{required} consecutive clean "
            "full reviews already recorded — write the summary canvas and "
            "set active=false."
        )

    if sub == "pr-reviewer":
        return (
            warn
            + "PR review loop: reviewer finished — collect the findings table "
            "into state, apply the closed-finding filter, then: "
            "(1) if open findings remain → triage + pr-fixer; "
            f"(2) if zero open findings → bump consecutive_clean_passes "
            f"(now {consecutive}/{required}) and launch another full "
            "pr-reviewer until consecutive cleans hit the requirement OR "
            "budget/escalation; "
            "(3) never stop on a single clean pass; never treat "
            "same-signature leftovers as passed — escalate recurrence."
        )

    if sub == "pr-fixer":
        return (
            warn
            + "PR review loop: fixer finished — reset is not needed here; "
            "launch a fresh full pr-reviewer for the next round. Keep looping "
            f"until {required} consecutive clean reviews or budget/escalation."
        )

    return (
        warn
        + "PR review loop: continue — launch the next subagent per the skill. "
        f"Success requires {required} consecutive clean full reviews (or "
        "budget/escalation), not a single clean pass."
    )


def _resolve_model_for_cost(
    state: dict[str, Any],
    event: dict[str, Any],
    pending: dict[str, Any] | None,
    rounds: list[Any],
) -> tuple[str, bool]:
    """Pick the model slug for this stop's cost estimate.

    Returns ``(model, pending_type_mismatch)``. Pending model is trusted only
    when ``pending.type`` matches the stop event's subagent type.
    """
    mismatch = False
    if pending and pending.get("model"):
        if _pending_matches_event(pending, event):
            return str(pending["model"]), False
        mismatch = True

    # Hook payloads: prefer subagent_model (subagentStart) over parent model.
    if event.get("subagent_model"):
        return str(event["subagent_model"]), mismatch

    model = str(event.get("model") or state.get("next_model") or "inherit")
    if rounds and isinstance(rounds[-1], dict):
        latest = rounds[-1]
        fixer_at = str(latest.get("fixer_started_at") or "")
        reviewer_at = str(latest.get("reviewer_started_at") or "")
        if fixer_at and (not reviewer_at or fixer_at >= reviewer_at):
            return (
                str(
                    event.get("model")
                    or state.get("fixer_model")
                    or state.get("next_model")
                    or "inherit"
                ),
                mismatch,
            )
        return (
            str(
                event.get("model")
                or state.get("reviewer_model")
                or state.get("next_model")
                or "inherit"
            ),
            mismatch,
        )
    return model, mismatch


def _resolve_started_at(
    state: dict[str, Any],
    event: dict[str, Any],
    pending: dict[str, Any] | None,
    rounds: list[Any],
) -> str:
    """Cutoff for the mtime-scan fallback when agent_transcript_path is absent."""
    if pending and pending.get("started_at") and _pending_matches_event(pending, event):
        return str(pending["started_at"])

    started = ""
    if rounds and isinstance(rounds[-1], dict):
        latest = rounds[-1]
        started = str(
            latest.get("fixer_started_at")
            or latest.get("reviewer_started_at")
            or latest.get("started_at")
            or ""
        )
    if not started:
        started = str(state.get("started_at") or "")
    return started or now_iso()


def _apply_event_ground_truth(
    cost: CostEstimate,
    event: dict[str, Any],
    *,
    pending_mismatch: bool,
) -> CostEstimate:
    """Overlay wall_clock / turns / tool_calls from the stop event when present."""
    assumptions = cost.assumptions
    notes: list[str] = []
    if pending_mismatch:
        notes.append("_pending_subagent type mismatch (stale)")

    wall = cost.wall_clock_s
    duration_raw = event.get("duration_ms")
    if isinstance(duration_raw, int | float) and float(duration_raw) >= 0:
        wall = float(duration_raw) / 1000.0
        notes.append("wall_clock_s from duration_ms")

    turns = cost.turns
    msg_raw = event.get("message_count")
    if isinstance(msg_raw, int | float) and int(msg_raw) >= 0:
        turns = int(msg_raw)
        notes.append("turns from message_count")

    tool_calls = cost.tool_calls
    tools_raw = event.get("tool_call_count")
    if isinstance(tools_raw, int | float) and int(tools_raw) >= 0:
        tool_calls = int(tools_raw)
        notes.append("tool_calls from tool_call_count")

    if notes:
        extra = "; ".join(notes)
        assumptions = f"{assumptions}; {extra}" if assumptions else extra

    return CostEstimate(
        tokens_in_est=cost.tokens_in_est,
        tokens_out_est=cost.tokens_out_est,
        tokens_est=cost.tokens_est,
        usd_est=cost.usd_est,
        turns=turns,
        tool_calls=tool_calls,
        wall_clock_s=wall,
        model=cost.model,
        assumptions=assumptions,
        known_model=cost.known_model,
        pricing_mode=cost.pricing_mode,
    )


def _maybe_warn_zero_cost(
    state: dict[str, Any],
    event: dict[str, Any],
    cost: CostEstimate,
) -> None:
    """Append a loud warning when completed subagent accounting found nothing."""
    status = str(event.get("status") or "completed").strip().lower() or "completed"
    if status != "completed" or cost.tokens_est > 0:
        return
    assumptions = str(cost.assumptions or "").lower()
    # Only warn on genuine discovery misses — not tiny legitimate estimates.
    if "no transcripts found" not in assumptions:
        return

    warning = (
        "cost accounting returned 0 tokens for a completed loop subagent "
        f"({loop_subagent_type(event) or 'unknown'}) — check agent_transcript_path "
        "and transcript discovery"
    )
    warnings = state.setdefault("_cost_warnings", [])
    if not isinstance(warnings, list):
        warnings = []
        state["_cost_warnings"] = warnings
    warnings.append(warning)


def record_round_cost(
    state: dict[str, Any],
    event: dict[str, Any],
    pricing: dict[str, Any],
) -> CostEstimate:
    """Accumulate cost for a finished loop subagent into ``state``.

    Prefers ``event["agent_transcript_path"]`` and ``state["_pending_subagent"]``
    (written by ``subagentStart``) so accounting does not depend on the
    orchestrator stamping ``*_started_at``. Mutates ``state`` in place —
    clears ``_pending_subagent`` after consuming it. Returns the estimate
    just recorded.
    """
    rounds_raw = state.get("rounds")
    rounds: list[Any] = rounds_raw if isinstance(rounds_raw, list) else []

    pending_raw = state.get("_pending_subagent")
    pending: dict[str, Any] | None = (
        pending_raw if isinstance(pending_raw, dict) else None
    )

    model, pending_mismatch = _resolve_model_for_cost(state, event, pending, rounds)
    started = _resolve_started_at(state, event, pending, rounds)
    transcript = event.get("agent_transcript_path")
    transcript_path = str(transcript).strip() if transcript else None

    cost = estimate_since(
        pricing,
        started_at_iso=started,
        model=model,
        state=state,
        transcript_path=transcript_path or None,
    )
    cost = _apply_event_ground_truth(cost, event, pending_mismatch=pending_mismatch)
    _maybe_warn_zero_cost(state, event, cost)
    cost_dict = cost.to_dict()

    totals = state.setdefault("totals", {})
    if not isinstance(totals, dict):
        totals = {}
        state["totals"] = totals
    totals["tokens_est"] = float(totals.get("tokens_est", 0) or 0) + cost.tokens_est
    totals["usd_est"] = round(float(totals.get("usd_est", 0) or 0) + cost.usd_est, 4)
    totals["turns"] = int(totals.get("turns", 0) or 0) + cost.turns
    totals["tool_calls"] = int(totals.get("tool_calls", 0) or 0) + cost.tool_calls
    totals["wall_clock_s"] = round(
        float(totals.get("wall_clock_s", 0) or 0) + cost.wall_clock_s, 3
    )

    if rounds and isinstance(rounds[-1], dict):
        existing = rounds[-1].get("cost")
        if isinstance(existing, dict) and existing.get("tokens_est"):
            rounds[-1]["cost"] = {
                "tokens_in_est": int(existing.get("tokens_in_est", 0) or 0)
                + cost.tokens_in_est,
                "tokens_out_est": int(existing.get("tokens_out_est", 0) or 0)
                + cost.tokens_out_est,
                "tokens_est": int(existing.get("tokens_est", 0) or 0) + cost.tokens_est,
                "usd_est": round(
                    float(existing.get("usd_est", 0) or 0) + cost.usd_est, 4
                ),
                "turns": int(existing.get("turns", 0) or 0) + cost.turns,
                "tool_calls": int(existing.get("tool_calls", 0) or 0) + cost.tool_calls,
                "wall_clock_s": round(
                    float(existing.get("wall_clock_s", 0) or 0) + cost.wall_clock_s, 3
                ),
                "model": cost.model,
                "assumptions": cost.assumptions,
            }
        else:
            rounds[-1]["cost"] = cost_dict

    state.pop("_pending_subagent", None)
    return cost


def main() -> int:
    """Record cost for a finished subagent and advise the parent on next steps."""
    event = read_stdin_json()
    state = load_state()
    if not is_active(state) or not is_loop_subagent(event):
        emit({})
        return 0

    # User + project hooks can both fire; skip a duplicate within 2s.
    last_hook = str(state.get("_last_round_hook_at") or "")
    if last_hook:
        try:
            from datetime import datetime

            elapsed = (
                datetime.fromisoformat(now_iso().replace("Z", "+00:00"))
                - datetime.fromisoformat(last_hook.replace("Z", "+00:00"))
            ).total_seconds()
            if 0 <= elapsed < 2.0:
                emit({})
                return 0
        except ValueError:
            pass
    state["_last_round_hook_at"] = now_iso()

    pricing = load_pricing()
    record_round_cost(state, event, pricing)
    save_state(state)

    emit({"followup_message": decide_round_followup(state, event)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
