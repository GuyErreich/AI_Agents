"""Unit tests for the npm dependency audit gate hook."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

HOOKS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOOKS))

import npm_dep_gate as gate  # noqa: E402


@pytest.fixture()
def gate_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate gate state under a temp repo root."""
    monkeypatch.setenv("REVIEW_LOOP_ROOT", str(tmp_path))
    monkeypatch.setattr(gate, "repo_root", lambda: tmp_path)
    return tmp_path


class TestIsDepPath:
    """Basename detection for manifests and lockfiles."""

    def test_package_json(self) -> None:
        assert gate.is_dep_path("/repo/package.json")

    def test_lockfile(self) -> None:
        assert gate.is_dep_path("/repo/package-lock.json")

    def test_nested_ignored(self) -> None:
        # Basename match is intentional — edits to any package.json count.
        assert gate.is_dep_path("/repo/packages/foo/package.json")

    def test_source_file(self) -> None:
        assert not gate.is_dep_path("/repo/src/app.ts")


class TestAuditSucceeded:
    """Output heuristics for npm audit success."""

    def test_clean(self) -> None:
        assert gate.audit_succeeded(
            "npm audit --audit-level=high",
            "found 0 vulnerabilities\n",
        )

    def test_high_sev_fails(self) -> None:
        assert not gate.audit_succeeded(
            "npm audit --audit-level=high",
            "2 high severity vulnerabilities\n",
        )

    def test_non_audit_command(self) -> None:
        assert not gate.audit_succeeded("npm run lint", "found 0 vulnerabilities\n")


class TestDispatch:
    """End-to-end pending / clear / follow-up behavior."""

    def test_file_edit_marks_pending(self, gate_home: Path) -> None:
        out = gate.dispatch(
            {
                "file_path": str(gate_home / "package-lock.json"),
                "edits": [{"old_string": "a", "new_string": "b"}],
            }
        )
        assert out == {}
        state = gate.load_gate_state()
        assert state["pending"] is True
        assert state["audit_ok"] is False

    def test_install_marks_pending(self, gate_home: Path) -> None:
        gate.dispatch({"command": "npm install lodash", "output": "added 1 package"})
        assert gate.load_gate_state()["pending"] is True

    def test_clean_audit_clears(self, gate_home: Path) -> None:
        gate.mark_pending(["package-lock.json"])
        out = gate.dispatch(
            {
                "command": "npm audit --audit-level=high",
                "output": "found 0 vulnerabilities\n",
            }
        )
        assert out == {}
        state = gate.load_gate_state()
        assert state["pending"] is False
        assert state["audit_ok"] is True

    def test_stop_followup_when_pending(self, gate_home: Path) -> None:
        gate.mark_pending(["package.json"])
        out = gate.dispatch({"status": "completed", "loop_count": 0})
        assert "followup_message" in out
        assert "npm audit" in out["followup_message"]

    def test_stop_silent_when_clear(self, gate_home: Path) -> None:
        gate.clear_pending()
        assert gate.dispatch({"status": "completed", "loop_count": 0}) == {}

    def test_stop_aborted_no_followup(self, gate_home: Path) -> None:
        gate.mark_pending(["package.json"])
        assert gate.dispatch({"status": "aborted", "loop_count": 0}) == {}

    def test_stop_loop_cap(self, gate_home: Path) -> None:
        gate.mark_pending(["package.json"])
        assert gate.dispatch({"status": "completed", "loop_count": 2}) == {}


class TestStateRoundTrip:
    """State file persistence."""

    def test_round_trip(self, gate_home: Path) -> None:
        gate.mark_pending(["package.json", "package-lock.json"])
        path = gate.state_path()
        assert path.is_file()
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        assert raw["pending"] is True
        assert "package.json" in raw["paths"]
