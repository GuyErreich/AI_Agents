"""Unit tests for validate_plugin packaging gates."""

from __future__ import annotations

import json
from pathlib import Path

import validate_plugin as vp


def _minimal_plugin(root: Path) -> Path:
    """Create a tiny fake plugin tree for stray/PEP723 checks."""
    plugin = root / "plugins" / "ai-agents"
    (plugin / ".cursor-plugin").mkdir(parents=True)
    (plugin / ".cursor-plugin" / "plugin.json").write_text(
        json.dumps(
            {
                "name": "ai-agents",
                "description": "test",
                "version": "0.0.1",
                "hooks": "./hooks/hooks.json",
            }
        ),
        encoding="utf-8",
    )
    hooks = plugin / "hooks"
    hooks.mkdir()
    (hooks / "hooks.json").write_text(
        json.dumps(
            {
                "version": 1,
                "hooks": {
                    "stop": [
                        {
                            "command": "bash ./hooks/run-python.sh npm_dep_gate.py",
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    return plugin


def test_stray_hooks_tests_fails(tmp_path: Path) -> None:
    """Tracked hooks/tests directory is rejected."""
    plugin = _minimal_plugin(tmp_path)
    (plugin / "hooks" / "tests").mkdir()
    errors: list[str] = []
    vp.check_stray_artifacts(plugin, errors)
    assert any("hooks/tests" in e for e in errors)


def test_missing_pep723_on_entrypoint_fails(tmp_path: Path) -> None:
    """Entrypoint without PEP 723 metadata is an error."""
    plugin = _minimal_plugin(tmp_path)
    script = plugin / "hooks" / "npm_dep_gate.py"
    script.write_text("print('hi')\n", encoding="utf-8")
    events = {
        "stop": [{"command": "bash ./hooks/run-python.sh npm_dep_gate.py"}],
    }
    errors: list[str] = []
    vp.check_pep723_scripts(plugin, events, errors)
    assert any("PEP 723" in e for e in errors)


def test_library_module_without_pep723_ok(tmp_path: Path) -> None:
    """Private ``_*.py`` library modules do not require PEP 723."""
    plugin = _minimal_plugin(tmp_path)
    (plugin / "hooks" / "_types.py").write_text("x = 1\n", encoding="utf-8")
    (plugin / "hooks" / "npm_dep_gate.py").write_text(
        "# /// script\n# requires-python = \">=3.12\"\n# ///\nprint(1)\n",
        encoding="utf-8",
    )
    events = {
        "stop": [{"command": "bash ./hooks/run-python.sh npm_dep_gate.py"}],
    }
    errors: list[str] = []
    vp.check_pep723_scripts(plugin, events, errors)
    assert errors == []


def test_current_tree_validates() -> None:
    """The committed plugin tree must pass manifest validation."""
    assert vp.main() == 0
