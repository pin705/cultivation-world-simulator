"""
Tests for AI Budget Tracker.

Covers:
- AIBudgetTracker: budget tracking, degradation, serialization
- Budget enforcement: graceful degradation when budget exhausted
- AI cost dashboard: summary generation, recommendations
"""

import pytest
import time
from unittest.mock import MagicMock, patch

from src.utils.llm.budget import AIBudgetTracker, AIBudgetState


# --- Fixtures ---

@pytest.fixture
def tracker():
    """Create a budget tracker with realistic values."""
    return AIBudgetTracker(
        daily_budget_cents=5000,  # $50/day
        monthly_budget_cents=100000,  # $1000/month
        cost_per_1m_input_tokens_cents=14,
        cost_per_1m_output_tokens_cents=28,
    )


# --- Tests for AIBudgetState ---

class TestAIBudgetState:
    """Test AIBudgetState dataclass."""

    def test_daily_budget_remaining_pct(self):
        state = AIBudgetState(daily_budget_cents=100, daily_cost_cents=30)
        assert state.daily_budget_remaining_pct == 70.0

    def test_daily_budget_remaining_pct_full(self):
        state = AIBudgetState(daily_budget_cents=100, daily_cost_cents=0)
        assert state.daily_budget_remaining_pct == 100.0

    def test_daily_budget_remaining_pct_zero(self):
        state = AIBudgetState(daily_budget_cents=100, daily_cost_cents=100)
        assert state.daily_budget_remaining_pct == 0.0

    def test_monthly_budget_remaining_pct(self):
        state = AIBudgetState(monthly_budget_cents=1000, monthly_cost_cents=200)
        assert state.monthly_budget_remaining_pct == 80.0

    def test_is_daily_budget_exhausted(self):
        state = AIBudgetState(daily_budget_cents=100, daily_cost_cents=100)
        assert state.is_daily_budget_exhausted is True

    def test_is_daily_budget_not_exhausted(self):
        state = AIBudgetState(daily_budget_cents=100, daily_cost_cents=50)
        assert state.is_daily_budget_exhausted is False

    def test_is_monthly_budget_exhausted(self):
        state = AIBudgetState(monthly_budget_cents=1000, monthly_cost_cents=1000)
        assert state.is_monthly_budget_exhausted is True

    def test_should_warn(self):
        state = AIBudgetState(
            daily_budget_cents=100,
            daily_cost_cents=85,
            warning_threshold_pct=80,
            has_warned_today=False,
        )
        assert state.should_warn is True

    def test_should_warn_already_warned(self):
        state = AIBudgetState(
            daily_budget_cents=100,
            daily_cost_cents=85,
            warning_threshold_pct=80,
            has_warned_today=True,
        )
        assert state.should_warn is False

    def test_should_warn_not_yet(self):
        state = AIBudgetState(
            daily_budget_cents=100,
            daily_cost_cents=50,
            warning_threshold_pct=80,
            has_warned_today=False,
        )
        assert state.should_warn is False


# --- Tests for AIBudgetTracker ---

class TestAIBudgetTrackerInitialization:
    """Test AIBudgetTracker initialization."""

    def test_init_with_defaults(self):
        tracker = AIBudgetTracker()
        assert tracker.state.daily_budget_cents == 5000
        assert tracker.state.monthly_budget_cents == 100000

    def test_init_with_custom_budgets(self):
        tracker = AIBudgetTracker(daily_budget_cents=200, monthly_budget_cents=500)
        assert tracker.state.daily_budget_cents == 200
        assert tracker.state.monthly_budget_cents == 500


class TestBudgetAllowance:
    """Test budget allowance checks."""

    def test_should_allow_when_budget_available(self, tracker):
        """Should allow call when budget is available."""
        allowed, reason = tracker.should_allow_llm_call()
        assert allowed is True
        assert reason == "ok"

    def test_should_deny_when_daily_exhausted(self, tracker):
        """Should deny call when daily budget is exhausted."""
        tracker.state.daily_cost_cents = 5000  # Equal to budget
        allowed, reason = tracker.should_allow_llm_call()
        assert allowed is False
        assert reason == "daily_budget_exhausted"

    def test_should_deny_when_monthly_exhausted(self, tracker):
        """Should deny call when monthly budget is exhausted."""
        tracker.state.monthly_cost_cents = 100000  # Equal to budget
        allowed, reason = tracker.should_allow_llm_call()
        assert allowed is False
        assert reason == "monthly_budget_exhausted"

    def test_should_warn_when_approaching_limit(self):
        """Should trigger warning when approaching budget limit."""
        tracker = AIBudgetTracker(daily_budget_cents=100, monthly_budget_cents=1000)
        tracker.state.daily_cost_cents = 85  # 85% used
        tracker.state.has_warned_today = False

        allowed, reason = tracker.should_allow_llm_call()
        assert allowed is True
        assert reason == "budget_warning"
        assert tracker.state.has_warned_today is True


