"""
AI Cost Dashboard Service

Provides AI cost tracking and budget information for a world.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.utils.llm.budget import AIBudgetTracker

if TYPE_CHECKING:
    from src.classes.core.world import World


def get_ai_budget_tracker(world: World) -> Optional[AIBudgetTracker]:
    """
    Get or create the AI budget tracker for the current world.
    
    Args:
        world: Current world instance
        
    Returns:
        AIBudgetTracker instance or None if world has no budget config
    """
    # Check if budget tracking is enabled
    from src.utils.config import CONFIG
    
    recap_config = getattr(CONFIG, "recap", None) or {}
    ai_budget_config = getattr(CONFIG, "ai_budget", None) or {}
    
    if not ai_budget_config.get("enabled", False):
        return None
    
    # Check if world has a budget tracker stored
    ai_budget_data = getattr(world, "_ai_budget_tracker_data", None)
    
    if ai_budget_data is not None:
        try:
            return AIBudgetTracker.from_dict(ai_budget_data)
        except Exception:
            pass
    
    # Create new tracker with default/config values
    daily_budget_cents = ai_budget_config.get("daily_budget_cents", 5000)
    monthly_budget_cents = ai_budget_config.get("monthly_budget_cents", 100000)
    
    tracker = AIBudgetTracker(
        daily_budget_cents=daily_budget_cents,
        monthly_budget_cents=monthly_budget_cents,
    )
    
    # Store in world for future use
    world._ai_budget_tracker_data = tracker.to_dict()
    
    return tracker


def save_ai_budget_tracker(world: World, tracker: AIBudgetTracker) -> None:
    """
    Save AI budget tracker state to world.
    
    Args:
        world: Current world instance
        tracker: Updated budget tracker
    """
    world._ai_budget_tracker_data = tracker.to_dict()


def build_ai_cost_dashboard(world: World) -> dict:
    """
    Build AI cost dashboard for monitoring.
    
    Args:
        world: Current world instance
        
    Returns:
        Dashboard dict with budget info, task breakdown, and recommendations
    """
    tracker = get_ai_budget_tracker(world)
    
    if tracker is None:
        return {
            "enabled": False,
            "message": "AI budget tracking is not enabled for this world",
        }
    
    summary = tracker.get_budget_summary()
    
    # Add recommendations
    recommendations = []
    if summary["daily"]["is_exhausted"]:
        recommendations.append({
            "type": "warning",
            "message": "Daily AI budget is exhausted. Using fallback heuristics.",
            "action": "Consider increasing daily_budget_cents or reducing simulation cadence.",
        })
    
    if summary["degradation_mode"]:
        recommendations.append({
            "type": "info",
            "message": "AI degradation mode active - using rule-based fallbacks for some tasks.",
            "action": "This is expected behavior when budget is exhausted.",
        })
    
    if summary["daily"]["remaining_pct"] < 20 and not summary["daily"]["is_exhausted"]:
        recommendations.append({
            "type": "warning",
            "message": f"Only {summary['daily']['remaining_pct']}% of daily AI budget remaining.",
            "action": "Consider reducing LLM-heavy tasks for the rest of the day.",
        })
    
    # Top cost tasks
    task_breakdown = summary.get("task_breakdown", {})
    top_tasks = sorted(
        task_breakdown.items(),
        key=lambda x: x[1].get("cost_cents", 0),
        reverse=True,
    )[:5]
    
    return {
        "enabled": True,
        "daily": summary["daily"],
        "monthly": summary["monthly"],
        "degradation_mode": summary["degradation_mode"],
        "top_cost_tasks": [
            {
                "task_name": name,
                "cost_cents": data.get("cost_cents", 0),
                "input_tokens": data.get("input_tokens", 0),
                "output_tokens": data.get("output_tokens", 0),
            }
            for name, data in top_tasks
        ],
        "recommendations": recommendations,
    }
