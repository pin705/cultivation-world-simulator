"""
Recap query builder for the public API.

Provides recap data for the recap-first gameplay loop.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.services.recap_service import RecapService

if TYPE_CHECKING:
    from src.classes.core.world import World


def build_recap_query(world: World, viewer_id: str) -> dict:
    """
    Build recap query response.
    
    Args:
        world: Current world instance
        viewer_id: Player's viewer ID
        
    Returns:
        Recap data dictionary for API response
    """
    service = RecapService(world)
    
    # Generate recap (no LLM summary in Phase 1)
    recap = service.generate_recap(
        viewer_id=viewer_id,
        generate_summary=False,
    )
    
    # Get action points remaining
    remaining, total = service.get_action_points_remaining(viewer_id)
    
    # Build response
    result = {
        "period_text": recap.period_text,
        "has_unread_recap": recap.has_unread_recap,
        "action_points": {
            "remaining": remaining,
            "total": total,
        },
    }
    
    # Sect section
    if recap.sect:
        result["sect"] = {
            "sect_id": recap.sect.sect_id,
            "sect_name": recap.sect.sect_name,
            "status_changes": recap.sect.status_changes[:10],  # Limit for performance
            "member_events": recap.sect.member_events[:10],
            "resource_changes": recap.sect.resource_changes[:10],
            "threats": recap.sect.threats[:5],
        }
    
    # Main disciple section
    if recap.main_disciple:
        result["main_disciple"] = {
            "avatar_id": recap.main_disciple.avatar_id,
            "name": recap.main_disciple.name,
            "cultivation_progress": recap.main_disciple.cultivation_progress,
            "major_events": recap.main_disciple.major_events[:10],
            "relationships": recap.main_disciple.relationships[:10],
            "current_status": recap.main_disciple.current_status,
        }
    
    # World section
    result["world"] = {
        "major_events": recap.world.major_events[:15],
        "sect_relations": recap.world.sect_relations[:10],
        "phenomenon": recap.world.phenomenon,
        "rankings_changed": recap.world.rankings_changed,
    }
    
    # Opportunities section
    result["opportunities"] = {
        "opportunities": recap.opportunities.opportunities[:5],
        "pending_decisions": recap.opportunities.pending_decisions[:5],
        "suggested_actions": recap.opportunities.suggested_actions[:5],
    }
    
    # Summary text
    if recap.summary_text:
        result["summary_text"] = recap.summary_text
    
    return result
