#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""Shared state and JSON helpers for review-loop hooks."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

STATE_DIR = Path(".review-loop")
LEGACY_STATE_DIR = Path(".cursor/review-loop")
STATE_PATH = STATE_DIR / "state.json"
PRICING_PATH = STATE_DIR / "pricing.json"
PREFERENCES_PATH = STATE_DIR / "preferences.json"
CLOSED_LEDGER_PATH = STATE_DIR / "closed-ledger.json"
LEGACY_RUNTIME_FILES = (
    "state.json",
    "pricing.json",
    "preferences.json",
    "closed-ledger.json",
    "review-lock.json",
)
DEFAULT_PRICING_REL = Path(
    "skills/code/ci/pr-review-loop/assets/pricing.default.json"
)
DEFAULT_PRICING_PLUGIN = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "code"
    / "ci"
    / "pr-review-loop"
    / "assets"
    / "pricing.default.json"
)
DEFAULT_PRICING_LEGACY_PROJECT = Path(
    ".cursor/skills/code/ci/pr-review-loop/assets/pricing.default.json"
)
# User-level skills copy (~/.cursor/skills) — fallback before plugin install
DEFAULT_PRICING_USER = (
    Path.home()
    / ".cursor"
    / "skills"
    / "code"
    / "ci"
    / "pr-review-loop"
    / "assets"
    / "pricing.default.json"
)

# Caps / models that survive across loop runs (not wiped on each preflight).
PREFERENCE_KEYS = (
    "max_rounds",
    "max_tokens_est",
    "max_usd_est",
    "pricing_mode",
    "reviewer_model",
    "fixer_model",
    "clean_passes_required",
    "manage_severity",
    "post_fix_focus",
    "diminishing_returns_round",
    "diminishing_returns_floor",
    "analysis_mode",
)

ANALYSIS_MODE_VALUES = ("review", "debug-like", "security")
ANALYSIS_MODE_ALIASES = {
    "review": "review",
    "default": "review",
    "standard": "review",
    "debug-like": "debug-like",
    "debug": "debug-like",
    "debuglike": "debug-like",
    "investigate": "debug-like",
    "security": "security",
    "sec": "security",
    "secure": "security",
}

# Minimum severity the loop manages (auto-fix / escalate). Below → Defer.
MANAGE_SEVERITY_ORDER = ("low", "medium", "high", "critical")
MANAGE_SEVERITY_ALIASES = {
    "low": "low",
    "all": "low",
    "medium": "medium",
    "med": "medium",
    "high": "high",
    "critical": "critical",
    "crit": "critical",
}

POST_FIX_FOCUS_VALUES = ("delta", "full")
POST_FIX_FOCUS_ALIASES = {
    "delta": "delta",
    "cheap": "delta",
    "full": "full",
}

# Only these focuses may credit consecutive_clean_passes.
WIDE_FOCUS_VALUES = ("full", "confirm")

# Finding sources that stay open even when their signature is already closed.
ESCALATING_SOURCES = frozenset({"recurrence", "contested"})
# Sources always kept in post-fix verify mode (even outside the surface).
VERIFY_KEEP_SOURCES = frozenset({"recurrence", "contested", "regression"})


def now_iso() -> str:
    """Return current UTC time as ISO-8601 without microseconds."""
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def repo_root() -> Path:
    """Resolve the active workspace root.

    Order: ``REVIEW_LOOP_ROOT`` (set by run-python.sh) → git toplevel → cwd.
    User-level hooks start in ``~/.cursor/``; the shim exports the workspace.
    """
    env = os.environ.get("REVIEW_LOOP_ROOT", "").strip()
    if env:
        path = Path(env)
        if path.is_dir():
            return path
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except OSError:
        pass
    return Path.cwd()


def migrate_legacy_runtime_dir(root: Path | None = None) -> Path:
    """Ensure ``.review-loop/`` exists; copy once from ``.cursor/review-loop/``.

    Runtime cache lives outside ``.cursor/`` so agents do not hit Cursor
    permission prompts on every write. Legacy files are copied when present
    and the new path is missing; never overwrite newer files.
    """
    base = root or repo_root()
    dest_dir = base / STATE_DIR
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"review-loop: could not create {STATE_DIR}: {exc}", file=sys.stderr)
        return dest_dir

    legacy_dir = base / LEGACY_STATE_DIR
    if not legacy_dir.is_dir():
        # Also migrate a lone legacy review-lock sitting under .cursor/
        legacy_lock = base / ".cursor" / "review-lock.json"
        new_lock = dest_dir / "review-lock.json"
        if legacy_lock.is_file() and not new_lock.exists():
            try:
                new_lock.write_bytes(legacy_lock.read_bytes())
            except OSError as exc:
                print(
                    f"review-loop: could not migrate review-lock.json: {exc}",
                    file=sys.stderr,
                )
        return dest_dir

    for name in LEGACY_RUNTIME_FILES:
        src = legacy_dir / name
        dst = dest_dir / name
        if not src.is_file() or dst.exists():
            continue
        try:
            dst.write_bytes(src.read_bytes())
        except OSError as exc:
            print(
                f"review-loop: could not migrate {name} from legacy dir: {exc}",
                file=sys.stderr,
            )

    legacy_lock = base / ".cursor" / "review-lock.json"
    new_lock = dest_dir / "review-lock.json"
    if legacy_lock.is_file() and not new_lock.exists():
        try:
            new_lock.write_bytes(legacy_lock.read_bytes())
        except OSError as exc:
            print(
                f"review-loop: could not migrate review-lock.json: {exc}",
                file=sys.stderr,
            )
    return dest_dir


