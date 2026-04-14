"""
AI Cost Dashboard Service

Provides AI usage monitoring and budget tracking for online operation.
Integrates with AIBudgetTracker to provide real-time cost visibility.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from src.classes.core.world import World


def get_ai_budget_tracker(world: World) -> Optional[Any]:
    """
    Get or create the AI budget tracker from world state.
    
    Args:
        world: Current world instance
        
    Returns:
        AIBudgetTracker instance or None if not initialized
    """
    try:
        from src.utils.llm.budget import AIBudgetTracker
        
        # Check if world has budget tracker stored
        budget_data = getattr(world, '_ai_budget_tracker', None)
        
        if budget_data is not None:
            if isinstance(budget_data, AIBudgetTracker):
                return budget_data
            elif isinstance(budget_data, dict):
                # Deserialize from saved state
                return AIBudgetTracker.from_dict(budget_data)
        
        # Create new tracker with defaults
        tracker = AIBudgetTracker(
            daily_budget_cents=5000,  # $50/day default
            monthly_budget_cents=100000,  # $1000/month default
        )
        
        # Store in world for future use
        world._ai_budget_tracker = tracker
        
        return tracker
    except Exception:
        # Budget tracking not available
        return None


def save_ai_budget_tracker(world: World, tracker: Any) -> None:
    """
    Save AI budget tracker state to world for persistence.
    
    Args:
        world: Current world instance
        tracker: AIBudgetTracker instance to save
    """
    try:
        world._ai_budget_tracker = tracker.to_dict()
    except Exception:
        pass


def build_ai_cost_dashboard(world: World) -> Dict[str, Any]:
    """
    Build AI cost dashboard for monitoring and alerts.
    
    Args:
        world: Current world instance
        
    Returns:
        Dashboard dict with budget info, usage stats, and recommendations
    """
    tracker = get_ai_budget_tracker(world)
    
    if tracker is None:
        return {
            "enabled": False,
            "message": "AI budget tracking not available",
        }
    
    summary = tracker.get_budget_summary()
    
    # Build recommendations
    recommendations = []
    
    if summary["daily"]["is_exhausted"]:
        recommendations.append({
            "type": "warning",
            "message": "Daily AI budget exhausted. Using fallback heuristics.",
            "action": "Consider increasing daily_budget_cents or reducing simulation cadence.",
        })
    
    if summary["degradation_mode"]:
        recommendations.append({
            "type": "info",
            "message": "AI degradation mode active - some tasks using rule-based fallbacks.",
            "action": "This is normal when budget is exhausted. Game continues with lower AI cost.",
        })
    
    if summary["daily"]["remaining_pct"] < 20 and not summary["daily"]["is_exhausted"]:
        recommendations.append({
            "type": "warning",
            "message": f"Only {summary['daily']['remaining_pct']}% of daily AI budget remaining.",
            "action": "Consider reducing AI-heavy tasks for the rest of the day.",
        })
    
    if summary["monthly"]["remaining_pct"] < 30 and not summary["monthly"]["is_exhausted"]:
        recommendations.append({
            "type": "warning",
            "message": f"Only {summary['monthly']['remaining_pct']}% of monthly AI budget remaining.",
            "action": "Review AI usage patterns and consider adjusting budget or simulation cadence.",
        })
    
    # Get top cost tasks
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
                "input_tokens": data.get("input_tokens", 0),
                "output_tokens": data.get("output_tokens", 0),
                "cost_cents": data.get("cost_cents", 0),
            }
            for name, data in top_tasks
        ],
        "fallback_calls": summary.get("fallback_calls", 0),
        "recommendations": recommendations,
    }
