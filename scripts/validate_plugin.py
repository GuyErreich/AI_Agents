#!/usr/bin/env python3
# Copyright (c) 2026 Guy Erreich
#
# SPDX-License-Identifier: MIT

"""Validate Cursor marketplace and plugin manifests against the on-disk tree.

Exit 0 when every listed plugin has a manifest, required fields, and
discoverable skills/rules/agents/hooks. Exit 1 and print failures otherwise.

Extra release checks (version consistency, logo, hook events, executable bits,
reference links, stray artifacts, context budget) always run.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE_PATH = REPO_ROOT / ".cursor-plugin" / "marketplace.json"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
KEBAB = re.compile(r"^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
FRONTMATTER_CLOSE = "\n---"
VERSION_RE = re.compile(
    r'^version\s*=\s*["\']([^"\']+)["\']\s*$',
    re.MULTILINE,
)
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
ALWAYS_APPLY_RE = re.compile(
    r"^alwaysApply:\s*(true|false)\s*$",
    re.MULTILINE | re.IGNORECASE,
)

# Cursor-documented hook events (plugins reference).
KNOWN_HOOK_EVENTS = frozenset(
    {
        "sessionStart",
        "sessionEnd",
        "preToolUse",
        "postToolUse",
        "postToolUseFailure",
        "subagentStart",
        "subagentStop",
        "beforeShellExecution",
        "afterShellExecution",
        "beforeMCPExecution",
        "afterMCPExecution",
        "beforeReadFile",
        "afterFileEdit",
        "beforeSubmitPrompt",
        "preCompact",
        "stop",
        "afterAgentResponse",
        "afterAgentThought",
        "beforeTabFileRead",
        "afterTabFileEdit",
        "workspaceOpen",
    }
)

# Soft budget: always-applied rules inject into every session.
MAX_ALWAYS_APPLY_RULES = 12
MAX_ALWAYS_APPLY_BYTES = 48_000

STRAY_SUFFIXES = (".pyc",)


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


def _pyproject_version() -> str:
    text = PYPROJECT_PATH.read_text(encoding="utf-8")
    match = VERSION_RE.search(text)
    if not match:
        raise ValueError(f"{_rel(PYPROJECT_PATH)}: missing version")
    return match.group(1)


def _git_ls_files_mode(path: Path) -> str | None:
    """Return the git index mode for ``path``, or None if untracked."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "-s", "--", str(path.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    # Format: <mode> <sha> <stage>\t<path>
    return result.stdout.split(None, 1)[0]


def _expect_tag_version() -> str | None:
    """Optional expected version from RELEASE_TAG / GITHUB_REF_NAME."""
    for key in ("RELEASE_TAG", "GITHUB_REF_NAME"):
        raw = os.environ.get(key, "").strip()
        if not raw:
            continue
        tag = raw.removeprefix("refs/tags/")
        # Strip channel suffixes used by Action-Semver-Control.
        for suffix in ("-dev", "-rc"):
            if tag.endswith(suffix):
                tag = tag[: -len(suffix)]
                break
        if re.fullmatch(r"\d+\.\d+\.\d+", tag):
            return tag
    return None


def check_version_consistency(plugin_root: Path, errors: list[str]) -> None:
    """Require pyproject, plugin.json, marketplace metadata, and tag to agree."""
    try:
        expected = _pyproject_version()
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
        return

    manifest_path = plugin_root / ".cursor-plugin" / "plugin.json"
    try:
        manifest = _load_json(manifest_path)
    except ValueError as exc:
        errors.append(str(exc))
        return
    plugin_ver = str(manifest.get("version") or "")
    if plugin_ver != expected:
        errors.append(
            f"{_rel(manifest_path)}: version {plugin_ver!r} != pyproject {expected!r}"
        )

    try:
        marketplace = _load_json(MARKETPLACE_PATH)
    except ValueError as exc:
        errors.append(str(exc))
        return
    metadata = marketplace.get("metadata") if isinstance(marketplace, dict) else None
    market_ver = ""
    if isinstance(metadata, dict):
        market_ver = str(metadata.get("version") or "")
    if market_ver != expected:
        errors.append(
            f"{_rel(MARKETPLACE_PATH)}: metadata.version {market_ver!r} != "
            f"pyproject {expected!r}"
        )

    tag_ver = _expect_tag_version()
    if tag_ver is not None and tag_ver != expected:
        errors.append(f"release tag version {tag_ver!r} != pyproject {expected!r}")


def _is_unsafe_path(value: str) -> bool:
    """Return True when ``value`` looks like an absolute or escaping path."""
    if not value or value.startswith(("http://", "https://", "mailto:")):
        return False
    if value.startswith(("/", "\\", "~")):
        return True
    parts = Path(value).parts
    return ".." in parts


