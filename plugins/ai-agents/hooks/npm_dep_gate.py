#!/usr/bin/env python3
# Copyright (c) 2026 Guy Erreich
#
# SPDX-License-Identifier: MIT

# /// script
# requires-python = ">=3.12"
# ///

"""npm dep-file gate — mark pending on package/lock edits; force audit on stop.

Project-specific (npm). Portable reviewer/CI stay agnostic via AGENT.md Validate.
Wired for afterFileEdit, afterShellExecution, and stop via hooks.json.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _loop_state import emit, now_iso, read_stdin_json, repo_root  # noqa: E402

DEP_BASENAMES = frozenset(
    {
        "package.json",
        "package-lock.json",
        "npm-shrinkwrap.json",
    }
)

# Shell commands that rewrite the lockfile / install tree.
_DEP_MUTATE_RE = re.compile(
    r"\bnpm\s+(?:install|i|ci|update|uninstall|remove|upgrade)\b",
    re.IGNORECASE,
)
_AUDIT_RE = re.compile(r"\bnpm\s+audit\b", re.IGNORECASE)
_AUDIT_CLEAN_RE = re.compile(r"found\s+0\s+vulnerabilities", re.IGNORECASE)
_AUDIT_FAIL_RE = re.compile(
    r"(?:\d+\s+(?:high|critical)\s+severity)|(?:npm\s+ERR!)",
    re.IGNORECASE,
)

FOLLOWUP = (
    "Dependency or lockfile files changed this turn, but `npm audit` has not "
    "passed yet. Run the AGENT.md Validate audit command "
    "(`npm audit --audit-level=high`) and `npm run lint`, report raw exit "
    "codes, then stop. Do not skip."
)

STATE_REL = Path(".cursor/hooks/state/npm-dep-gate.json")


def state_path() -> Path:
    """Path to the durable pending-audit marker for this workspace."""
    return repo_root() / STATE_REL


def load_gate_state() -> dict[str, Any]:
    """Load gate state; missing or corrupt → empty defaults."""
    path = state_path()
    if not path.is_file():
        return {"pending": False, "paths": [], "audit_ok": False}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"pending": False, "paths": [], "audit_ok": False}
    if not isinstance(raw, dict):
        return {"pending": False, "paths": [], "audit_ok": False}
    paths = raw.get("paths")
    return {
        "pending": bool(raw.get("pending")),
        "paths": [str(p) for p in paths] if isinstance(paths, list) else [],
        "audit_ok": bool(raw.get("audit_ok")),
        "updated_at": str(raw.get("updated_at") or ""),
    }


def save_gate_state(state: dict[str, Any]) -> None:
    """Persist gate state under the workspace hooks state dir."""
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "pending": bool(state.get("pending")),
        "paths": list(state.get("paths") or []),
        "audit_ok": bool(state.get("audit_ok")),
        "updated_at": now_iso(),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def is_dep_path(file_path: str) -> bool:
    """True when the edited path is a root npm manifest or lockfile basename."""
    name = Path(file_path).name
    return name in DEP_BASENAMES


def mark_pending(paths: list[str]) -> None:
    """Mark that dep files changed and audit is required before stop."""
    state = load_gate_state()
    existing = {str(p) for p in state.get("paths") or []}
    existing.update(paths)
    state["pending"] = True
    state["audit_ok"] = False
    state["paths"] = sorted(existing)
    save_gate_state(state)


def clear_pending() -> None:
    """Clear the pending gate after a successful audit."""
    save_gate_state({"pending": False, "paths": [], "audit_ok": True})


def audit_succeeded(command: str, output: str) -> bool:
    """Heuristic: command was npm audit and output looks clean."""
    if not _AUDIT_RE.search(command):
        return False
    if _AUDIT_FAIL_RE.search(output) or "npm ERR!" in output:
        return False
    return bool(_AUDIT_CLEAN_RE.search(output))


def handle_after_file_edit(event: dict[str, Any]) -> None:
    """Mark pending when package.json or a lockfile is edited."""
    file_path = str(event.get("file_path") or "")
    if file_path and is_dep_path(file_path):
        mark_pending([Path(file_path).name])


def handle_after_shell(event: dict[str, Any]) -> None:
    """Mark pending on dep-mutating npm commands; clear on successful audit."""
    command = str(event.get("command") or "")
    output = str(event.get("output") or "")
    if audit_succeeded(command, output):
        clear_pending()
        return
    if _DEP_MUTATE_RE.search(command):
        mark_pending(["shell:" + command.strip()[:80]])


def handle_stop(event: dict[str, Any]) -> str | None:
    """Return a follow-up message when pending audit has not passed."""
    if str(event.get("status") or "") != "completed":
        return None
    state = load_gate_state()
    if not state.get("pending") or state.get("audit_ok"):
        return None
    # Avoid infinite nagging if the agent already got the follow-up once.
    loop_count = event.get("loop_count")
    try:
        loops = int(loop_count)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        loops = 0
    if loops >= 2:
        return None
    return FOLLOWUP


def dispatch(event: dict[str, Any]) -> dict[str, Any]:
    """Route by hook payload shape; always return a JSON-serializable object."""
    if "file_path" in event and "edits" in event:
        handle_after_file_edit(event)
        return {}
    if "command" in event and "output" in event:
        handle_after_shell(event)
        return {}
    if "status" in event and "loop_count" in event:
        msg = handle_stop(event)
        return {"followup_message": msg} if msg else {}
    return {}


def main() -> int:
    """Entrypoint for afterFileEdit / afterShellExecution / stop."""
    try:
        event = read_stdin_json()
        emit(dispatch(event if isinstance(event, dict) else {}))
    except Exception:
        # Fail open — never block the agent on gate bugs.
        emit({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