def state_path(root: Path | None = None) -> Path:
    """Return absolute path to state.json."""
    migrate_legacy_runtime_dir(root)
    base = root or repo_root()
    return base / STATE_PATH


def load_state(root: Path | None = None) -> dict[str, Any]:
    """Load loop state; return empty dict if missing or invalid."""
    path = state_path(root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def save_state(data: dict[str, Any], root: Path | None = None) -> None:
    """Write state.json; never raise — hooks must always emit JSON."""
    path = state_path(root)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"review-loop: could not write state.json: {exc}", file=sys.stderr)


def preferences_path(root: Path | None = None) -> Path:
    """Return absolute path to preferences.json (durable caps across runs)."""
    migrate_legacy_runtime_dir(root)
    base = root or repo_root()
    return base / PREFERENCES_PATH


def ledger_path(root: Path | None = None) -> Path:
    """Return absolute path to closed-ledger.json (durable per-PR memory)."""
    migrate_legacy_runtime_dir(root)
    base = root or repo_root()
    return base / CLOSED_LEDGER_PATH


def load_closed_ledger(root: Path | None = None) -> dict[str, Any]:
    """Load the durable closed-findings ledger; empty dict on missing/invalid."""
    path = ledger_path(root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"by_pr": {}}
    if not isinstance(data, dict):
        return {"by_pr": {}}
    by_pr = data.get("by_pr")
    if not isinstance(by_pr, dict):
        data["by_pr"] = {}
    return data


def save_closed_ledger(data: dict[str, Any], root: Path | None = None) -> None:
    """Persist closed-ledger.json; never raise."""
    path = ledger_path(root)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if "by_pr" not in data or not isinstance(data.get("by_pr"), dict):
            data = {"by_pr": data.get("by_pr") if isinstance(data.get("by_pr"), dict) else {}}
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        print(
            f"review-loop: could not write closed-ledger.json: {exc}",
            file=sys.stderr,
        )


def load_pr_closed_memory(
    pr_number: int, root: Path | None = None
) -> dict[str, Any]:
    """Return the ledger entry for one PR, or an empty template."""
    ledger = load_closed_ledger(root)
    by_pr = ledger.get("by_pr") if isinstance(ledger.get("by_pr"), dict) else {}
    key = str(int(pr_number))
    raw = by_pr.get(key)
    if not isinstance(raw, dict):
        return {
            "pr_number": int(pr_number),
            "branch": "",
            "updated_at": "",
            "last_clean_fingerprint": "",
            "last_outcome": "",
            "closed_findings": [],
            "accepted_by_design": [],
        }
    return {
        "pr_number": int(raw.get("pr_number") or pr_number),
        "branch": str(raw.get("branch") or ""),
        "updated_at": str(raw.get("updated_at") or ""),
        "last_clean_fingerprint": str(raw.get("last_clean_fingerprint") or ""),
        "last_outcome": str(raw.get("last_outcome") or ""),
        "closed_findings": list(raw.get("closed_findings") or [])
        if isinstance(raw.get("closed_findings"), list)
        else [],
        "accepted_by_design": list(raw.get("accepted_by_design") or [])
        if isinstance(raw.get("accepted_by_design"), list)
        else [],
    }


def _merge_closed_lists(
    existing: list[Any], incoming: list[Any]
) -> list[dict[str, Any]]:
    """Merge closed/accepted entries idempotently by signature."""
    by_sig: dict[str, dict[str, Any]] = {}
    for row in existing + incoming:
        if not isinstance(row, dict):
            continue
        sig = str(row.get("signature") or "").strip()
        if not sig:
            continue
        prev = by_sig.get(sig)
        if prev is None:
            by_sig[sig] = dict(row)
            continue
        # Prefer newer / richer fields (fix_shape, rationale).
        merged = dict(prev)
        for key, value in row.items():
            if value in (None, "", [], {}):
                continue
            if key not in merged or not merged.get(key):
                merged[key] = value
            elif key in {"fix_shape", "rationale", "status", "location", "finding"}:
                merged[key] = value
        by_sig[sig] = merged
    return list(by_sig.values())