def _collect_path_like_strings(node: Any, *, prefix: str = "") -> list[tuple[str, str]]:
    """Walk JSON and collect string values that look like file paths."""
    found: list[tuple[str, str]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            path = f"{prefix}.{key}" if prefix else key
            # Manifest path fields and nested path references.
            if isinstance(value, str) and key in {
                "logo",
                "rules",
                "skills",
                "agents",
                "hooks",
                "commands",
                "mcpServers",
                "source",
                "pluginRoot",
            }:
                found.append((path, value))
            else:
                found.extend(_collect_path_like_strings(value, prefix=path))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(_collect_path_like_strings(value, prefix=f"{prefix}[{index}]"))
    return found


def check_manifest_paths(
    label: str,
    document: dict[str, Any],
    errors: list[str],
) -> None:
    """Reject absolute paths and ``..`` segments in manifest path fields."""
    for field, value in _collect_path_like_strings(document):
        if _is_unsafe_path(value):
            errors.append(
                f"{label}: {field} must be a relative path without '..' (got {value!r})"
            )


def check_readme(errors: list[str]) -> None:
    """Require a root README for marketplace submission."""
    readme = REPO_ROOT / "README.md"
    if not readme.is_file():
        errors.append("README.md: missing (required for marketplace submission)")
        return
    if not readme.read_text(encoding="utf-8").strip():
        errors.append("README.md: empty (required for marketplace submission)")


def check_logo(plugin_root: Path, manifest: dict[str, Any], errors: list[str]) -> None:
    """Require a committed logo referenced by relative path."""
    logo = str(manifest.get("logo") or "").strip()
    if not logo:
        errors.append(
            f"{_rel(plugin_root / '.cursor-plugin' / 'plugin.json')}: "
            "logo is required (relative path to committed asset)"
        )
        return
    if logo.startswith(("http://", "https://")):
        errors.append(
            f"{_rel(plugin_root / '.cursor-plugin' / 'plugin.json')}: "
            "logo must be a relative path in the repo, not a URL"
        )
        return
    if _is_unsafe_path(logo):
        errors.append(
            f"{_rel(plugin_root / '.cursor-plugin' / 'plugin.json')}: "
            f"logo must be a relative path without '..' (got {logo!r})"
        )
        return
    logo_path = (plugin_root / logo).resolve()
    if not logo_path.is_file():
        errors.append(f"{_rel(plugin_root)}: logo not found: {logo}")
        return
    mode = _git_ls_files_mode(logo_path)
    in_ci = bool(os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"))
    if mode is None and (REPO_ROOT / ".git").exists() and in_ci:
        # Allow untracked during local authoring; CI checkout is always tracked.
        errors.append(f"{_rel(logo_path)}: logo is not tracked by git")


def check_hook_events(
    hooks_path: Path,
    events: dict[str, Any],
    errors: list[str],
) -> None:
    """Reject unknown hook event names."""
    for event in events:
        if event not in KNOWN_HOOK_EVENTS:
            errors.append(
                f"{_rel(hooks_path)}: unknown hook event {event!r} "
                f"(known: {', '.join(sorted(KNOWN_HOOK_EVENTS))})"
            )


def check_executable_bits(
    plugin_root: Path,
    events: dict[str, Any],
    errors: list[str],
) -> None:
    """Ensure hook command scripts are executable in the git index."""
    scripts: set[Path] = set()
    for entries in events.values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            command = str(entry.get("command") or "").strip()
            if not command:
                continue
            script = command.split()[0]
            scripts.add((plugin_root / script).resolve())

    for script_path in sorted(scripts):
        if not script_path.is_file():
            continue
        mode = _git_ls_files_mode(script_path)
        if mode is None:
            # Fall back to filesystem bit when not in git (e.g. temp copy).
            if not os.access(script_path, os.X_OK):
                errors.append(f"{_rel(script_path)}: not executable")
            continue
        if mode != "100755":
            errors.append(f"{_rel(script_path)}: git mode {mode} (expected 100755)")


def check_reference_links(plugin_root: Path, errors: list[str]) -> None:
    """Fail when markdown relative links under skills/rules/agents are broken."""
    roots = [
        plugin_root / "skills",
        plugin_root / "rules",
        plugin_root / "agents",
    ]
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".md", ".mdc", ".markdown"}:
                continue
            text = path.read_text(encoding="utf-8")
            for _label, target in MD_LINK_RE.findall(text):
                target = target.strip()
                if not target or target.startswith(
                    ("http://", "https://", "mailto:", "#")
                ):
                    continue
                # Strip anchors.
                file_part = target.split("#", 1)[0]
                if not file_part:
                    continue
                resolved = (path.parent / file_part).resolve()
                try:
                    resolved.relative_to(plugin_root.resolve())
                except ValueError:
                    errors.append(f"{_rel(path)}: link escapes plugin root: {target}")
                    continue
                if not resolved.exists():
                    errors.append(f"{_rel(path)}: broken link: {target}")


def _git_ignored(path: Path) -> bool:
    """Return True when git would ignore ``path`` (local caches are OK)."""
    if not (REPO_ROOT / ".git").exists():
        return False
    try:
        result = subprocess.run(
            [
                "git",
                "check-ignore",
                "-q",
                "--",
                str(path.relative_to(REPO_ROOT)),
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
        )
    except OSError:
        return False
    return result.returncode == 0


def check_stray_artifacts(plugin_root: Path, errors: list[str]) -> None:
    """Reject cache / state paths that would ship (tracked / not gitignored)."""
    for path in plugin_root.rglob("*"):
        if _git_ignored(path):
            continue
        rel = path.relative_to(plugin_root).as_posix()
        if path.is_dir() and path.name in {"__pycache__", ".pytest_cache"}:
            errors.append(f"{_rel(path)}: stray cache directory must not ship")
        if rel.startswith("hooks/state/") or rel == "hooks/state":
            errors.append(f"{_rel(path)}: hooks/state must not ship")
        if path.is_file() and path.suffix in STRAY_SUFFIXES:
            errors.append(f"{_rel(path)}: stray bytecode must not ship")


def check_context_budget(plugin_root: Path, errors: list[str]) -> None:
    """Fail when always-applied rules exceed the soft context budget."""
    rules_dir = plugin_root / "rules"
    if not rules_dir.is_dir():
        return
    always: list[Path] = []
    total_bytes = 0
    for path in sorted(rules_dir.rglob("*.mdc")):
        text = path.read_text(encoding="utf-8")
        match = ALWAYS_APPLY_RE.search(text)
        if match and match.group(1).lower() == "true":
            always.append(path)
            total_bytes += len(text.encode("utf-8"))
    if len(always) > MAX_ALWAYS_APPLY_RULES:
        errors.append(
            f"{_rel(plugin_root)}: {len(always)} alwaysApply rules "
            f"(max {MAX_ALWAYS_APPLY_RULES})"
        )
    if total_bytes > MAX_ALWAYS_APPLY_BYTES:
        errors.append(
            f"{_rel(plugin_root)}: alwaysApply rules total {total_bytes} bytes "
            f"(max {MAX_ALWAYS_APPLY_BYTES})"
        )


def check_pep723_scripts(
    plugin_root: Path,
    events: dict[str, Any],
    errors: list[str],
) -> None:
    """Hook Python entrypoints via uv run --script need PEP 723 metadata."""
    for entries in events.values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            command = str(entry.get("command") or "").strip()
            parts = command.split()
            if len(parts) < 2:
                continue
            # ./hooks/run-python.sh review_loop_budget.py
            script_name = parts[-1]
            if not script_name.endswith(".py"):
                continue
            script_path = (plugin_root / "hooks" / script_name).resolve()
            if not script_path.is_file():
                continue
            text = script_path.read_text(encoding="utf-8")
            if "# /// script" not in text:
                errors.append(
                    f"{_rel(script_path)}: missing PEP 723 script metadata "
                    "(required for uv run --script)"
                )


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

    check_manifest_paths(_rel(manifest_path), manifest, errors)
    check_logo(plugin_root, manifest, errors)

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
        check_version_consistency(plugin_root, errors)
        check_reference_links(plugin_root, errors)
        check_stray_artifacts(plugin_root, errors)
        check_context_budget(plugin_root, errors)
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

    check_hook_events(hooks_path, events, errors)
    check_executable_bits(plugin_root, events, errors)
    check_pep723_scripts(plugin_root, events, errors)

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
                errors.append(f"{_rel(hooks_path)}: {loc} command not found: {script}")

    check_version_consistency(plugin_root, errors)
    check_reference_links(plugin_root, errors)
    check_stray_artifacts(plugin_root, errors)
    check_context_budget(plugin_root, errors)


def main() -> int:
    """Validate marketplace.json and every plugin it lists."""
    errors: list[str] = []
    check_readme(errors)
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

    check_manifest_paths(_rel(MARKETPLACE_PATH), marketplace, errors)

    plugin_root_prefix = Path(
        str((marketplace.get("metadata") or {}).get("pluginRoot") or ".")
    )
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        errors.append(f"{_rel(MARKETPLACE_PATH)}: plugins must be a non-empty list")
    else:
        seen_names: set[str] = set()
        for index, entry in enumerate(plugins):
            if not isinstance(entry, dict):
                errors.append(
                    f"{_rel(MARKETPLACE_PATH)}: plugins[{index}] must be an object"
                )
                continue
            plugin_name = str(entry.get("name") or "").strip()
            if plugin_name:
                if not KEBAB.match(plugin_name):
                    errors.append(
                        f"{_rel(MARKETPLACE_PATH)}: plugins[{index}].name "
                        "must be lowercase kebab-case"
                    )
                if plugin_name in seen_names:
                    errors.append(
                        f"{_rel(MARKETPLACE_PATH)}: duplicate plugin name "
                        f"{plugin_name!r}"
                    )
                seen_names.add(plugin_name)
            if not str(entry.get("description") or "").strip():
                errors.append(
                    f"{_rel(MARKETPLACE_PATH)}: plugins[{index}].description "
                    "is required"
                )
            source = str(entry.get("source") or "").strip()
            if not source:
                errors.append(
                    f"{_rel(MARKETPLACE_PATH)}: plugins[{index}] missing source"
                )
                continue
            if _is_unsafe_path(source):
                errors.append(
                    f"{_rel(MARKETPLACE_PATH)}: plugins[{index}].source "
                    f"must be a relative path without '..' (got {source!r})"
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
