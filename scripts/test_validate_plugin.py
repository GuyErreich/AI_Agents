# Copyright (c) 2026 Guy Erreich
#
# SPDX-License-Identifier: MIT

"""Smoke-test plugin validation against this repository."""

from __future__ import annotations

from pathlib import Path

import validate_plugin


def test_current_tree_validates() -> None:
    """The committed plugin tree must pass manifest validation."""
    assert validate_plugin.main() == 0


def _write_skill(path: Path, *, name: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nname: {name}\ndescription: test skill\n---\n# Test\n",
        encoding="utf-8",
    )
    return path


def test_skill_name_must_match_folder(tmp_path: Path) -> None:
    """Frontmatter name must equal the folder that contains SKILL.md."""
    skill = _write_skill(tmp_path / "commit" / "SKILL.md", name="ci-commit")
    errors: list[str] = []
    validate_plugin.check_skill_identity([skill], errors)
    assert any("ci-commit" in item and "commit" in item for item in errors)


def test_duplicate_skill_folder_names(tmp_path: Path) -> None:
    """Two SKILL.md parents with the same folder name fail validation."""
    first = _write_skill(tmp_path / "a" / "hierarchy" / "SKILL.md", name="hierarchy")
    second = _write_skill(
        tmp_path / "b" / "hierarchy" / "SKILL.md", name="agent-hierarchy"
    )
    errors: list[str] = []
    validate_plugin.check_skill_identity([first, second], errors)
    assert any("duplicate skill folder name 'hierarchy'" in item for item in errors)


def test_matching_unique_skill_names_pass(tmp_path: Path) -> None:
    """Aligned unique names produce no identity errors."""
    python = _write_skill(tmp_path / "python" / "SKILL.md", name="python")
    nodejs = _write_skill(tmp_path / "nodejs" / "SKILL.md", name="nodejs")
    errors: list[str] = []
    validate_plugin.check_skill_identity([python, nodejs], errors)
    assert errors == []
