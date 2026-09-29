"""Unit tests for review_loop_init."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import review_loop_init as init


def test_budget_only_and_analysis_aliases(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Normalize budget-only rounds and analysis_mode aliases on init."""
    monkeypatch.setenv("REVIEW_LOOP_ROOT", str(tmp_path))
    event = {
        "pr_number": 42,
        "pr_url": "https://example.test/pr/42",
        "branch": "feature/x",
        "toolchain_mode": "uv",
        "pricing_updated": "2026-09",
        "overrides": {
            "max_rounds": "budget-only",
            "analysis_mode": "debug",
            "max_usd_est": 1.5,
        },
    }
    monkeypatch.setattr(init, "read_stdin_json", lambda: event)
    assert init.main() == 0
    state = json.loads(capsys.readouterr().out.strip())
    assert state["max_rounds"] is None
    assert state["analysis_mode"] == "debug-like"
    assert state["max_usd_est"] == 1.5
    assert state["pr_number"] == 42
    prefs = json.loads(
        (tmp_path / ".review-loop" / "preferences.json").read_text(encoding="utf-8")
    )
    assert prefs["max_rounds"] is None
