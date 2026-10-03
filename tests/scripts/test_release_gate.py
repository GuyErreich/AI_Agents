"""Unit tests for scripts/release_gate.py."""

from __future__ import annotations

import release_gate
from pytest_mock import MockerFixture


def test_main_runs_all_checks_when_ok(mocker: MockerFixture) -> None:
    """Successful subprocesses yield exit 0."""
    mocker.patch.object(release_gate, "_run", return_value=0)
    assert release_gate.main(["--skip-degraded"]) == 0


def test_main_stops_on_first_failure(mocker: MockerFixture) -> None:
    """First non-zero check exits with that code."""
    mocker.patch.object(release_gate, "_run", side_effect=[0, 7])
    assert release_gate.main(["--skip-degraded"]) == 7
