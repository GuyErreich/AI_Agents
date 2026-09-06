#!/usr/bin/env python3
# Copyright (c) 2026 Guy Erreich
#
# SPDX-License-Identifier: MIT

"""Clean-clone hook install smoke test.

Copies only ``plugins/ai-agents`` into a scratch local-plugins dir (no repo
root pyproject/uv.lock/.venv) and drives each hooks.json command with sample
stdin JSON. Modes:

- ``uv``: PATH must include uv (or we install nothing — require preinstalled).
- ``python``: hide uv; require system python3 >= 3.12.
- ``degraded``: hide uv and python3 >= 3.12; expect allow/degraded JSON, exit 0.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_SRC = REPO_ROOT / "plugins" / "ai-agents"

SAMPLE_PAYLOADS: dict[str, dict] = {
    "review_loop_budget.py": {
        "subagent_type": "pr-reviewer",
        "workspace_roots": [],
    },
    "review_loop_round.py": {
        "subagent_type": "pr-reviewer",
        "status": "completed",
        "workspace_roots": [],
    },
    "review_loop_git_guard.py": {
        "command": "git status",
        "workspace_roots": [],
    },
    "npm_dep_gate.py": {
        "file_path": "package.json",
        "workspace_roots": [],
    },
}


def _load_hook_commands(plugin_root: Path) -> list[tuple[str, str]]:
    hooks_path = plugin_root / "hooks" / "hooks.json"
    hooks = json.loads(hooks_path.read_text(encoding="utf-8"))
    events = hooks.get("hooks") or {}
    out: list[tuple[str, str]] = []
    for event, entries in events.items():
        for entry in entries:
            command = str(entry.get("command") or "").strip()
            if command:
                out.append((event, command))
    return out


def _script_from_command(command: str) -> str:
    parts = command.split()
    return parts[-1] if parts else ""


def _hide_bins(tmpdir: Path, names: list[str]) -> str:
    """Return a PATH with stub bins that fail, shadowing real tools."""
    bin_dir = tmpdir / "hidden-bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        stub = bin_dir / name
        stub.write_text("#!/bin/sh\nexit 127\n", encoding="utf-8")
        stub.chmod(0o755)
    return f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"


def _run_hook(
    *,
    plugin_root: Path,
    workspace: Path,
    command: str,
    payload: dict,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-c", command],
        cwd=plugin_root,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def run_smoke(*, mode: str) -> int:
    """Execute the smoke test; return process exit code."""
    with tempfile.TemporaryDirectory(prefix="ai-agents-smoke-") as raw:
        tmp = Path(raw)
        plugin_dst = tmp / "local" / "ai-agents"
        plugin_dst.parent.mkdir(parents=True)
        shutil.copytree(
            PLUGIN_SRC,
            plugin_dst,
            ignore=shutil.ignore_patterns(
                "__pycache__",
                ".pytest_cache",
                "tests",
                "state",
                "*.pyc",
            ),
        )
        # Ensure run-python.sh is executable in the copy.
        run_py = plugin_dst / "hooks" / "run-python.sh"
        run_py.chmod(run_py.stat().st_mode | 0o111)

        workspace = tmp / "workspace"
        workspace.mkdir()
        (workspace / ".git").mkdir()  # soft signal for resolve_root

        env = os.environ.copy()
        env["REVIEW_LOOP_ROOT"] = str(workspace)
        env.pop("VIRTUAL_ENV", None)

        if mode == "uv":
            if shutil.which("uv") is None:
                print("uv not found on PATH", file=sys.stderr)
                return 1
        elif mode == "python":
            env["PATH"] = _hide_bins(tmp, ["uv"])
        elif mode == "degraded":
            env["PATH"] = _hide_bins(tmp, ["uv", "python3", "python"])
        else:
            print(f"unknown mode: {mode}", file=sys.stderr)
            return 1

        failures = 0
        for event, command in _load_hook_commands(plugin_dst):
            script = _script_from_command(command)
            payload = dict(SAMPLE_PAYLOADS.get(script, {"workspace_roots": []}))
            payload["workspace_roots"] = [str(workspace)]
            result = _run_hook(
                plugin_root=plugin_dst,
                workspace=workspace,
                command=command,
                payload=payload,
                env=env,
            )
            # Hooks must always exit 0 (failClosed only on crash).
            if result.returncode != 0:
                print(
                    f"FAIL {event} {command}: exit {result.returncode}\n"
                    f"stdout={result.stdout!r}\nstderr={result.stderr!r}",
                    file=sys.stderr,
                )
                failures += 1
                continue
            stdout = result.stdout.strip()
            if not stdout:
                # Some hooks may print nothing in inactive state; accept empty
                # only for degraded mode.
                if mode != "degraded":
                    print(
                        f"FAIL {event} {command}: empty stdout",
                        file=sys.stderr,
                    )
                    failures += 1
                else:
                    print(f"ok {event} {script} (empty degraded)")
                continue
            try:
                json.loads(stdout.splitlines()[-1])
            except json.JSONDecodeError:
                # Degraded defaults are JSON; require parseable last line.
                print(
                    f"FAIL {event} {command}: non-JSON stdout: {stdout!r}",
                    file=sys.stderr,
                )
                failures += 1
                continue
            print(f"ok {event} {script}")

        if failures:
            print(f"{failures} hook smoke failure(s)", file=sys.stderr)
            return 1
        print(f"hook install smoke ok (mode={mode})")
        return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("uv", "python", "degraded"),
        default="uv",
        help="Toolchain mode to simulate.",
    )
    args = parser.parse_args(argv)
    return run_smoke(mode=args.mode)


if __name__ == "__main__":
    raise SystemExit(main())
