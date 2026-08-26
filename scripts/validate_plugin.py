#!/usr/bin/env python3
# Copyright (c) 2026 Guy Erreich
#
# SPDX-License-Identifier: MIT

"""Validate Cursor marketplace and plugin manifests against the on-disk tree.

Exit 0 when every listed plugin has a manifest, required fields, and
discoverable skills/rules/agents/hooks. Exit 1 and print failures otherwise.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE_PATH = REPO_ROOT / ".cursor-plugin" / "marketplace.json"
KEBAB = re.compile(r"^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
FRONTMATTER_CLOSE = "\n---"


def _load_json(path: Path) -> Any:
    """Parse JSON or raise a tagged error string."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"missing {path.relative_to(REPO_ROOT)}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON {path.relative_to(REPO_ROOT)}: {exc}") from exc


def _frontmatter(path: Path) -> dict[str, str]:
    """Return simple ``key: value`` pairs from YAML frontmatter."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    close = text.find(FRONTMATTER_CLOSE, 3)
    if close == -1:
        return {}
    fields: dict[str, str] = {}
    for raw in text[4:close].splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip("\"'")
    return fields


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def validate_plugin(plugin_root: Path, errors: list[str]) -> None:
    """Check one Cursor plugin directory."""
    manifest_path = plugin_root / ".cursor-plugin" / "plugin.json"
    try:
        manifest = _load_json(manifest_path)
    except ValueError as exc:
        errors.append(str(exc))
        return
    if not isinstance(manifest, dict):
        errors.append(f"{_rel(manifest_path)}: root must be an object")
        return

    name = str(manifest.get("name") or "")
    if not name or not KEBAB.match(name):
        errors.append(f"{_rel(manifest_path)}: name must be lowercase kebab-case")
    if not str(manifest.get("description") or "").strip():
        errors.append(f"{_rel(manifest_path)}: description is required")

    skills_dir = plugin_root / "skills"
    skill_files = sorted(skills_dir.rglob("SKILL.md")) if skills_dir.is_dir() else []
    if not skill_files:
        errors.append(f"{_rel(plugin_root)}: no skills/**/SKILL.md found")
    for skill in skill_files:
        meta = _frontmatter(skill)
        if not meta.get("name"):
            errors.append(f"{_rel(skill)}: missing frontmatter name")
        if not meta.get("description"):
            errors.append(f"{_rel(skill)}: missing frontmatter description")

    rules_dir = plugin_root / "rules"
    rule_files = sorted(rules_dir.rglob("*.mdc")) if rules_dir.is_dir() else []
    if not rule_files:
        errors.append(f"{_rel(plugin_root)}: no rules/**/*.mdc found")
    for rule in rule_files:
        meta = _frontmatter(rule)
        if not meta.get("description"):
            errors.append(f"{_rel(rule)}: missing frontmatter description")

    agents_dir = plugin_root / "agents"
    if agents_dir.is_dir():
        for agent in sorted(agents_dir.glob("*.md")):
            meta = _frontmatter(agent)
            if not meta.get("name"):
                errors.append(f"{_rel(agent)}: missing frontmatter name")
            if not meta.get("description"):
                errors.append(f"{_rel(agent)}: missing frontmatter description")

    hooks_rel = str(manifest.get("hooks") or "hooks/hooks.json")
    hooks_path = (plugin_root / hooks_rel).resolve()
    if not hooks_path.is_file():
        errors.append(f"{_rel(plugin_root)}: hooks file missing ({hooks_rel})")
        return
    try:
        hooks_doc = _load_json(hooks_path)
    except ValueError as exc:
        errors.append(str(exc))
        return
    events = hooks_doc.get("hooks") if isinstance(hooks_doc, dict) else None
    if not isinstance(events, dict):
        errors.append(f"{_rel(hooks_path)}: hooks.hooks must be an object")
        return
    for event, entries in events.items():
        if not isinstance(entries, list):
            errors.append(f"{_rel(hooks_path)}: hooks.{event} must be a list")
            continue
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                loc = f"hooks.{event}[{index}]"
                errors.append(f"{_rel(hooks_path)}: {loc} must be an object")
                continue
            command = str(entry.get("command") or "").strip()
            if not command:
                loc = f"hooks.{event}[{index}]"
                errors.append(f"{_rel(hooks_path)}: {loc} missing command")
                continue
            script = command.split()[0]
            script_path = (plugin_root / script).resolve()
            if not script_path.is_file():
                loc = f"hooks.{event}[{index}]"
                errors.append(
                    f"{_rel(hooks_path)}: {loc} command not found: {script}"
                )


def main() -> int:
    """Validate marketplace.json and every plugin it lists."""
    errors: list[str] = []
    try:
        marketplace = _load_json(MARKETPLACE_PATH)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    if not isinstance(marketplace, dict):
        print(f"{_rel(MARKETPLACE_PATH)}: root must be an object", file=sys.stderr)
        return 1
    if not KEBAB.match(str(marketplace.get("name") or "")):
        errors.append(f"{_rel(MARKETPLACE_PATH)}: name must be lowercase kebab-case")
    owner = marketplace.get("owner")
    if not isinstance(owner, dict) or not str(owner.get("name") or "").strip():
        errors.append(f"{_rel(MARKETPLACE_PATH)}: owner.name is required")

    plugin_root_prefix = Path(
        str((marketplace.get("metadata") or {}).get("pluginRoot") or ".")
    )
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        errors.append(f"{_rel(MARKETPLACE_PATH)}: plugins must be a non-empty list")
    else:
        for index, entry in enumerate(plugins):
            if not isinstance(entry, dict):
                errors.append(
                    f"{_rel(MARKETPLACE_PATH)}: plugins[{index}] must be an object"
                )
                continue
            source = str(entry.get("source") or "").strip()
            if not source:
                errors.append(
                    f"{_rel(MARKETPLACE_PATH)}: plugins[{index}] missing source"
                )
                continue
            plugin_dir = (REPO_ROOT / plugin_root_prefix / source).resolve()
            if not plugin_dir.is_dir():
                errors.append(
                    f"{_rel(MARKETPLACE_PATH)}: plugins[{index}] "
                    f"source not found: {source}"
                )
                continue
            validate_plugin(plugin_dir, errors)

    if errors:
        for item in errors:
            print(item, file=sys.stderr)
        print(f"{len(errors)} plugin validation error(s)", file=sys.stderr)
        return 1
    print("plugin validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
