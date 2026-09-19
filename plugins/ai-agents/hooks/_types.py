# Copyright (c) 2026 Guy Erreich
#
# SPDX-License-Identifier: MIT


"""Shared JSON/state type aliases for review-loop hooks (stdlib only)."""

from __future__ import annotations

from typing import TypedDict, cast

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]
type JsonObject = dict[str, JsonValue]


class LoopPreferences(TypedDict, total=False):
    max_rounds: int | None
    max_tokens_est: int
    max_usd_est: float
    pricing_mode: str
    reviewer_model: str
    fixer_model: str
    clean_passes_required: int
    manage_severity: str
    post_fix_focus: str
    diminishing_returns_round: int
    diminishing_returns_floor: str
    analysis_mode: str


# HookEvent is JsonObject for Cursor stdin payloads
type HookEvent = JsonObject


def as_object(value: object, default: JsonObject | None = None) -> JsonObject:
    """Narrow ``value`` to a JSON object."""
    if isinstance(value, dict):
        return cast(JsonObject, value)
    return {} if default is None else default


def as_list(value: object) -> list[JsonValue]:
    """Narrow ``value`` to a JSON array."""
    if isinstance(value, list):
        return cast(list[JsonValue], value)
    return []


def as_str(value: object, default: str = "") -> str:
    """Coerce a JSON value to ``str``."""
    if value is None:
        return default
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return str(value)
    return default


def as_int(value: object, default: int = 0) -> int:
    """Coerce a JSON value to ``int``."""
    if isinstance(value, bool):
        return int(value)
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def as_float(value: object, default: float = 0.0) -> float:
    """Coerce a JSON value to ``float``."""
    if isinstance(value, bool):
        return float(value)
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def as_json(value: object) -> JsonValue:
    """Cast an already-JSON-shaped value to ``JsonValue``."""
    return cast(JsonValue, value)
