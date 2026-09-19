"""Unit tests for scripts/hook_install_smoke.py helpers."""

from __future__ import annotations

import shutil
from pathlib import Path

import hook_install_smoke as smoke


def test_script_from_command() -> None:
    """Last token of the hook command is the script name."""
    assert (
        smoke._script_from_command("bash ./hooks/run-python.sh review_loop_budget.py")
        == "review_loop_budget.py"
    )


def test_copytree_ignore_drops_tests(tmp_path: Path) -> None:
    """Plugin copy for smoke install must not include a tests directory."""
    src = tmp_path / "src"
    hooks = src / "hooks"
    hooks.mkdir(parents=True)
    (hooks / "hooks.json").write_text("{}", encoding="utf-8")
    (hooks / "tests").mkdir()
    (hooks / "tests" / "x.py").write_text("pass\n", encoding="utf-8")
    (hooks / "state").mkdir()
    dst = tmp_path / "dst"
    shutil.copytree(
        src,
        dst,
        ignore=shutil.ignore_patterns(
            "__pycache__",
            ".pytest_cache",
            "tests",
            "state",
            "*.pyc",
        ),
    )
    assert (dst / "hooks" / "hooks.json").is_file()
    assert not (dst / "hooks" / "tests").exists()
    assert not (dst / "hooks" / "state").exists()


def test_hide_bins_shadows_names(tmp_path: Path) -> None:
    """Hidden PATH stubs exit 127 for shadowed binaries."""
    path = smoke._hide_bins(tmp_path, ["uv"])
    assert str(tmp_path / "hidden-bin") in path
    stub = tmp_path / "hidden-bin" / "uv"
    assert stub.is_file()
