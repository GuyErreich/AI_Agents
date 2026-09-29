#!/usr/bin/env python3
# Copyright (c) 2026 Guy Erreich
#
# SPDX-License-Identifier: MIT

# /// script
# requires-python = ">=3.12"
# ///


"""subagentStart budget guard for the PR review loop."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# Allow importing sibling modules when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _types import (
    HookEvent,
    JsonObject,
    JsonValue,
    as_float,
    as_int,
    as_list,
    as_object,
)  # noqa: E402
from _cost import project_next_cost  # noqa: E402
from _loop_state import (  # noqa: E402
    emit,
    is_active,
    is_loop_subagent,
    load_state,
    loop_subagent_type,
    now_iso,
    read_stdin_json,
    resolve_max_rounds,
    save_state,
)


def current_pr_fingerprint() -> str:
    """Return the current pr-tier fingerprint via review-lock.py."""
    try:
        result = subprocess.run(
            ["python3", "scripts/review-lock.py", "fingerprint", "pr", "--json"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return ""
    if result.returncode != 0 or not result.stdout.strip():
        return ""
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return ""
    return str(data.get("fingerprint", "") or "")


def resolve_upcoming_model(
    state: JsonObject,
    event: HookEvent | None = None,
    *,
    extra_fallback: str | None = None,
) -> str:
    """Resolve the model slug for an upcoming / just-started loop subagent.

    Priority: ``subagent_model`` → ``model`` → ``state.next_model`` →
    optional ``extra_fallback`` (e.g. ``reviewer_model``) → ``inherit``.
    """
    event = event or {}
    return str(
        event.get("subagent_model")
        or event.get("model")
        or state.get("next_model")
        or extra_fallback
        or "inherit"
    )


def decide_subagent_start(
    state: JsonObject,
    event: HookEvent | None = None,
    *,
    fingerprint: str | None = None,
) -> JsonObject:
    """Return the permission payload for launching a loop subagent.

    Pure decision helper — unit-tested so budget regressions cannot silently
    allow over-cap spend or block the final allowed round.
    """
    event = event or {}
    # Ignore explore / generalPurpose / etc. even if a loop is active.
    if not is_loop_subagent(event):
        return {"permission": "allow"}

    if not is_active(state):
        return {"permission": "allow"}

    if state.get("escalation_pending"):
        return {
            "permission": "deny",
            "user_message": (
                "PR review loop escalation is pending — resolve it before "
                "another round."
            ),
            "agent_message": (
                "Budget hook denied subagentStart: escalation_pending=true."
            ),
        }

    round_n = as_int(state.get("round"), 0)
    max_rounds = resolve_max_rounds(state)
    rounds: list[JsonValue] = as_list(state.get("rounds"))
    if max_rounds is not None and round_n > max_rounds:
        return {
            "permission": "deny",
            "user_message": (
                f"PR review loop hit max_rounds={max_rounds}. Raise the cap or stop."
            ),
            "agent_message": "Budget hook denied subagentStart: round cap reached.",
        }

    last_fp = str(state.get("last_fingerprint", "") or "")
    if last_fp and round_n >= 1:
        current_fp = current_pr_fingerprint() if fingerprint is None else fingerprint
        if current_fp and current_fp == last_fp:
            # Never block the next full review — unchanged tree still needs
            # re-scan (false cleans / recurrence). Only block a repeated fixer
            # on the same fingerprint (nothing new to apply).
            sub = ""
            for key in ("subagent_type", "subagentType", "agent_type", "type"):
                raw = event.get(key)
                if isinstance(raw, str) and raw.strip():
                    sub = raw.strip()
                    break
            latest = rounds[-1] if rounds else None
            latest_n_raw = latest.get("n") if isinstance(latest, dict) else None
            latest_n = as_int(latest_n_raw, 0) if latest_n_raw not in (None, "") else 0
            if (
                sub == "pr-fixer"
                and isinstance(latest, dict)
                and latest.get("fixed")
                and latest_n == round_n
                and str(latest.get("focus") or "") != "confirm"
            ):
                return {
                    "permission": "deny",
                    "user_message": (
                        "PR fingerprint unchanged after a fix pass — escalate "
                        "(fix likely did not stick); do not re-launch fixer."
                    ),
                    "agent_message": (
                        "Budget hook denied pr-fixer: unchanged fingerprint after fix."
                    ),
                }

    totals = as_object(state.get("totals"))
    spent_t = as_float(totals.get("tokens_est"), 0.0)
    spent_u = as_float(totals.get("usd_est"), 0.0)

    upcoming_model = resolve_upcoming_model(
        state,
        event,
        extra_fallback=str(state.get("reviewer_model") or "") or None,
    )
    proj_t, proj_u = project_next_cost(state, model=upcoming_model)
    max_t = as_float(state.get("max_tokens_est"), 1_000_000.0)
    max_u = as_float(state.get("max_usd_est"), 2.0)

    if spent_t + proj_t > max_t or spent_u + proj_u > max_u:
        return {
            "permission": "deny",
            "user_message": (
                f"Projected spend would exceed budget. "
                f"spent≈{spent_t:.0f} tok / ${spent_u:.2f}; "
                f"projected next≈{proj_t:.0f} tok / ${proj_u:.2f}; "
                f"caps={max_t:.0f} tok / ${max_u:.2f}. "
                "Raise the budget to continue, or stop."
            ),
            "agent_message": "Budget hook denied subagentStart: projective cost cap.",
        }

    return {"permission": "allow"}


def record_subagent_start(
    state: JsonObject,
    event: HookEvent | None = None,
) -> JsonObject | None:
    """Build a ``_pending_subagent`` bridge record for an allowed loop start.

    Returns ``None`` when the event is not a loop subagent (or inactive) —
    callers must not persist anything in that case. Ground-truth model and
    start time come from the hook payload so cost accounting does not depend
    on the orchestrator stamping ``*_started_at`` into state.
    """
    event = event or {}
    if not is_active(state) or not is_loop_subagent(event):
        return None
    return {
        "type": loop_subagent_type(event),
        "model": resolve_upcoming_model(state, event),
        "started_at": now_iso(),
    }


def main() -> int:
    """Deny new subagents when loop caps or escalations block progress."""
    event = read_stdin_json()
    state = load_state()
    decision = decide_subagent_start(state, event)
    if decision.get("permission") == "allow":
        pending = record_subagent_start(state, event)
        if pending is not None:
            state["_pending_subagent"] = pending
            save_state(state)
    emit(decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
