"""Unit tests for scripts/bootstrap_github.py."""

from __future__ import annotations

import bootstrap_github as boot
import pytest


def test_dry_run_environments_prints_payloads(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--dry-run`` prints PUT payloads without calling gh."""
    boot.apply_environments("GuyErreich/AI_Agents", dry_run=True)
    out = capsys.readouterr().out
    assert "PUT" in out
    assert "environments/staging" in out
    assert "environments/production" in out


def test_dry_run_rulesets_prints_payloads(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--dry-run`` prints ruleset POST payloads."""
    boot.apply_rulesets("GuyErreich/AI_Agents", dry_run=True)
    out = capsys.readouterr().out
    assert "POST" in out
    assert "rulesets" in out
    assert "Standard Flow" in out


def test_main_dry_run_complete(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() returns 0 on dry-run without network."""
    monkeypatch.setattr(
        "sys.argv",
        ["bootstrap_github.py", "--dry-run", "--repo", "org/repo"],
    )
    assert boot.main() == 0
