"""Regression tests for PR review-loop cost accounting (issue #67).

Spent totals must accumulate after each subagentStop even when the
orchestrator forgets to stamp ``*_started_at``. Cost must prefer
``agent_transcript_path`` over the mtime filesystem scan.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

HOOKS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOOKS))

from _cost import estimate_since, project_next_cost  # noqa: E402
from review_loop_budget import record_subagent_start, resolve_upcoming_model  # noqa: E402
from review_loop_round import decide_round_followup, record_round_cost  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
PRICING_PATH = (
    PLUGIN_ROOT
    / "skills"
    / "code"
    / "ci"
    / "pr-review-loop"
    / "assets"
    / "pricing.default.json"
)


@pytest.fixture
def pricing() -> dict[str, Any]:
    """Load the committed default pricing table."""
    return json.loads(PRICING_PATH.read_text(encoding="utf-8"))


def _write_transcript(path: Path, *, turns: int = 3) -> Path:
    """Write a minimal JSONL transcript large enough for nonzero cost."""
    lines: list[str] = []
    for i in range(turns):
        lines.append(
            json.dumps(
                {
                    "role": "user",
                    "message": {
                        "content": [{"type": "text", "text": f"user turn {i} " + ("x" * 4000)}]
                    },
                }
            )
        )
        lines.append(
            json.dumps(
                {
                    "role": "assistant",
                    "message": {
                        "content": [
                            {"type": "text", "text": f"assistant turn {i} " + ("y" * 4000)}
                        ]
                    },
                }
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


class TestEstimateSinceTranscriptPath:
    """Explicit transcript_path must bypass the mtime scan."""

    def test_path_bypasses_empty_scan(
        self, pricing: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        transcript = _write_transcript(tmp_path / "sub.jsonl")
        import _cost as cost_mod

        monkeypatch.setattr(
            cost_mod,
            "find_subagent_transcripts",
            lambda *_a, **_k: [],
        )

        est = estimate_since(
            pricing,
            started_at_iso="2099-01-01T00:00:00+00:00",
            model="inherit",
            transcript_path=transcript,
        )
        assert est.tokens_est > 0
        assert est.usd_est > 0

    def test_missing_path_falls_back_to_scan(
        self, pricing: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        transcript = _write_transcript(tmp_path / "found.jsonl")
        import _cost as cost_mod

        monkeypatch.setattr(
            cost_mod,
            "find_subagent_transcripts",
            lambda *_a, **_k: [transcript],
        )
        est = estimate_since(
            pricing,
            started_at_iso="2000-01-01T00:00:00+00:00",
            model="inherit",
            transcript_path=tmp_path / "does-not-exist.jsonl",
        )
        assert est.tokens_est > 0


class TestRecordSubagentStart:
    """subagentStart must bridge model/start time into state."""

    def test_loop_subagent_returns_pending(self) -> None:
        state = {"active": True, "next_model": "inherit"}
        pending = record_subagent_start(
            state,
            {
                "subagent_type": "pr-reviewer",
                "subagent_model": "claude-sonnet-5-thinking-high",
            },
        )
        assert pending is not None
        assert pending["type"] == "pr-reviewer"
        assert pending["model"] == "claude-sonnet-5-thinking-high"
        assert pending["started_at"]

    def test_fixer_returns_pending(self) -> None:
        state = {"active": True}
        pending = record_subagent_start(
            state,
            {"subagent_type": "pr-fixer", "subagent_model": "inherit"},
        )
        assert pending is not None
        assert pending["type"] == "pr-fixer"

    def test_explore_returns_none(self) -> None:
        assert (
            record_subagent_start(
                {"active": True},
                {"subagent_type": "explore"},
            )
            is None
        )

    def test_general_purpose_returns_none(self) -> None:
        assert (
            record_subagent_start(
                {"active": True},
                {"subagent_type": "generalPurpose"},
            )
            is None
        )

    def test_inactive_returns_none(self) -> None:
        assert (
            record_subagent_start(
                {"active": False},
                {"subagent_type": "pr-reviewer", "subagent_model": "inherit"},
            )
            is None
        )


class TestRecordRoundCost:
    """Issue #67 repro: zero stamps + agent_transcript_path → nonzero totals."""

    def test_zero_stamps_with_transcript_path_accumulates(
        self, pricing: dict[str, Any], tmp_path: Path
    ) -> None:
        transcript = _write_transcript(tmp_path / "agent.jsonl")
        state: dict[str, Any] = {
            "active": True,
            "totals": {"tokens_est": 0, "usd_est": 0, "turns": 0, "tool_calls": 0},
            "rounds": [
                {
                    "n": 1,
                    "focus": "full",
                    # Intentionally omit started_at / reviewer_started_at /
                    # fixer_started_at — the bug condition.
                    "findings": [],
                }
            ],
            "_pending_subagent": {
                "type": "pr-reviewer",
                "model": "inherit",
                "started_at": "2026-01-01T00:00:00+00:00",
            },
        }
        event = {
            "subagent_type": "pr-reviewer",
            "agent_transcript_path": str(transcript),
            "status": "completed",
        }

        cost = record_round_cost(state, event, pricing)

        assert cost.tokens_est > 0
        assert cost.usd_est > 0
        totals = state["totals"]
        assert float(totals["tokens_est"]) > 0
        assert float(totals["usd_est"]) > 0
        round_cost = state["rounds"][0]["cost"]
        assert int(round_cost["tokens_est"]) > 0
        assert "_pending_subagent" not in state

    def test_accumulates_across_stops(
        self, pricing: dict[str, Any], tmp_path: Path
    ) -> None:
        t1 = _write_transcript(tmp_path / "r1.jsonl")
        t2 = _write_transcript(tmp_path / "r2.jsonl")
        state: dict[str, Any] = {
            "active": True,
            "totals": {"tokens_est": 0, "usd_est": 0, "turns": 0, "tool_calls": 0},
            "rounds": [{"n": 1, "findings": []}],
            "_pending_subagent": {
                "type": "pr-reviewer",
                "model": "inherit",
                "started_at": "2026-01-01T00:00:00+00:00",
            },
        }
        record_round_cost(
            state,
            {
                "subagent_type": "pr-reviewer",
                "agent_transcript_path": str(t1),
            },
            pricing,
        )
        first = float(state["totals"]["tokens_est"])
        state["_pending_subagent"] = {
            "type": "pr-fixer",
            "model": "inherit",
            "started_at": "2026-01-01T01:00:00+00:00",
        }
        record_round_cost(
            state,
            {
                "subagent_type": "pr-fixer",
                "agent_transcript_path": str(t2),
            },
            pricing,
        )
        assert float(state["totals"]["tokens_est"]) > first


