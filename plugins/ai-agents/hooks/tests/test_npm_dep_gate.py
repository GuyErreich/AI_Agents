"""Unit tests for the npm/uv dependency audit gate hook."""

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


@pytest.fixture()
def npm_project(gate_home: Path) -> Path:
    """Seed a minimal npm project."""
    (gate_home / "package.json").write_text('{"name":"x","version":"1.0.0"}\n')
    return gate_home


@pytest.fixture()
def uv_project(gate_home: Path) -> Path:
    """Seed a minimal uv project."""
    (gate_home / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "0.1.0"\n')
    (gate_home / "uv.lock").write_text("version = 1\n")
    return gate_home


class TestIsDepPath:
    """Basename detection for manifests and lockfiles."""

    def test_package_json(self) -> None:
        assert gate.is_npm_dep_path("/repo/package.json")
        assert gate.is_dep_path("/repo/package.json")

    def test_lockfile(self) -> None:
        assert gate.is_npm_dep_path("/repo/package-lock.json")

    def test_uv_lock(self) -> None:
        assert gate.is_uv_dep_path("/repo/uv.lock")
        assert gate.is_dep_path("/repo/uv.lock")

    def test_source_file(self) -> None:
        assert not gate.is_dep_path("/repo/src/app.ts")


class TestStripEmbedded:
    """HEREDOC / quote stripping for false-positive avoidance."""

    def test_strips_heredoc_npm_install(self) -> None:
        cmd = """/usr/bin/gh issue create --body "$(cat <<'EOF'
use npm install --package-lock-only here
EOF
)" """
        cleaned = gate.strip_embedded_payloads(cmd)
        assert "npm install" not in cleaned

    def test_keeps_primary_npm_install(self) -> None:
        cleaned = gate.strip_embedded_payloads("npm install lodash")
        assert "npm install" in cleaned


class TestAuditSucceeded:
    """Output heuristics for audit success."""

    def test_npm_clean(self) -> None:
        assert gate.audit_succeeded(
            "npm audit --audit-level=high",
            "found 0 vulnerabilities\n",
        )

    def test_npm_high_sev_fails(self) -> None:
        assert not gate.audit_succeeded(
            "npm audit --audit-level=high",
            "2 high severity vulnerabilities\n",
        )

    def test_npm_enolock_fails(self) -> None:
        assert not gate.audit_succeeded(
            "npm audit --audit-level=high",
            "npm error code ENOLOCK\n",
        )

    def test_uv_clean(self) -> None:
        assert gate.audit_succeeded(
            "uv audit --frozen",
            "Audited 40 packages with 0 vulnerabilities\n",
        )

    def test_uv_clean_osv_phrasing(self) -> None:
        assert gate.audit_succeeded(
            "uv audit --frozen",
            "Found no known vulnerabilities and no adverse project statuses in 9 packages\n",
        )

    def test_uv_findings_fail(self) -> None:
        assert not gate.audit_succeeded(
            "uv audit --frozen",
            "2 vulnerabilities found\n",
        )


class TestDispatchNpm:
    """Pending / clear / follow-up for npm projects."""

    def test_file_edit_marks_pending(self, npm_project: Path) -> None:
        out = gate.dispatch(
            {
                "file_path": str(npm_project / "package-lock.json"),
                "edits": [{"old_string": "a", "new_string": "b"}],
            }
        )
        assert out == {}
        state = gate.load_gate_state()
        assert state["pending"] is True
        assert state["ecosystem"] == "npm"

    def test_install_marks_pending(self, npm_project: Path) -> None:
        gate.dispatch({"command": "npm install lodash", "output": "added 1 package"})
        assert gate.load_gate_state()["pending"] is True

    def test_heredoc_npm_install_ignored(self, npm_project: Path) -> None:
        cmd = """/usr/bin/gh issue create --body "$(cat <<'EOF'
npm install --package-lock-only
EOF
)" """
        gate.dispatch({"command": cmd, "output": ""})
        assert gate.load_gate_state()["pending"] is False

    def test_clean_audit_clears(self, npm_project: Path) -> None:
        gate.mark_pending(["package-lock.json"], ecosystem="npm")
        gate.dispatch(
            {
                "command": "npm audit --audit-level=high",
                "output": "found 0 vulnerabilities\n",
            }
        )
        state = gate.load_gate_state()
        assert state["pending"] is False
        assert state["audit_ok"] is True

    def test_stop_followup_when_pending(self, npm_project: Path) -> None:
        gate.mark_pending(["package.json"], ecosystem="npm")
        out = gate.dispatch({"status": "completed", "loop_count": 0})
        assert "npm audit" in out["followup_message"]


class TestDispatchUv:
    """Pending / clear / follow-up for uv projects."""

    def test_uv_lock_edit_marks_pending(self, uv_project: Path) -> None:
        gate.dispatch(
            {
                "file_path": str(uv_project / "uv.lock"),
                "edits": [{"old_string": "a", "new_string": "b"}],
            }
        )
        state = gate.load_gate_state()
        assert state["pending"] is True
        assert state["ecosystem"] == "uv"

    def test_uv_lock_cmd_marks_pending(self, uv_project: Path) -> None:
        gate.dispatch({"command": "uv lock --upgrade", "output": "Resolved"})
        assert gate.load_gate_state()["ecosystem"] == "uv"

    def test_uv_audit_clears(self, uv_project: Path) -> None:
        gate.mark_pending(["uv.lock"], ecosystem="uv")
        gate.dispatch(
            {
                "command": "uv audit --frozen",
                "output": "Audited 10 packages with 0 vulnerabilities\n",
            }
        )
        assert gate.load_gate_state()["pending"] is False

    def test_stop_followup_uv(self, uv_project: Path) -> None:
        gate.mark_pending(["uv.lock"], ecosystem="uv")
        out = gate.dispatch({"status": "completed", "loop_count": 0})
        assert "uv audit" in out["followup_message"]


class TestNonMatchingProject:
    """No npm/uv project → no gate."""

    def test_npm_edit_ignored_without_package_json(self, gate_home: Path) -> None:
        # Bare package-lock without package.json should not arm the gate.
        gate.dispatch(
            {
                "file_path": str(gate_home / "package-lock.json"),
                "edits": [{"old_string": "a", "new_string": "b"}],
            }
        )
        assert gate.load_gate_state()["pending"] is False

    def test_shell_npm_ignored_without_project(self, gate_home: Path) -> None:
        gate.dispatch({"command": "npm install lodash", "output": "added"})
        assert gate.load_gate_state()["pending"] is False

    def test_stale_npm_pending_cleared_on_uv_only_repo(self, uv_project: Path) -> None:
        gate.mark_pending(["shell:gh issue … npm install"], ecosystem="npm")
        out = gate.dispatch({"status": "completed", "loop_count": 0})
        assert out == {}
        assert gate.load_gate_state()["pending"] is False


class TestStopCaps:
    """Stop follow-up caps and abort."""

    def test_stop_silent_when_clear(self, npm_project: Path) -> None:
        gate.clear_pending()
        assert gate.dispatch({"status": "completed", "loop_count": 0}) == {}

    def test_stop_aborted_no_followup(self, npm_project: Path) -> None:
        gate.mark_pending(["package.json"], ecosystem="npm")
        assert gate.dispatch({"status": "aborted", "loop_count": 0}) == {}

    def test_stop_loop_cap(self, npm_project: Path) -> None:
        gate.mark_pending(["package.json"], ecosystem="npm")
        assert gate.dispatch({"status": "completed", "loop_count": 2}) == {}


class TestStateRoundTrip:
    """State file persistence."""

    def test_round_trip(self, npm_project: Path) -> None:
        gate.mark_pending(["package.json", "package-lock.json"], ecosystem="npm")
        path = gate.state_path()
        assert path.is_file()
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        assert raw["pending"] is True
        assert raw["ecosystem"] == "npm"
        assert "package.json" in raw["paths"]
