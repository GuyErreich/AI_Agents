#!/usr/bin/env python3
# Copyright (c) 2026 Guy Erreich
#
# SPDX-License-Identifier: MIT

# /// script
# requires-python = ">=3.12"
# ///


"""beforeShellExecution git guard for the PR review loop."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _loop_state import (  # noqa: E402
    allow,
    ask,
    deny,
    is_active,
    load_state,
    read_stdin_json,
)
from _types import JsonObject, as_object  # noqa: E402

FORCE_PUSH = re.compile(
    r"\bgit\s+push\b.*(--force|--force-with-lease|-f)\b",
    re.IGNORECASE,
)
PUSH_PROTECTED = re.compile(
    r"\bgit\s+push\b.*\b(origin\s+)?(dev|main|master)\b",
    re.IGNORECASE,
)
COMMIT_RE = re.compile(r"\bgit\s+commit\b", re.IGNORECASE)
PUSH_RE = re.compile(r"\bgit\s+push\b", re.IGNORECASE)


def decide(command: str, state: JsonObject) -> JsonObject:
    """Return the permission payload for ``command`` given loop ``state``.

    Args:
        command: Shell command string from the beforeShellExecution event.
        state: Current review-loop state object.

    Returns:
        A JSON permission payload (``allow`` / ``deny`` / ``ask``).
    """
    if not is_active(state):
        return {"permission": "allow"}

    if FORCE_PUSH.search(command):
        return {
            "permission": "deny",
            "user_message": "Force-push is forbidden during the PR review loop.",
            "agent_message": "Git guard denied force-push.",
        }

    if PUSH_PROTECTED.search(command):
        return {
            "permission": "deny",
            "user_message": (
                "Pushing to dev/main/master is forbidden during the PR review loop."
            ),
            "agent_message": "Git guard denied push to protected branch.",
        }

    if state.get("escalation_pending") and (
        COMMIT_RE.search(command) or PUSH_RE.search(command)
    ):
        return {
            "permission": "deny",
            "user_message": (
                "Escalation pending — commit/push blocked until you resolve it."
            ),
            "agent_message": ("Git guard denied commit/push while escalation_pending."),
        }

    # Non-git commands: allow. Ambiguous git: allow read-only git.
    if command.strip().startswith("git ") and not (
        COMMIT_RE.search(command) or PUSH_RE.search(command)
    ):
        return {"permission": "allow"}

    if not command.strip():
        return {
            "permission": "ask",
            "user_message": (
                "Empty shell command during review loop — confirm before continuing."
            ),
        }

    return {"permission": "allow"}


def main() -> int:
    """Block dangerous git ops while the review loop is active."""
    event = read_stdin_json()
    command = str(event.get("command") or "")
    state = load_state()
    payload = decide(command, as_object(state))
    permission = str(payload.get("permission") or "allow")
    if permission == "deny":
        deny(
            str(payload.get("user_message") or ""),
            str(payload["agent_message"]) if "agent_message" in payload else None,
        )
    elif permission == "ask":
        ask(str(payload.get("user_message") or ""))
    else:
        allow()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
