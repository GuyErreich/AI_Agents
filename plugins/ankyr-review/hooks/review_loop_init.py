#!/usr/bin/env python3
# Copyright (c) 2026 Guy Erreich
#
# SPDX-License-Identifier: MIT

# /// script
# requires-python = ">=3.12"
# ///

"""Initialize a fresh PR review-loop run from durable preferences.

Reads JSON on stdin::

    {
      "pr_number": 60,
      "pr_url": "https://…",
      "branch": "feature/…",
      "toolchain_mode": "uv",
      "pricing_updated": "2026-08",
      "overrides": {
        "max_rounds": null,
        "max_usd_est": 2.0,
        "manage_severity": "high",
        "post_fix_focus": "delta",
        "analysis_mode": "debug-like"
      }
    }

Writes ``preferences.json`` + ``state.json`` and prints the new state JSON.
Never resets ``max_rounds`` to 3 unless preferences are missing that key and
no override was provided.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _loop_state import (  # noqa: E402
    emit,
    normalize_analysis_mode,
    read_stdin_json,
    start_loop_state,
)


def main() -> int:
    """Bootstrap state from preferences + overrides; print state JSON."""
    event = read_stdin_json()
    overrides_raw = event.get("overrides")
    overrides = overrides_raw if isinstance(overrides_raw, dict) else {}

    # Normalize common string forms for unlimited rounds.
    if "max_rounds" in overrides:
        raw = overrides["max_rounds"]
        unlimited = raw == 0 or (
            isinstance(raw, str)
            and raw.strip().lower()
            in {
                "none",
                "null",
                "unlimited",
                "inf",
                "budget",
                "budget-only",
                "",
            }
        )
        if unlimited:
            overrides["max_rounds"] = None

    # Invocation phrases: "analysis debug", "debug-like review", "analysis_mode=security".
    if "analysis_mode" in overrides:
        overrides["analysis_mode"] = normalize_analysis_mode(overrides["analysis_mode"])

    state = start_loop_state(
        pr_number=int(event.get("pr_number") or 0),
        pr_url=str(event.get("pr_url") or ""),
        branch=str(event.get("branch") or ""),
        toolchain_mode=str(event.get("toolchain_mode") or "uv"),
        pricing_updated=str(event.get("pricing_updated") or ""),
        overrides=overrides,
    )
    emit(state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
