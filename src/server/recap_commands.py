"""
Recap command handlers for the public API.

Handles recap acknowledgment and action point spending.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.services.recap_service import RecapService

if TYPE_CHECKING:
    from src.classes.core.world import World


def handle_acknowledge_recap(world: World, viewer_id: str) -> dict:
    """
    Handle player acknowledging recap and refreshing action points.
    
    Args:
        world: Current world instance
        viewer_id: Player's viewer ID
        
    Returns:
        Updated player state
    """
    service = RecapService(world)
    
    # Acknowledge recap (updates timestamps and refreshes action points)
    player_state = service.acknowledge_recap(
        viewer_id=viewer_id,
        current_month=world.month_stamp,
    )
    
    return {
        "last_recap_month_stamp": player_state.last_recap_month_stamp,
        "last_acknowledge_month_stamp": player_state.last_acknowledge_month_stamp,
        "action_points": {
            "total": player_state.action_points_total,
            "spent": player_state.action_points_spent,
            "remaining": player_state.action_points_total - player_state.action_points_spent,
        },
    }


def handle_spend_action_point(world: World, viewer_id: str) -> dict:
    """
    Handle spending one action point.
    
    Args:
        world: Current world instance
        viewer_id: Player's viewer ID
        
    Returns:
        Updated action points state
        
    Raises:
        ValueError if no action points remaining
    """
    service = RecapService(world)
    
    # Try to spend action point
    success = service.spend_action_point(viewer_id)
    if not success:
        raise ValueError("No action points remaining")
    
    remaining, total = service.get_action_points_remaining(viewer_id)
    
    return {
        "action_points": {
            "total": total,
            "spent": total - remaining,
            "remaining": remaining,
        },
    }