def merge_closed_memory(
    state: dict[str, Any], root: Path | None = None
) -> dict[str, Any]:
    """Write state closed/accepted into the durable PR ledger (idempotent)."""
    try:
        pr_number = int(state.get("pr_number") or 0)
    except (TypeError, ValueError):
        pr_number = 0
    if pr_number <= 0:
        return state

    ledger = load_closed_ledger(root)
    by_pr = ledger.setdefault("by_pr", {})
    if not isinstance(by_pr, dict):
        by_pr = {}
        ledger["by_pr"] = by_pr

    key = str(pr_number)
    prior = load_pr_closed_memory(pr_number, root)
    closed = _merge_closed_lists(
        prior.get("closed_findings") or [],
        list(state.get("closed_findings") or []),
    )
    accepted = _merge_closed_lists(
        prior.get("accepted_by_design") or [],
        list(state.get("accepted_by_design") or []),
    )
    entry = {
        "pr_number": pr_number,
        "branch": str(state.get("branch") or prior.get("branch") or ""),
        "updated_at": now_iso(),
        "last_clean_fingerprint": str(
            state.get("last_clean_fingerprint")
            or prior.get("last_clean_fingerprint")
            or ""
        ),
        "last_outcome": str(
            state.get("last_outcome") or prior.get("last_outcome") or ""
        ),
        "closed_findings": closed,
        "accepted_by_design": accepted,
    }
    by_pr[key] = entry
    save_closed_ledger(ledger, root)
    return state


def mark_run_outcome(
    state: dict[str, Any],
    outcome: str,
    fingerprint: str = "",
    root: Path | None = None,
) -> dict[str, Any]:
    """Record loop outcome on state and durable ledger."""
    normalized = str(outcome or "").strip().lower()
    state["last_outcome"] = normalized
    if fingerprint:
        state["last_clean_fingerprint"] = str(fingerprint).strip()
        if normalized == "confirmed_clean":
            # Keep last_fingerprint in sync for budget guards.
            state["last_fingerprint"] = str(fingerprint).strip()
    merge_closed_memory(state, root)
    return state


def should_short_circuit_confirm(
    state: dict[str, Any], current_fingerprint: str
) -> bool:
    """True when prior run confirmed clean at this exact PR fingerprint."""
    fp = str(current_fingerprint or "").strip()
    if not fp:
        return False
    if str(state.get("last_outcome") or "").strip().lower() != "confirmed_clean":
        return False
    return str(state.get("last_clean_fingerprint") or "").strip() == fp


def default_preferences() -> dict[str, Any]:
    """Built-in defaults used only when preferences.json is missing a key."""
    manage = "medium"
    return {
        "max_rounds": 3,
        "max_tokens_est": 1_000_000,
        "max_usd_est": 2.0,
        "pricing_mode": "auto",
        "reviewer_model": "inherit",
        "fixer_model": "inherit",
        "clean_passes_required": 2,
        "manage_severity": manage,
        "post_fix_focus": "delta",
        "diminishing_returns_round": 2,
        "diminishing_returns_floor": default_diminishing_returns_floor(manage),
        "analysis_mode": "review",
    }


def normalize_analysis_mode(value: Any) -> str:
    """Return canonical analysis_mode (`review`|`debug-like`|`security`).

    Aliases: ``debug`` → ``debug-like``; ``sec`` / ``secure`` → ``security``.
    This is prompt-level reviewer behavior — not Cursor's UI Debug mode.
    """
    if value is None:
        return "review"
    raw = str(value).strip().lower().replace("_", "-").replace(" ", "-")
    if raw in ANALYSIS_MODE_ALIASES:
        return ANALYSIS_MODE_ALIASES[raw]
    if raw in ANALYSIS_MODE_VALUES:
        return raw
    return "review"


def normalize_manage_severity(value: Any) -> str:
    """Return a canonical manage_severity floor (`low`|`medium`|`high`|`critical`)."""
    if value is None:
        return "medium"
    raw = str(value).strip().lower()
    if raw in MANAGE_SEVERITY_ALIASES:
        return MANAGE_SEVERITY_ALIASES[raw]
    if raw in MANAGE_SEVERITY_ORDER:
        return raw
    return "medium"


def default_diminishing_returns_floor(manage_severity: Any) -> str:
    """One severity tier above manage_severity, capped at critical."""
    base = normalize_manage_severity(manage_severity)
    idx = MANAGE_SEVERITY_ORDER.index(base)
    return MANAGE_SEVERITY_ORDER[min(idx + 1, len(MANAGE_SEVERITY_ORDER) - 1)]


def normalize_diminishing_returns_floor(value: Any, manage_severity: Any) -> str:
    """Canonical diminishing_returns_floor; derive from manage_severity when unset."""
    if value is None:
        return default_diminishing_returns_floor(manage_severity)
    raw = str(value).strip().lower()
    if raw in {"", "auto", "default", "derived"}:
        return default_diminishing_returns_floor(manage_severity)
    if raw in MANAGE_SEVERITY_ALIASES:
        return MANAGE_SEVERITY_ALIASES[raw]
    if raw in MANAGE_SEVERITY_ORDER:
        return raw
    return default_diminishing_returns_floor(manage_severity)


def normalize_diminishing_returns_round(value: Any) -> int:
    """Return a positive int round threshold (default 2)."""
    if value is None:
        return 2
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 2
    return max(1, parsed)


