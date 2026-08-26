# Copyright (c) 2026 Guy Erreich
#
# SPDX-License-Identifier: MIT

"""Smoke-test plugin validation against this repository."""

from __future__ import annotations

import validate_plugin


def test_current_tree_validates() -> None:
    """The committed plugin tree must pass manifest validation."""
    assert validate_plugin.main() == 0
