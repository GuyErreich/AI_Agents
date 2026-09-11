#!/usr/bin/env python3
# Copyright (c) 2026 Guy Erreich
#
# SPDX-License-Identifier: MIT

"""Sync plugin/marketplace JSON versions from pyproject.toml.

Action-Semver-Control's VersionFileUpdater cannot update JSON lines that end
with a comma. Keep pyproject.toml as the source of truth and propagate here.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"
PLUGIN_JSON = REPO_ROOT / "plugins" / "ai-agents" / ".cursor-plugin" / "plugin.json"
MARKETPLACE_JSON = REPO_ROOT / ".cursor-plugin" / "marketplace.json"

VERSION_RE = re.compile(
    r'^version\s*=\s*["\']([^"\']+)["\']\s*$',
    re.MULTILINE,
)


def read_pyproject_version(path: Path | None = None) -> str:
    """Return the project version from ``pyproject.toml``."""
    target = path if path is not None else PYPROJECT
    text = target.read_text(encoding="utf-8")
    match = VERSION_RE.search(text)
    if not match:
        raise ValueError(f'no version = "..." found in {target}')
    return match.group(1)


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be an object")
    return data


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def sync_plugin_json(version: str, *, check_only: bool) -> bool:
    """Update ``plugin.json`` version. Return True if a change was needed."""
    data = _load_json(PLUGIN_JSON)
    current = str(data.get("version") or "")
    if current == version:
        return False
    if check_only:
        return True
    data["version"] = version
    _write_json(PLUGIN_JSON, data)
    return True


def sync_marketplace_json(version: str, *, check_only: bool) -> bool:
    """Update marketplace metadata.version. Return True if change needed."""
    data = _load_json(MARKETPLACE_JSON)
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
        data["metadata"] = metadata
    current = str(metadata.get("version") or "")
    if current == version:
        return False
    if check_only:
        return True
    metadata["version"] = version
    _write_json(MARKETPLACE_JSON, data)
    return True


def main(argv: list[str] | None = None) -> int:
    """CLI entry: sync or check version consistency."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if JSON versions drift from pyproject.toml (no writes).",
    )
    args = parser.parse_args(argv)

    try:
        version = read_pyproject_version()
    except (OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1

    try:
        plugin_dirty = sync_plugin_json(version, check_only=args.check)
        market_dirty = sync_marketplace_json(version, check_only=args.check)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(exc, file=sys.stderr)
        return 1

    if args.check:
        if plugin_dirty or market_dirty:
            print(
                f"version drift: pyproject.toml={version}; run scripts/sync_version.py",
                file=sys.stderr,
            )
            return 1
        print(f"version sync ok ({version})")
        return 0

    changed = []
    if plugin_dirty:
        changed.append(_display_path(PLUGIN_JSON))
    if market_dirty:
        changed.append(_display_path(MARKETPLACE_JSON))
    if changed:
        print(f"synced version {version} -> {', '.join(changed)}")
    else:
        print(f"already at {version}")
    return 0


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
