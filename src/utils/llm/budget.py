"""
AI Budget Tracker

Per-world AI budget tracking with graceful degradation.
Tracks token usage, cost, and enforces daily budget caps.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


# Estimated cost per 1M tokens (USD) - adjust based on provider
# DeepSeek: $0.14/1M input, $0.28/1M output (as of 2026-04)
DEFAULT_COST_PER_1M_INPUT_TOKENS = 0.14
DEFAULT_COST_PER_1M_OUTPUT_TOKENS = 0.28


@dataclass
class AIBudgetState:
    """Tracks AI budget state for a single world."""
    
    # Budget limits
    daily_budget_cents: int = 5000  # $50/day default
    monthly_budget_cents: int = 100000  # $1000/month default
    
    # Current usage tracking
    current_day_start_timestamp: float = field(default_factory=time.time)
    current_month_start_timestamp: float = field(default_factory=time.time)
    
    # Daily usage
    daily_input_tokens: int = 0
    daily_output_tokens: int = 0
    daily_cost_cents: int = 0  # Actual cost in cents
    
    # Monthly usage
    monthly_input_tokens: int = 0
    monthly_output_tokens: int = 0
    monthly_cost_cents: int = 0
    
    # Per-task breakdown (for analytics)
    task_usage: dict[str, dict[str, int]] = field(default_factory=dict)
    # Structure: {task_name: {"input_tokens": N, "output_tokens": N, "cost_cents": N}}
    
    # Graceful degradation state
    degradation_mode: bool = False  # True when budget exhausted, using fallbacks
    fallback_count_today: int = 0  # How many calls fell back today
    total_calls_today: int = 0  # Total calls attempted today
    
    # Budget warnings
    warning_threshold_pct: int = 80  # Warn at 80% of budget
    has_warned_today: bool = False
    
    @property
    def daily_budget_remaining_pct(self) -> float:
        """Percentage of daily budget remaining."""
        if self.daily_budget_cents <= 0:
            return 0.0
        remaining = max(0, self.daily_budget_cents - self.daily_cost_cents)
        return (remaining / self.daily_budget_cents) * 100
    
    @property
    def monthly_budget_remaining_pct(self) -> float:
        """Percentage of monthly budget remaining."""
        if self.monthly_budget_cents <= 0:
            return 0.0
        remaining = max(0, self.monthly_budget_cents - self.monthly_cost_cents)
        return (remaining / self.monthly_budget_cents) * 100
    
    @property
    def is_daily_budget_exhausted(self) -> bool:
        """Check if daily budget is exhausted."""
        return self.daily_cost_cents >= self.daily_budget_cents
    
    @property
    def is_monthly_budget_exhausted(self) -> bool:
        """Check if monthly budget is exhausted."""
        return self.monthly_cost_cents >= self.monthly_budget_cents
    
    @property
    def should_warn(self) -> bool:
        """Check if we should warn about approaching budget limit."""
        if self.has_warned_today:
            return False
        return self.daily_budget_remaining_pct <= (100 - self.warning_threshold_pct)


class AIBudgetTracker:
    """
    Per-world AI budget tracker with graceful degradation.
    
    Usage:
        tracker = AIBudgetTracker(daily_budget_cents=5000)
        
        # Before making LLM call
        if tracker.is_daily_budget_exhausted:
            # Use fallback/heuristic instead
            return fallback_response()
        
        # After LLM call
        tracker.record_usage(
            task_name="action_decision",
            input_tokens=150,
            output_tokens=80,
            cost_cents=3
        )
    """
    
    def __init__(
        self,
        *,
        daily_budget_cents: int = 5000,
        monthly_budget_cents: int = 100000,
        cost_per_1m_input_tokens_cents: int = int(DEFAULT_COST_PER_1M_INPUT_TOKENS * 100),
        cost_per_1m_output_tokens_cents: int = int(DEFAULT_COST_PER_1M_OUTPUT_TOKENS * 100),
    ):
        self.state = AIBudgetState(
            daily_budget_cents=daily_budget_cents,
            monthly_budget_cents=monthly_budget_cents,
        )
        self.cost_per_1m_input_tokens_cents = cost_per_1m_input_tokens_cents
        self.cost_per_1m_output_tokens_cents = cost_per_1m_output_tokens_cents
    
    def reset_daily_if_new_day(self) -> None:
        """Reset daily counters if it's a new day."""
        now = time.time()
        seconds_in_day = 86400
        
        if now - self.state.current_day_start_timestamp >= seconds_in_day:
            self.state.current_day_start_timestamp = now
            self.state.daily_input_tokens = 0
            self.state.daily_output_tokens = 0
            self.state.daily_cost_cents = 0
            self.state.fallback_count_today = 0
            self.state.total_calls_today = 0
            self.state.has_warned_today = False
            self.state.degradation_mode = False
    
    def reset_monthly_if_new_month(self) -> None:
        """Reset monthly counters if it's a new month."""
        now = time.time()
        seconds_in_month = 86400 * 30  # Approximate
        
        if now - self.state.current_month_start_timestamp >= seconds_in_month:
            self.state.current_month_start_timestamp = now
            self.state.monthly_input_tokens = 0
            self.state.monthly_output_tokens = 0
            self.state.monthly_cost_cents = 0
    
    def should_allow_llm_call(self) -> tuple[bool, str]:
        """
        Check if LLM call should be allowed based on budget.
        
        Returns:
            (allowed: bool, reason: str)
        """
        self.reset_daily_if_new_day()
        self.reset_monthly_if_new_month()
        
        if self.state.is_daily_budget_exhausted:
            return False, "daily_budget_exhausted"
        
        if self.state.is_monthly_budget_exhausted:
            return False, "monthly_budget_exhausted"
        
        # Check warning threshold
        if self.state.should_warn:
            self.state.has_warned_today = True
            return True, "budget_warning"
        
        return True, "ok"
    
    def record_usage(
        self,
        *,
        task_name: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """
        Record AI usage after a successful LLM call.
        
        Args:
            task_name: Name of the task (e.g., "action_decision", "story_teller")
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
        """
        # Calculate cost
        input_cost_cents = (input_tokens * self.cost_per_1m_input_tokens_cents) // 1_000_000
        output_cost_cents = (output_tokens * self.cost_per_1m_output_tokens_cents) // 1_000_000
        total_cost_cents = input_cost_cents + output_cost_cents
        
        # Update daily counters
        self.state.daily_input_tokens += input_tokens
        self.state.daily_output_tokens += output_tokens
        self.state.daily_cost_cents += total_cost_cents
        self.state.total_calls_today += 1
        
        # Update monthly counters
        self.state.monthly_input_tokens += input_tokens
        self.state.monthly_output_tokens += output_tokens
        self.state.monthly_cost_cents += total_cost_cents
        
        # Update per-task breakdown
        if task_name not in self.state.task_usage:
            self.state.task_usage[task_name] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_cents": 0,
            }
        self.state.task_usage[task_name]["input_tokens"] += input_tokens
        self.state.task_usage[task_name]["output_tokens"] += output_tokens
        self.state.task_usage[task_name]["cost_cents"] += total_cost_cents
        
        # Check if budget is now exhausted
        if self.state.is_daily_budget_exhausted:
            self.state.degradation_mode = True
    
    def record_fallback(self, task_name: str) -> None:
        """Record that a fallback/heuristic was used instead of LLM."""
        self.state.total_calls_today += 1
        self.state.fallback_count_today += 1
    
    def get_budget_summary(self) -> dict:
        """Get comprehensive budget summary for dashboard."""
        self.reset_daily_if_new_day()
        self.reset_monthly_if_new_month()
        
        return {
            "daily": {
                "budget_cents": self.state.daily_budget_cents,
                "used_cents": self.state.daily_cost_cents,
                "remaining_cents": max(0, self.state.daily_budget_cents - self.state.daily_cost_cents),
                "remaining_pct": round(self.state.daily_budget_remaining_pct, 1),
                "input_tokens": self.state.daily_input_tokens,
                "output_tokens": self.state.daily_output_tokens,
                "total_calls": self.state.total_calls_today,
                "fallback_calls": self.state.fallback_count_today,
                "is_exhausted": self.state.is_daily_budget_exhausted,
            },
            "monthly": {
                "budget_cents": self.state.monthly_budget_cents,
                "used_cents": self.state.monthly_cost_cents,
                "remaining_cents": max(0, self.state.monthly_budget_cents - self.state.monthly_cost_cents),
                "remaining_pct": round(self.state.monthly_budget_remaining_pct, 1),
                "input_tokens": self.state.monthly_input_tokens,
                "output_tokens": self.state.monthly_output_tokens,
                "is_exhausted": self.state.is_monthly_budget_exhausted,
            },
            "degradation_mode": self.state.degradation_mode,
            "task_breakdown": dict(self.state.task_usage),
        }
    
    def to_dict(self) -> dict:
        """Serialize state for saving."""
        return {
            "daily_budget_cents": self.state.daily_budget_cents,
            "monthly_budget_cents": self.state.monthly_budget_cents,
            "current_day_start_timestamp": self.state.current_day_start_timestamp,
            "current_month_start_timestamp": self.state.current_month_start_timestamp,
            "daily_input_tokens": self.state.daily_input_tokens,
            "daily_output_tokens": self.state.daily_output_tokens,
            "daily_cost_cents": self.state.daily_cost_cents,
            "monthly_input_tokens": self.state.monthly_input_tokens,
            "monthly_output_tokens": self.state.monthly_output_tokens,
            "monthly_cost_cents": self.state.monthly_cost_cents,
            "task_usage": dict(self.state.task_usage),
            "degradation_mode": self.state.degradation_mode,
            "fallback_count_today": self.state.fallback_count_today,
            "total_calls_today": self.state.total_calls_today,
            "has_warned_today": self.state.has_warned_today,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AIBudgetTracker":
        """Deserialize state from saved data."""
        tracker = cls(
            daily_budget_cents=data.get("daily_budget_cents", 5000),
            monthly_budget_cents=data.get("monthly_budget_cents", 100000),
        )
        
        state = tracker.state
        state.current_day_start_timestamp = data.get("current_day_start_timestamp", time.time())
        state.current_month_start_timestamp = data.get("current_month_start_timestamp", time.time())
        state.daily_input_tokens = data.get("daily_input_tokens", 0)
        state.daily_output_tokens = data.get("daily_output_tokens", 0)
        state.daily_cost_cents = data.get("daily_cost_cents", 0)
        state.monthly_input_tokens = data.get("monthly_input_tokens", 0)
        state.monthly_output_tokens = data.get("monthly_output_tokens", 0)
        state.monthly_cost_cents = data.get("monthly_cost_cents", 0)
        state.task_usage = dict(data.get("task_usage", {}))
        state.degradation_mode = data.get("degradation_mode", False)
        state.fallback_count_today = data.get("fallback_count_today", 0)
        state.total_calls_today = data.get("total_calls_today", 0)
        state.has_warned_today = data.get("has_warned_today", False)
        
        return tracker
