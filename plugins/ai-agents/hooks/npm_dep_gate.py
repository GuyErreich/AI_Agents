#!/usr/bin/env python3
# Copyright (c) 2026 Guy Erreich
#
# SPDX-License-Identifier: MIT

# /// script
# requires-python = ">=3.12"
# ///

"""Dependency audit gate — npm and uv; force audit on stop after dep edits.

Marks pending when real package manifests/lockfiles change, or when a primary
npm/uv mutate command runs. Ignores ``npm install`` text inside HEREDOCs /
quoted strings (e.g. ``gh issue create`` bodies). On stop, asks for the
matching ecosystem audit (npm or uv). Portable reviewer/CI stay agnostic via
AGENT.md Validate.

Wired for afterFileEdit, afterShellExecution, and stop via hooks.json.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Literal

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _loop_state import emit, now_iso, read_stdin_json, repo_root  # noqa: E402

Ecosystem = Literal["npm", "uv"]

NPM_BASENAMES = frozenset(
    {
        "package.json",
        "package-lock.json",
        "npm-shrinkwrap.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "bun.lock",
        "bun.lockb",
    }
)
UV_BASENAMES = frozenset(
    {
        "uv.lock",
        "pyproject.toml",
    }
)

# Primary-command mutators (matched after stripping quotes / heredocs).
_NPM_MUTATE_RE = re.compile(
    r"(?:^|[\n;&|])\s*(?:sudo\s+)?npm\s+(?:install|i|ci|update|uninstall|remove|upgrade)\b",
    re.IGNORECASE | re.MULTILINE,
)
_UV_MUTATE_RE = re.compile(
    r"(?:^|[\n;&|])\s*(?:sudo\s+)?uv\s+"
    r"(?:add|remove|lock|sync|pip\s+install|pip\s+uninstall)\b",
    re.IGNORECASE | re.MULTILINE,
)
_NPM_AUDIT_RE = re.compile(
    r"(?:^|[\n;&|])\s*(?:sudo\s+)?npm\s+audit\b",
    re.IGNORECASE | re.MULTILINE,
)
_UV_AUDIT_RE = re.compile(
    r"(?:^|[\n;&|])\s*(?:sudo\s+)?uv\s+audit\b",
    re.IGNORECASE | re.MULTILINE,
)
_NPM_AUDIT_CLEAN_RE = re.compile(r"found\s+0\s+vulnerabilities", re.IGNORECASE)
_NPM_AUDIT_FAIL_RE = re.compile(
    r"(?:\d+\s+(?:high|critical)\s+severity)|(?:npm\s+ERR!)|(?:ENOLOCK)",
    re.IGNORECASE,
)
# uv audit: treat explicit vulnerability counts / "vulnerable" as fail;
# clean when exit-looking text says no issues / no known vulnerabilities.
_UV_AUDIT_FAIL_RE = re.compile(
    r"(?:\b[1-9]\d*\s+vulnerabilit)|(?:\bvulnerable\b)|(?:\berror\b.*\baudit\b)",
    re.IGNORECASE,
)
_UV_AUDIT_CLEAN_RE = re.compile(
    r"(?:no\s+known\s+vulnerabilit)|(?:0\s+vulnerabilit)|(?:audited\s+\d+\s+packages?\s+with\s+0)",
    re.IGNORECASE,
)

FOLLOWUP_NPM = (
    "Dependency or lockfile files changed this turn, but `npm audit` has not "
    "passed yet. Run the AGENT.md Validate audit command "
    "(`npm audit --audit-level=high`) and `npm run lint`, report raw exit "
    "codes, then stop. Do not skip."
)
FOLLOWUP_UV = (
    "Python dependency or lockfile files changed this turn, but `uv audit` "
    "has not passed yet. Run `uv audit --frozen` (use `uv audit --upgrade` "
    "to remediate when appropriate), then the AGENT.md lint command if "
    "present, report raw exit codes, then stop. Do not skip."
)

STATE_REL = Path(".cursor/hooks/state/npm-dep-gate.json")

_HEREDOC_RE = re.compile(
    r"<<-?\s*(['\"]?)(\w+)\1.*?^\s*\2\s*$",
    re.DOTALL | re.MULTILINE,
)
_DOUBLE_QUOTE_RE = re.compile(r'"(?:\\.|[^"\\])*"', re.DOTALL)
_SINGLE_QUOTE_RE = re.compile(r"'(?:\\.|[^'\\])*'", re.DOTALL)


def state_path() -> Path:
    """Path to the durable pending-audit marker for this workspace."""
    return repo_root() / STATE_REL


def load_gate_state() -> dict[str, Any]:
    """Load gate state; missing or corrupt → empty defaults."""
    path = state_path()
    if not path.is_file():
        return {"pending": False, "paths": [], "audit_ok": False, "ecosystem": ""}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"pending": False, "paths": [], "audit_ok": False, "ecosystem": ""}
    if not isinstance(raw, dict):
        return {"pending": False, "paths": [], "audit_ok": False, "ecosystem": ""}
    paths = raw.get("paths")
    eco = str(raw.get("ecosystem") or "")
    if eco not in ("npm", "uv", ""):
        eco = ""
    return {
        "pending": bool(raw.get("pending")),
        "paths": [str(p) for p in paths] if isinstance(paths, list) else [],
        "audit_ok": bool(raw.get("audit_ok")),
        "ecosystem": eco,
        "updated_at": str(raw.get("updated_at") or ""),
    }


def save_gate_state(state: dict[str, Any]) -> None:
    """Persist gate state under the workspace hooks state dir."""
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    eco = str(state.get("ecosystem") or "")
    if eco not in ("npm", "uv"):
        eco = ""
    payload = {
        "pending": bool(state.get("pending")),
        "paths": list(state.get("paths") or []),
        "audit_ok": bool(state.get("audit_ok")),
        "ecosystem": eco,
        "updated_at": now_iso(),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def is_npm_project(root: Path | None = None) -> bool:
    """True when the workspace looks like an npm/Node project."""
    base = root if root is not None else repo_root()
    return (base / "package.json").is_file()


def is_uv_project(root: Path | None = None) -> bool:
    """True when the workspace looks like a uv/Python project."""
    base = root if root is not None else repo_root()
    if (base / "uv.lock").is_file():
        return True
    pyproject = base / "pyproject.toml"
    if not pyproject.is_file():
        return False
    try:
        text = pyproject.read_text(encoding="utf-8")
    except OSError:
        return False
    return "[project]" in text or "tool.uv" in text


def strip_embedded_payloads(command: str) -> str:
    """Remove HEREDOCs and quoted strings so body text cannot trip mutators."""
    cleaned = _HEREDOC_RE.sub(" ", command)
    cleaned = _DOUBLE_QUOTE_RE.sub(" ", cleaned)
    cleaned = _SINGLE_QUOTE_RE.sub(" ", cleaned)
    return cleaned


def is_npm_dep_path(file_path: str) -> bool:
    """True when the edited path is an npm manifest or lockfile basename."""
    return Path(file_path).name in NPM_BASENAMES


def is_uv_dep_path(file_path: str) -> bool:
    """True when the edited path is a uv lock or pyproject basename."""
    return Path(file_path).name in UV_BASENAMES


def is_dep_path(file_path: str) -> bool:
    """True when the path is an npm or uv dependency file (compat helper)."""
    return is_npm_dep_path(file_path) or is_uv_dep_path(file_path)


def mark_pending(paths: list[str], *, ecosystem: Ecosystem) -> None:
    """Mark that dep files changed and audit is required before stop."""
    state = load_gate_state()
    existing = {str(p) for p in state.get("paths") or []}
    existing.update(paths)
    prev = str(state.get("ecosystem") or "")
    # Prefer the newly observed ecosystem; keep prior if same family.
    state["ecosystem"] = ecosystem if ecosystem else prev
    state["pending"] = True
    state["audit_ok"] = False
    state["paths"] = sorted(existing)
    save_gate_state(state)


def clear_pending() -> None:
    """Clear the pending gate after a successful audit."""
    save_gate_state(
        {"pending": False, "paths": [], "audit_ok": True, "ecosystem": ""}
    )


def npm_audit_succeeded(command: str, output: str) -> bool:
    """Heuristic: primary command was npm audit and output looks clean."""
    cleaned = strip_embedded_payloads(command)
    if not _NPM_AUDIT_RE.search(cleaned):
        return False
    if _NPM_AUDIT_FAIL_RE.search(output) or "npm ERR!" in output:
        return False
    return bool(_NPM_AUDIT_CLEAN_RE.search(output))


def uv_audit_succeeded(command: str, output: str) -> bool:
    """Heuristic: primary command was uv audit and output looks clean."""
    cleaned = strip_embedded_payloads(command)
    if not _UV_AUDIT_RE.search(cleaned):
        return False
    if _UV_AUDIT_FAIL_RE.search(output):
        return False
    # Prefer an explicit clean signal; also accept empty/short success output
    # when no fail pattern matched (uv may print little on success).
    if _UV_AUDIT_CLEAN_RE.search(output):
        return True
    # No vulnerability wording and no error → treat as pass.
    return "vulnerabilit" not in output.lower() and "error:" not in output.lower()


def audit_succeeded(command: str, output: str) -> bool:
    """True when an ecosystem audit command succeeded."""
    return npm_audit_succeeded(command, output) or uv_audit_succeeded(command, output)


def handle_after_file_edit(event: dict[str, Any]) -> None:
    """Mark pending when npm/uv dep files are edited in a matching project."""
    file_path = str(event.get("file_path") or "")
    if not file_path:
        return
    name = Path(file_path).name
    if is_npm_dep_path(file_path) and is_npm_project():
        mark_pending([name], ecosystem="npm")
        return
    if is_uv_dep_path(file_path) and is_uv_project():
        mark_pending([name], ecosystem="uv")


def handle_after_shell(event: dict[str, Any]) -> None:
    """Mark pending on primary npm/uv mutators; clear on successful audit."""
    command = str(event.get("command") or "")
    output = str(event.get("output") or "")
    if audit_succeeded(command, output):
        clear_pending()
        return
    cleaned = strip_embedded_payloads(command)
    if is_npm_project() and _NPM_MUTATE_RE.search(cleaned):
        mark_pending(["shell:" + command.strip()[:80]], ecosystem="npm")
        return
    if is_uv_project() and _UV_MUTATE_RE.search(cleaned):
        mark_pending(["shell:" + command.strip()[:80]], ecosystem="uv")


def _resolve_ecosystem(state: dict[str, Any]) -> Ecosystem | None:
    """Pick follow-up ecosystem; drop stale npm pending on non-npm repos."""
    eco = str(state.get("ecosystem") or "")
    if eco == "npm":
        if is_npm_project():
            return "npm"
        return None
    if eco == "uv":
        if is_uv_project():
            return "uv"
        return None
    # Legacy state without ecosystem: infer from workspace.
    if is_npm_project():
        return "npm"
    if is_uv_project():
        return "uv"
    return None


def handle_stop(event: dict[str, Any]) -> str | None:
    """Return a follow-up message when pending audit has not passed."""
    if str(event.get("status") or "") != "completed":
        return None
    state = load_gate_state()
    if not state.get("pending") or state.get("audit_ok"):
        return None
    ecosystem = _resolve_ecosystem(state)
    if ecosystem is None:
        # Stale false-positive (e.g. heredoc npm text on a uv-only repo).
        clear_pending()
        return None
    loop_count = event.get("loop_count")
    try:
        loops = int(loop_count)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        loops = 0
    if loops >= 2:
        return None
    return FOLLOWUP_NPM if ecosystem == "npm" else FOLLOWUP_UV


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
