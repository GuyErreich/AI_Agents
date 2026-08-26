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


def main() -> int:
    """Block dangerous git ops while the review loop is active."""
    event = read_stdin_json()
    command = str(event.get("command") or "")
    state = load_state()

    if not is_active(state):
        allow()
        return 0

    if FORCE_PUSH.search(command):
        deny(
            "Force-push is forbidden during the PR review loop.",
            "Git guard denied force-push.",
        )
        return 0

    if PUSH_PROTECTED.search(command):
        deny(
            "Pushing to dev/main/master is forbidden during the PR review loop.",
            "Git guard denied push to protected branch.",
        )
        return 0

    if state.get("escalation_pending") and (
        COMMIT_RE.search(command) or PUSH_RE.search(command)
    ):
        deny(
            "Escalation pending — commit/push blocked until you resolve it.",
            "Git guard denied commit/push while escalation_pending.",
        )
        return 0

    # Non-git commands: allow. Ambiguous git: ask.
    if command.strip().startswith("git ") and not (
        COMMIT_RE.search(command) or PUSH_RE.search(command)
    ):
        allow()
        return 0

    if not command.strip():
        ask("Empty shell command during review loop — confirm before continuing.")
        return 0

    allow()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