class TestUsageRecording:
    """Test usage recording."""

    def test_record_usage_updates_daily(self, tracker):
        """Should update daily counters."""
        # Use large token counts to get actual costs
        tracker.record_usage(task_name="action_decision", input_tokens=100000, output_tokens=50000)

        assert tracker.state.daily_input_tokens == 100000
        assert tracker.state.daily_output_tokens == 50000
        assert tracker.state.daily_cost_cents > 0
        assert tracker.state.total_calls_today == 1

    def test_record_usage_updates_monthly(self, tracker):
        """Should update monthly counters."""
        tracker.record_usage(task_name="action_decision", input_tokens=100000, output_tokens=50000)

        assert tracker.state.monthly_input_tokens == 100000
        assert tracker.state.monthly_output_tokens == 50000
        assert tracker.state.monthly_cost_cents > 0

    def test_record_updates_task_breakdown(self, tracker):
        """Should track per-task usage."""
        tracker.record_usage(task_name="action_decision", input_tokens=100000, output_tokens=50000)
        tracker.record_usage(task_name="story_teller", input_tokens=200000, output_tokens=100000)

        assert "action_decision" in tracker.state.task_usage
        assert "story_teller" in tracker.state.task_usage
        assert tracker.state.task_usage["action_decision"]["input_tokens"] == 100000
        assert tracker.state.task_usage["story_teller"]["input_tokens"] == 200000

    def test_record_multiple_calls_same_task(self, tracker):
        """Should accumulate usage for same task."""
        tracker.record_usage(task_name="action_decision", input_tokens=100000, output_tokens=50000)
        tracker.record_usage(task_name="action_decision", input_tokens=150000, output_tokens=75000)

        assert tracker.state.task_usage["action_decision"]["input_tokens"] == 250000
        assert tracker.state.task_usage["action_decision"]["output_tokens"] == 125000

    def test_record_fallback(self, tracker):
        """Should record fallback usage."""
        tracker.record_fallback("action_decision")

        assert tracker.state.total_calls_today == 1
        assert tracker.state.fallback_count_today == 1


class TestBudgetExhaustion:
    """Test budget exhaustion behavior."""

    def test_degradation_mode_when_daily_exhausted(self, tracker):
        """Should enter degradation mode when daily budget is exhausted."""
        tracker.state.daily_cost_cents = 4999  # Just under budget
        assert tracker.state.degradation_mode is False

        # Record usage that will push it over
        tracker.record_usage(task_name="action_decision", input_tokens=100000, output_tokens=50000)

        # Budget should be exceeded now
        assert tracker.state.daily_cost_cents >= tracker.state.daily_budget_cents
        assert tracker.state.degradation_mode is True

    def test_should_allow_after_exhaustion(self, tracker):
        """Should deny calls after budget is exhausted."""
        # Exhaust budget
        tracker.state.daily_cost_cents = 5000

        allowed, reason = tracker.should_allow_llm_call()
        assert allowed is False
        assert reason == "daily_budget_exhausted"


class TestDailyReset:
    """Test daily counter reset."""

    def test_reset_daily_if_new_day(self, tracker):
        """Should reset daily counters if it's a new day."""
        # Set day start to 2 days ago
        tracker.state.current_day_start_timestamp = time.time() - (2 * 86400)
        tracker.state.daily_cost_cents = 2500
        tracker.state.total_calls_today = 10

        tracker.reset_daily_if_new_day()

        assert tracker.state.daily_cost_cents == 0
        assert tracker.state.total_calls_today == 0
        # Day start should be recent (within last second)
        assert time.time() - tracker.state.current_day_start_timestamp < 1

    def test_no_reset_if_same_day(self, tracker):
        """Should not reset if still same day."""
        tracker.state.current_day_start_timestamp = time.time() - 3600  # 1 hour ago
        tracker.state.daily_cost_cents = 2500

        tracker.reset_daily_if_new_day()

        assert tracker.state.daily_cost_cents == 2500  # Unchanged


