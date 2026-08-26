#!/bin/bash
# Interpreter resolver for review-loop Python hooks.
# Works as a project hook (cwd = repo) or user hook (cwd = ~/.cursor/).
# Always exits 0 with valid JSON so failClosed only fires on genuine crashes.
set -eu

case "$0" in
  /*) _self="$0" ;;
  *) _self="$PWD/$0" ;;
esac
HOOKS_DIR="${_self%/*}"

SCRIPT_NAME="${1:-}"
if [ -z "$SCRIPT_NAME" ]; then
  printf '%s\n' '{"permission":"allow","agent_message":"run-python.sh: missing script name"}'
  exit 0
fi

if [ "$SCRIPT_NAME" = "--detect" ]; then
  if command -v uv >/dev/null 2>&1; then
    printf '%s\n' "uv"
  elif command -v python3 >/dev/null 2>&1; then
    ver="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)"
    major="${ver%%.*}"
    minor="${ver#*.}"
    if [ "${major:-0}" -gt 3 ] || { [ "${major:-0}" -eq 3 ] && [ "${minor:-0}" -ge 12 ]; }; then
      printf '%s\n' "python3 fallback"
    else
      printf '%s\n' "hooks degraded"
    fi
  else
    printf '%s\n' "hooks degraded"
  fi
  exit 0
fi

SCRIPT_PATH="$HOOKS_DIR/$SCRIPT_NAME"

INPUT=""
if [ ! -t 0 ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    INPUT="${INPUT}${line}
"
  done
fi

# Resolve active workspace: REVIEW_LOOP_ROOT > workspace_roots[0] > git toplevel > cwd
resolve_root() {
  if [ -n "${REVIEW_LOOP_ROOT:-}" ] && [ -d "$REVIEW_LOOP_ROOT" ]; then
    printf '%s\n' "$REVIEW_LOOP_ROOT"
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    root="$(REVIEW_LOOP_HOOK_INPUT="$INPUT" python3 - <<'PY' 2>/dev/null || true
import json, os, subprocess
from pathlib import Path
raw = os.environ.get("REVIEW_LOOP_HOOK_INPUT", "")
roots = []
try:
    data = json.loads(raw) if raw.strip() else {}
    wr = data.get("workspace_roots") or []
    if isinstance(wr, list):
        roots = [str(x) for x in wr if x]
except Exception:
    pass
for cand in roots:
    p = Path(cand)
    if p.is_dir():
        print(p)
        raise SystemExit(0)
# Prefer git toplevel from cwd when it looks like a project checkout
try:
    r = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=False,
    )
    if r.returncode == 0 and r.stdout.strip():
        print(r.stdout.strip())
        raise SystemExit(0)
except Exception:
    pass
print(Path.cwd())
PY
)"
    if [ -n "$root" ] && [ -d "$root" ]; then
      printf '%s\n' "$root"
      return
    fi
  fi
  printf '%s\n' "$PWD"
}

REPO_ROOT="$(resolve_root)"
export REVIEW_LOOP_ROOT="$REPO_ROOT"
STATE_DIR="$REPO_ROOT/.review-loop"
ALERT_MARKER="$STATE_DIR/.toolchain-alert"

degraded_default() {
  case "$SCRIPT_NAME" in
    review_loop_budget.py) printf '%s\n' '{"permission":"allow"}' ;;
    review_loop_round.py) printf '%s\n' '{}' ;;
    review_loop_git_guard.py) printf '%s\n' '{"permission":"ask","user_message":"Review-loop hooks degraded (no usable Python). Approve shell commands carefully."}' ;;
    npm_dep_gate.py) printf '%s\n' '{}' ;;
    *) printf '%s\n' '{"permission":"allow"}' ;;
  esac
}

emit_alert_once() {
  msg="$1"
  if command -v mkdir >/dev/null 2>&1; then
    mkdir -p "$STATE_DIR" 2>/dev/null || true
  fi
  if [ ! -f "$ALERT_MARKER" ]; then
    printf '%s\n' "$msg" >&2
    printf '%s\n' "$msg" >"$ALERT_MARKER" 2>/dev/null || true
  fi
}

run_with() {
  runner="$1"
  shift
  # Run from workspace root so relative .review-loop/ paths resolve
  ( cd "$REPO_ROOT" && printf '%s' "$INPUT" | $runner "$@" "$SCRIPT_PATH" )
}

if command -v uv >/dev/null 2>&1; then
  if [ -f "$SCRIPT_PATH" ]; then
    run_with "uv run --script" || degraded_default
    exit 0
  fi
fi

if command -v python3 >/dev/null 2>&1; then
  ver="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)"
  major="${ver%%.*}"
  minor="${ver#*.}"
  if [ "${major:-0}" -gt 3 ] || { [ "${major:-0}" -eq 3 ] && [ "${minor:-0}" -ge 12 ]; }; then
    if [ -f "$SCRIPT_PATH" ]; then
      emit_alert_once "uv not found — review-loop hooks are running on system python3. Install uv for the pinned toolchain: curl -LsSf https://astral.sh/uv/install.sh | sh"
      run_with "python3" || degraded_default
      exit 0
    fi
  fi
fi

emit_alert_once "No uv and no python3>=3.12 — review-loop hooks degraded. Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
degraded_default
exit 0