def should_defer_for_diminishing_returns(
    round_n: int, severity: Any, state: dict[str, Any]
) -> bool:
    """True when round has crossed the threshold and severity is below the ratcheted floor."""
    try:
        threshold = int(state.get("diminishing_returns_round", 2) or 2)
    except (TypeError, ValueError):
        threshold = 2
    if round_n < threshold:
        return False
    floor = normalize_diminishing_returns_floor(
        state.get("diminishing_returns_floor"), state.get("manage_severity")
    )
    return not severity_meets_floor(severity, floor)


def normalize_post_fix_focus(value: Any) -> str:
    """Return canonical post_fix_focus (`delta`|`full`)."""
    if value is None:
        return "delta"
    raw = str(value).strip().lower()
    if raw in POST_FIX_FOCUS_ALIASES:
        return POST_FIX_FOCUS_ALIASES[raw]
    if raw in POST_FIX_FOCUS_VALUES:
        return raw
    return "delta"


def clean_pass_counts(focus: Any) -> bool:
    """Only wide-scope reviews (full / confirm) may credit a clean pass."""
    return str(focus or "").strip().lower() in WIDE_FOCUS_VALUES


def apply_clean_pass(
    state: dict[str, Any],
    *,
    focus: Any,
    coverage_ok: bool = True,
) -> int:
    """Increment consecutive_clean_passes only for wide, coverage-OK reviews.

    A clean ``delta`` leaves the counter untouched (fix verified, not a clean
    pass). Returns the resulting consecutive_clean_passes value.
    """
    current = int(state.get("consecutive_clean_passes", 0) or 0)
    if not coverage_ok or not clean_pass_counts(focus):
        state["consecutive_clean_passes"] = current
        return current
    current += 1
    state["consecutive_clean_passes"] = current
    return current


def resolve_round_focus(
    *,
    round_n: int,
    consecutive_clean_passes: int,
    just_finished_fixer: bool,
    post_fix_focus: Any = "delta",
    invocation_focus: Any = None,
    force_full: bool = False,
    last_focus: Any = None,
    last_round_clean: bool = False,
) -> str:
    """Pick reviewer focus for the next round.

    Defaults: round 1 → full; after fixer → post_fix_focus (delta);
    after first *counted* clean → confirm; force_full (coverage miss) → full.
    A clean narrow (delta) pass never counts — next focus is confirm.
    """
    if invocation_focus is not None:
        raw = str(invocation_focus).strip().lower()
        if raw in {"full", "delta", "confirm"}:
            return raw
    if force_full:
        return "full"
    # A clean narrow pass never counts — go wide next to earn a real clean.
    if last_round_clean and not clean_pass_counts(last_focus):
        return "confirm"
    if consecutive_clean_passes >= 1:
        return "confirm"
    if just_finished_fixer:
        return normalize_post_fix_focus(post_fix_focus)
    if round_n <= 1:
        return "full"
    return normalize_post_fix_focus(post_fix_focus)


def validate_still_fresh(
    state: dict[str, Any], current_fingerprint: str
) -> bool:
    """True when stored lint+build pass matches the current PR fingerprint."""
    if not current_fingerprint:
        return False
    if str(state.get("last_validate_fingerprint") or "") != current_fingerprint:
        return False
    return (
        str(state.get("last_lint") or "") == "pass"
        and str(state.get("last_build") or "") == "pass"
    )


def severity_meets_floor(severity: Any, floor: Any) -> bool:
    """True when finding severity is at or above the manage_severity floor."""
    sev = str(severity or "").strip().lower()
    floor_norm = normalize_manage_severity(floor)
    if sev not in MANAGE_SEVERITY_ORDER:
        # Unknown labels are managed (safe default — do not silently drop).
        return True
    return MANAGE_SEVERITY_ORDER.index(sev) >= MANAGE_SEVERITY_ORDER.index(
        floor_norm
    )