class TestMonthlyReset:
    """Test monthly counter reset."""

    def test_reset_monthly_if_new_month(self, tracker):
        """Should reset monthly counters if it's a new month."""
        # Set month start to 2 months ago
        tracker.state.current_month_start_timestamp = time.time() - (60 * 86400)
        tracker.state.monthly_cost_cents = 50000

        tracker.reset_monthly_if_new_month()

        assert tracker.state.monthly_cost_cents == 0


class TestSerialization:
    """Test serialization/deserialization."""

    def test_to_dict_contains_all_fields(self, tracker):
        """to_dict should contain all necessary fields."""
        tracker.state.daily_cost_cents = 2500
        tracker.state.monthly_cost_cents = 50000

        data = tracker.to_dict()

        assert data["daily_budget_cents"] == 5000
        assert data["daily_cost_cents"] == 2500
        assert data["monthly_budget_cents"] == 100000
        assert data["monthly_cost_cents"] == 50000

    def test_from_dict_restores_state(self, tracker):
        """from_dict should restore tracker state."""
        tracker.record_usage(task_name="action_decision", input_tokens=100000, output_tokens=50000)

        data = tracker.to_dict()
        restored = AIBudgetTracker.from_dict(data)

        assert restored.state.daily_cost_cents == tracker.state.daily_cost_cents
        assert restored.state.monthly_input_tokens == tracker.state.monthly_input_tokens
        assert "action_decision" in restored.state.task_usage

    def test_round_trip_preserves_data(self):
        """Round-trip serialization should preserve all data."""
        original = AIBudgetTracker(
            daily_budget_cents=200,
            monthly_budget_cents=2000,
        )
        original.record_usage(task_name="action_decision", input_tokens=100000, output_tokens=50000)
        original.record_usage(task_name="story_teller", input_tokens=200000, output_tokens=100000)
        original.record_fallback("action_decision")

        data = original.to_dict()
        restored = AIBudgetTracker.from_dict(data)

        assert restored.state.daily_budget_cents == 200
        assert restored.state.monthly_budget_cents == 2000
        assert restored.state.daily_input_tokens == 300000
        assert restored.state.fallback_count_today == 1


class TestBudgetSummary:
    """Test budget summary generation."""

    def test_summary_structure(self, tracker):
        """Summary should have correct structure."""
        tracker.record_usage(task_name="action_decision", input_tokens=100000, output_tokens=50000)

        summary = tracker.get_budget_summary()

        assert "daily" in summary
        assert "monthly" in summary
        assert "degradation_mode" in summary
        assert "task_breakdown" in summary

    def test_summary_daily_fields(self, tracker):
        """Daily summary should have all required fields."""
        tracker.record_usage(task_name="action_decision", input_tokens=100000, output_tokens=50000)

        summary = tracker.get_budget_summary()
        daily = summary["daily"]

        assert "budget_cents" in daily
        assert "used_cents" in daily
        assert "remaining_cents" in daily
        assert "remaining_pct" in daily
        assert "input_tokens" in daily
        assert "output_tokens" in daily
        assert "total_calls" in daily
        assert "fallback_calls" in daily
        assert "is_exhausted" in daily

    def test_summary_monthly_fields(self, tracker):
        """Monthly summary should have all required fields."""
        summary = tracker.get_budget_summary()
        monthly = summary["monthly"]

        assert "budget_cents" in monthly
        assert "used_cents" in monthly
        assert "remaining_cents" in monthly
        assert "remaining_pct" in monthly
        assert "input_tokens" in monthly
        assert "output_tokens" in monthly
        assert "is_exhausted" in monthly

    def test_summary_task_breakdown(self, tracker):
        """Summary should include task breakdown."""
        tracker.record_usage(task_name="action_decision", input_tokens=100000, output_tokens=50000)

        summary = tracker.get_budget_summary()

        assert "action_decision" in summary["task_breakdown"]
        assert summary["task_breakdown"]["action_decision"]["input_tokens"] == 100000