class TestProjectNextCostLeavesCold:
    """Once rounds have costs, projection must leave cold defaults."""

    def test_last_and_average_after_history(self) -> None:
        state = {
            "pricing_mode": "auto",
            "rounds": [
                {"cost": {"tokens_est": 80_000, "usd_est": 0.04}},
                {"cost": {"tokens_est": 120_000, "usd_est": 0.08}},
            ],
        }
        tok, usd = project_next_cost(state)
        # max(last=120k, avg=100k) = 120k; max(last=0.08, avg=0.06) = 0.08
        assert tok == pytest.approx(120_000.0)
        assert usd == pytest.approx(0.08)
        # Must leave cold USD (0.15), proving history-based projection.
        assert usd != pytest.approx(0.15)


class TestDecideRoundFollowupStatus:
    """A: error/aborted stops must not look like normal completions."""

    def test_error_status_for_reviewer(self) -> None:
        msg = decide_round_followup(
            {
                "active": True,
                "round": 1,
                "max_rounds": 5,
                "totals": {"tokens_est": 1000, "usd_est": 0.01},
                "max_tokens_est": 1_000_000,
                "max_usd_est": 2.0,
                "consecutive_clean_passes": 0,
                "clean_passes_required": 2,
            },
            {"subagent_type": "pr-reviewer", "status": "error"},
        )
        assert "status=error" in msg
        assert "not completed" in msg
        assert "collect the findings" not in msg

    def test_aborted_status_for_fixer(self) -> None:
        msg = decide_round_followup(
            {
                "active": True,
                "round": 1,
                "max_rounds": 5,
                "totals": {"tokens_est": 1000, "usd_est": 0.01},
                "max_tokens_est": 1_000_000,
                "max_usd_est": 2.0,
                "consecutive_clean_passes": 0,
                "clean_passes_required": 2,
            },
            {"subagent_type": "pr-fixer", "status": "aborted"},
        )
        assert "status=aborted" in msg
        assert "fixer finished" not in msg

    def test_over_budget_formats_numbers(self) -> None:
        msg = decide_round_followup(
            {
                "active": True,
                "round": 1,
                "max_rounds": None,
                "totals": {"tokens_est": 900_000, "usd_est": 1.8},
                "max_tokens_est": 1_000_000,
                "max_usd_est": 2.0,
                "pricing_mode": "auto",
                "rounds": [{"cost": {"tokens_est": 200_000, "usd_est": 0.4}}],
                "consecutive_clean_passes": 0,
                "clean_passes_required": 2,
            },
            {"subagent_type": "pr-reviewer", "status": "completed"},
        )
        assert "spent≈900000" in msg or "spent≈900000 tok" in msg
        assert "caps=" in msg
        assert "projected next≈" in msg