def load_preferences(root: Path | None = None) -> dict[str, Any]:
    """Load durable loop preferences; fill missing keys from defaults.

    Explicit ``null`` for ``max_rounds`` is preserved (budget-only / unlimited).
    """
    prefs = default_preferences()
    path = preferences_path(root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return prefs
    if not isinstance(data, dict):
        return prefs
    for key in PREFERENCE_KEYS:
        if key not in data:
            continue
        # Allow explicit null for max_rounds (unlimited).
        if key == "max_rounds" or data[key] is not None:
            prefs[key] = data[key]
    prefs["manage_severity"] = normalize_manage_severity(
        prefs.get("manage_severity")
    )
    prefs["post_fix_focus"] = normalize_post_fix_focus(
        prefs.get("post_fix_focus")
    )
    prefs["diminishing_returns_round"] = normalize_diminishing_returns_round(
        prefs.get("diminishing_returns_round")
    )
    prefs["diminishing_returns_floor"] = normalize_diminishing_returns_floor(
        prefs.get("diminishing_returns_floor"),
        prefs.get("manage_severity"),
    )
    prefs["analysis_mode"] = normalize_analysis_mode(prefs.get("analysis_mode"))
    return prefs


def save_preferences(data: dict[str, Any], root: Path | None = None) -> None:
    """Persist preference keys only (never wipe with a full state dump)."""
    path = preferences_path(root)
    merged = default_preferences()
    for key in PREFERENCE_KEYS:
        if key in data:
            merged[key] = data[key]
    merged["manage_severity"] = normalize_manage_severity(
        merged.get("manage_severity")
    )
    merged["post_fix_focus"] = normalize_post_fix_focus(
        merged.get("post_fix_focus")
    )
    merged["diminishing_returns_round"] = normalize_diminishing_returns_round(
        merged.get("diminishing_returns_round")
    )
    merged["diminishing_returns_floor"] = normalize_diminishing_returns_floor(
        merged.get("diminishing_returns_floor"),
        merged.get("manage_severity"),
    )
    merged["analysis_mode"] = normalize_analysis_mode(merged.get("analysis_mode"))
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        print(
            f"review-loop: could not write preferences.json: {exc}",
            file=sys.stderr,
        )


def apply_preference_overrides(
    prefs: dict[str, Any], overrides: dict[str, Any]
) -> dict[str, Any]:
    """Return a copy of prefs with invocation overrides applied."""
    merged = dict(prefs)
    for key in PREFERENCE_KEYS:
        if key not in overrides:
            continue
        if key == "max_rounds":
            merged[key] = overrides[key]
            continue
        if key == "manage_severity":
            merged[key] = normalize_manage_severity(overrides[key])
            continue
        if key == "post_fix_focus":
            merged[key] = normalize_post_fix_focus(overrides[key])
            continue
        if key == "diminishing_returns_round":
            merged[key] = normalize_diminishing_returns_round(overrides[key])
            continue
        if key == "diminishing_returns_floor":
            # Normalized after manage_severity is settled below.
            merged[key] = overrides[key]
            continue
        if key == "analysis_mode":
            merged[key] = normalize_analysis_mode(overrides[key])
            continue
        if overrides[key] is not None:
            merged[key] = overrides[key]
    if "manage_severity" in merged:
        merged["manage_severity"] = normalize_manage_severity(
            merged.get("manage_severity")
        )
    if "post_fix_focus" in merged:
        merged["post_fix_focus"] = normalize_post_fix_focus(
            merged.get("post_fix_focus")
        )
    if "diminishing_returns_round" in merged:
        merged["diminishing_returns_round"] = normalize_diminishing_returns_round(
            merged.get("diminishing_returns_round")
        )
    if "analysis_mode" in merged:
        merged["analysis_mode"] = normalize_analysis_mode(merged.get("analysis_mode"))
    # Re-derive floor when manage_severity changed and floor was not explicitly overridden.
    if "diminishing_returns_floor" not in overrides and "manage_severity" in overrides:
        merged["diminishing_returns_floor"] = default_diminishing_returns_floor(
            merged.get("manage_severity")
        )
    else:
        merged["diminishing_returns_floor"] = normalize_diminishing_returns_floor(
            merged.get("diminishing_returns_floor"),
            merged.get("manage_severity"),
        )
    return merged


def start_loop_state(
    *,
    pr_number: int,
    pr_url: str,
    branch: str,
    toolchain_mode: str = "uv",
    pricing_updated: str = "",
    overrides: dict[str, Any] | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Create a fresh run state from durable preferences + this-run overrides.

    Does **not** reset preferences to factory defaults. Invocation overrides
    (e.g. budget-only → ``max_rounds: null``) are written into both
    ``preferences.json`` and the new ``state.json``.

    Seeds ``closed_findings`` / ``accepted_by_design`` from the PR closed
    ledger so a new loop run retains prior fixes and does not rediscover them.
    """
    prefs = apply_preference_overrides(load_preferences(root), overrides or {})
    save_preferences(prefs, root)

    memory = load_pr_closed_memory(pr_number, root)
    seeded_closed = list(memory.get("closed_findings") or [])
    seeded_accepted = list(memory.get("accepted_by_design") or [])
    seeded = bool(seeded_closed or seeded_accepted)

    state: dict[str, Any] = {
        "active": False,
        "pr_number": pr_number,
        "pr_url": pr_url,
        "branch": branch,
        "started_at": now_iso(),
        "pricing_mode": prefs.get("pricing_mode", "auto"),
        "reviewer_model": prefs.get("reviewer_model", "inherit"),
        "fixer_model": prefs.get("fixer_model", "inherit"),
        "next_model": prefs.get("reviewer_model", "inherit"),
        "max_rounds": prefs.get("max_rounds"),
        "max_tokens_est": prefs.get("max_tokens_est", 1_000_000),
        "max_usd_est": prefs.get("max_usd_est", 2.0),
        "clean_passes_required": int(prefs.get("clean_passes_required") or 2),
        "manage_severity": normalize_manage_severity(
            prefs.get("manage_severity", "medium")
        ),
        "post_fix_focus": normalize_post_fix_focus(
            prefs.get("post_fix_focus", "delta")
        ),
        "diminishing_returns_round": normalize_diminishing_returns_round(
            prefs.get("diminishing_returns_round", 2)
        ),
        "diminishing_returns_floor": normalize_diminishing_returns_floor(
            prefs.get("diminishing_returns_floor"),
            prefs.get("manage_severity", "medium"),
        ),
        "analysis_mode": normalize_analysis_mode(prefs.get("analysis_mode", "review")),
        "consecutive_clean_passes": 0,
        "round": 0,
        "escalation_pending": False,
        "toolchain_mode": toolchain_mode,
        "pricing_updated": pricing_updated,
        "last_fingerprint": "",
        "last_validate_fingerprint": "",
        "last_lint": "",
        "last_build": "",
        "last_clean_fingerprint": str(memory.get("last_clean_fingerprint") or ""),
        "last_outcome": str(memory.get("last_outcome") or ""),
        "seeded_from_ledger": seeded,
        "accepted_by_design": seeded_accepted,
        "closed_findings": seeded_closed,
        "escalations": [],
        "rounds": [],
        "totals": {
            "tokens_est": 0,
            "usd_est": 0,
            "turns": 0,
            "tool_calls": 0,
            "wall_clock_s": 0,
        },
    }
    save_state(state, root)
    return state


def closed_signatures(state: dict[str, Any]) -> set[str]:
    """Return signature ids already fixed or accepted this loop run."""
    out: set[str] = set()
    for entry in state.get("closed_findings") or []:
        if not isinstance(entry, dict):
            continue
        sig = entry.get("signature")
        if isinstance(sig, str) and sig.strip():
            out.add(sig.strip())
    for entry in state.get("accepted_by_design") or []:
        if not isinstance(entry, dict):
            continue
        sig = entry.get("signature")
        if isinstance(sig, str) and sig.strip():
            out.add(sig.strip())
    return out


def append_closed_finding(
    state: dict[str, Any],
    *,
    signature: str,
    location: str,
    finding: str,
    status: str,
    closed_in_round: int,
    rationale: str = "",
    fix_shape: str = "",
    root: Path | None = None,
) -> dict[str, Any]:
    """Record a fixed or accepted finding so later rounds do not re-report it.

    Idempotent on ``signature``. When ``status`` is ``accepted``, also mirrors
    into ``accepted_by_design``. ``fix_shape`` records what the fixer changed
    so later rounds can detect contested reverse-fixes. Persists into the
    durable PR closed ledger immediately.
    """
    sig = signature.strip()
    if not sig:
        return state
    if sig in closed_signatures(state):
        return state

    entry: dict[str, Any] = {
        "signature": sig,
        "location": location,
        "finding": finding,
        "status": status,
        "closed_in_round": closed_in_round,
    }
    if rationale:
        entry["rationale"] = rationale
    if fix_shape:
        entry["fix_shape"] = fix_shape

    closed = list(state.get("closed_findings") or [])
    closed.append(entry)
    state["closed_findings"] = closed

    if status == "accepted":
        accepted = list(state.get("accepted_by_design") or [])
        accepted.append(
            {
                "signature": sig,
                "location": location,
                "finding": finding,
                "rationale": rationale,
            }
        )
        state["accepted_by_design"] = accepted

    merge_closed_memory(state, root)
    return state


def fixed_locations(state: dict[str, Any]) -> set[str]:
    """Return paths and path:line locations closed with status fixed this run."""
    out: set[str] = set()
    for entry in state.get("closed_findings") or []:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("status") or "").strip().lower() != "fixed":
            continue
        loc = str(entry.get("location") or "").strip()
        if not loc:
            continue
        out.add(loc)
        path = finding_path(loc)
        if path:
            out.add(path)
    return out


def finding_path(location: Any) -> str:
    """Strip ``:line`` (and optional column) from a location string."""
    text = str(location or "").strip()
    if not text:
        return ""
    # Windows drive letters: C:\foo — only split on : when looking like path:line
    if len(text) >= 3 and text[1] == ":" and text[0].isalpha():
        # Keep drive; split remaining on last :digits if present
        rest = text[2:]
        if ":" in rest:
            maybe_path, maybe_line = rest.rsplit(":", 1)
            if maybe_line.isdigit() or (
                maybe_line.count(":") == 0 and maybe_line.replace(".", "", 1).isdigit()
            ):
                return text[:2] + maybe_path
        return text
    if ":" in text:
        path, maybe_line = text.rsplit(":", 1)
        if maybe_line.isdigit():
            return path.strip()
    return text


def fix_ledger_entries(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Compact rows for prompt context: fixed entries with a fix_shape."""
    rows: list[dict[str, Any]] = []
    for entry in state.get("closed_findings") or []:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("status") or "").strip().lower() != "fixed":
            continue
        shape = str(entry.get("fix_shape") or "").strip()
        if not shape:
            continue
        loc = str(entry.get("location") or "").strip()
        rows.append(
            {
                "location": loc,
                "path": finding_path(loc),
                "signature": str(entry.get("signature") or "").strip(),
                "status": "fixed",
                "fix_shape": shape,
            }
        )
    return rows


def format_fix_ledger_for_prompt(state: dict[str, Any]) -> str:
    """Markdown table of deliberate fix shapes for reviewer/fixer prompts."""
    rows = fix_ledger_entries(state)
    if not rows:
        return (
            "## Fix ledger\n\n"
            "_No fixed shapes recorded yet this PR (or shapes lack fix_shape)._\n"
        )
    lines = [
        "## Fix ledger (do not silently reverse)",
        "",
        "| Location | Signature | Fix shape |",
        "|---|---|---|",
    ]
    for row in rows:
        loc = row["location"].replace("|", "\\|")
        sig = row["signature"].replace("|", "\\|")
        shape = row["fix_shape"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {loc} | `{sig}` | {shape} |")
    lines.append("")
    return "\n".join(lines)


def is_contested_against_ledger(
    finding: dict[str, Any] | None, state: dict[str, Any]
) -> bool:
    """True when a finding targets a path already fixed with a non-empty fix_shape.

    Those must escalate as contested — never auto-fix in the opposite direction.
    """
    if not isinstance(finding, dict):
        return False
    loc = str(
        finding.get("location")
        or finding.get("Location")
        or finding.get("path")
        or ""
    ).strip()
    path = finding_path(loc)
    if not path:
        return False
    for entry in fix_ledger_entries(state):
        if entry["path"] == path or entry["location"] == loc:
            return True
        # Also match when finding is path-only and ledger has path:line
        if finding_path(entry["location"]) == path:
            return True
    return False


def has_fixed_this_run(state: dict[str, Any]) -> bool:
    """True when any closed finding has status fixed (including ledger-seeded)."""
    for entry in state.get("closed_findings") or []:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("status") or "").strip().lower() == "fixed":
            return True
    return False


def verify_surface_paths(
    state: dict[str, Any],
    fixer_paths: list[str] | None = None,
) -> set[str]:
    """Paths in scope for post-fix verify (fixed locations ∪ fixer-touched).

    Orchestrator should pass one-hop dependents (imports/callers/siblings) in
    ``fixer_paths`` alongside the last fixer diff.
    """
    out: set[str] = set()
    for loc in fixed_locations(state):
        path = finding_path(loc)
        if path:
            out.add(path)
    for raw in fixer_paths or []:
        path = finding_path(str(raw))
        if path:
            out.add(path)
    return out


def _finding_location(finding: dict[str, Any]) -> str:
    return str(
        finding.get("location")
        or finding.get("Location")
        or finding.get("path")
        or ""
    ).strip()


def _finding_severity(finding: dict[str, Any]) -> str:
    return str(
        finding.get("severity") or finding.get("Severity") or ""
    ).strip().lower()


def _finding_source(finding: dict[str, Any]) -> str:
    return str(
        finding.get("source") or finding.get("Source") or ""
    ).strip().lower()


def is_outside_verify_surface(
    finding: dict[str, Any] | None,
    state: dict[str, Any],
    fixer_paths: list[str] | None = None,
) -> bool:
    """True when a finding's path is not in the post-fix verify surface."""
    if not isinstance(finding, dict):
        return True
    path = finding_path(_finding_location(finding))
    if not path:
        return True
    return path not in verify_surface_paths(state, fixer_paths)


def filter_post_fix_findings(
    findings: list[dict[str, Any]],
    state: dict[str, Any],
    *,
    fixer_paths: list[str] | None = None,
    round_n: int = 0,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split findings into (keep, defer) under post-fix verify mode.

    When no fixed findings exist yet, all rows are kept (round-1 discovery).
    Otherwise keep recurrence/contested/regression, Critical (any path), and
    anything inside the verify surface; defer the rest as drive-by noise.
    ``round_n`` is accepted for orchestrator logging / future policy hooks.
    """
    _ = round_n  # reserved for callers / future ratchets
    if not has_fixed_this_run(state):
        keep = [row for row in findings if isinstance(row, dict)]
        return keep, []

    surface = verify_surface_paths(state, fixer_paths)
    keep: list[dict[str, Any]] = []
    defer: list[dict[str, Any]] = []
    for row in findings:
        if not isinstance(row, dict):
            continue
        source = _finding_source(row)
        if source in VERIFY_KEEP_SOURCES:
            keep.append(row)
            continue
        severity = _finding_severity(row)
        if severity == "critical":
            keep.append(row)
            continue
        path = finding_path(_finding_location(row))
        if path and path in surface:
            keep.append(row)
            continue
        deferred = dict(row)
        deferred["_defer_reason"] = "post-fix verify"
        defer.append(deferred)
    return keep, defer


def filter_open_findings(
    findings: list[dict[str, Any]],
    state: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split findings into (open, dropped_as_closed) by signature.

    Rows whose ``source`` / ``Source`` is in ``ESCALATING_SOURCES``
    (``recurrence``, ``contested``) stay open so the orchestrator can
    escalate them once.
    """
    closed = closed_signatures(state)
    open_rows: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for row in findings:
        if not isinstance(row, dict):
            continue
        source = str(row.get("source") or row.get("Source") or "").strip().lower()
        sig = str(row.get("signature") or row.get("Signature") or "").strip()
        if source in ESCALATING_SOURCES:
            open_rows.append(row)
            continue
        if sig and sig in closed:
            dropped.append(row)
            continue
        open_rows.append(row)
    return open_rows, dropped


def is_active(state: dict[str, Any]) -> bool:
    """Return True when the review loop is currently running."""
    return bool(state.get("active"))


# Only these Task subagent_type values are gated/accounted by loop hooks.
LOOP_SUBAGENT_TYPES = frozenset({"pr-reviewer", "pr-fixer"})


def loop_subagent_type(event: dict[str, Any] | None) -> str:
    """Extract the Task subagent type from a hook event payload."""
    if not event:
        return ""
    for key in ("subagent_type", "subagentType", "agent_type", "type"):
        raw = event.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return ""


def is_loop_subagent(event: dict[str, Any] | None) -> bool:
    """Return True when the event is for pr-reviewer or pr-fixer."""
    return loop_subagent_type(event) in LOOP_SUBAGENT_TYPES


def resolve_max_rounds(state: dict[str, Any]) -> int | None:
    """Return the round cap, or ``None`` when rounds are unlimited (budget-only).

    Unlimited when ``max_rounds`` is missing-as-explicit-null, ``0``, ``null``,
    or the strings ``none`` / ``unlimited`` / ``budget`` / ``budget-only``.
    Default when the key is absent: ``3``.
    """
    if "max_rounds" not in state:
        return 3
    raw = state.get("max_rounds")
    if raw is None:
        return None
    if isinstance(raw, str):
        text = raw.strip().lower()
        if text in {"", "none", "null", "unlimited", "inf", "budget", "budget-only"}:
            return None
        try:
            value = int(text)
        except ValueError:
            return 3
    elif isinstance(raw, bool):
        return 3
    elif isinstance(raw, int | float):
        value = int(raw)
    else:
        return 3
    if value <= 0:
        return None
    return value


def read_stdin_json() -> dict[str, Any]:
    """Parse JSON from stdin; return empty dict on empty/invalid input."""
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def emit(payload: dict[str, Any]) -> None:
    """Write a JSON response to stdout."""
    sys.stdout.write(json.dumps(payload))
    sys.stdout.write("\n")


def allow(message: str | None = None) -> None:
    """Emit a permission allow response."""
    payload: dict[str, Any] = {"permission": "allow"}
    if message:
        payload["agent_message"] = message
    emit(payload)


def deny(user_message: str, agent_message: str | None = None) -> None:
    """Emit a permission deny response."""
    payload: dict[str, Any] = {
        "permission": "deny",
        "user_message": user_message,
    }
    if agent_message:
        payload["agent_message"] = agent_message
    emit(payload)


def ask(user_message: str, agent_message: str | None = None) -> None:
    """Emit a permission ask response."""
    payload: dict[str, Any] = {
        "permission": "ask",
        "user_message": user_message,
    }
    if agent_message:
        payload["agent_message"] = agent_message
    emit(payload)


def bootstrap_pricing(root: Path | None = None) -> Path:
    """Copy default pricing into place when missing or schema-stale; return path."""
    migrate_legacy_runtime_dir(root)
    base = root or repo_root()
    dest = base / PRICING_PATH
    src = DEFAULT_PRICING_PLUGIN
    if not src.is_file():
        src = base / DEFAULT_PRICING_REL
    if not src.is_file():
        src = base / DEFAULT_PRICING_LEGACY_PROJECT
    if not src.is_file() and DEFAULT_PRICING_USER.is_file():
        src = DEFAULT_PRICING_USER

    needs_copy = not dest.is_file()
    if dest.is_file():
        try:
            existing = json.loads(dest.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = {}
        # Refresh when the Auto/api mode table is absent (pre-mode schema).
        if not isinstance(existing, dict) or "modes" not in existing:
            needs_copy = True

    if not needs_copy:
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.is_file():
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        dest.write_text(
            json.dumps(
                {
                    "updated": "unknown",
                    "source": "fallback empty table",
                    "chars_per_token": 3.9,
                    "cached_prefix_discount": 0.5,
                    "default_mode": "auto",
                    "modes": {
                        "auto": {
                            "label": "Cursor Auto (routed / included usage)",
                            "usd_multiplier": 1.0,
                            "model_key": "auto",
                            "max_tokens_est": 1_000_000,
                            "max_usd_est": 2.0,
                            "cold_project_tokens": 120_000,
                            "cold_project_usd": 0.15,
                        },
                        "api": {
                            "label": "Named model / API-like list rates",
                            "usd_multiplier": 1.0,
                            "model_key": None,
                            "max_tokens_est": 400_000,
                            "max_usd_est": 3.0,
                            "cold_project_tokens": 80_000,
                            "cold_project_usd": 0.75,
                        },
                    },
                    "models": {
                        "auto": {
                            "input_per_mtok": 0.2,
                            "output_per_mtok": 0.8,
                        },
                        "default": {
                            "input_per_mtok": 2.0,
                            "output_per_mtok": 10.0,
                        },
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    return dest


def load_pricing(root: Path | None = None) -> dict[str, Any]:
    """Load pricing.json, bootstrapping from the default asset if needed."""
    path = bootstrap_pricing(root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}
