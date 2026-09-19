"""Unit tests for review_loop_git_guard."""

from __future__ import annotations

import json

import pytest
import review_loop_git_guard as guard
from review_loop_git_guard import decide


@pytest.mark.parametrize(
    ("command", "state", "permission"),
    [
        ("git status", {"active": False}, "allow"),
        ("git push --force origin HEAD", {"active": True}, "deny"),
        ("git push --force-with-lease", {"active": True}, "deny"),
        ("git push -f origin feature/x", {"active": True}, "deny"),
        ("git push origin main", {"active": True}, "deny"),
        ("git push origin dev", {"active": True}, "deny"),
        ("git push origin master", {"active": True}, "deny"),
        (
            "git commit -m 'x'",
            {"active": True, "escalation_pending": True},
            "deny",
        ),
        (
            "git push origin feature/x",
            {"active": True, "escalation_pending": True},
            "deny",
        ),
        ("git status", {"active": True}, "allow"),
        ("git diff", {"active": True}, "allow"),
        ("", {"active": True}, "ask"),
        ("echo hi", {"active": True}, "allow"),
        ("git push origin feature/x", {"active": True}, "allow"),
    ],
)
def test_decide_permissions(
    command: str, state: dict[str, object], permission: str
) -> None:
    """Permission matrix for active/inactive/escalation cases."""
    payload = decide(command, state)
    assert payload["permission"] == permission


def test_main_emits_deny_for_force_push(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """main() prints a deny JSON payload for force-push while active."""
    monkeypatch.setattr(
        guard,
        "read_stdin_json",
        lambda: {"command": "git push --force origin HEAD"},
    )
    monkeypatch.setattr(
        guard,
        "load_state",
        lambda: {"active": True},
    )
    assert guard.main() == 0
    out = json.loads(capsys.readouterr().out.strip())
    assert out["permission"] == "deny"
