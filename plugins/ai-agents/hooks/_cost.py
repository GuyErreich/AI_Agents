#!/usr/bin/env python3
# Copyright (c) 2026 Guy Erreich
#
# SPDX-License-Identifier: MIT

# /// script
# requires-python = ">=3.12"
# ///

"""Estimate tokens and dollars from Cursor agent-transcript JSONL files.

Cursor does not persist billed token counts. This reconstructs an estimate by
modelling context re-send: every assistant turn re-sends prior messages. A
naive character count would understate the bill.

Pricing modes:
- ``auto`` — Cursor Auto / inherit / Composer-on-plan (much cheaper effective $)
- ``api`` — named frontier models at approximate API list rates
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class CostEstimate:
    """Estimated cost for one or more transcripts."""

    tokens_in_est: int
    tokens_out_est: int
    tokens_est: int
    usd_est: float
    turns: int
    tool_calls: int
    wall_clock_s: float
    model: str
    assumptions: str
    known_model: bool
    pricing_mode: str = "auto"

    def to_dict(self) -> dict[str, Any]:
        """Serialize for state.json."""
        return asdict(self)


# User-facing aliases → Task `model` slugs (keep `inherit` as the cheap default).
MODEL_ALIASES: dict[str, str] = {
    "auto": "inherit",
    "inherit": "inherit",
    "composer": "inherit",
    "fast": "composer-2.5-fast",
    "opus": "claude-opus-5-thinking-high",
    "opus-5": "claude-opus-5-thinking-high",
    "opus5": "claude-opus-5-thinking-high",
    "claude-opus-5": "claude-opus-5-thinking-high",
    "claude-opus-5-thinking-high": "claude-opus-5-thinking-high",
    "sonnet": "claude-sonnet-5-thinking-high",
    "sonnet-5": "claude-sonnet-5-thinking-high",
    "sonnet5": "claude-sonnet-5-thinking-high",
    "claude-sonnet-5": "claude-sonnet-5-thinking-high",
    "claude-sonnet-5-thinking-high": "claude-sonnet-5-thinking-high",
    "fable": "claude-fable-5-thinking-high",
    "claude-fable-5-thinking-high": "claude-fable-5-thinking-high",
    "grok": "cursor-grok-4.5-high-fast",
    "cursor-grok-4.5-high-fast": "cursor-grok-4.5-high-fast",
    "gpt": "gpt-5.6-sol-medium",
    "gpt-5.6": "gpt-5.6-sol-medium",
    "gpt-5.6-sol-medium": "gpt-5.6-sol-medium",
    "gpt-5.6-terra-medium": "gpt-5.6-terra-medium",
    "composer-2.5-fast": "composer-2.5-fast",
}


def normalize_loop_model(raw: str | None) -> str:
    """Map a user/model hint to a Task ``model`` slug. Default: ``inherit``."""
    text = (raw or "").strip().lower()
    if not text:
        return "inherit"
    if text in MODEL_ALIASES:
        return MODEL_ALIASES[text]
    # Allow exact Task slugs that are not aliased yet.
    if (
        text.startswith("claude-")
        or text.startswith("gpt-")
        or text.startswith("cursor-")
    ):
        return text
    return "inherit"


def segment_pricing_mode(model: str | None) -> str:
    """Return ``auto`` or ``api`` rates for one subagent model (segment honesty)."""
    slug = normalize_loop_model(model)
    if slug in {"inherit", "auto"} or "composer" in slug or "auto" in slug:
        return "auto"
    if any(
        key in slug
        for key in ("claude", "opus", "sonnet", "gpt", "o1", "o3", "gemini", "grok")
    ):
        return "api"
    return "auto"


def resolve_pricing_mode(
    pricing: dict[str, Any],
    *,
    state: dict[str, Any] | None = None,
    model: str | None = None,
    explicit: str | None = None,
) -> str:
    """Return ``auto`` or ``api`` for budget/rate selection.

    Priority: explicit arg → **model segment** (named frontier → api for that
    estimate) → state.pricing_mode → pricing.default_mode → ``auto``.

    Loop-level caps stay on ``state.pricing_mode`` (default auto) so people are
    not pushed into expensive budgets; named-model *estimates* still use api
    rates so projective checks stay honest.
    """
    if explicit in {"auto", "api"}:
        return explicit
    if model:
        return segment_pricing_mode(model)
    if state:
        mode = str(state.get("pricing_mode") or "").strip().lower()
        if mode in {"auto", "api"}:
            return mode
    default = str(pricing.get("default_mode") or "auto").strip().lower()
    return default if default in {"auto", "api"} else "auto"


def _as_dict(value: object) -> dict[str, Any]:
    """Narrow an unknown value to a plain dict, else empty."""
    if isinstance(value, dict):
        return {str(k): v for k, v in value.items()}
    return {}


def resolve_model_key(
    pricing: dict[str, Any],
    model: str,
    pricing_mode: str,
) -> str:
    """Map a raw model slug to a pricing.models key."""
    models = _as_dict(pricing.get("models"))
    slug = (model or "").strip().lower() or "default"

    if pricing_mode == "auto":
        auto_cfg = _as_dict(_as_dict(pricing.get("modes")).get("auto"))
        preferred = str(auto_cfg.get("model_key") or "auto")
        if preferred in models:
            return preferred
        if "auto" in models:
            return "auto"
        if "inherit" in models:
            return "inherit"

    normalized = normalize_loop_model(slug)
    if normalized in models:
        return normalized
    if slug in models:
        return slug
    for key in models:
        if key != "default" and key in slug:
            return str(key)
    # Map opus-5 / sonnet-5 Task slugs onto closest priced keys.
    if "opus" in slug:
        for candidate in ("claude-opus-5", "claude-opus-4", "default"):
            if candidate in models:
                return candidate
    if "sonnet" in slug:
        for candidate in ("claude-sonnet-5", "claude-sonnet-4", "default"):
            if candidate in models:
                return candidate
    return "default"


def mode_budget_defaults(
    pricing: dict[str, Any], pricing_mode: str
) -> dict[str, float]:
    """Return recommended caps / cold-start projection for a pricing mode."""
    modes = _as_dict(pricing.get("modes"))
    cfg = _as_dict(modes.get(pricing_mode))
    if pricing_mode == "auto":
        return {
            "max_tokens_est": float(cfg.get("max_tokens_est", 1_000_000) or 1_000_000),
            "max_usd_est": float(cfg.get("max_usd_est", 2.0) or 2.0),
            "cold_project_tokens": float(
                cfg.get("cold_project_tokens", 120_000) or 120_000
            ),
            "cold_project_usd": float(cfg.get("cold_project_usd", 0.15) or 0.15),
        }
    return {
        "max_tokens_est": float(cfg.get("max_tokens_est", 400_000) or 400_000),
        "max_usd_est": float(cfg.get("max_usd_est", 3.0) or 3.0),
        "cold_project_tokens": float(cfg.get("cold_project_tokens", 80_000) or 80_000),
        "cold_project_usd": float(cfg.get("cold_project_usd", 0.75) or 0.75),
    }


def _message_text(message: dict[str, Any]) -> str:
    """Flatten a transcript message content into plain text for sizing."""
    content = message.get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            parts.append(str(block.get("text", "")))
        elif "input" in block:
            parts.append(json.dumps(block.get("input"), default=str))
        elif "name" in block:
            parts.append(str(block.get("name", "")))
    return "\n".join(parts)


def _count_tool_calls(message: dict[str, Any]) -> int:
    """Count tool-call content blocks in a message."""
    content = message.get("content")
    if not isinstance(content, list):
        return 0
    count = 0
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") in {"tool_use", "tool_call", "function_call"} or (
            "name" in block and "input" in block
        ):
            count += 1
    return count


def read_transcript(path: Path) -> list[dict[str, Any]]:
    """Load a JSONL transcript into a list of message objects."""
    rows: list[dict[str, Any]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return rows
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            rows.append(obj)
    return rows


def estimate_transcript(
    path: Path,
    pricing: dict[str, Any],
    model: str = "default",
    *,
    pricing_mode: str | None = None,
    state: dict[str, Any] | None = None,
) -> CostEstimate:
    """Estimate cost for a single transcript with context re-send modelling."""
    mode = resolve_pricing_mode(
        pricing, state=state, model=model, explicit=pricing_mode
    )
    model_key = resolve_model_key(pricing, model, mode)

    chars_per_token = float(pricing.get("chars_per_token", 3.9) or 3.9)
    if chars_per_token <= 0:
        chars_per_token = 3.9
    discount = float(pricing.get("cached_prefix_discount", 0.5) or 0.5)
    discount = min(max(discount, 0.0), 1.0)

    models = _as_dict(pricing.get("models"))
    model_rates = models.get(model_key)
    rates: dict[str, Any]
    if isinstance(model_rates, dict):
        rates = model_rates
        known_model = True
    else:
        rates = _as_dict(models.get("default"))
        known_model = False
    input_rate = float(rates.get("input_per_mtok", 2.0) or 2.0)
    output_rate = float(rates.get("output_per_mtok", 10.0) or 10.0)

    mode_cfg = _as_dict(_as_dict(pricing.get("modes")).get(mode))
    usd_multiplier = float(mode_cfg.get("usd_multiplier", 1.0) or 1.0)

    rows = read_transcript(path)
    cumulative_chars = 0
    tokens_in = 0.0
    tokens_out = 0.0
    turns = 0
    tool_calls = 0
    prior_prefix_chars = 0

    for row in rows:
        role = row.get("role")
        message = row.get("message") if isinstance(row.get("message"), dict) else row
        if role not in {"user", "assistant"} and row.get("type") not in {
            None,
            "message",
        }:
            continue
        if role not in {"user", "assistant"}:
            continue

        text = _message_text(message if isinstance(message, dict) else {})
        chars = len(text)
        tool_calls += _count_tool_calls(message if isinstance(message, dict) else {})

        if role == "user":
            cumulative_chars += chars
            continue

        turns += 1
        fresh_chars = max(cumulative_chars - prior_prefix_chars, 0)
        cached_chars = prior_prefix_chars
        effective_input_chars = fresh_chars + (cached_chars * (1.0 - discount))
        tokens_in += effective_input_chars / chars_per_token
        tokens_out += chars / chars_per_token
        prior_prefix_chars = cumulative_chars
        cumulative_chars += chars

    tokens_in_i = int(round(tokens_in))
    tokens_out_i = int(round(tokens_out))
    tokens_total = tokens_in_i + tokens_out_i

    usd = 0.0
    if known_model or "default" in models:
        usd = (
            (tokens_in_i / 1_000_000.0) * input_rate
            + (tokens_out_i / 1_000_000.0) * output_rate
        ) * usd_multiplier

    updated = str(pricing.get("updated", "unknown"))
    mode_label = str(mode_cfg.get("label") or mode)
    assumptions = (
        f"pricing_mode={mode} ({mode_label}); model_key={model_key}; "
        f"chars/token {chars_per_token}; cached_prefix_discount {discount}; "
        f"prices dated {updated}"
        + ("" if known_model else " (unknown model — default rates)")
    )

    return CostEstimate(
        tokens_in_est=tokens_in_i,
        tokens_out_est=tokens_out_i,
        tokens_est=tokens_total,
        usd_est=round(usd, 4),
        turns=turns,
        tool_calls=tool_calls,
        wall_clock_s=0.0,
        model=model_key if known_model else f"{model_key}|default",
        assumptions=assumptions,
        known_model=known_model,
        pricing_mode=mode,
    )


def find_subagent_transcripts(
    started_at_iso: str | None = None,
    transcripts_root: Path | None = None,
) -> list[Path]:
    """Find subagent JSONL files newer than started_at under agent-transcripts."""
    roots: list[Path] = []
    if transcripts_root is not None:
        roots.append(transcripts_root)
    else:
        projects = Path.home() / ".cursor" / "projects"
        if projects.is_dir():
            roots.extend(projects.iterdir())

    cutoff = 0.0
    if started_at_iso:
        try:
            from datetime import datetime

            cutoff = datetime.fromisoformat(
                started_at_iso.replace("Z", "+00:00")
            ).timestamp()
        except ValueError:
            cutoff = 0.0

    found: list[Path] = []
    for root in roots:
        sub = root / "agent-transcripts"
        if not sub.is_dir():
            candidates = list(root.glob("**/subagents/*.jsonl"))
        else:
            candidates = list(sub.glob("**/subagents/*.jsonl"))
        for path in candidates:
            try:
                if path.stat().st_mtime >= cutoff - 1.0:
                    found.append(path)
            except OSError:
                continue

    found.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return found


def estimate_since(
    pricing: dict[str, Any],
    started_at_iso: str,
    model: str = "default",
    transcripts_root: Path | None = None,
    *,
    state: dict[str, Any] | None = None,
    pricing_mode: str | None = None,
    transcript_path: str | Path | None = None,
) -> CostEstimate:
    """Estimate cost for a finished subagent.

    Prefer ``transcript_path`` (from ``subagentStop.agent_transcript_path``)
    when readable — that is the authoritative file. Fall back to an mtime
    scan of subagent transcripts newer than ``started_at_iso`` only when
    the explicit path is missing or unreadable.
    """
    mode = resolve_pricing_mode(
        pricing, state=state, model=model, explicit=pricing_mode
    )

    if transcript_path:
        path = Path(transcript_path)
        # Cursor may pass a path without the .jsonl suffix.
        if not path.is_file() and path.with_suffix(".jsonl").is_file():
            path = path.with_suffix(".jsonl")
        if path.is_file():
            return estimate_transcript(
                path, pricing, model=model, pricing_mode=mode, state=state
            )

    paths = find_subagent_transcripts(started_at_iso, transcripts_root)
    if not paths:
        return CostEstimate(
            tokens_in_est=0,
            tokens_out_est=0,
            tokens_est=0,
            usd_est=0.0,
            turns=0,
            tool_calls=0,
            wall_clock_s=0.0,
            model=model,
            assumptions="no transcripts found since started_at",
            known_model=False,
            pricing_mode=mode,
        )

    primary = paths[0]
    est = estimate_transcript(
        primary, pricing, model=model, pricing_mode=mode, state=state
    )
    if len(paths) > 1:
        for extra in paths[1:]:
            try:
                if abs(extra.stat().st_mtime - primary.stat().st_mtime) > 600:
                    continue
            except OSError:
                continue
            other = estimate_transcript(
                extra, pricing, model=model, pricing_mode=mode, state=state
            )
            est = CostEstimate(
                tokens_in_est=est.tokens_in_est + other.tokens_in_est,
                tokens_out_est=est.tokens_out_est + other.tokens_out_est,
                tokens_est=est.tokens_est + other.tokens_est,
                usd_est=round(est.usd_est + other.usd_est, 4),
                turns=est.turns + other.turns,
                tool_calls=est.tool_calls + other.tool_calls,
                wall_clock_s=est.wall_clock_s + other.wall_clock_s,
                model=est.model,
                assumptions=est.assumptions,
                known_model=est.known_model and other.known_model,
                pricing_mode=mode,
            )
    return est


def cold_projection(
    state: dict[str, Any],
    *,
    model: str | None = None,
) -> tuple[float, float]:
    """Cold-start token/USD projection for the next subagent launch.

    Uses loop ``pricing_mode`` for token/cold defaults (auto by default), then
    scales USD up when the *upcoming* model is a named frontier segment so the
    first launch is denied before spend if it would blow the cheap Auto cap.
    """
    loop_mode = str(state.get("pricing_mode") or "auto").strip().lower()
    if loop_mode not in {"auto", "api"}:
        loop_mode = "auto"
    cold_t, cold_u = (120_000.0, 0.15) if loop_mode == "auto" else (80_000.0, 0.75)

    upcoming = normalize_loop_model(
        model or state.get("next_model") or state.get("reviewer_model") or "inherit"
    )
    if segment_pricing_mode(upcoming) == "api" and loop_mode == "auto":
        # Named model under Auto caps — use api-ish cold USD so we alert early.
        cold_u = max(cold_u, 0.75)
    return cold_t, cold_u


def project_next_cost(
    state: dict[str, Any],
    *,
    model: str | None = None,
) -> tuple[float, float]:
    """Project next subagent tokens and USD from prior rounds (or cold start).

    Uses max(last round, running average). Returns (tokens, usd).
    """
    cold_t, cold_u = cold_projection(state, model=model)

    rounds = state.get("rounds")
    if not isinstance(rounds, list) or not rounds:
        return cold_t, cold_u

    costs: list[tuple[float, float]] = []
    for entry in rounds:
        if not isinstance(entry, dict):
            continue
        cost = entry.get("cost")
        if not isinstance(cost, dict):
            continue
        costs.append(
            (
                float(cost.get("tokens_est", 0) or 0),
                float(cost.get("usd_est", 0) or 0),
            )
        )
    if not costs:
        return cold_t, cold_u

    last_t, last_u = costs[-1]
    avg_t = sum(t for t, _ in costs) / len(costs)
    avg_u = sum(u for _, u in costs) / len(costs)
    return max(last_t, avg_t), max(last_u, avg_u)


def workspace_env_hint() -> str | None:
    """Return CURSOR_PROJECT or similar env hint if set."""
    return os.environ.get("CURSOR_PROJECT_DIR") or os.environ.get("CURSOR_WORKSPACE")
