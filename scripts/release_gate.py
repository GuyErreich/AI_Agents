#!/usr/bin/env python3
# Copyright (c) 2026 Guy Erreich
#
# SPDX-License-Identifier: MIT

"""Local release-gate orchestrator (mirrors CI release-gate checks).

Runs: uv audit, sync --check, validate_plugin, hook install smoke (with uv),
and optionally the degraded-toolchain smoke. Intended for the release milestone.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str], *, env: dict[str, str] | None = None) -> int:
    print("+", " ".join(cmd), flush=True)
    result = subprocess.run(cmd, cwd=REPO_ROOT, env=env, check=False)
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    """Run release-gate checks; return first non-zero exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-degraded",
        action="store_true",
        help="Skip the no-uv / no-python3.12 degraded smoke tests.",
    )
    args = parser.parse_args(argv)

    checks: list[list[str]] = [
        ["uv", "audit", "--frozen"],
        [sys.executable, str(REPO_ROOT / "scripts" / "sync_version.py"), "--check"],
        [sys.executable, str(REPO_ROOT / "scripts" / "validate_plugin.py")],
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "hook_install_smoke.py"),
            "--mode",
            "uv",
        ],
    ]
    if not args.skip_degraded:
        checks.append(
            [
                sys.executable,
                str(REPO_ROOT / "scripts" / "hook_install_smoke.py"),
                "--mode",
                "degraded",
            ]
        )

    env = os.environ.copy()
    env.setdefault("CI", "1")
    for cmd in checks:
        code = _run(cmd, env=env)
        if code != 0:
            return code
    print("release gate ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
