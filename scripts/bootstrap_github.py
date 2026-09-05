#!/usr/bin/env python3
# Copyright (c) 2026 Guy Erreich
#
# SPDX-License-Identifier: MIT

"""Apply GitHub environments and branch rulesets for AI_Agents CD.

Run locally after signing in with ``gh auth login``:

    uv run python scripts/bootstrap_github.py --repo GuyErreich/AI_Agents

Use ``--dry-run`` to print the payloads without calling the GitHub API.
"""

from __future__ import annotations

import argparse
import json
import subprocess


def _gh_api(
    method: str,
    path: str,
    payload: dict | None = None,
    *,
    dry_run: bool,
) -> None:
    cmd = ["gh", "api", "-X", method, path]
    if payload is not None:
        cmd.extend(["--input", "-"])
    if dry_run:
        print(f"# {method} {path}")
        if payload is not None:
            print(json.dumps(payload, indent=2))
        return
    proc = subprocess.run(
        cmd,
        input=json.dumps(payload).encode() if payload is not None else None,
        check=False,
        capture_output=True,
        text=payload is None,
    )
    if proc.returncode != 0:
        stderr = proc.stderr.decode() if isinstance(proc.stderr, bytes) else proc.stderr
        raise RuntimeError(f"gh api failed ({path}): {stderr}")


def _user_id(*, dry_run: bool) -> int:
    if dry_run:
        return 0
    out = subprocess.check_output(["gh", "api", "user", "--jq", ".id"], text=True)
    return int(out.strip())


def apply_environments(repo: str, *, dry_run: bool) -> None:
    user_id = _user_id(dry_run=dry_run)
    base = f"repos/{repo}/environments"
    _gh_api(
        "PUT",
        f"{base}/staging",
        {
            "can_admins_bypass": True,
            "deployment_branch_policy": {
                "protected_branches": False,
                "custom_branch_policies": True,
            },
        },
        dry_run=dry_run,
    )
    _gh_api(
        "PUT",
        f"{base}/production",
        {
            "can_admins_bypass": True,
            "reviewers": [{"type": "User", "id": user_id}],
            "deployment_branch_policy": {
                "protected_branches": False,
                "custom_branch_policies": True,
            },
        },
        dry_run=dry_run,
    )
    if not dry_run:
        # Branch tips (marketplace indexes branches) plus publish tags.
        _gh_api(
            "POST",
            f"{base}/staging/deployment-branch-policies",
            {"name": "staging", "type": "branch"},
            dry_run=dry_run,
        )
        _gh_api(
            "POST",
            f"{base}/staging/deployment-branch-policies",
            {"name": "*.*.*-rc", "type": "tag"},
            dry_run=dry_run,
        )
        _gh_api(
            "POST",
            f"{base}/production/deployment-branch-policies",
            {"name": "master", "type": "branch"},
            dry_run=dry_run,
        )
        _gh_api(
            "POST",
            f"{base}/production/deployment-branch-policies",
            {"name": "*.*.*", "type": "tag"},
            dry_run=dry_run,
        )


def apply_rulesets(repo: str, *, dry_run: bool) -> None:
    gh_actions = 15368
    codeql = 57789
    standard = {
        "name": "Standard Flow (dev, staging & master)",
        "target": "branch",
        "enforcement": "active",
        "conditions": {
            "ref_name": {
                "include": [
                    "refs/heads/dev",
                    "refs/heads/staging",
                    "refs/heads/master",
                ],
                "exclude": [],
            }
        },
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {"type": "required_signatures"},
            {
                "type": "required_status_checks",
                "parameters": {
                    "strict_required_status_checks_policy": True,
                    "do_not_enforce_on_create": False,
                    "required_status_checks": [
                        {"context": "Lint, test, plugin", "integration_id": gh_actions},
                        {"context": "Workflow lint", "integration_id": gh_actions},
                        {"context": "Gitleaks", "integration_id": gh_actions},
                        {"context": "SAST", "integration_id": gh_actions},
                        {"context": "Analyze Python", "integration_id": codeql},
                        {"context": "license-check", "integration_id": gh_actions},
                    ],
                },
            },
            {
                "type": "pull_request",
                "parameters": {
                    "required_approving_review_count": 1,
                    "dismiss_stale_reviews_on_push": True,
                    "require_code_owner_review": True,
                    "require_last_push_approval": True,
                    "required_review_thread_resolution": True,
                    "require_extra_approval_for_unattributed_changes": True,
                    "allowed_merge_methods": ["squash"],
                },
            },
            {"type": "copilot_code_review", "parameters": {"review_on_push": True}},
            {"type": "code_quality", "parameters": {"severity": "errors"}},
            {
                "type": "code_scanning",
                "parameters": {
                    "code_scanning_tools": [
                        {
                            "tool": "CodeQL",
                            "security_alerts_threshold": "high_or_higher",
                            "alerts_threshold": "errors",
                        }
                    ]
                },
            },
            {
                "type": "code_coverage",
                "parameters": {"minimum_coverage": 90, "max_coverage_drop": 5},
            },
        ],
        # Repository admins: bypass only via PR. Auto Semver Bot (same Integration
        # as Action-Semver-Control): always, so finalize auto-promote / promote
        # can update staging without required checks on a direct ref update.
        "bypass_actors": [
            {
                "actor_id": 5,
                "actor_type": "RepositoryRole",
                "bypass_mode": "pull_request",
            },
            {
                "actor_id": 2720857,
                "actor_type": "Integration",
                "bypass_mode": "always",
            },
        ],
    }
    linear_dev = {
        "name": "Linear history (dev only)",
        "target": "branch",
        "enforcement": "active",
        "conditions": {
            "ref_name": {"include": ["refs/heads/dev"], "exclude": []},
        },
        "rules": [{"type": "required_linear_history"}],
    }
    _gh_api("POST", f"repos/{repo}/rulesets", standard, dry_run=dry_run)
    _gh_api("POST", f"repos/{repo}/rulesets", linear_dev, dry_run=dry_run)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="GuyErreich/AI_Agents")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--environments-only", action="store_true")
    parser.add_argument("--rulesets-only", action="store_true")
    args = parser.parse_args()

    if not args.rulesets_only:
        apply_environments(args.repo, dry_run=args.dry_run)
    if not args.environments_only:
        apply_rulesets(args.repo, dry_run=args.dry_run)
    print("bootstrap complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
