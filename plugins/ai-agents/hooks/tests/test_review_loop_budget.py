"""Unit tests for review-loop cost and budget guards.

These protect against regressions that could silently overspend (or wrongly
block) before a subagent starts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOOKS))

from _cost import (  # noqa: E402
    cold_projection,
    estimate_transcript,
    normalize_loop_model,
    project_next_cost,
    resolve_pricing_mode,
    segment_pricing_mode,
)
from review_loop_budget import decide_subagent_start  # noqa: E402

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
def pricing() -> dict:
    """Load the committed default pricing table."""
    return json.loads(PRICING_PATH.read_text(encoding="utf-8"))


class TestNormalizeLoopModel:
    """Role-model aliases must default cheap and map frontier names."""

    def test_default_inherit(self) -> None:
        assert normalize_loop_model(None) == "inherit"
        assert normalize_loop_model("") == "inherit"
        assert normalize_loop_model("auto") == "inherit"

    def test_opus_alias(self) -> None:
        assert normalize_loop_model("opus") == "claude-opus-5-thinking-high"
        assert normalize_loop_model("opus-5") == "claude-opus-5-thinking-high"

    def test_unknown_falls_back_to_inherit(self) -> None:
        assert normalize_loop_model("totally-unknown-model") == "inherit"


class TestPricingMode:
    """Loop caps stay auto; named segments estimate at api rates."""

    def test_segment_modes(self) -> None:
        assert segment_pricing_mode("inherit") == "auto"
        assert segment_pricing_mode("auto") == "auto"
        assert segment_pricing_mode("opus") == "api"

    def test_loop_caps_stay_auto_by_default(self, pricing: dict) -> None:
        assert resolve_pricing_mode(pricing, state={"pricing_mode": "auto"}) == "auto"

    def test_named_model_forces_api_estimate(self, pricing: dict) -> None:
        assert (
            resolve_pricing_mode(pricing, state={"pricing_mode": "auto"}, model="opus")
            == "api"
        )

    def test_explicit_wins(self, pricing: dict) -> None:
        assert resolve_pricing_mode(pricing, model="opus", explicit="auto") == "auto"


class TestColdProjection:
    """Cold USD must rise for named models under Auto caps."""

    def test_auto_cold_is_cheap(self) -> None:
        state = {"pricing_mode": "auto", "reviewer_model": "inherit"}
        _tok, usd = cold_projection(state, model="inherit")
        assert usd == pytest.approx(0.15)

    def test_opus_cold_under_auto_caps_is_expensive(self) -> None:
        state = {
            "pricing_mode": "auto",
            "reviewer_model": "claude-opus-5-thinking-high",
        }
        _tok, usd = cold_projection(state, model="claude-opus-5-thinking-high")
        assert usd >= 0.75


class TestProjectNextCost:
    """Preflight projection must catch over-cap before any spend."""

    def test_empty_rounds_uses_cold(self) -> None:
        state = {"pricing_mode": "auto", "rounds": []}
        tok, usd = project_next_cost(state, model="inherit")
        assert tok == pytest.approx(120_000.0)
        assert usd == pytest.approx(0.15)

    def test_uses_max_of_last_and_average(self) -> None:
        state = {
            "pricing_mode": "auto",
            "rounds": [
                {"cost": {"tokens_est": 100_000, "usd_est": 0.05}},
                {"cost": {"tokens_est": 200_000, "usd_est": 0.10}},
            ],
        }
        tok, usd = project_next_cost(state)
        assert tok == pytest.approx(200_000.0)
        assert usd == pytest.approx(0.10)


class TestEstimateTranscript:
    """Auto estimates must stay far below named-frontier API estimates."""

    def test_auto_much_cheaper_than_opus(self, pricing: dict, tmp_path: Path) -> None:
        path = tmp_path / "t.jsonl"
        lines: list[str] = []
        for _ in range(5):
            lines.append(
                json.dumps({"role": "user", "message": {"content": "x" * 20_000}})
            )
            lines.append(
                json.dumps(
                    {
                        "role": "assistant",
                        "message": {"content": "y" * 20_000},
                    }
                )
            )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        auto = estimate_transcript(path, pricing, model="inherit", pricing_mode="auto")
        api = estimate_transcript(
            path,
            pricing,
            model="claude-opus-5-thinking-high",
            pricing_mode="api",
        )
        assert auto.tokens_est == api.tokens_est
        assert auto.usd_est < api.usd_est / 5


class TestDecideSubagentStart:
    """Budget hook decisions that gate real spend."""

    @staticmethod
    def _loop_event(**extra: object) -> dict:
        return {"subagent_type": "pr-reviewer", **extra}

    def test_inactive_allows(self) -> None:
        assert decide_subagent_start({"active": False})["permission"] == "allow"

    def test_non_loop_subagent_allowed_even_when_loop_escalated(self) -> None:
        out = decide_subagent_start(
            {"active": True, "escalation_pending": True},
            {"subagent_type": "explore"},
            fingerprint="",
        )
        assert out["permission"] == "allow"

    def test_general_purpose_not_gated(self) -> None:
        out = decide_subagent_start(
            {
                "active": True,
                "round": 99,
                "max_rounds": 1,
                "max_tokens_est": 1,
                "max_usd_est": 0.01,
                "totals": {"tokens_est": 0, "usd_est": 0},
            },
            {"subagent_type": "generalPurpose"},
            fingerprint="",
        )
        assert out["permission"] == "allow"

    def test_escalation_denies(self) -> None:
        out = decide_subagent_start(
            {"active": True, "escalation_pending": True},
            self._loop_event(),
            fingerprint="",
        )
        assert out["permission"] == "deny"
        assert "escalation" in out["user_message"].lower()

    def test_final_round_allowed(self) -> None:
        state = {
            "active": True,
            "round": 3,
            "max_rounds": 3,
            "max_tokens_est": 1_000_000,
            "max_usd_est": 2.0,
            "pricing_mode": "auto",
            "reviewer_model": "inherit",
            "rounds": [{"n": 3, "focus": "confirm", "fixed": []}],
            "totals": {"tokens_est": 1000, "usd_est": 0.01},
        }
        assert (
            decide_subagent_start(state, self._loop_event(), fingerprint="")[
                "permission"
            ]
            == "allow"
        )

    def test_past_max_rounds_denies(self) -> None:
        state = {
            "active": True,
            "round": 4,
            "max_rounds": 3,
            "rounds": [],
            "totals": {},
        }
        out = decide_subagent_start(state, self._loop_event(), fingerprint="")
        assert out["permission"] == "deny"
        assert "max_rounds" in out["user_message"]

    def test_budget_only_allows_past_default_round_cap(self) -> None:
        state = {
            "active": True,
            "round": 10,
            "max_rounds": None,
            "max_tokens_est": 1_000_000,
            "max_usd_est": 2.0,
            "pricing_mode": "auto",
            "reviewer_model": "inherit",
            "rounds": [{"n": 10, "focus": "confirm", "fixed": []}],
            "totals": {"tokens_est": 50_000, "usd_est": 0.05},
        }
        assert (
            decide_subagent_start(state, self._loop_event(), fingerprint="")[
                "permission"
            ]
            == "allow"
        )

    def test_max_rounds_zero_means_unlimited(self) -> None:
        from _loop_state import resolve_max_rounds

        assert resolve_max_rounds({"max_rounds": 0}) is None
        assert resolve_max_rounds({"max_rounds": "budget-only"}) is None
        assert resolve_max_rounds({"max_rounds": "unlimited"}) is None
        assert resolve_max_rounds({"max_rounds": 3}) == 3
        assert resolve_max_rounds({}) == 3

    def test_cold_over_tiny_cap_denies_before_spend(self) -> None:
        state = {
            "active": True,
            "round": 1,
            "max_rounds": 3,
            "max_tokens_est": 1000,
            "max_usd_est": 0.01,
            "pricing_mode": "auto",
            "reviewer_model": "inherit",
            "rounds": [],
            "totals": {"tokens_est": 0, "usd_est": 0},
        }
        out = decide_subagent_start(
            state, self._loop_event(model="inherit"), fingerprint=""
        )
        assert out["permission"] == "deny"
        assert "Projected spend" in out["user_message"]

    def test_named_model_cold_denies_under_auto_dollar_cap(self) -> None:
        """Opus cold (~$0.75) must not sneak under a $0.50 Auto cap."""
        state = {
            "active": True,
            "round": 1,
            "max_rounds": 3,
            "max_tokens_est": 1_000_000,
            "max_usd_est": 0.50,
            "pricing_mode": "auto",
            "reviewer_model": "claude-opus-5-thinking-high",
            "rounds": [],
            "totals": {"tokens_est": 0, "usd_est": 0},
        }
        out = decide_subagent_start(
            state,
            self._loop_event(model="claude-opus-5-thinking-high"),
            fingerprint="",
        )
        assert out["permission"] == "deny"

    def test_confirm_focus_allowed_on_unchanged_fingerprint(self) -> None:
        state = {
            "active": True,
            "round": 3,
            "max_rounds": 3,
            "max_tokens_est": 1_000_000,
            "max_usd_est": 2.0,
            "pricing_mode": "auto",
            "last_fingerprint": "abc",
            "rounds": [
                {
                    "n": 3,
                    "focus": "confirm",
                    "fixed": ["sig1"],
                }
            ],
            "totals": {"tokens_est": 10_000, "usd_est": 0.05},
        }
        out = decide_subagent_start(state, self._loop_event(), fingerprint="abc")
        assert out["permission"] == "allow"

    def test_unchanged_fingerprint_allows_next_reviewer(self) -> None:
        state = {
            "active": True,
            "round": 2,
            "max_rounds": 3,
            "max_tokens_est": 1_000_000,
            "max_usd_est": 2.0,
            "pricing_mode": "auto",
            "last_fingerprint": "abc",
            "rounds": [
                {
                    "n": 2,
                    "focus": "full",
                    "fixed": ["sig1"],
                }
            ],
            "totals": {"tokens_est": 10_000, "usd_est": 0.05},
        }
        out = decide_subagent_start(state, self._loop_event(), fingerprint="abc")
        assert out["permission"] == "allow"

    def test_unchanged_fingerprint_after_fix_denies_fixer(self) -> None:
        state = {
            "active": True,
            "round": 2,
            "max_rounds": 3,
            "max_tokens_est": 1_000_000,
            "max_usd_est": 2.0,
            "pricing_mode": "auto",
            "last_fingerprint": "abc",
            "rounds": [
                {
                    "n": 2,
                    "focus": "full",
                    "fixed": ["sig1"],
                }
            ],
            "totals": {"tokens_est": 10_000, "usd_est": 0.05},
        }
        out = decide_subagent_start(
            state,
            {"subagent_type": "pr-fixer"},
            fingerprint="abc",
        )
        assert out["permission"] == "deny"
        assert "fingerprint" in out["user_message"].lower()


class TestPreferencesPersist:
    """max_rounds must not reset to 3 across loop starts."""

    def test_null_max_rounds_survives_fresh_start(self, tmp_path: Path) -> None:
        from _loop_state import load_preferences, start_loop_state

        first = start_loop_state(
            pr_number=1,
            pr_url="https://example/pr/1",
            branch="feature/x",
            overrides={"max_rounds": None, "max_usd_est": 2.0},
            root=tmp_path,
        )
        assert first["max_rounds"] is None
        prefs = load_preferences(tmp_path)
        assert prefs["max_rounds"] is None

        second = start_loop_state(
            pr_number=2,
            pr_url="https://example/pr/2",
            branch="feature/y",
            overrides={},
            root=tmp_path,
        )
        assert second["max_rounds"] is None
        assert second["max_usd_est"] == 2.0

    def test_explicit_round_cap_persists(self, tmp_path: Path) -> None:
        from _loop_state import start_loop_state

        start_loop_state(
            pr_number=1,
            pr_url="u",
            branch="b",
            overrides={"max_rounds": 5},
            root=tmp_path,
        )
        again = start_loop_state(
            pr_number=2,
            pr_url="u2",
            branch="b2",
            root=tmp_path,
        )
        assert again["max_rounds"] == 5


class TestClosedFindings:
    """Fixed/accepted signatures must not re-enter open triage."""

    def test_start_state_has_empty_closed_list(self, tmp_path: Path) -> None:
        from _loop_state import start_loop_state

        state = start_loop_state(
            pr_number=1,
            pr_url="u",
            branch="b",
            root=tmp_path,
        )
        assert state["closed_findings"] == []

    def test_filter_drops_closed_keeps_recurrence(self) -> None:
        from _loop_state import append_closed_finding, filter_open_findings

        state: dict = {"closed_findings": [], "accepted_by_design": []}
        append_closed_finding(
            state,
            signature="abc123deadbeef00",
            location="src/a.ts:10",
            finding="missing cleanup",
            status="fixed",
            closed_in_round=1,
        )
        open_rows, dropped = filter_open_findings(
            [
                {
                    "signature": "abc123deadbeef00",
                    "finding": "missing cleanup again",
                },
                {
                    "signature": "abc123deadbeef00",
                    "Source": "recurrence",
                    "finding": "still missing cleanup",
                },
                {
                    "signature": "fff0001112223334",
                    "finding": "different issue",
                },
            ],
            state,
        )
        assert len(dropped) == 1
        assert dropped[0]["signature"] == "abc123deadbeef00"
        assert len(open_rows) == 2
        assert open_rows[0]["Source"] == "recurrence"
        assert open_rows[1]["signature"] == "fff0001112223334"

    def test_append_accepted_mirrors_by_design(self) -> None:
        from _loop_state import append_closed_finding, closed_signatures

        state: dict = {"closed_findings": [], "accepted_by_design": []}
        append_closed_finding(
            state,
            signature="sig1",
            location="a.ts:1",
            finding="intentional",
            status="accepted",
            closed_in_round=2,
            rationale="product rule X",
        )
        # Idempotent
        append_closed_finding(
            state,
            signature="sig1",
            location="a.ts:1",
            finding="intentional",
            status="accepted",
            closed_in_round=2,
            rationale="product rule X",
        )
        assert len(state["closed_findings"]) == 1
        assert len(state["accepted_by_design"]) == 1
        assert "sig1" in closed_signatures(state)


class TestRoundFollowup:
    """Hook must not false-trigger success on empty findings mid-flight."""

    def test_reviewer_stop_does_not_declare_passed_on_empty_findings(self) -> None:
        from review_loop_round import decide_round_followup

        msg = decide_round_followup(
            {
                "escalation_pending": False,
                "round": 3,
                "max_rounds": None,
                "max_tokens_est": 1_000_000,
                "max_usd_est": 2.0,
                "clean_passes_required": 2,
                "consecutive_clean_passes": 0,
                "rounds": [{"n": 3, "findings": []}],
                "totals": {"tokens_est": 10_000, "usd_est": 0.05},
            },
            {"subagent_type": "pr-reviewer"},
        )
        assert "canvas" not in msg or "consecutive" in msg
        assert "single clean" in msg.lower() or "collect the findings" in msg.lower()
        assert "active=false" not in msg

    def test_recorded_consecutive_cleans_allows_canvas(self) -> None:
        from review_loop_round import decide_round_followup

        msg = decide_round_followup(
            {
                "escalation_pending": False,
                "round": 4,
                "max_rounds": None,
                "max_tokens_est": 1_000_000,
                "max_usd_est": 2.0,
                "clean_passes_required": 2,
                "consecutive_clean_passes": 2,
                "rounds": [{"n": 4, "findings": []}],
                "totals": {"tokens_est": 10_000, "usd_est": 0.05},
            },
            {"subagent_type": "pr-reviewer"},
        )
        assert "active=false" in msg
        assert "2/2" in msg

    def test_start_state_includes_clean_gate(self, tmp_path: Path) -> None:
        from _loop_state import start_loop_state

        state = start_loop_state(
            pr_number=1,
            pr_url="u",
            branch="b",
            root=tmp_path,
        )
        assert state["clean_passes_required"] == 2
        assert state["consecutive_clean_passes"] == 0
        assert state["manage_severity"] == "medium"
        assert state["post_fix_focus"] == "delta"
        assert state["diminishing_returns_round"] == 2
        assert state["diminishing_returns_floor"] == "high"
        assert state["last_validate_fingerprint"] == ""


class TestManageSeverity:
    """Severity floor preference + helpers."""

    def test_default_and_override_persist(self, tmp_path: Path) -> None:
        from _loop_state import load_preferences, start_loop_state

        first = start_loop_state(
            pr_number=1,
            pr_url="u",
            branch="b",
            overrides={"manage_severity": "high"},
            root=tmp_path,
        )
        assert first["manage_severity"] == "high"
        assert load_preferences(tmp_path)["manage_severity"] == "high"

        second = start_loop_state(
            pr_number=2,
            pr_url="u2",
            branch="b2",
            root=tmp_path,
        )
        assert second["manage_severity"] == "high"

    def test_aliases_and_floor_check(self) -> None:
        from _loop_state import normalize_manage_severity, severity_meets_floor

        assert normalize_manage_severity("HIGH") == "high"
        assert normalize_manage_severity("crit") == "critical"
        assert normalize_manage_severity("all") == "low"
        assert normalize_manage_severity("nope") == "medium"

        assert severity_meets_floor("High", "medium") is True
        assert severity_meets_floor("Low", "medium") is False
        assert severity_meets_floor("Medium", "high") is False
        assert severity_meets_floor("Critical", "critical") is True
        assert severity_meets_floor("Weird", "medium") is True

    def test_post_fix_focus_and_round_focus(self, tmp_path: Path) -> None:
        from _loop_state import (
            normalize_post_fix_focus,
            resolve_round_focus,
            start_loop_state,
            validate_still_fresh,
        )

        assert normalize_post_fix_focus("FULL") == "full"
        assert normalize_post_fix_focus("cheap") == "delta"

        state = start_loop_state(
            pr_number=1,
            pr_url="u",
            branch="b",
            overrides={"post_fix_focus": "delta"},
            root=tmp_path,
        )
        assert state["post_fix_focus"] == "delta"
        assert state["last_validate_fingerprint"] == ""

        assert (
            resolve_round_focus(
                round_n=1,
                consecutive_clean_passes=0,
                just_finished_fixer=False,
            )
            == "full"
        )
        assert (
            resolve_round_focus(
                round_n=2,
                consecutive_clean_passes=0,
                just_finished_fixer=True,
                post_fix_focus="delta",
            )
            == "delta"
        )
        assert (
            resolve_round_focus(
                round_n=3,
                consecutive_clean_passes=1,
                just_finished_fixer=False,
            )
            == "confirm"
        )
        assert (
            resolve_round_focus(
                round_n=2,
                consecutive_clean_passes=0,
                just_finished_fixer=True,
                force_full=True,
            )
            == "full"
        )
        assert (
            resolve_round_focus(
                round_n=2,
                consecutive_clean_passes=0,
                just_finished_fixer=True,
                invocation_focus="confirm",
            )
            == "confirm"
        )

        state["last_validate_fingerprint"] = "abc"
        state["last_lint"] = "pass"
        state["last_build"] = "pass"
        assert validate_still_fresh(state, "abc") is True
        assert validate_still_fresh(state, "xyz") is False
        state["last_lint"] = "fail"
        assert validate_still_fresh(state, "abc") is False


class TestDiminishingReturns:
    """Round-based ratchet helpers + preference round-trip."""

    def test_default_floor_one_tier_above(self) -> None:
        from _loop_state import default_diminishing_returns_floor

        assert default_diminishing_returns_floor("low") == "medium"
        assert default_diminishing_returns_floor("medium") == "high"
        assert default_diminishing_returns_floor("high") == "critical"
        assert default_diminishing_returns_floor("critical") == "critical"

    def test_normalize_floor_aliases_and_fallback(self) -> None:
        from _loop_state import normalize_diminishing_returns_floor

        assert normalize_diminishing_returns_floor(None, "medium") == "high"
        assert normalize_diminishing_returns_floor("auto", "low") == "medium"
        assert normalize_diminishing_returns_floor("HIGH", "medium") == "high"
        assert normalize_diminishing_returns_floor("crit", "medium") == "critical"
        assert normalize_diminishing_returns_floor("nope", "high") == "critical"

    def test_should_defer_respects_round_and_floor(self) -> None:
        from _loop_state import should_defer_for_diminishing_returns

        state = {
            "manage_severity": "medium",
            "diminishing_returns_round": 4,
            "diminishing_returns_floor": "high",
        }
        # Below threshold — never defer via ratchet.
        assert should_defer_for_diminishing_returns(3, "Medium", state) is False
        assert should_defer_for_diminishing_returns(1, "Low", state) is False

        # At/above threshold — defer below floor; keep High/Critical.
        assert should_defer_for_diminishing_returns(4, "Medium", state) is True
        assert should_defer_for_diminishing_returns(5, "Low", state) is True
        assert should_defer_for_diminishing_returns(4, "High", state) is False
        assert should_defer_for_diminishing_returns(4, "Critical", state) is False

    def test_preference_round_trip(self, tmp_path: Path) -> None:
        from _loop_state import (
            apply_preference_overrides,
            default_preferences,
            load_preferences,
            start_loop_state,
        )

        first = start_loop_state(
            pr_number=1,
            pr_url="u",
            branch="b",
            overrides={
                "diminishing_returns_round": 3,
                "diminishing_returns_floor": "critical",
            },
            root=tmp_path,
        )
        assert first["diminishing_returns_round"] == 3
        assert first["diminishing_returns_floor"] == "critical"
        prefs = load_preferences(tmp_path)
        assert prefs["diminishing_returns_round"] == 3
        assert prefs["diminishing_returns_floor"] == "critical"

        second = start_loop_state(
            pr_number=2,
            pr_url="u2",
            branch="b2",
            root=tmp_path,
        )
        assert second["diminishing_returns_round"] == 3
        assert second["diminishing_returns_floor"] == "critical"

        # Changing manage_severity without an explicit floor re-derives the floor.
        derived = apply_preference_overrides(
            default_preferences(),
            {"manage_severity": "high"},
        )
        assert derived["manage_severity"] == "high"
        assert derived["diminishing_returns_floor"] == "critical"

        # Explicit floor wins even when manage_severity changes.
        kept = apply_preference_overrides(
            default_preferences(),
            {
                "manage_severity": "low",
                "diminishing_returns_floor": "critical",
            },
        )
        assert kept["manage_severity"] == "low"
        assert kept["diminishing_returns_floor"] == "critical"


class TestAnalysisMode:
    """analysis_mode preference: normalize, default, persist."""

    def test_normalize_aliases(self) -> None:
        from _loop_state import normalize_analysis_mode

        assert normalize_analysis_mode(None) == "review"
        assert normalize_analysis_mode("review") == "review"
        assert normalize_analysis_mode("DEBUG") == "debug-like"
        assert normalize_analysis_mode("debug-like") == "debug-like"
        assert normalize_analysis_mode("debug_like") == "debug-like"
        assert normalize_analysis_mode("sec") == "security"
        assert normalize_analysis_mode("security") == "security"
        assert normalize_analysis_mode("nope") == "review"

    def test_default_preferences(self) -> None:
        from _loop_state import default_preferences

        assert default_preferences()["analysis_mode"] == "review"

    def test_persists_across_loop_starts(self, tmp_path: Path) -> None:
        from _loop_state import load_preferences, start_loop_state

        first = start_loop_state(
            pr_number=1,
            pr_url="u",
            branch="b",
            overrides={"analysis_mode": "debug"},
            root=tmp_path,
        )
        assert first["analysis_mode"] == "debug-like"
        prefs = load_preferences(tmp_path)
        assert prefs["analysis_mode"] == "debug-like"

        second = start_loop_state(
            pr_number=2,
            pr_url="u2",
            branch="b2",
            root=tmp_path,
        )
        assert second["analysis_mode"] == "debug-like"

    def test_security_override(self, tmp_path: Path) -> None:
        from _loop_state import start_loop_state

        state = start_loop_state(
            pr_number=1,
            pr_url="u",
            branch="b",
            overrides={"analysis_mode": "security"},
            root=tmp_path,
        )
        assert state["analysis_mode"] == "security"


class TestCleanPassScope:
    """Only wide-scope reviews may credit consecutive_clean_passes."""

    def test_clean_pass_counts(self) -> None:
        from _loop_state import clean_pass_counts

        assert clean_pass_counts("delta") is False
        assert clean_pass_counts("full") is True
        assert clean_pass_counts("confirm") is True
        assert clean_pass_counts("FULL") is True
        assert clean_pass_counts(None) is False

    def test_apply_clean_pass_scopes(self) -> None:
        from _loop_state import apply_clean_pass

        state: dict = {"consecutive_clean_passes": 0}
        assert apply_clean_pass(state, focus="delta", coverage_ok=True) == 0
        assert state["consecutive_clean_passes"] == 0

        assert apply_clean_pass(state, focus="full", coverage_ok=True) == 1
        assert state["consecutive_clean_passes"] == 1

        assert apply_clean_pass(state, focus="confirm", coverage_ok=False) == 1
        assert state["consecutive_clean_passes"] == 1

        assert apply_clean_pass(state, focus="confirm", coverage_ok=True) == 2
        assert state["consecutive_clean_passes"] == 2

    def test_resolve_focus_after_clean_delta(self) -> None:
        from _loop_state import resolve_round_focus

        assert (
            resolve_round_focus(
                round_n=3,
                consecutive_clean_passes=0,
                just_finished_fixer=False,
                last_focus="delta",
                last_round_clean=True,
            )
            == "confirm"
        )
        # Must not fall through to post_fix_focus=delta.
        assert (
            resolve_round_focus(
                round_n=3,
                consecutive_clean_passes=0,
                just_finished_fixer=False,
                post_fix_focus="delta",
                last_focus="delta",
                last_round_clean=True,
            )
            == "confirm"
        )
        # Clean full already counted — confirm stays next.
        assert (
            resolve_round_focus(
                round_n=3,
                consecutive_clean_passes=1,
                just_finished_fixer=False,
                last_focus="full",
                last_round_clean=True,
            )
            == "confirm"
        )


class TestContestedFindings:
    """Contested sources stay open; fix_shape / fixed_locations ledger."""

    def test_filter_keeps_contested_open(self) -> None:
        from _loop_state import append_closed_finding, filter_open_findings

        state: dict = {"closed_findings": [], "accepted_by_design": []}
        append_closed_finding(
            state,
            signature="abc123deadbeef00",
            location="src/a.ts:10",
            finding="missing cleanup",
            status="fixed",
            closed_in_round=1,
            fix_shape="added dispose in useEffect cleanup",
        )
        open_rows, dropped = filter_open_findings(
            [
                {
                    "signature": "abc123deadbeef00",
                    "source": "contested",
                    "finding": "prefer onUnmount helper instead",
                },
                {
                    "signature": "abc123deadbeef00",
                    "finding": "missing cleanup again",
                },
            ],
            state,
        )
        assert len(dropped) == 1
        assert len(open_rows) == 1
        assert open_rows[0]["source"] == "contested"

    def test_append_persists_fix_shape_and_fixed_locations(self) -> None:
        from _loop_state import append_closed_finding, fixed_locations

        state: dict = {"closed_findings": [], "accepted_by_design": []}
        append_closed_finding(
            state,
            signature="sig-fix",
            location="src/comp.tsx:42",
            finding="race on hydrate",
            status="fixed",
            closed_in_round=2,
            fix_shape="disable edits until isHydrated",
        )
        append_closed_finding(
            state,
            signature="sig-accept",
            location="src/other.ts:1",
            finding="intentional",
            status="accepted",
            closed_in_round=2,
            rationale="by design",
        )
        entry = state["closed_findings"][0]
        assert entry["fix_shape"] == "disable edits until isHydrated"
        locs = fixed_locations(state)
        assert "src/comp.tsx:42" in locs
        assert "src/comp.tsx" in locs
        assert "src/other.ts:1" not in locs
        assert "src/other.ts" not in locs


class TestDurableClosedLedger:
    """PR-scoped closed memory survives across start_loop_state runs."""

    def test_second_start_seeds_prior_closed_and_fix_shape(
        self, tmp_path: Path
    ) -> None:
        from _loop_state import append_closed_finding, start_loop_state

        first = start_loop_state(
            pr_number=60,
            pr_url="u",
            branch="feature/x",
            root=tmp_path,
        )
        append_closed_finding(
            first,
            signature="sig-seed-1",
            location="src/a.ts:10",
            finding="missing cleanup",
            status="fixed",
            closed_in_round=1,
            fix_shape="added dispose in useEffect",
            root=tmp_path,
        )

        second = start_loop_state(
            pr_number=60,
            pr_url="u",
            branch="feature/x",
            root=tmp_path,
        )
        assert second["seeded_from_ledger"] is True
        assert len(second["closed_findings"]) == 1
        assert second["closed_findings"][0]["signature"] == "sig-seed-1"
        assert (
            second["closed_findings"][0]["fix_shape"]
            == "added dispose in useEffect"
        )

    def test_append_persists_across_fresh_start(self, tmp_path: Path) -> None:
        from _loop_state import (
            append_closed_finding,
            load_pr_closed_memory,
            start_loop_state,
        )

        state = start_loop_state(
            pr_number=7,
            pr_url="u",
            branch="b",
            root=tmp_path,
        )
        append_closed_finding(
            state,
            signature="persist-sig",
            location="src/b.ts:2",
            finding="n+1 query",
            status="fixed",
            closed_in_round=2,
            fix_shape="batch with Promise.all",
            root=tmp_path,
        )
        memory = load_pr_closed_memory(7, tmp_path)
        assert any(e.get("signature") == "persist-sig" for e in memory["closed_findings"])

        again = start_loop_state(
            pr_number=7,
            pr_url="u",
            branch="b",
            root=tmp_path,
        )
        assert any(
            e.get("signature") == "persist-sig" for e in again["closed_findings"]
        )

    def test_short_circuit_only_on_matching_fingerprint(
        self, tmp_path: Path
    ) -> None:
        from _loop_state import (
            mark_run_outcome,
            should_short_circuit_confirm,
            start_loop_state,
        )

        state = start_loop_state(
            pr_number=3,
            pr_url="u",
            branch="b",
            root=tmp_path,
        )
        mark_run_outcome(state, "confirmed_clean", "fp-abc", root=tmp_path)
        seeded = start_loop_state(
            pr_number=3,
            pr_url="u",
            branch="b",
            root=tmp_path,
        )
        assert should_short_circuit_confirm(seeded, "fp-abc") is True
        assert should_short_circuit_confirm(seeded, "fp-other") is False
        assert should_short_circuit_confirm(seeded, "") is False

        dirty = start_loop_state(
            pr_number=3,
            pr_url="u",
            branch="b",
            root=tmp_path,
        )
        mark_run_outcome(dirty, "stopped", "fp-abc", root=tmp_path)
        again = start_loop_state(
            pr_number=3,
            pr_url="u",
            branch="b",
            root=tmp_path,
        )
        assert should_short_circuit_confirm(again, "fp-abc") is False

    def test_different_pr_does_not_inherit_ledger(self, tmp_path: Path) -> None:
        from _loop_state import append_closed_finding, start_loop_state

        a = start_loop_state(
            pr_number=10,
            pr_url="u",
            branch="a",
            root=tmp_path,
        )
        append_closed_finding(
            a,
            signature="only-pr-10",
            location="src/a.ts:1",
            finding="x",
            status="fixed",
            closed_in_round=1,
            fix_shape="shape-a",
            root=tmp_path,
        )
        b = start_loop_state(
            pr_number=11,
            pr_url="u",
            branch="b",
            root=tmp_path,
        )
        assert b["closed_findings"] == []
        assert b["seeded_from_ledger"] is False

    def test_is_contested_against_ledger_path_rules(self, tmp_path: Path) -> None:
        from _loop_state import (
            append_closed_finding,
            is_contested_against_ledger,
            start_loop_state,
        )

        state = start_loop_state(
            pr_number=20,
            pr_url="u",
            branch="b",
            root=tmp_path,
        )
        append_closed_finding(
            state,
            signature="with-shape",
            location="src/fixed.ts:10",
            finding="race",
            status="fixed",
            closed_in_round=1,
            fix_shape="gate on isReady",
            root=tmp_path,
        )
        append_closed_finding(
            state,
            signature="no-shape",
            location="src/bare.ts:5",
            finding="nit",
            status="fixed",
            closed_in_round=1,
            root=tmp_path,
        )
        assert (
            is_contested_against_ledger(
                {"location": "src/fixed.ts:99", "finding": "prefer other gate"},
                state,
            )
            is True
        )
        assert (
            is_contested_against_ledger(
                {"location": "src/other.ts:1", "finding": "unrelated"},
                state,
            )
            is False
        )
        assert (
            is_contested_against_ledger(
                {"location": "src/bare.ts:5", "finding": "still nit"},
                state,
            )
            is False
        )

    def test_format_fix_ledger_includes_location_and_shape(
        self, tmp_path: Path
    ) -> None:
        from _loop_state import (
            append_closed_finding,
            format_fix_ledger_for_prompt,
            start_loop_state,
        )

        state = start_loop_state(
            pr_number=21,
            pr_url="u",
            branch="b",
            root=tmp_path,
        )
        append_closed_finding(
            state,
            signature="ledger-sig",
            location="src/comp.tsx:42",
            finding="hydrate race",
            status="fixed",
            closed_in_round=1,
            fix_shape="disable edits until hydrated",
            root=tmp_path,
        )
        text = format_fix_ledger_for_prompt(state)
        assert "src/comp.tsx:42" in text
        assert "disable edits until hydrated" in text
        assert "ledger-sig" in text
        assert "Fix ledger" in text


class TestPostFixVerifyFilter:
    """After fixes exist, defer drive-bys outside the verify surface."""

    def test_no_fixed_yet_keeps_unrelated_path(self) -> None:
        from _loop_state import filter_post_fix_findings

        state: dict = {"closed_findings": [], "accepted_by_design": []}
        findings = [
            {
                "signature": "sig-b",
                "location": "src/b.ts:1",
                "severity": "Medium",
                "finding": "nit",
            }
        ]
        keep, defer = filter_post_fix_findings(findings, state)
        assert len(keep) == 1
        assert defer == []

    def test_after_fixed_defers_outside_keeps_same_path(self) -> None:
        from _loop_state import append_closed_finding, filter_post_fix_findings

        state: dict = {
            "pr_number": 0,
            "closed_findings": [],
            "accepted_by_design": [],
        }
        append_closed_finding(
            state,
            signature="sig-a",
            location="src/a.ts:10",
            finding="missing cleanup",
            status="fixed",
            closed_in_round=1,
            fix_shape="added dispose",
        )
        keep, defer = filter_post_fix_findings(
            [
                {
                    "signature": "sig-b",
                    "location": "src/b.ts:1",
                    "severity": "Medium",
                    "finding": "drive-by nit",
                },
                {
                    "signature": "sig-a2",
                    "location": "src/a.ts:99",
                    "severity": "High",
                    "finding": "related leak",
                },
            ],
            state,
        )
        assert len(keep) == 1
        assert keep[0]["location"] == "src/a.ts:99"
        assert len(defer) == 1
        assert defer[0]["location"] == "src/b.ts:1"
        assert defer[0]["_defer_reason"] == "post-fix verify"

    def test_recurrence_and_contested_always_kept(self) -> None:
        from _loop_state import append_closed_finding, filter_post_fix_findings

        state: dict = {
            "pr_number": 0,
            "closed_findings": [],
            "accepted_by_design": [],
        }
        append_closed_finding(
            state,
            signature="sig-a",
            location="src/a.ts:10",
            finding="x",
            status="fixed",
            closed_in_round=1,
            fix_shape="shape-a",
        )
        keep, defer = filter_post_fix_findings(
            [
                {
                    "signature": "sig-a",
                    "location": "src/elsewhere.ts:1",
                    "severity": "Medium",
                    "source": "recurrence",
                    "finding": "still broken",
                },
                {
                    "signature": "sig-c",
                    "location": "src/elsewhere.ts:2",
                    "severity": "Medium",
                    "source": "contested",
                    "finding": "prefer other shape",
                },
            ],
            state,
        )
        assert len(keep) == 2
        assert defer == []

    def test_critical_outside_surface_kept(self) -> None:
        from _loop_state import append_closed_finding, filter_post_fix_findings

        state: dict = {
            "pr_number": 0,
            "closed_findings": [],
            "accepted_by_design": [],
        }
        append_closed_finding(
            state,
            signature="sig-a",
            location="src/a.ts:10",
            finding="x",
            status="fixed",
            closed_in_round=1,
            fix_shape="shape-a",
        )
        keep, defer = filter_post_fix_findings(
            [
                {
                    "signature": "sig-crit",
                    "location": "src/secret.ts:1",
                    "severity": "Critical",
                    "finding": "hardcoded secret",
                }
            ],
            state,
        )
        assert len(keep) == 1
        assert keep[0]["severity"] == "Critical"
        assert defer == []

    def test_verify_surface_paths_strips_line(
        self, tmp_path: Path
    ) -> None:
        from _loop_state import (
            append_closed_finding,
            start_loop_state,
            verify_surface_paths,
        )

        state = start_loop_state(
            pr_number=99,
            pr_url="u",
            branch="b",
            root=tmp_path,
        )
        append_closed_finding(
            state,
            signature="sig",
            location="src/a.ts:10",
            finding="x",
            status="fixed",
            closed_in_round=1,
            fix_shape="shape",
            root=tmp_path,
        )
        surface = verify_surface_paths(state, fixer_paths=["src/dep.ts:3"])
        assert "src/a.ts" in surface
        assert "src/dep.ts" in surface
        assert "src/a.ts:10" not in surface


class TestRuntimeDirOutsideCursor:
    """Runtime cache lives in .review-loop/, not .cursor/."""

    def test_start_writes_under_dot_review_loop(self, tmp_path: Path) -> None:
        from _loop_state import STATE_DIR, start_loop_state

        start_loop_state(
            pr_number=1,
            pr_url="u",
            branch="b",
            root=tmp_path,
        )
        assert (tmp_path / STATE_DIR / "state.json").is_file()
        assert (tmp_path / STATE_DIR / "preferences.json").is_file()
        assert not (tmp_path / ".cursor" / "review-loop").exists()

    def test_migrates_legacy_cursor_dir(self, tmp_path: Path) -> None:
        from _loop_state import STATE_DIR, load_preferences, migrate_legacy_runtime_dir

        legacy = tmp_path / ".cursor" / "review-loop"
        legacy.mkdir(parents=True)
        (legacy / "preferences.json").write_text(
            '{"max_rounds": 9, "max_usd_est": 1.5}\n',
            encoding="utf-8",
        )
        (legacy / "closed-ledger.json").write_text(
            '{"by_pr": {"1": {"pr_number": 1, "closed_findings": [], '
            '"accepted_by_design": []}}}\n',
            encoding="utf-8",
        )
        migrate_legacy_runtime_dir(tmp_path)
        prefs = load_preferences(tmp_path)
        assert prefs["max_rounds"] == 9
        assert (tmp_path / STATE_DIR / "preferences.json").is_file()
        assert (tmp_path / STATE_DIR / "closed-ledger.json").is_file()

    def test_does_not_overwrite_newer_files(self, tmp_path: Path) -> None:
        from _loop_state import STATE_DIR, migrate_legacy_runtime_dir

        legacy = tmp_path / ".cursor" / "review-loop"
        legacy.mkdir(parents=True)
        (legacy / "preferences.json").write_text('{"max_rounds": 1}\n', encoding="utf-8")
        dest = tmp_path / STATE_DIR
        dest.mkdir(parents=True)
        (dest / "preferences.json").write_text('{"max_rounds": 99}\n', encoding="utf-8")
        migrate_legacy_runtime_dir(tmp_path)
        text = (dest / "preferences.json").read_text(encoding="utf-8")
        assert '"max_rounds": 99' in text