class TestWallClockAndGroundTruth:
    """B+C: duration_ms and message/tool counts from the stop event."""

    def test_duration_ms_sets_and_accumulates_wall_clock(
        self, pricing: dict[str, Any], tmp_path: Path
    ) -> None:
        t1 = _write_transcript(tmp_path / "w1.jsonl")
        t2 = _write_transcript(tmp_path / "w2.jsonl")
        state: dict[str, Any] = {
            "active": True,
            "totals": {
                "tokens_est": 0,
                "usd_est": 0,
                "turns": 0,
                "tool_calls": 0,
                "wall_clock_s": 0,
            },
            "rounds": [{"n": 1, "findings": []}],
            "_pending_subagent": {
                "type": "pr-reviewer",
                "model": "inherit",
                "started_at": "2026-01-01T00:00:00+00:00",
            },
        }
        cost1 = record_round_cost(
            state,
            {
                "subagent_type": "pr-reviewer",
                "agent_transcript_path": str(t1),
                "status": "completed",
                "duration_ms": 45_000,
            },
            pricing,
        )
        assert cost1.wall_clock_s == pytest.approx(45.0)
        assert state["rounds"][0]["cost"]["wall_clock_s"] == pytest.approx(45.0)

        state["_pending_subagent"] = {
            "type": "pr-fixer",
            "model": "inherit",
            "started_at": "2026-01-01T01:00:00+00:00",
        }
        cost2 = record_round_cost(
            state,
            {
                "subagent_type": "pr-fixer",
                "agent_transcript_path": str(t2),
                "status": "completed",
                "duration_ms": 30_000,
            },
            pricing,
        )
        assert cost2.wall_clock_s == pytest.approx(30.0)
        assert state["rounds"][0]["cost"]["wall_clock_s"] == pytest.approx(75.0)
        assert float(state["totals"]["wall_clock_s"]) == pytest.approx(75.0)

    def test_event_counts_override_transcript(
        self, pricing: dict[str, Any], tmp_path: Path
    ) -> None:
        transcript = _write_transcript(tmp_path / "counts.jsonl", turns=3)
        state: dict[str, Any] = {
            "active": True,
            "totals": {"tokens_est": 0, "usd_est": 0, "turns": 0, "tool_calls": 0},
            "rounds": [{"n": 1, "findings": []}],
            "_pending_subagent": {
                "type": "pr-reviewer",
                "model": "inherit",
                "started_at": "2026-01-01T00:00:00+00:00",
            },
        }
        cost = record_round_cost(
            state,
            {
                "subagent_type": "pr-reviewer",
                "agent_transcript_path": str(transcript),
                "status": "completed",
                "message_count": 99,
                "tool_call_count": 42,
            },
            pricing,
        )
        assert cost.turns == 99
        assert cost.tool_calls == 42
        assert "turns from message_count" in cost.assumptions
        assert "tool_calls from tool_call_count" in cost.assumptions


