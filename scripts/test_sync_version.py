# Copyright (c) 2026 Guy Erreich
#
# SPDX-License-Identifier: MIT

"""Tests for scripts/sync_version.py."""

from __future__ import annotations

import json
from pathlib import Path

import sync_version


def test_read_pyproject_version() -> None:
    """pyproject.toml in this repo declares a semver version."""
    version = sync_version.read_pyproject_version()
    assert version.count(".") >= 2


def test_sync_is_noop_when_aligned(tmp_path: Path, monkeypatch) -> None:
    """--check succeeds when JSON versions match pyproject."""
    version = sync_version.read_pyproject_version()
    assert sync_version.main(["--check"]) == 0
    assert version


def test_sync_updates_drifted_json(tmp_path: Path, monkeypatch) -> None:
    """sync_version rewrites plugin.json when version drifts."""
    plugin = tmp_path / "plugin.json"
    market = tmp_path / "marketplace.json"
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nversion = "9.9.9"\n', encoding="utf-8")
    plugin.write_text(
        json.dumps({"name": "ai-agents", "version": "0.0.1"}, indent=2) + "\n",
        encoding="utf-8",
    )
    market.write_text(
        json.dumps(
            {"name": "ai-agents", "metadata": {"version": "0.0.1"}},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(sync_version, "PYPROJECT", pyproject)
    monkeypatch.setattr(sync_version, "PLUGIN_JSON", plugin)
    monkeypatch.setattr(sync_version, "MARKETPLACE_JSON", market)

    assert sync_version.main(["--check"]) == 1
    assert sync_version.main([]) == 0
    assert json.loads(plugin.read_text(encoding="utf-8"))["version"] == "9.9.9"
    assert (
        json.loads(market.read_text(encoding="utf-8"))["metadata"]["version"] == "9.9.9"
    )
    assert sync_version.main(["--check"]) == 0