class TestPendingTypeCheck:
    """D: stale _pending_subagent must not leak model/started_at."""

    def test_type_mismatch_ignores_pending_model(
        self, pricing: dict[str, Any], tmp_path: Path
    ) -> None:
        transcript = _write_transcript(tmp_path / "mismatch.jsonl")
        state: dict[str, Any] = {
            "active": True,
            "fixer_model": "inherit",
            "reviewer_model": "inherit",
            "next_model": "inherit",
            "totals": {"tokens_est": 0, "usd_est": 0, "turns": 0, "tool_calls": 0},
            "rounds": [{"n": 1, "findings": []}],
            "_pending_subagent": {
                "type": "pr-reviewer",
                "model": "claude-opus-5-thinking-high",
                "started_at": "2026-01-01T00:00:00+00:00",
            },
        }
        cost = record_round_cost(
            state,
            {
                "subagent_type": "pr-fixer",
                "agent_transcript_path": str(transcript),
                "status": "completed",
                "subagent_model": "inherit",
            },
            pricing,
        )
        assert "type mismatch" in cost.assumptions
        # Pending opus model must not win when types disagree.
        assert "opus" not in str(cost.model).lower()
        assert "_pending_subagent" not in state


class TestLoudZeroCost:
    """E: zero-cost discovery misses must surface in state + followup."""

    def test_zero_cost_warns(
        self, pricing: dict[str, Any], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import _cost as cost_mod

        monkeypatch.setattr(
            cost_mod,
            "find_subagent_transcripts",
            lambda *_a, **_k: [],
        )
        state: dict[str, Any] = {
            "active": True,
            "round": 1,
            "max_rounds": 5,
            "totals": {"tokens_est": 0, "usd_est": 0, "turns": 0, "tool_calls": 0},
            "max_tokens_est": 1_000_000,
            "max_usd_est": 2.0,
            "consecutive_clean_passes": 0,
            "clean_passes_required": 2,
            "rounds": [{"n": 1, "findings": []}],
            "_pending_subagent": {
                "type": "pr-reviewer",
                "model": "inherit",
                "started_at": "2026-01-01T00:00:00+00:00",
            },
        }
        cost = record_round_cost(
            state,
            {
                "subagent_type": "pr-reviewer",
                "status": "completed",
                # No agent_transcript_path — forces scan, which is empty.
            },
            pricing,
        )
        assert cost.tokens_est == 0
        assert state.get("_cost_warnings")
        assert "0 tokens" in state["_cost_warnings"][-1]

        msg = decide_round_followup(
            state,
            {"subagent_type": "pr-reviewer", "status": "completed"},
        )
        assert msg.startswith("WARNING:")
        assert "0 tokens" in msg


class TestResolveUpcomingModel:
    """F: shared model resolver used by budget start helpers."""

    def test_priority_chain(self) -> None:
        assert (
            resolve_upcoming_model(
                {"next_model": "inherit", "reviewer_model": "opus"},
                {"subagent_model": "sonnet", "model": "gpt"},
                extra_fallback="opus",
            )
            == "sonnet"
        )
        assert (
            resolve_upcoming_model(
                {"next_model": "inherit"},
                {"model": "gpt"},
            )
            == "gpt"
        )
        assert (
            resolve_upcoming_model(
                {"next_model": "fast"},
                {},
                extra_fallback="opus",
            )
            == "fast"
        )
        assert (
            resolve_upcoming_model(
                {},
                {},
                extra_fallback="opus",
            )
            == "opus"
        )
        assert resolve_upcoming_model({}, {}) == "inherit"
